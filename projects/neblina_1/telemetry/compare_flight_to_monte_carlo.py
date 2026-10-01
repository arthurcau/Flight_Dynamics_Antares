"""Compare the retained Neblina 1 telemetry section with saved RocketPy runs.

The script reads the raw file only to verify its checksum. Analysis uses the
audited Parquet artifacts, preserves acquisition order, and writes new files
only under results/. It does not infer an absolute flight time or attitude.

Run from the repository root with:

    .venv/bin/python projects/neblina_1/telemetry/compare_flight_to_monte_carlo.py

Review notes by Cau.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import subprocess
import sys
from typing import Any
from zoneinfo import ZoneInfo

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]
RAW_PATH = REPO_ROOT / "data/flight_data/Dados de Vôo Neblina - LASC 2026.log"
AUDIT_DIR = REPO_ROOT / "results/neblina_1/20260927T044042.086265Z_telemetry_audit"
OBSERVED_DIR = REPO_ROOT / "results/neblina_1/20260927T044054.574382Z_observed_reconstruction"
REFERENCE_DIR = REPO_ROOT / "results/neblina_1/current_model_reference_v5_final_20260927"
CAMPAIGN_DIR = REPO_ROOT / "results/neblina_1/20260927T223147.432625Z_neblina_1_42"
GYRO_CHANNELS = tuple(
    f"mpu{imu}_g{axis}_dps" for imu in (1, 2) for axis in ("x", "y", "z")
)
SAMPLED_TO_ROCKETPY_INPUTS = (
    ("launch_inclination", "rocketpy_inclination"),
    ("launch_heading", "rocketpy_heading"),
    ("vehicle_mass", "rocketpy_mass"),
    ("site_elevation", "rocketpy_elevation"),
    ("power_off_drag_multiplier", "rocketpy_power_off_drag_factor"),
    ("power_on_drag_multiplier", "rocketpy_power_on_drag_factor"),
)


def sha256_file(path: Path) -> str:
    """Return a file digest without changing the source."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return value


def _load_primary_trace() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Select the original records referenced by the exact repeated section."""
    audit_manifest = _read_json(AUDIT_DIR / "telemetry_manifest.json")
    inventory = _read_json(AUDIT_DIR / "telemetry_inventory.json")
    raw_hash_before = sha256_file(RAW_PATH)
    if raw_hash_before != audit_manifest["source_sha256"]:
        raise ValueError("Raw telemetry checksum does not match its audit manifest")
    if inventory.get("source_sha256") != raw_hash_before:
        raise ValueError("Telemetry inventory was generated from a different raw source")
    for artifact_name in ("telemetry_samples.parquet", "telemetry_segments.parquet"):
        artifact_path = AUDIT_DIR / artifact_name
        expected_hash = audit_manifest["artifacts"][artifact_name]["sha256"]
        if sha256_file(artifact_path) != expected_hash:
            raise ValueError(f"Audited input artifact checksum mismatch: {artifact_name}")
    observed_manifest = _read_json(OBSERVED_DIR / "reconstruction_manifest.json")
    if observed_manifest.get("source_sha256") != raw_hash_before:
        raise ValueError("Observed-section artifact was derived from a different raw source")
    if observed_manifest.get("audit_manifest_sha256") != sha256_file(AUDIT_DIR / "telemetry_manifest.json"):
        raise ValueError("Observed-section artifact references a different telemetry audit")
    observed_hash = sha256_file(OBSERVED_DIR / "observed_section.parquet")
    if observed_hash != observed_manifest["artifacts"]["observed_section.parquet"]["sha256"]:
        raise ValueError("Observed-section duplicate mapping failed its recorded checksum")

    repeated = pd.read_parquet(OBSERVED_DIR / "observed_section.parquet")
    duplicate_rows = repeated.loc[repeated["is_exact_duplicate_copy"].astype(bool)]
    source_records = duplicate_rows["duplicate_of_record_index"].dropna().astype(int)
    if len(source_records) != len(duplicate_rows) or source_records.nunique() != len(source_records):
        raise ValueError("Repeated-section provenance does not identify unique source records")
    source_ids = set(source_records.tolist())

    long = pd.read_parquet(AUDIT_DIR / "telemetry_samples.parquet")
    if set(long["source_sha256"].dropna().unique()) != {raw_hash_before}:
        raise ValueError("Audited samples do not point to the verified raw source")
    primary = long.loc[long["record_index"].isin(source_ids)].copy()
    if primary["record_index"].nunique() != len(source_ids):
        raise ValueError("Not all source records from the repeated section are available")
    declared = primary.drop_duplicates("canonical_channel_name").set_index("canonical_channel_name")
    for channel in ("time_ms", "bmp1_rel_alt_m", "bmp2_rel_alt_m", *GYRO_CHANNELS):
        if channel not in declared.index:
            raise ValueError(f"Required channel is absent from the audited section: {channel}")
    if declared.loc["time_ms", "unit"] != "ms" or declared.loc["time_ms", "unit_status"] != "HEADER_LABEL":
        raise ValueError("Elapsed time conversion requires the documented ms header label")
    for channel in ("bmp1_rel_alt_m", "bmp2_rel_alt_m"):
        if declared.loc[channel, "unit"] != "m" or declared.loc[channel, "unit_status"] != "HEADER_LABEL":
            raise ValueError(f"Altitude plot requires the documented metre header label: {channel}")
    for channel in GYRO_CHANNELS:
        if declared.loc[channel, "unit"] != "deg/s" or declared.loc[channel, "unit_status"] != "HEADER_LABEL":
            raise ValueError(f"Angular-rate plot requires the documented deg/s header label: {channel}")
    segments = pd.read_parquet(AUDIT_DIR / "telemetry_segments.parquet")
    timestamps = primary.loc[
        primary["canonical_channel_name"].eq("time_ms"),
        ["record_index", "numeric_value", "source_line_number"],
    ].drop_duplicates("record_index").merge(
        segments[["record_index", "segment_id", "raw_time"]],
        on="record_index", how="left", validate="one_to_one",
    ).sort_values("record_index")
    if len(timestamps) != len(source_ids):
        raise ValueError("The selected section has missing or duplicate clock records")
    if timestamps["segment_id"].nunique() != 1:
        raise ValueError("Selected section crosses clock segments; no elapsed-time axis is justified")
    if timestamps["numeric_value"].diff().dropna().lt(0).any():
        raise ValueError("Selected section contains a backward clock jump")
    primary = primary.merge(
        segments[["record_index", "segment_id", "raw_time"]],
        on="record_index", how="left", validate="many_to_one",
    )
    time_by_record = timestamps.set_index("record_index")["numeric_value"]
    primary["block_elapsed_s"] = (
        primary["record_index"].map(time_by_record) - float(time_by_record.iloc[0])
    ) / 1000.0
    primary = primary.sort_values(["record_index", "canonical_channel_name"], kind="stable")

    pivot = primary.pivot(
        index="record_index", columns="canonical_channel_name", values="numeric_value",
    ).sort_index()
    record_metadata = timestamps.set_index("record_index").rename(
        columns={"numeric_value": "raw_time_ms"}
    )
    wide = record_metadata.join(pivot, how="left")
    wide["block_elapsed_s"] = (wide["raw_time_ms"] - wide["raw_time_ms"].iloc[0]) / 1000.0
    wide["source_sha256"] = raw_hash_before
    wide = wide.reset_index()

    return primary, wide, {
        "raw_sha256_before": raw_hash_before,
        "source_record_count": int(len(source_ids)),
        "source_record_index_first": int(min(source_ids)),
        "source_record_index_last": int(max(source_ids)),
        "source_line_first": int(timestamps["source_line_number"].min()),
        "source_line_last": int(timestamps["source_line_number"].max()),
        "clock_segment_id": int(timestamps["segment_id"].iloc[0]),
        "elapsed_from_first_sample_s": float(wide["block_elapsed_s"].iloc[-1]),
        "median_sample_interval_s": float(wide["raw_time_ms"].diff().median() / 1000.0),
        "maximum_sample_interval_s": float(wide["raw_time_ms"].diff().max() / 1000.0),
        "intervals_over_2s": int((wide["raw_time_ms"].diff() > 2000).sum()),
        "whole_dataset": {
            "declared_channel_count": int(len(inventory["header_channels"])),
            "numeric_record_count": int(inventory["record_count"]),
            "parse_issue_count": int(inventory["parse_issue_count"]),
            "timestamp_backward_jump_count": int(inventory["timebase"]["timestamp_backward_jump_count"]),
            "clock_segment_count": int(inventory["timebase"]["segment_count"]),
            "gps_status": inventory["gps"]["status"],
            "gps_in_range_coordinate_pair_count": int(inventory["gps"]["in_range_coordinate_pair_count"]),
        },
    }


def _gyro_summary(wide: pd.DataFrame) -> dict[str, dict[str, Any]]:
    summary: dict[str, dict[str, Any]] = {}
    for channel in GYRO_CHANNELS:
        values = pd.to_numeric(wide[channel], errors="coerce").dropna()
        counts = values.value_counts()
        summary[channel] = {
            "count": int(len(values)),
            "minimum_header_labeled_deg_s": float(values.min()),
            "maximum_header_labeled_deg_s": float(values.max()),
            "maximum_absolute_header_labeled_deg_s": float(values.abs().max()),
            "count_absolute_value_over_100": int(values.abs().gt(100).sum()),
            "most_repeated_value": float(counts.index[0]),
            "most_repeated_value_count": int(counts.iloc[0]),
        }
    return summary


def _input_pairing_diagnostics(cases: pd.DataFrame) -> dict[str, dict[str, Any]]:
    """Check whether declared sample values match the values logged by RocketPy."""
    diagnostics: dict[str, dict[str, Any]] = {}
    for sampled, realized in SAMPLED_TO_ROCKETPY_INPUTS:
        if sampled not in cases or realized not in cases:
            diagnostics[sampled] = {"status": "REQUIRED_INPUT_FIELD_MISSING"}
            continue
        paired = cases[[sampled, realized]].apply(pd.to_numeric, errors="coerce").dropna()
        if paired.empty:
            diagnostics[sampled] = {"status": "NO_FINITE_PAIRED_VALUES"}
            continue
        difference = paired[realized] - paired[sampled]
        diagnostics[sampled] = {
            "rocketpy_logged_field": realized,
            "case_count": int(len(paired)),
            "exact_match_count": int(paired[sampled].eq(paired[realized]).sum()),
            "pearson_correlation": float(paired[sampled].corr(paired[realized], method="pearson")),
            "spearman_correlation": float(paired[sampled].corr(paired[realized], method="spearman")),
            "mean_rocketpy_minus_declared": float(difference.mean()),
            "maximum_absolute_difference": float(difference.abs().max()),
            "status": "DESCRIPTIVE_PAIRING_DIAGNOSTIC_ONLY",
        }
    return diagnostics


def _model_snapshot_comparison(
    reference_manifest: dict[str, Any], campaign_manifest: dict[str, Any],
) -> dict[str, Any]:
    reference_snapshot = reference_manifest.get("git", {}).get("working_tree_snapshot_sha256")
    campaign_snapshot = campaign_manifest.get("git", {}).get("working_tree_snapshot_sha256")
    if not reference_snapshot or not campaign_snapshot:
        status = "SNAPSHOT_PROVENANCE_INCOMPLETE"
    elif reference_snapshot == campaign_snapshot:
        status = "SAME_CODE_SNAPSHOT"
    else:
        status = "MODEL_SNAPSHOT_MISMATCH"
    return {
        "status": status,
        "reference_working_tree_snapshot_sha256": reference_snapshot,
        "monte_carlo_working_tree_snapshot_sha256": campaign_snapshot,
        "configuration_hashes_match": (
            reference_manifest.get("configuration_hashes")
            == campaign_manifest.get("configuration_hashes")
        ),
    }


def _verify_reference_artifacts(
    reference_dir: Path, manifest: dict[str, Any], artifact_names: tuple[str, ...],
) -> dict[str, str]:
    """Verify every reference artifact before it contributes to the analysis."""
    verified_hashes: dict[str, str] = {}
    for artifact_name in artifact_names:
        path = reference_dir / artifact_name
        expected_hash = manifest.get("output_hashes", {}).get(artifact_name)
        if expected_hash is None:
            raise ValueError(f"RocketPy reference manifest has no hash for {artifact_name}")
        actual_hash = sha256_file(path)
        if actual_hash != expected_hash:
            raise ValueError(f"RocketPy reference artifact checksum mismatch: {artifact_name}")
        verified_hashes[artifact_name] = actual_hash
    return verified_hashes


def _mc_apogee() -> tuple[pd.DataFrame, dict[str, Any]]:
    inputs = pd.read_parquet(CAMPAIGN_DIR / "samples/inputs.parquet")
    outputs = pd.read_parquet(CAMPAIGN_DIR / "scenarios/nominal/outputs.parquet")
    if inputs["case_id"].duplicated().any() or outputs["case_id"].duplicated().any():
        raise ValueError("Monte Carlo case IDs must be unique")
    if set(inputs["case_id"]) != set(outputs["case_id"]):
        raise ValueError("Saved Monte Carlo inputs and outputs do not contain the same case IDs")
    pairing_columns = ["case_id"] + [
        column for pair in SAMPLED_TO_ROCKETPY_INPUTS for column in pair
    ]
    pairing_columns = list(dict.fromkeys(pairing_columns))
    joined = outputs.merge(
        inputs[pairing_columns],
        on="case_id", how="left", validate="one_to_one",
    )
    if joined["rocketpy_elevation"].isna().any():
        raise ValueError("Some Monte Carlo cases lack their realized RocketPy elevation")
    # RocketPy apogee is ASL; subtract the exact elevation passed to that case.
    joined["apogee_agl_recomputed"] = joined["apogee"] - joined["rocketpy_elevation"]
    if "apogee_agl" in joined:
        joined["stored_agl_minus_recomputed_m"] = joined["apogee_agl"] - joined["apogee_agl_recomputed"]
    values = joined["apogee_agl_recomputed"].astype(float)
    asl_values = joined["apogee"].astype(float)
    failures = pd.read_parquet(CAMPAIGN_DIR / "scenarios/nominal/failures.parquet")
    scenario_manifest = yaml.safe_load(
        (CAMPAIGN_DIR / "scenarios/nominal/manifest.yaml").read_text(encoding="utf-8")
    )
    if scenario_manifest["run"]["completed_cases"] != len(outputs):
        raise ValueError("Saved Monte Carlo output count disagrees with the scenario manifest")
    if scenario_manifest["run"]["failed_cases"] != len(failures):
        raise ValueError("Saved Monte Carlo failure count disagrees with the scenario manifest")
    input_log = (CAMPAIGN_DIR / "scenarios/nominal/mc_sim.inputs.txt").read_text(encoding="utf-8")
    nonstandard_tokens = {
        token: input_log.count(token) for token in ("Infinity", "-Infinity", "NaN")
        if token in input_log
    }
    summary = {
        "campaign_id": CAMPAIGN_DIR.name,
        "profile": "debug",
        "scenario": "nominal",
        "seed": 42,
        "successful_cases": int(len(joined)),
        "failed_cases": int(len(failures)),
        "weather_method": (
            "one archived deterministic base profile reused across cases; configured per-case x/y wind perturbations applied"
        ),
        "declared_vs_rocketpy_logged_input_pairing": _input_pairing_diagnostics(joined),
        "input_log_nonstandard_json_numeric_tokens": nonstandard_tokens,
        "apogee_agl_m": {
            "mean": float(values.mean()),
            "sample_standard_deviation": float(values.std(ddof=1)),
            "minimum": float(values.min()),
            "p05": float(values.quantile(0.05)),
            "median": float(values.median()),
            "p90": float(values.quantile(0.90)),
            "p95": float(values.quantile(0.95)),
            "p99": float(values.quantile(0.99)),
            "maximum": float(values.max()),
        },
        "apogee_asl_m": {
            "minimum": float(asl_values.min()),
            "p05": float(asl_values.quantile(0.05)),
            "median": float(asl_values.median()),
            "p95": float(asl_values.quantile(0.95)),
            "maximum": float(asl_values.max()),
        },
    }
    if "stored_agl_minus_recomputed_m" in joined:
        difference = joined["stored_agl_minus_recomputed_m"].dropna()
        summary["legacy_stored_agl_artifact_difference_m"] = {
            "count": int(len(difference)),
            "maximum_absolute": float(difference.abs().max()) if len(difference) else None,
        }
    return joined, summary


def _weather_plot(profile: pd.DataFrame, provenance: dict[str, Any], output: Path) -> None:
    altitude = profile["altitude_asl_m"]
    wind_speed = np.hypot(profile["wind_east_mps"], profile["wind_north_mps"])
    figure, (wind_axis, density_axis) = plt.subplots(1, 2, figsize=(12, 6), sharey=True)
    wind_axis.plot(profile["wind_east_mps"], altitude, label="east component")
    wind_axis.plot(profile["wind_north_mps"], altitude, label="north component")
    wind_axis.plot(wind_speed, altitude, label="component magnitude")
    wind_axis.set_xlabel("Wind [m/s]")
    wind_axis.set_ylabel("Altitude ASL [m]")
    wind_axis.legend(fontsize=8)
    wind_axis.grid(alpha=0.25)
    density_axis.plot(profile["density_kg_m3"], altitude, color="tab:green", label="density")
    density_axis.set_xlabel("Density [kg/m³]")
    density_axis.legend(fontsize=8)
    density_axis.grid(alpha=0.25)
    valid_time = provenance.get("valid_time_utc", "unknown valid time")
    figure.suptitle(
        "Archived MAGI input profile — candidate forecast, not observed flight weather\n"
        f"{provenance.get('source', 'unknown source')}; valid {valid_time}"
    )
    figure.tight_layout()
    figure.savefig(output, dpi=160)
    plt.close(figure)


def _telemetry_plot(wide: pd.DataFrame, output: Path) -> None:
    figure, axes = plt.subplots(
        7, 1, figsize=(14, 17), sharex=True,
        gridspec_kw={"height_ratios": [1.4, 1, 1, 1, 1, 1, 1]},
    )
    altitude_axis = axes[0]
    time = wide["block_elapsed_s"]
    for channel, label in (("bmp1_rel_alt_m", "BMP1 onboard relative altitude"),
                           ("bmp2_rel_alt_m", "BMP2 onboard relative altitude")):
        altitude_axis.plot(time, wide[channel], linestyle="none", marker="o", markersize=3, label=label)
    altitude_axis.set_ylabel("Recorded altitude channel [m]")
    altitude_axis.legend()
    altitude_axis.grid(alpha=0.25)
    altitude_axis.set_title("Recorded altimeter outputs; vertical reference and calibration unknown")

    for axis, channel in zip(axes[1:], GYRO_CHANNELS):
        axis.plot(time, wide[channel], linestyle="none", marker=".", markersize=4)
        axis.set_ylabel(f"{channel.replace('_dps', '')} [header deg/s]")
        axis.grid(alpha=0.25)
    axes[1].set_title("Raw gyroscope components; no calibration, integration, or filtering")
    axes[-1].set_xlabel("Seconds from first retained record (device-clock-relative only)")

    figure.suptitle(
        "Neblina 1 retained telemetry section\n"
        "Raw sample markers only; sparse intervals are not interpolated; not an attitude estimate",
        y=0.995,
    )
    figure.subplots_adjust(left=0.14, right=0.98, bottom=0.06, top=0.92, hspace=0.28)
    figure.savefig(output, dpi=160)
    plt.close(figure)


def _peak_aligned_residuals(
    wide: pd.DataFrame,
    simulated: pd.DataFrame,
    metrics: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, dict[str, Any]]]:
    peak_time = float(metrics["apogee_time"])
    peak_height = float(metrics["apogee_agl"])
    observed_peak_time = float(wide.loc[wide["bmp2_rel_alt_m"].idxmax(), "block_elapsed_s"])
    model_time = (simulated["time_s"].to_numpy(dtype=float) - peak_time)
    model_height = simulated["altitude_agl_m"].to_numpy(dtype=float) - peak_height
    if not np.all(np.diff(model_time) > 0):
        raise ValueError("RocketPy reference time series must be strictly increasing")
    rows: list[dict[str, Any]] = []
    for channel in ("bmp1_rel_alt_m", "bmp2_rel_alt_m"):
        peak_index = wide[channel].idxmax()
        peak = float(wide.loc[peak_index, channel])
        observed_peak_time = float(wide.loc[peak_index, "block_elapsed_s"])
        for _, sample in wide.iterrows():
            relative_time = float(sample["block_elapsed_s"] - observed_peak_time)
            measured_relative_height = float(sample[channel] - peak)
            in_model_domain = model_time[0] <= relative_time <= model_time[-1]
            modeled_relative_height = (
                float(np.interp(relative_time, model_time, model_height))
                if in_model_domain else None
            )
            rows.append({
                "channel": channel,
                "record_index": int(sample["record_index"]),
                "source_line_number": int(sample["source_line_number"]),
                "observed_peak_relative_time_s": relative_time,
                "observed_peak_relative_altitude_m": measured_relative_height,
                "modeled_peak_relative_altitude_m": modeled_relative_height,
                "observed_minus_modeled_m": (
                    measured_relative_height - modeled_relative_height
                    if modeled_relative_height is not None else None
                ),
                "comparison_status": "PEAK_ALIGNED_WITHIN_MODEL_DOMAIN" if in_model_domain else "OUTSIDE_MODEL_TIME_DOMAIN",
            })
    residuals = pd.DataFrame(rows)
    summary: dict[str, dict[str, Any]] = {}
    valid = residuals.loc[residuals["comparison_status"].eq("PEAK_ALIGNED_WITHIN_MODEL_DOMAIN")].copy()
    for channel in ("bmp1_rel_alt_m", "bmp2_rel_alt_m"):
        channel_rows = valid.loc[valid["channel"].eq(channel)]
        summary[channel] = {"conditional_peak_aligned_residuals": {}}
        for phase, mask in (
            ("ascent", channel_rows["observed_peak_relative_time_s"].lt(0)),
            ("post_peak", channel_rows["observed_peak_relative_time_s"].gt(0)),
        ):
            values = channel_rows.loc[mask, "observed_minus_modeled_m"].astype(float)
            phase_summary: dict[str, Any] = {
                "count": int(len(values)),
                "mean_bias_m": float(values.mean()) if len(values) else None,
                "rmse_m": float(np.sqrt(np.mean(np.square(values)))) if len(values) else None,
            }
            if phase == "post_peak" and len(values):
                phase_rows = channel_rows.loc[mask]
                max_index = phase_rows["observed_minus_modeled_m"].idxmax()
                phase_summary["maximum_positive_residual_m"] = float(
                    phase_rows.loc[max_index, "observed_minus_modeled_m"]
                )
                phase_summary["time_of_maximum_positive_residual_s"] = float(
                    phase_rows.loc[max_index, "observed_peak_relative_time_s"]
                )
                ordered_rows = phase_rows.sort_values("observed_peak_relative_time_s")
                first_row = ordered_rows.iloc[0]
                phase_summary["first_post_peak_sample_time_s"] = float(
                    first_row["observed_peak_relative_time_s"]
                )
                phase_summary["first_post_peak_sample_residual_m"] = float(
                    first_row["observed_minus_modeled_m"]
                )
                phase_summary["first_positive_residual_time_s"] = (
                    float(phase_rows.loc[phase_rows["observed_minus_modeled_m"].gt(0),
                                         "observed_peak_relative_time_s"].min())
                    if phase_rows["observed_minus_modeled_m"].gt(0).any() else None
                )
                phase_summary["last_positive_residual_time_s"] = (
                    float(phase_rows.loc[phase_rows["observed_minus_modeled_m"].gt(0),
                                         "observed_peak_relative_time_s"].max())
                    if phase_rows["observed_minus_modeled_m"].gt(0).any() else None
                )
                phase_summary["first_negative_after_last_positive_time_s"] = (
                    float(phase_rows.loc[
                        phase_rows["observed_peak_relative_time_s"].gt(
                            phase_summary["last_positive_residual_time_s"]
                        ) & phase_rows["observed_minus_modeled_m"].lt(0),
                        "observed_peak_relative_time_s",
                    ].min())
                    if phase_summary["last_positive_residual_time_s"] is not None
                    and phase_rows.loc[
                        phase_rows["observed_peak_relative_time_s"].gt(
                            phase_summary["last_positive_residual_time_s"]
                        ) & phase_rows["observed_minus_modeled_m"].lt(0)
                    ].shape[0]
                    else None
                )
            summary[channel]["conditional_peak_aligned_residuals"][phase] = phase_summary
        summary[channel]["outside_model_time_domain_count"] = int(
            residuals.loc[residuals["channel"].eq(channel), "comparison_status"]
            .eq("OUTSIDE_MODEL_TIME_DOMAIN").sum()
        )
    return residuals, summary


def _peak_aligned_plot(
    residuals: pd.DataFrame,
    simulated: pd.DataFrame,
    metrics: dict[str, Any],
    output: Path,
) -> None:
    peak_time = float(metrics["apogee_time"])
    peak_height = float(metrics["apogee_agl"])
    figure, axis = plt.subplots(figsize=(11, 6))
    model_time = simulated["time_s"] - peak_time
    axis.plot(
        model_time, simulated["altitude_agl_m"] - peak_height,
        color="black", linewidth=1.4, label="current reference RocketPy profile",
    )
    for channel, label in (("bmp1_rel_alt_m", "BMP1 recorded minus its peak"),
                           ("bmp2_rel_alt_m", "BMP2 recorded minus its peak")):
        observed = residuals.loc[residuals["channel"].eq(channel)]
        axis.scatter(observed["observed_peak_relative_time_s"], observed["observed_peak_relative_altitude_m"],
                     s=17, alpha=0.75, label=label)
    axis.axvline(0, color="0.4", linestyle="--", linewidth=0.8)
    axis.axhline(0, color="0.4", linestyle=":", linewidth=0.8)
    axis.set_xlabel("Time relative to each trace's recorded / modeled altitude peak [s]")
    axis.set_ylabel("Altitude relative to that trace's peak [m]")
    axis.set_title(
        "Peak-aligned altitude shape comparison\n"
        "Vertical offset and time origin removed; this does not validate apogee time"
    )
    axis.grid(alpha=0.25)
    axis.legend(fontsize=8)
    figure.tight_layout()
    figure.savefig(output, dpi=160)
    plt.close(figure)


def _residual_plot(residuals: pd.DataFrame, output: Path) -> None:
    figure, axis = plt.subplots(figsize=(11, 5))
    valid = residuals.loc[residuals["comparison_status"].eq("PEAK_ALIGNED_WITHIN_MODEL_DOMAIN")]
    for channel, label in (("bmp1_rel_alt_m", "BMP1"), ("bmp2_rel_alt_m", "BMP2")):
        rows = valid.loc[valid["channel"].eq(channel)]
        axis.scatter(
            rows["observed_peak_relative_time_s"], rows["observed_minus_modeled_m"],
            s=18, alpha=0.75, label=label,
        )
    axis.axvline(0, color="0.4", linestyle="--", linewidth=0.8)
    axis.axhline(0, color="0.4", linestyle=":", linewidth=0.8)
    axis.set_xlabel("Time relative to measured / modeled altitude peak [s]")
    axis.set_ylabel("Observed minus modeled relative altitude [m]")
    axis.set_title(
        "Conditional shape residual after peak alignment\n"
        "Model sampled by linear interpolation; no telemetry interpolation or extrapolation"
    )
    axis.grid(alpha=0.25)
    axis.legend()
    figure.tight_layout()
    figure.savefig(output, dpi=160)
    plt.close(figure)


def _mc_plot(
    cases: pd.DataFrame,
    wide: pd.DataFrame,
    output: Path,
) -> None:
    observed_peaks = [float(wide[channel].max()) for channel in ("bmp1_rel_alt_m", "bmp2_rel_alt_m")]
    figure, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    panels = (
        ("apogee_agl_recomputed", "MC apogee AGL [m]", "sensor max treated as AGL (conditional)"),
        ("apogee", "MC apogee ASL [m]", "sensor max treated as ASL (alternative only)"),
    )
    for axis, (column, xlabel, interpretation) in zip(axes, panels):
        axis.hist(cases[column].dropna(), bins="sturges", color="tab:blue", alpha=0.75, edgecolor="white")
        for index, peak in enumerate(observed_peaks):
            axis.axvline(
                peak, color=("tab:red" if index == 0 else "tab:orange"), linestyle="--",
                label=f"BMP{index + 1} recorded max: {peak:.1f} m",
            )
        axis.set_xlabel(xlabel)
        axis.set_title(interpretation)
        axis.grid(axis="y", alpha=0.2)
        axis.legend(fontsize=7)
    axes[0].set_ylabel("Monte Carlo case count")
    figure.suptitle(
        "50 debug Monte Carlo apogees versus recorded altimeter maxima\n"
        "Flight altitude datum is undocumented; deterministic reference omitted because its code snapshot differs"
    )
    figure.tight_layout()
    figure.savefig(output, dpi=160)
    plt.close(figure)


def _package_version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def run(output_dir: Path) -> Path:
    results_root = (REPO_ROOT / "results").resolve()
    output_dir = output_dir if output_dir.is_absolute() else REPO_ROOT / output_dir
    output_dir = output_dir.resolve()
    if not output_dir.is_relative_to(results_root) or output_dir == results_root:
        raise ValueError("Comparison artifacts must be written beneath results/")

    long_trace, wide, telemetry = _load_primary_trace()
    reference_manifest = _read_json(REFERENCE_DIR / "manifest.json")
    campaign_manifest = _read_json(CAMPAIGN_DIR / "manifest.json")
    reference_artifact_hashes = _verify_reference_artifacts(
        REFERENCE_DIR,
        reference_manifest,
        ("flight_metrics.json", "simulated_timeseries.parquet", "atmosphere_profile.parquet"),
    )
    metrics = _read_json(REFERENCE_DIR / "flight_metrics.json")
    launch = yaml.safe_load((CAMPAIGN_DIR / "config_snapshot/config/launch.yaml").read_text())
    weather_provenance = reference_manifest.get("atmosphere_provenance", {})
    weather = pd.read_parquet(REFERENCE_DIR / "atmosphere_profile.parquet")
    simulated = pd.read_parquet(REFERENCE_DIR / "simulated_timeseries.parquet")
    cases, mc = _mc_apogee()
    model_snapshot_comparison = _model_snapshot_comparison(reference_manifest, campaign_manifest)
    residuals, residual_summary = _peak_aligned_residuals(wide, simulated, metrics)
    output_dir.mkdir(parents=True, exist_ok=False)

    long_trace.to_parquet(output_dir / "primary_flight_trace.parquet", index=False)
    _telemetry_plot(wide, output_dir / "altitude_and_raw_angular_rates.png")
    residuals.to_parquet(output_dir / "peak_aligned_shape_residuals.parquet", index=False)
    _peak_aligned_plot(residuals, simulated, metrics, output_dir / "peak_aligned_altitude_shape.png")
    _residual_plot(residuals, output_dir / "peak_aligned_altitude_residuals.png")
    _weather_plot(weather, weather_provenance, output_dir / "candidate_weather_profile.png")
    _mc_plot(cases, wide, output_dir / "mc_apogee_vs_recorded_peaks.png")

    peaks = {}
    for channel in ("bmp1_rel_alt_m", "bmp2_rel_alt_m"):
        index = wide[channel].idxmax()
        row = wide.loc[index]
        peaks[channel] = {
            "recorded_max_m": float(row[channel]),
            "record_index": int(row["record_index"]),
            "source_line_number": int(row["source_line_number"]),
            "raw_device_time_ms": float(row["raw_time_ms"]),
            "block_elapsed_s": float(row["block_elapsed_s"]),
            "status": "MEASURED_ONBOARD_DERIVED_CHANNEL; VERTICAL_DATUM_UNKNOWN",
        }
    observed_peak = max(item["recorded_max_m"] for item in peaks.values())
    corrected_stats = mc["apogee_agl_m"]
    difference_to_mc_max = observed_peak - corrected_stats["maximum"]
    difference_to_mc_p95 = observed_peak - corrected_stats["p95"]
    config_date = launch["launch"]["datetime"]
    planned_datetime_local = datetime.fromisoformat(
        f"{config_date['date']}T{config_date['time']}"
    ).replace(tzinfo=ZoneInfo(config_date["timezone"]))
    planned_datetime_utc = planned_datetime_local.astimezone(timezone.utc)
    weather_valid_time = datetime.fromisoformat(
        weather_provenance["valid_time_utc"].replace("Z", "+00:00")
    )
    report = {
        "schema_version": "1.0",
        "status": {
            "telemetry_trace": "PARTIAL_FLIGHT_TRACE_RETAINED_WITH_PROVENANCE",
            "attitude": "INSUFFICIENT_OBSERVABILITY",
            "weather_correlation": "NOT_ASSESSABLE",
            "rocketpy_comparison": "CONDITIONAL_APOGEE_AND_PEAK_ALIGNED_SHAPE_ONLY",
        },
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": {
            "raw_file": "data/flight_data/Dados de Vôo Neblina - LASC 2026.log",
            "raw_sha256_before": telemetry["raw_sha256_before"],
            "raw_sha256_after": sha256_file(RAW_PATH),
            "audit_manifest_sha256": sha256_file(AUDIT_DIR / "telemetry_manifest.json"),
            "observed_duplicate_manifest_source": "observed_reconstruction/observed_section.parquet",
            "primary_trace": telemetry,
            "exact_duplicate_copy_excluded_from_primary_trace": True,
        },
        "dataset_inventory": telemetry["whole_dataset"],
        "flight_clock": {
            "absolute_time": "UNKNOWN",
            "elapsed_time_axis": "from first retained sample in source order; device counter labeled ms",
            "launch_alignment": "UNKNOWN; no ignition-time or epoch anchor in raw telemetry",
            "planned_launch_datetime": config_date,
        },
        "recorded_altitude_peaks": peaks,
        "peak_aligned_shape_residuals": {
            "status": "CONDITIONAL_SHAPE_DIAGNOSTIC_NOT_TIME_VALIDATION",
            "method": "align onboard channel maxima with modeled apogee; subtract each trace peak; linearly sample the modeled series at retained telemetry times only",
            "summary": residual_summary,
        },
        "raw_gyro_summary": _gyro_summary(wide),
        "attitude_limitations": [
            "Sensor model, scale, bias, mounting orientation, and body-frame mapping are undocumented.",
            "No verified attitude reference is present; gyro integration would accumulate unknown bias and drift.",
            "The y-axis gyro channels repeat an extreme code many times, consistent with possible clipping or a sentinel; hardware range is unknown.",
            "The selected section has sparse samples and multi-second gaps, so fast oscillations cannot be resolved.",
            "The plotted values are raw header-labeled angular rates, not Euler angles or reconstructed attitude.",
        ],
        "rocketpy_reference": {
            "variant_id": reference_manifest.get("variant_id"),
            "status": reference_manifest.get("status"),
            "validation_status": reference_manifest.get("validation_status"),
            "apogee_agl_m": float(metrics["apogee_agl"]),
            "apogee_asl_m": float(metrics["apogee_asl"]),
            "apogee_time_s_from_model_ignition": float(metrics["apogee_time"]),
            "main_deployment_time_s_after_apogee": float(
                metrics["main_event"]["deploy_time"] - metrics["apogee_time"]
            ),
            "main_deployment_time_basis": "main_event.deploy_time, after configured deployment lag",
            "manifest_sha256": sha256_file(REFERENCE_DIR / "manifest.json"),
            "flight_metrics_sha256": reference_artifact_hashes["flight_metrics.json"],
        },
        "model_snapshot_comparison": model_snapshot_comparison,
        "monte_carlo": {
            **mc,
            "campaign_status": campaign_manifest.get("status"),
            "manifest_sha256": sha256_file(CAMPAIGN_DIR / "manifest.json"),
            "apogee_agl_calculation": "output ASL minus realized rocketpy_elevation for each case",
            "legacy_output_agl_column_used_for_comparison": False,
            "sensor_peak_minus_mc_max_if_sensor_is_agl_m": float(difference_to_mc_max),
            "sensor_peak_minus_mc_p95_if_sensor_is_agl_m": float(difference_to_mc_p95),
            "sensor_peak_minus_mc_max_if_sensor_is_asl_m": float(
                observed_peak - mc["apogee_asl_m"]["maximum"]
            ),
            "deterministic_reference_peak_difference_if_sensor_is_agl_m": float(
                observed_peak - metrics["apogee_agl"]
            ),
            "deterministic_reference_peak_difference_if_sensor_is_asl_m": float(
                observed_peak - metrics["apogee_asl"]
            ),
            "datum_interpretation": "CONDITIONAL_MAGNITUDE_ONLY",
            "limitations": [
                "Only 50 debug-profile cases; tail probabilities are poorly resolved.",
                "The same archived deterministic atmosphere base profile was reused; configured per-case x/y wind perturbations are present, but are not time-matched flight weather.",
                "The Monte Carlo is the current model's uncertainty setup, not a frozen preflight or as-flown reconstruction.",
                "The onboard altitude channel's vertical datum and calibration are unknown.",
                "The output time series for individual Monte Carlo cases was not retained; only apogee outcomes are compared.",
            ],
        },
        "weather": {
            "correlation_status": "NOT_ASSESSABLE",
            "reason": "Actual launch date/time is unknown, onboard GPS has no finite coordinates, and attitude/airspeed are not observable from documented calibration.",
            "candidate_profile_provenance": weather_provenance,
            "planned_launch_time_status": config_date.get("status"),
            "planned_launch_time_utc": planned_datetime_utc.isoformat(),
            "candidate_profile_minus_planned_time_hours": (
                weather_valid_time - planned_datetime_utc
            ).total_seconds() / 3600.0,
        },
        "provenance": {
            "audit_manifest_sha256": sha256_file(AUDIT_DIR / "telemetry_manifest.json"),
            "telemetry_samples_parquet_sha256": sha256_file(AUDIT_DIR / "telemetry_samples.parquet"),
            "telemetry_segments_parquet_sha256": sha256_file(AUDIT_DIR / "telemetry_segments.parquet"),
            "observed_section_manifest_sha256": sha256_file(OBSERVED_DIR / "reconstruction_manifest.json"),
            "observed_section_parquet_sha256": sha256_file(OBSERVED_DIR / "observed_section.parquet"),
            "reference_manifest_sha256": sha256_file(REFERENCE_DIR / "manifest.json"),
            "reference_flight_metrics_json_sha256": reference_artifact_hashes["flight_metrics.json"],
            "reference_timeseries_parquet_sha256": reference_artifact_hashes["simulated_timeseries.parquet"],
            "reference_atmosphere_parquet_sha256": reference_artifact_hashes["atmosphere_profile.parquet"],
            "campaign_manifest_sha256": sha256_file(CAMPAIGN_DIR / "manifest.json"),
            "campaign_inputs_parquet_sha256": sha256_file(CAMPAIGN_DIR / "samples/inputs.parquet"),
            "campaign_outputs_parquet_sha256": sha256_file(CAMPAIGN_DIR / "scenarios/nominal/outputs.parquet"),
            "git_commit": subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, check=True,
                capture_output=True, text=True,
            ).stdout.strip(),
            "working_tree_dirty": bool(subprocess.run(
                ["git", "status", "--porcelain"], cwd=REPO_ROOT, check=True,
                capture_output=True, text=True,
            ).stdout.strip()),
            "python": sys.version.split()[0],
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "matplotlib": matplotlib.__version__,
            "rocketpy": _package_version("rocketpy"),
            "analysis_script_sha256": sha256_file(Path(__file__).resolve()),
        },
    }
    if report["source"]["raw_sha256_before"] != report["source"]["raw_sha256_after"]:
        raise RuntimeError("Raw telemetry changed while comparison was running")

    analysis_path = output_dir / "comparison.json"
    analysis_path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    report_path = output_dir / "diagnostic_report.md"
    report_path.write_text(_render_report(report), encoding="utf-8")
    generated = sorted(path for path in output_dir.iterdir() if path.is_file())
    artifact_manifest = {
        "schema_version": "1.0",
        "source_sha256": telemetry["raw_sha256_before"],
        "input_manifest_hashes": report["provenance"],
        "artifacts": {
            path.name: {"sha256": sha256_file(path), "size_bytes": path.stat().st_size}
            for path in generated
        },
    }
    (output_dir / "artifact_manifest.json").write_text(
        json.dumps(artifact_manifest, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    return output_dir


def _render_report(data: dict[str, Any]) -> str:
    peaks = data["recorded_altitude_peaks"]
    mc = data["monte_carlo"]
    stats = mc["apogee_agl_m"]
    gyro = data["raw_gyro_summary"]
    time = data["source"]["primary_trace"]
    residual = data["peak_aligned_shape_residuals"]["summary"]["bmp2_rel_alt_m"]["conditional_peak_aligned_residuals"]
    legacy_difference = mc.get("legacy_stored_agl_artifact_difference_m", {}).get("maximum_absolute")
    infinity_count = mc.get("input_log_nonstandard_json_numeric_tokens", {}).get("Infinity", 0)
    return f"""# Neblina 1 telemetry and Monte Carlo comparison

## What was compared

The raw file `{data['source']['raw_file']}` was read only for a SHA-256 check. Its hash before and after processing is `{data['source']['raw_sha256_before']}`. The analysis uses the audited Parquet samples and retains source record and line numbers. The exact repeated 86-record `DADOS DE VÔO` copy was not counted twice; its original source records were selected using the audit's duplicate mapping.

The retained trace contains {time['source_record_count']} records from source lines {time['source_line_first']}–{time['source_line_last']}. Device-clock time spans {time['elapsed_from_first_sample_s']:.2f} s from the first selected record; median sample interval is {time['median_sample_interval_s']:.2f} s, maximum interval is {time['maximum_sample_interval_s']:.2f} s, and {time['intervals_over_2s']} intervals exceed 2 s. This is a block-local device-clock axis, not a verified time since ignition.

The whole-file audit found {data['dataset_inventory']['declared_channel_count']} declared channels, {data['dataset_inventory']['numeric_record_count']:,} numeric records, {data['dataset_inventory']['parse_issue_count']} non-sample/parse-issue lines, {data['dataset_inventory']['timestamp_backward_jump_count']} backward clock jumps across {data['dataset_inventory']['clock_segment_count']} segments, and {data['dataset_inventory']['gps_in_range_coordinate_pair_count']} in-range GPS coordinate pairs (`{data['dataset_inventory']['gps_status']}`). The audit retains source order and clock segments; it does not assign reset causes or stitch a global time axis.

## Recorded altitude and attitude observability

The two onboard-derived altitude channels peak at {peaks['bmp1_rel_alt_m']['recorded_max_m']:.2f} m (BMP1) and {peaks['bmp2_rel_alt_m']['recorded_max_m']:.2f} m (BMP2), both at record {peaks['bmp1_rel_alt_m']['record_index']} / source line {peaks['bmp1_rel_alt_m']['source_line_number']}. The channels agree within {abs(peaks['bmp1_rel_alt_m']['recorded_max_m'] - peaks['bmp2_rel_alt_m']['recorded_max_m']):.2f} m at that sample. These are measured onboard-derived channel values; their vertical reference and calibration are unknown.

Absolute attitude cannot be reconstructed defensibly from the available metadata. The figure `altitude_and_raw_angular_rates.png` therefore plots raw, header-labeled gyro channels as sample markers. It does not integrate them into Euler angles. Both MPU y-axis channels contain {gyro['mpu1_gy_dps']['most_repeated_value_count']} repeats of the recorded value {gyro['mpu1_gy_dps']['most_repeated_value']:.3f} deg/s, and {gyro['mpu1_gy_dps']['count_absolute_value_over_100']} samples exceed 100 deg/s in magnitude. This is consistent with possible clipping or a special code, but sensor range and encoding are unknown. Fast oscillations cannot be evaluated from these sparse data and gaps; the plot does not establish stability or instability.

Both barometric altitude channels have usable finite readings in this section, though their reference/calibration is unknown. Gyroscope channels are present, while their axis mapping and calibration are unknown. Accelerometer channels are recorded with header unit `g` but are not used to infer inertial acceleration or orientation. GPS is present in the file but has no valid coordinate pair.

## RocketPy comparison

The saved deterministic reference predicts {data['rocketpy_reference']['apogee_agl_m']:.1f} m AGL at {data['rocketpy_reference']['apogee_time_s_from_model_ignition']:.2f} s after model ignition. Its manifest labels it `{data['rocketpy_reference']['status']}` and `{data['rocketpy_reference']['validation_status']}`; it is a current reference, not a recovered frozen preflight or as-flown model. The deterministic reference and Monte Carlo campaign have `{data['model_snapshot_comparison']['status']}` (`{data['model_snapshot_comparison']['reference_working_tree_snapshot_sha256']}` vs `{data['model_snapshot_comparison']['monte_carlo_working_tree_snapshot_sha256']}`), even though their recorded configuration hashes match: the simulation code snapshots differ. The deterministic marker is therefore omitted from the Monte Carlo histogram; treat the reference run and campaign distribution as separate contextual results.

The saved Monte Carlo contains {mc['successful_cases']} successful debug cases and {mc['failed_cases']} failures. Corrected AGL is recomputed case by case as RocketPy ASL apogee minus the realized `rocketpy_elevation`; this avoids the stale derived `apogee_agl` values in the existing output artifact. The corrected distribution has median {stats['median']:.1f} m, 5th–95th percentile {stats['p05']:.1f}–{stats['p95']:.1f} m, and observed sample range {stats['minimum']:.1f}–{stats['maximum']:.1f} m.

The archived `outputs.parquet` AGL column differs from that per-case recomputation by up to {legacy_difference:.2f} m; the old run artifact was left untouched. For each case, the logged RocketPy elevation is compared with the declared `site_elevation` sample, and the other available sampled inputs are compared with their `rocketpy_` log fields in `comparison.json`. Those per-case values do not match (for site elevation, Pearson correlation is {mc['declared_vs_rocketpy_logged_input_pairing']['site_elevation']['pearson_correlation']:+.3f}); interpret apogee as a run-level distribution, not as paired input-to-output sensitivity evidence. Its text input log contains {infinity_count} `Infinity` tokens, which are not valid standard JSON numbers and need a separate artifact-format fix.

If the onboard relative-altitude maximum is treated as AGL, the larger sensor peak is {mc['sensor_peak_minus_mc_max_if_sensor_is_agl_m']:+.1f} m above the largest of these 50 simulated cases and {mc['sensor_peak_minus_mc_p95_if_sensor_is_agl_m']:+.1f} m above their 95th percentile; it is {mc['deterministic_reference_peak_difference_if_sensor_is_agl_m']:+.1f} m above the separate deterministic reference result. If the same channel is treated as ASL, it lies inside the Monte Carlo sample range ({mc['apogee_asl_m']['minimum']:.1f}–{mc['apogee_asl_m']['maximum']:.1f} m) and is {mc['deterministic_reference_peak_difference_if_sensor_is_asl_m']:+.1f} m above the deterministic reference ASL apogee. This datum choice changes the apparent agreement, so these are conditional magnitude comparisons, not a statistically defensible rejection: the sample is small, the sensor datum is unknown, the two model snapshots differ, and the current model's uncertainty assumptions are not a calibrated flight-specific distribution. The companion plot shows both interpretations separately.

`peak_aligned_altitude_shape.png` subtracts each measured channel's own peak and aligns that peak to the modelled apogee. This removes the unknown vertical offset and clock origin for a shape-only view. Alignment is imposed for plotting, so it cannot validate apogee timing or event-time accuracy. For BMP2 within the overlapping model-time domain, ascent residual mean/RMSE are {residual['ascent']['mean_bias_m']:+.1f}/{residual['ascent']['rmse_m']:.1f} m and post-peak mean/RMSE are {residual['post_peak']['mean_bias_m']:+.1f}/{residual['post_peak']['rmse_m']:.1f} m, with residual defined as observed minus modeled altitude relative to each peak. The first post-peak sample at +{residual['post_peak']['first_post_peak_sample_time_s']:.2f} s has residual {residual['post_peak']['first_post_peak_sample_residual_m']:+.1f} m; the residual is positive by +{residual['post_peak']['first_positive_residual_time_s']:.2f} s, reaches {residual['post_peak']['maximum_positive_residual_m']:.1f} m at +{residual['post_peak']['time_of_maximum_positive_residual_s']:.2f} s, stays positive through +{residual['post_peak']['last_positive_residual_time_s']:.2f} s, and is negative again at +{residual['post_peak']['first_negative_after_last_positive_time_s']:.2f} s. RocketPy's configured main deployment is +{data['rocketpy_reference']['main_deployment_time_s_after_apogee']:.2f} s after its apogee. The change in residual trend occurs near this modeled recovery transition, which makes recovery timing and descent rate worth reviewing; telemetry does not directly show deployment, so this is not evidence of a cause. Positive post-peak residual means the recorded channel remains higher than the model at the same peak-relative time. These are conditional diagnostics: model values are linearly sampled, while measured samples are not interpolated or extrapolated. The telemetry is sparse and likely affected by altimeter response.

## Weather and limitations

The saved atmosphere is a cached deterministic Open-Meteo GFS Seamless profile valid at `{data['weather']['candidate_profile_provenance'].get('valid_time_utc', 'unknown')}`. It is the model input candidate available in the current reference, not an observation of weather during the actual flight. The launch configuration records `{data['flight_clock']['planned_launch_datetime'].get('date')}` at `{data['flight_clock']['planned_launch_datetime'].get('time')}` as `{data['flight_clock']['planned_launch_datetime'].get('status')}`; converted to UTC, that planned time is `{data['weather']['planned_launch_time_utc']}`. The archived profile is valid {data['weather']['candidate_profile_minus_planned_time_hours']:+.1f} hours from the planned launch time. No verified actual launch timestamp ties the device counter to that weather profile. GPS coordinates are unavailable, and airspeed/attitude are not observable with the documented metadata. Weather correlation is therefore `NOT_ASSESSABLE`; no causal or correlational claim is made.

The Monte Carlo reuses one archived deterministic base atmosphere profile across 50 debug cases; its configuration also perturbs the x/y wind components per case (factor standard deviation 0.2, with an additional 1 m/s x-component standard deviation). It does not retain each case's time history and compares apogee only. These perturbations are model inputs, not measured flight weather or a time-matched weather ensemble. The raw telemetry remains ignored by Git and unchanged; PyCharm's orange file color reflects that Git-ignored status, not an inability to read the file.

## Artifacts

- `primary_flight_trace.parquet`: source-linked selected records and channels, with block-local elapsed time added.
- `altitude_and_raw_angular_rates.png`: recorded altitude and uncalibrated gyro channels.
- `peak_aligned_altitude_shape.png`: explicitly peak-aligned shape comparison.
- `peak_aligned_shape_residuals.parquet` and `peak_aligned_altitude_residuals.png`: conditional shape residuals within the modeled time domain.
- `mc_apogee_vs_recorded_peaks.png`: separate conditional AGL and ASL interpretations.
- `candidate_weather_profile.png`: archived candidate atmosphere profile.
- `comparison.json` and `artifact_manifest.json`: findings, provenance, and hashes.

Reproduce with:

```bash
.venv/bin/python projects/neblina_1/telemetry/compare_flight_to_monte_carlo.py
```
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path,
        help="new output directory under results/ (defaults to a UTC-stamped directory)",
    )
    args = parser.parse_args()
    if args.output is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        output = REPO_ROOT / "results/neblina_1" / f"{stamp}_flight_mc_comparison"
    else:
        output = args.output
    print(run(output))


if __name__ == "__main__":
    main()
