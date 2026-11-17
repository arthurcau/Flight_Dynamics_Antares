"""Conservative, segment-local observations from audited telemetry tables."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd


ALTITUDE_CHANNELS = ("bmp1_rel_alt_m", "bmp2_rel_alt_m")


def build_observed_section(
    samples: pd.DataFrame,
    segments: pd.DataFrame,
    *,
    section_marker: str,
    altitude_channels: tuple[str, str] = ALTITUDE_CHANNELS,
    timebase_diagnostics: pd.DataFrame | None = None,
    duplicate_blocks: list[dict] | None = None,
) -> tuple[pd.DataFrame, dict, dict]:
    """Derive only recorded relative-altitude observations and interval rates.

    The source order, clock segment, and source line remain explicit. Interval
    rates are secants between samples, not instantaneous inertial velocity.
    A recorded altitude extremum is distinct from a physical apogee estimate.
    """

    selected = samples.loc[samples["section_marker"].eq(section_marker)].copy()
    if selected.empty:
        raise ValueError(f"No audited samples carry section marker {section_marker!r}")
    channels = ("time_ms", *altitude_channels)
    selected = selected.loc[selected["raw_channel_name"].isin(channels)]
    if set(selected["raw_channel_name"]) != set(channels):
        raise ValueError("The marked section lacks a required time or altitude channel")
    if selected.duplicated(["record_index", "raw_channel_name"]).any():
        raise ValueError("Audited samples contain duplicate record/channel keys")
    origins = selected.loc[selected["raw_channel_name"].isin(altitude_channels), "data_origin"].dropna().unique()
    if len(origins) != 1 or origins[0] != "DERIVED":
        raise ValueError("Altitude channels must be labeled DERIVED in the audit")

    wide = selected.pivot(index="record_index", columns="raw_channel_name", values="numeric_value")
    lineage = selected.loc[selected["raw_channel_name"].eq("time_ms"), ["record_index", "source_line_number"]]
    frame = lineage.merge(wide.reset_index(), on="record_index", validate="one_to_one")
    frame = frame.merge(
        segments[["record_index", "segment_id", "raw_time", "segment_elapsed_s"]],
        on="record_index", validate="one_to_one",
    ).sort_values("record_index", kind="stable").reset_index(drop=True)
    if timebase_diagnostics is not None:
        diagnostics = timebase_diagnostics[["record_index", "interval_class"]]
        if diagnostics["record_index"].duplicated().any():
            raise ValueError("Timebase diagnostics contain duplicate record IDs")
        frame = frame.merge(diagnostics, on="record_index", validate="one_to_one")
    else:
        frame["interval_class"] = "AUDIT_CLASS_UNAVAILABLE"

    duplicate_of: dict[int, tuple[int, str]] = {}
    for block in duplicate_blocks or []:
        duplicate_start = int(block["duplicate_start_record_index"])
        duplicate_end = int(block["duplicate_end_record_index"])
        original_start = int(block["original_start_record_index"])
        original_end = int(block["original_end_record_index"])
        if duplicate_end - duplicate_start != original_end - original_start:
            raise ValueError("Exact-duplicate block has inconsistent original and copy lengths")
        for copy_index in range(duplicate_start, duplicate_end + 1):
            lineage = (original_start + copy_index - duplicate_start, str(block.get("mechanism", "UNKNOWN")))
            if copy_index in duplicate_of and duplicate_of[copy_index] != lineage:
                raise ValueError(f"Conflicting exact-duplicate lineage for record {copy_index}")
            duplicate_of[copy_index] = lineage
    frame["is_exact_duplicate_copy"] = frame["record_index"].isin(duplicate_of)
    frame["duplicate_of_record_index"] = pd.array(
        [duplicate_of.get(int(index), (None, None))[0] for index in frame["record_index"]],
        dtype="Int64",
    )
    frame["duplicate_mechanism"] = [
        duplicate_of.get(int(index), (None, "NOT_IDENTIFIED_AS_DUPLICATE"))[1]
        for index in frame["record_index"]
    ]
    if frame["segment_id"].nunique(dropna=False) != 1:
        raise ValueError("Marked section spans multiple clock segments; explicit alignment is required")
    if frame["segment_elapsed_s"].isna().any() or not np.isfinite(frame["segment_elapsed_s"]).all():
        raise ValueError("Marked section has missing or unsupported clock values")
    if (frame["segment_elapsed_s"].diff().dropna() <= 0).any():
        raise ValueError("Marked section clock is not strictly increasing")
    if not np.allclose(frame["time_ms"], frame["raw_time"], equal_nan=True):
        raise ValueError("Audited sample and segment raw timestamps disagree")

    frame["section_elapsed_s"] = frame["segment_elapsed_s"] - frame["segment_elapsed_s"].iloc[0]
    frame["interval_duration_s"] = frame["section_elapsed_s"].diff()
    interval_quality = {
        "FIRST_SAMPLE": "FIRST_SAMPLE",
        "NORMAL_INTERVAL": "NORMAL_INTERVAL",
        "TIMESTAMP_GAP": "LONG_INTERVAL_RETAINED",
        "INTERVAL_ACROSS_MISSING_TIMESTAMP": "INTERVAL_ACROSS_MISSING_TIMESTAMP_RETAINED",
        "DUPLICATE_TIMESTAMP": "DUPLICATE_TIMESTAMP",
        "TIME_VALUE_MISSING": "TIME_VALUE_MISSING",
    }
    frame["interval_quality"] = frame["interval_class"].map(interval_quality).fillna(
        "AUDIT_CLASS_UNAVAILABLE"
    )
    for channel in altitude_channels:
        frame[f"{channel.removesuffix('_rel_alt_m')}_interval_rate_mps"] = (
            frame[channel].diff() / frame["interval_duration_s"]
        )
    a, b = altitude_channels
    frame["altimeter_difference_m"] = frame[b] - frame[a]

    peak_indices = []
    for channel in altitude_channels:
        finite = frame[channel].dropna()
        if finite.empty:
            peak_indices.append(None)
        else:
            peak_indices.append(int(finite.idxmax()))
    common_peak = peak_indices[0] if peak_indices[0] is not None and peak_indices[0] == peak_indices[1] else None
    if common_peak is None:
        recorded_peak = {"status": "INSUFFICIENT_OBSERVABILITY", "reason": "Both altimeters do not share a finite recorded peak"}
        apogee = {"status": "INSUFFICIENT_OBSERVABILITY", "reason": "No common interior peak"}
    else:
        peak = frame.iloc[common_peak]
        recorded_peak = {
            "status": "DIRECTLY_RECORDED_EXTREMUM",
            "event": "RECORDED_RELATIVE_ALTITUDE_EXTREMUM",
            "confidence": "HIGH_FOR_RECORDED_SAMPLE_VALUES",
            "origin": "DERIVED_ONBOARD",
            "record_index": int(peak["record_index"]),
            "source_line_number": int(peak["source_line_number"]),
            "raw_time": float(peak["raw_time"]),
            "section_elapsed_s": float(peak["section_elapsed_s"]),
            "altitudes_m": {channel: float(peak[channel]) for channel in altitude_channels},
            "evidence_channels": list(altitude_channels),
            "method": "common maximum among retained finite onboard-relative-altitude samples",
            "time_uncertainty": "COUNTER_RESOLUTION_AND_SENSOR_LAG_UNKNOWN",
        }
        if 0 < common_peak < len(frame) - 1 and all(
            math.isfinite(float(frame.loc[common_peak - 1, channel]))
            and math.isfinite(float(frame.loc[common_peak + 1, channel]))
            and frame.loc[common_peak - 1, channel] < peak[channel]
            and frame.loc[common_peak + 1, channel] < peak[channel]
            for channel in altitude_channels
        ):
            apogee = {
                "status": "INSUFFICIENT_OBSERVABILITY",
                "event": "PHYSICAL_APOGEE",
                "timestamp": None,
                "confidence": "NOT_ASSIGNABLE",
                "recorded_extremum_record_index": int(peak["record_index"]),
                "evidence_channels": list(altitude_channels),
                "method": "physical event time is not inferred from an onboard-relative-altitude extremum",
                "reason": "Onboard altitude conversion, vertical reference, and sensor transient response are undocumented; adjacent sample times cannot bound physical apogee",
                "time_uncertainty": "NOT_QUANTIFIABLE",
            }
        else:
            apogee = {
                "status": "INSUFFICIENT_OBSERVABILITY", "event": "PHYSICAL_APOGEE",
                "timestamp": None, "confidence": "NOT_ASSIGNABLE",
                "evidence_channels": list(altitude_channels),
                "method": "No strict common interior recorded extremum is available",
                "reason": "Recorded relative altitude cannot establish physical apogee timing",
                "time_uncertainty": "NOT_QUANTIFIABLE",
            }

    def unobservable_event(name: str, channels: list[str], reason: str) -> dict:
        """Registre um evento que os canais disponíveis não permitem observar.

        Retorna metadados com nome, canais e justificativa, sem estimar instante
        ou valor físico ausente no registro.
        """
        return {
            "status": "INSUFFICIENT_OBSERVABILITY",
            "event": name,
            "timestamp": None,
            "confidence": "NOT_ASSIGNABLE",
            "evidence_channels": channels,
            "method": "NOT_DETECTED",
            "reason": reason,
            "time_uncertainty": "NOT_QUANTIFIABLE",
        }

    events = {
        "recorded_relative_altitude_peak": recorded_peak,
        "apogee_candidate": apogee,
        "liftoff": unobservable_event(
            "LIFTOFF", ["mpu1_ay_g", "mpu2_ay_g", *altitude_channels],
            "No verified prelaunch reference; accelerometer scale, mounting axis, and saturation are unknown",
        ),
        "burnout": unobservable_event(
            "BURNOUT", ["mpu1_ay_g", "mpu2_ay_g"],
            "Acceleration is uncalibrated and repeated full-scale-like values may indicate clipping",
        ),
        "recovery": unobservable_event("RECOVERY_DEPLOYMENT", [], "No deployment event channel is present"),
        "impact": unobservable_event(
            "IMPACT", list(altitude_channels),
            "No direct impact event or validated absolute altitude is available",
        ),
    }
    summary = {
        "status": "PARTIAL",
        "section_marker": section_marker,
        "segment_id": int(frame["segment_id"].iloc[0]),
        "record_count": len(frame),
        "first_record_index": int(frame["record_index"].iloc[0]),
        "last_record_index": int(frame["record_index"].iloc[-1]),
        "first_source_line_number": int(frame["source_line_number"].iloc[0]),
        "last_source_line_number": int(frame["source_line_number"].iloc[-1]),
        "raw_time_start": float(frame["raw_time"].iloc[0]),
        "raw_time_end": float(frame["raw_time"].iloc[-1]),
        "counter_span_s_assuming_header_ms": float(frame["section_elapsed_s"].iloc[-1]),
        "interval_quality_counts": {
            str(key): int(value) for key, value in frame["interval_quality"].value_counts().items()
        },
        "maximum_recorded_interval_s": float(frame["interval_duration_s"].max()),
        "clock_unit_basis": "HEADER_LABEL_MS_UNVERIFIED",
        "clock_mechanism": "UNKNOWN",
        "duplicate_copy_record_count": int(frame["is_exact_duplicate_copy"].sum()),
        "altitude_origin": "DERIVED_ONBOARD",
        "altitude_reference": "UNKNOWN_VERTICAL_REFERENCE",
        "vertical_rate_origin": "DERIVED_INTERVAL_SECANT_FROM_ONBOARD_ALTITUDE",
        "position_3d_status": "INSUFFICIENT_OBSERVABILITY",
        "attitude_status": "BLOCKED_BY_MISSING_METADATA",
        "inertial_acceleration_status": "BLOCKED_BY_MISSING_METADATA",
    }
    return frame, events, summary
