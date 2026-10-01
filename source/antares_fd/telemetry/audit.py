"""Provenance-preserving timebase and channel-quality diagnostics."""

from __future__ import annotations

import json
import math
import statistics
from collections import Counter
from typing import Any, Iterable

import numpy as np
import pandas as pd

from .loader import ParsedTelemetry
from .timebase import segment_timebase


FLAG_COLUMNS = (
    "dataset_id",
    "channel_name",
    "quality_flag",
    "severity",
    "source_line_number",
    "end_source_line_number",
    "timestamp_value",
    "trigger",
    "details_json",
)

SAMPLE_COLUMNS = (
    "dataset_id",
    "record_index",
    "source_line_number",
    "section_marker",
    "canonical_channel_name",
    "raw_channel_name",
    "raw_value",
    "numeric_value",
    "value_status",
    "timestamp_value",
    "timestamp_unit",
    "unit",
    "unit_status",
    "source_sensor",
    "sensor_class",
    "sensor_axis",
    "coordinate_frame",
    "data_type",
    "data_origin",
    "raw_source_file",
    "source_sha256",
    "conversion_applied",
    "calibration_status",
)

_TIME_UNIT_TO_SECONDS = {
    "ms": 0.001,
    "millisecond": 0.001,
    "milliseconds": 0.001,
    "s": 1.0,
    "sec": 1.0,
    "second": 1.0,
    "seconds": 1.0,
    "us": 0.000001,
    "µs": 0.000001,
    "microsecond": 0.000001,
    "microseconds": 0.000001,
    "ns": 0.000000001,
    "nanosecond": 0.000000001,
    "nanoseconds": 0.000000001,
    "min": 60.0,
    "minute": 60.0,
    "minutes": 60.0,
    "h": 3600.0,
    "hr": 3600.0,
    "hour": 3600.0,
    "hours": 3600.0,
}


def _flag(
    rows: list[dict[str, Any]],
    dataset_id: str,
    quality_flag: str,
    trigger: str,
    *,
    channel_name: str | None = None,
    severity: str = "WARNING",
    source_line_number: int | None = None,
    end_source_line_number: int | None = None,
    timestamp_value: float | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    rows.append(
        {
            "dataset_id": dataset_id,
            "channel_name": channel_name,
            "quality_flag": quality_flag,
            "severity": severity,
            "source_line_number": source_line_number,
            "end_source_line_number": end_source_line_number,
            "timestamp_value": timestamp_value,
            "trigger": trigger,
            "details_json": json.dumps(details or {}, sort_keys=True, ensure_ascii=False),
        }
    )


def _finite_values(parsed: ParsedTelemetry, channel: str) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    return [
        (record, record["values"][channel])
        for record in parsed.records
        if record["values"][channel]["value_status"] == "VALID"
    ]


def _robust_spread(values: list[float]) -> float | None:
    if not values:
        return None
    median = statistics.median(values)
    return float(1.4826 * statistics.median(abs(value - median) for value in values))


def _metadata_for_channel(channel: str, channels: dict[str, dict[str, Any]]) -> dict[str, Any]:
    try:
        return channels[channel]
    except KeyError as exc:
        raise ValueError(f"No provenance metadata declared for raw channel {channel!r}") from exc


def classify_gps(
    channel_names: Iterable[str],
    records: Iterable[dict[str, Any]],
    *,
    latitude_channel: str = "gps_lat_deg",
    longitude_channel: str = "gps_lon_deg",
    timestamp_channel: str = "time_ms",
    timestamp_unit: str | None = "ms",
) -> dict[str, Any]:
    """Classify in-range coordinate pairs; no GPS fix quality is inferred."""

    names = set(channel_names)
    record_list = list(records)
    if not {latitude_channel, longitude_channel}.issubset(names):
        return {
            "status": "GPS_CHANNEL_ABSENT",
            "coordinate_channels_present": sorted(names.intersection({latitude_channel, longitude_channel})),
            "in_range_coordinate_pair_count": 0,
            "record_count": len(record_list),
            "first_in_range_coordinate_pair_timestamp": None,
            "last_in_range_coordinate_pair_timestamp": None,
            "first_in_range_coordinate_pair_source_line_number": None,
            "last_in_range_coordinate_pair_source_line_number": None,
            "timestamp_unit": timestamp_unit,
            "coordinate_pair_transition_count": 0,
            "coordinate_pair_intervals": [],
            "fix_quality_status": "UNKNOWN_NOT_RECORDED",
        }

    valid_records: list[dict[str, Any]] = []
    validity_intervals: list[dict[str, Any]] = []
    interval_start: dict[str, Any] | None = None

    def is_valid(record: dict[str, Any]) -> bool:
        lat = record["values"][latitude_channel]["numeric_value"]
        lon = record["values"][longitude_channel]["numeric_value"]
        return lat is not None and lon is not None and -90 <= lat <= 90 and -180 <= lon <= 180

    def boundary(record: dict[str, Any]) -> dict[str, Any]:
        time_cell = record.get("values", {}).get(timestamp_channel, {})
        source_value = time_cell.get("numeric_value")
        return {
            "record_index": record.get("record_index"),
            "source_line_number": record.get("source_line_number"),
            "timestamp_value": source_value,
        }

    previous_valid = False
    validity_transitions = 0
    for record_index, record in enumerate(record_list):
        current_valid = is_valid(record)
        if current_valid:
            valid_records.append(record)
            if not previous_valid:
                interval_start = record
        elif previous_valid and interval_start is not None:
            validity_intervals.append({"start": boundary(interval_start), "end": boundary(previous_record)})
            interval_start = None
        if record_index > 0 and current_valid != previous_valid:
            validity_transitions += 1
        previous_valid = current_valid
        previous_record = record
    if previous_valid and interval_start is not None:
        validity_intervals.append({"start": boundary(interval_start), "end": boundary(record_list[-1])})

    count = len(valid_records)
    record_count = len(record_list)

    if count == 0:
        status = "GPS_PRESENT_BUT_INVALID"
    elif count < record_count:
        status = "GPS_COORDINATE_PAIRS_INTERMITTENT"
    else:
        status = "GPS_COORDINATE_PAIRS_ALL_ROWS"
    return {
        "status": status,
        "coordinate_channels_present": [latitude_channel, longitude_channel],
        "in_range_coordinate_pair_count": count,
        "record_count": record_count,
        "first_in_range_coordinate_pair_timestamp": boundary(valid_records[0])["timestamp_value"] if valid_records else None,
        "last_in_range_coordinate_pair_timestamp": boundary(valid_records[-1])["timestamp_value"] if valid_records else None,
        "first_in_range_coordinate_pair_source_line_number": boundary(valid_records[0])["source_line_number"] if valid_records else None,
        "last_in_range_coordinate_pair_source_line_number": boundary(valid_records[-1])["source_line_number"] if valid_records else None,
        "timestamp_unit": timestamp_unit,
        "coordinate_pair_transition_count": validity_transitions,
        "coordinate_pair_intervals": validity_intervals,
        "fix_quality_status": "UNKNOWN_NOT_RECORDED",
    }


def find_exact_duplicate_blocks(parsed: ParsedTelemetry) -> list[dict[str, Any]]:
    """Find marked sections repeated verbatim earlier in the same raw stream.

    Comparison uses every raw channel token, including missing-value spelling.
    This is evidence of repetition only; the acquisition mechanism is unknown.
    """

    tokens = [
        tuple(record["values"][channel]["raw_value"] for channel in parsed.channels)
        for record in parsed.records
    ]
    result: list[dict[str, Any]] = []
    start = 0
    while start < len(tokens):
        marker = parsed.records[start]["section_marker"]
        end = start + 1
        while end < len(tokens) and parsed.records[end]["section_marker"] == marker:
            end += 1
        if marker is not None:
            count = end - start
            for original in range(start - count + 1):
                if tokens[original] != tokens[start]:
                    continue
                if tokens[original : original + count] != tokens[start:end]:
                    continue
                result.append(
                    {
                        "original_start_record_index": original,
                        "original_end_record_index": original + count - 1,
                        "original_start_source_line_number": parsed.records[original]["source_line_number"],
                        "original_end_source_line_number": parsed.records[original + count - 1]["source_line_number"],
                        "duplicate_start_record_index": start,
                        "duplicate_end_record_index": end - 1,
                        "duplicate_start_source_line_number": parsed.records[start]["source_line_number"],
                        "duplicate_end_source_line_number": parsed.records[end - 1]["source_line_number"],
                        "record_count": count,
                        "section_marker": marker,
                        "comparison": "RAW_TOKENS_ALL_CHANNELS_IN_FILE_ORDER",
                        "mechanism": "UNKNOWN",
                    }
                )
        start = end
    return result


def audit_dataset(
    parsed: ParsedTelemetry,
    *,
    dataset_id: str,
    channel_metadata: list[dict[str, Any]],
    raw_source_file: str,
    gap_factor: float = 1.5,
) -> dict[str, Any]:
    """Return canonical inventory, long-form samples, and diagnostic tables."""

    if not math.isfinite(gap_factor) or gap_factor <= 1:
        raise ValueError("gap_factor must be finite and greater than 1")
    metadata_by_raw = {entry["raw_channel_name"]: entry for entry in channel_metadata}
    if len(metadata_by_raw) != len(channel_metadata):
        raise ValueError("Channel provenance contains duplicate raw_channel_name entries")
    if set(metadata_by_raw) != set(parsed.channels):
        missing = sorted(set(parsed.channels) - set(metadata_by_raw))
        extra = sorted(set(metadata_by_raw) - set(parsed.channels))
        raise ValueError(f"Channel provenance does not match the source header; missing={missing}, extra={extra}")

    timestamp_channel = next(
        (entry for entry in channel_metadata if entry.get("is_timestamp_channel")), None
    )
    if timestamp_channel is None:
        raise ValueError("Exactly one channel must be declared as the timestamp channel")
    time_name = timestamp_channel["raw_channel_name"]
    if sum(bool(entry.get("is_timestamp_channel")) for entry in channel_metadata) != 1:
        raise ValueError("Exactly one channel must be declared as the timestamp channel")

    source_time_unit = timestamp_channel.get("unit")
    time_unit_status = timestamp_channel.get("unit_status", "UNKNOWN")
    time_unit_key = str(source_time_unit or "").strip().casefold().replace(" ", "")
    seconds_per_unit = (
        None
        if time_unit_status == "UNKNOWN" or not time_unit_key
        else _TIME_UNIT_TO_SECONDS.get(time_unit_key)
    )
    time_values: list[float | None] = [
        record["values"][time_name]["numeric_value"] for record in parsed.records
    ]
    segments = segment_timebase(
        parsed,
        timestamp_channel=time_name,
        seconds_per_unit=seconds_per_unit,
    )
    segment_ids = segments["segment_id"].to_numpy()
    backward_jumps = int(segment_ids[-1])
    positive_deltas = [
        current - previous
        for previous, current in zip(time_values, time_values[1:])
        if previous is not None and current is not None and current > previous
    ]
    if not positive_deltas:
        raise ValueError("The timebase has no positive timestamp intervals")
    counts = Counter(positive_deltas)
    nominal_interval = min(counts, key=lambda value: (-counts[value], value))
    median_interval = float(statistics.median(positive_deltas))
    gap_threshold = nominal_interval * gap_factor

    timebase_rows: list[dict[str, Any]] = []
    gap_durations: list[float] = []
    duplicates = gaps = 0
    last_finite_time: float | None = None
    last_finite_line: int | None = None
    for index, record in enumerate(parsed.records):
        current = time_values[index]
        if index == 0:
            timebase_rows.append(
                {
                    "record_index": record["record_index"],
                    "source_line_number": record["source_line_number"],
                    "previous_source_line_number": None,
                    "previous_timestamp_value": None,
                    "timestamp_value": current,
                    "delta": None,
                    "interval_class": "FIRST_SAMPLE" if current is not None else "TIME_VALUE_MISSING",
                    "nominal_interval": nominal_interval,
                    "estimated_missing_samples": None,
                }
            )
            if current is not None:
                last_finite_time = current
                last_finite_line = record["source_line_number"]
            continue
        previous_record = parsed.records[index - 1]
        previous = time_values[index - 1]
        comparison_time = previous if previous is not None else last_finite_time
        comparison_line = previous_record["source_line_number"] if previous is not None else last_finite_line
        delta = None if current is None or comparison_time is None else current - comparison_time
        estimated_missing = None
        if current is None:
            interval_class = "TIME_VALUE_MISSING"
        elif comparison_time is None:
            interval_class = "FIRST_FINITE_TIMESTAMP"
        elif segment_ids[index] > segment_ids[index - 1]:
            interval_class = "TIMESTAMP_BACKWARD_JUMP"
        elif previous is None:
            interval_class = "INTERVAL_ACROSS_MISSING_TIMESTAMP"
        elif delta == 0:
            interval_class = "DUPLICATE_TIMESTAMP"
            duplicates += 1
        elif delta > gap_threshold:
            interval_class = "TIMESTAMP_GAP"
            gaps += 1
            gap_durations.append(float(delta - nominal_interval))
            estimated_missing = max(0, int(round(delta / nominal_interval)) - 1)
        else:
            interval_class = "NORMAL_INTERVAL"
        timebase_rows.append(
            {
                "record_index": record["record_index"],
                "source_line_number": record["source_line_number"],
                "previous_source_line_number": comparison_line,
                "previous_timestamp_value": comparison_time,
                "timestamp_value": current,
                "delta": delta,
                "interval_class": interval_class,
                "nominal_interval": nominal_interval,
                "estimated_missing_samples": estimated_missing,
            }
        )
        if current is not None:
            last_finite_time = current
            last_finite_line = record["source_line_number"]

    effective_hz = (
        len(positive_deltas) / (sum(positive_deltas) * seconds_per_unit)
        if seconds_per_unit is not None
        else None
    )
    interval_histogram = [
        {"interval": value, "count": count}
        for value, count in sorted(counts.items(), key=lambda item: item[0])
    ]
    timebase_summary = {
        "timestamp_channel": time_name,
        "time_unit": source_time_unit or "UNKNOWN",
        "time_unit_status": time_unit_status,
        "seconds_per_timestamp_unit": seconds_per_unit,
        "frequency_status": "COMPUTED" if seconds_per_unit is not None else "UNAVAILABLE_UNKNOWN_OR_UNSUPPORTED_UNIT",
        "initial_timestamp": time_values[0],
        "final_timestamp": time_values[-1],
        "minimum_timestamp": min(value for value in time_values if value is not None),
        "maximum_timestamp": max(value for value in time_values if value is not None),
        "record_count": len(parsed.records),
        "nominal_interval": nominal_interval,
        "median_positive_interval": median_interval,
        "effective_sample_frequency_hz": float(effective_hz) if effective_hz is not None else None,
        "median_interval_frequency_hz": 1.0 / (median_interval * seconds_per_unit) if seconds_per_unit is not None else None,
        "minimum_positive_interval": min(positive_deltas),
        "maximum_positive_interval": max(positive_deltas),
        "duplicate_timestamp_count": duplicates,
        "non_monotonic_timestamp_count": backward_jumps,
        "timestamp_backward_jump_count": backward_jumps,
        "gap_count": gaps,
        "gap_threshold": gap_threshold,
        "gap_detection_rule": f"positive delta > {gap_factor:g} × modal positive interval",
        "estimated_missing_samples_across_gaps": sum(
            int(row["estimated_missing_samples"] or 0) for row in timebase_rows
        ),
        "total_gap_duration_excess_over_nominal": float(sum(gap_durations)),
        "positive_interval_histogram": interval_histogram,
    }
    timebase_summary["segment_count"] = backward_jumps + 1
    timebase_summary["global_corrected_time_status"] = "UNAVAILABLE_UNJUSTIFIED_RESET_OFFSETS"

    flags: list[dict[str, Any]] = []
    for row in timebase_rows:
        classification = row["interval_class"]
        if classification == "TIMESTAMP_GAP":
            _flag(flags, dataset_id, "TIMESTAMP_GAP", "Positive interval exceeds configured modal-interval threshold", source_line_number=row["previous_source_line_number"], end_source_line_number=row["source_line_number"], timestamp_value=row["timestamp_value"], details={"delta": row["delta"], "nominal_interval": nominal_interval, "estimated_missing_samples": row["estimated_missing_samples"]})
        elif classification == "TIMESTAMP_BACKWARD_JUMP":
            _flag(flags, dataset_id, "TIMESTAMP_BACKWARD_JUMP", "Timestamp decreased relative to the preceding finite reading; cause unknown", source_line_number=row["previous_source_line_number"], end_source_line_number=row["source_line_number"], timestamp_value=row["timestamp_value"], details={"delta": row["delta"]})
            _flag(flags, dataset_id, "NON_MONOTONIC_TIME", "Timestamp decreased relative to the preceding finite reading; cause unknown", source_line_number=row["previous_source_line_number"], end_source_line_number=row["source_line_number"], timestamp_value=row["timestamp_value"], details={"delta": row["delta"]})
        elif classification == "DUPLICATE_TIMESTAMP":
            _flag(flags, dataset_id, "DUPLICATE_TIMESTAMP", "Adjacent records have identical timestamps", source_line_number=row["previous_source_line_number"], end_source_line_number=row["source_line_number"], timestamp_value=row["timestamp_value"])
        elif classification == "TIME_VALUE_MISSING":
            _flag(flags, dataset_id, "MISSING_TIMESTAMP", "At least one adjacent timestamp is missing", source_line_number=row["source_line_number"], timestamp_value=row["timestamp_value"])

    # Positional rows avoid allocating one Python dict per channel observation.
    # The named column contract is unchanged when the DataFrame is constructed.
    sample_rows: list[tuple[Any, ...]] = []
    channel_summaries: list[dict[str, Any]] = []
    for channel in parsed.channels:
        metadata = _metadata_for_channel(channel, metadata_by_raw)
        values = _finite_values(parsed, channel)
        numbers = [float(value["numeric_value"]) for _, value in values]
        missing_count = sum(record["values"][channel]["value_status"] == "MISSING" for record in parsed.records)
        non_numeric_count = sum(record["values"][channel]["value_status"] == "NON_NUMERIC" for record in parsed.records)
        non_finite_count = sum(record["values"][channel]["value_status"] == "NON_FINITE" for record in parsed.records)
        stats = {
            "dataset_id": dataset_id,
            "canonical_channel_name": metadata["canonical_name"],
            "raw_channel_name": channel,
            "source_sensor": metadata["source_sensor"],
            "sensor_class": metadata["sensor_class"],
            "sensor_axis": metadata.get("sensor_axis"),
            "coordinate_frame": metadata["coordinate_frame"],
            "unit": metadata.get("unit"),
            "unit_status": metadata["unit_status"],
            "unit_source": metadata.get("unit_source"),
            "data_type": metadata["data_type"],
            "data_origin": metadata["data_origin"],
            "raw_source_file": raw_source_file,
            "conversion_applied": metadata.get("conversion_applied"),
            "calibration_status": metadata["calibration_status"],
            "count": len(parsed.records),
            "valid_count": len(numbers),
            "missing_count": missing_count,
            "missing_fraction": missing_count / len(parsed.records),
            "non_numeric_count": non_numeric_count,
            "non_finite_count": non_finite_count,
            "minimum": min(numbers) if numbers else None,
            "maximum": max(numbers) if numbers else None,
            "mean": float(statistics.fmean(numbers)) if numbers else None,
            "median": float(statistics.median(numbers)) if numbers else None,
            "standard_deviation": float(statistics.stdev(numbers)) if len(numbers) > 1 else (0.0 if numbers else None),
            "robust_spread_mad_scaled": _robust_spread(numbers),
            "unique_finite_values": len(set(numbers)),
            "first_valid_source_line_number": values[0][0]["source_line_number"] if values else None,
            "last_valid_source_line_number": values[-1][0]["source_line_number"] if values else None,
            "first_valid_timestamp": time_values[values[0][0]["record_index"]] if values else None,
            "last_valid_timestamp": time_values[values[-1][0]["record_index"]] if values else None,
            "timestamp_unit": source_time_unit or "UNKNOWN",
        }
        channel_summaries.append(stats)

        if missing_count:
            _flag(flags, dataset_id, "MISSING_VALUES", "One or more samples are explicitly missing", channel_name=metadata["canonical_name"], details={"missing_count": missing_count, "missing_fraction": stats["missing_fraction"]})
        if non_numeric_count or non_finite_count:
            _flag(flags, dataset_id, "INVALID_NUMERIC_VALUES", "One or more channel tokens could not be represented as finite numbers", channel_name=metadata["canonical_name"], details={"non_numeric_count": non_numeric_count, "non_finite_count": non_finite_count})
        if metadata.get("unit") is None or metadata.get("unit_status") == "UNKNOWN":
            _flag(flags, dataset_id, "UNIT_UNKNOWN", "No supported unit is declared for this channel", channel_name=metadata["canonical_name"])
        elif metadata.get("unit_status") == "UNIT_ASSUMED":
            _flag(flags, dataset_id, "UNIT_ASSUMED", "Unit is explicitly assumed and has not been verified", channel_name=metadata["canonical_name"], details={"unit": metadata.get("unit")})
        if channel == time_name and source_time_unit is not None and time_unit_status != "UNKNOWN" and seconds_per_unit is None:
            _flag(flags, dataset_id, "TIME_UNIT_UNSUPPORTED", "Timestamp unit is declared but has no supported conversion to seconds; frequency is unavailable", channel_name=metadata["canonical_name"], details={"unit": source_time_unit})
        frame = str(metadata["coordinate_frame"])
        if "UNKNOWN" in frame:
            _flag(flags, dataset_id, "FRAME_UNKNOWN", "Coordinate frame or reference datum is not fully documented", channel_name=metadata["canonical_name"], details={"coordinate_frame": frame})
        if metadata.get("sensor_class") in {None, "", "UNKNOWN"} or metadata.get("source_sensor") in {None, "", "UNKNOWN"}:
            _flag(flags, dataset_id, "INSUFFICIENT_METADATA", "Sensor identity or class is not documented", channel_name=metadata["canonical_name"])

        if len(numbers) > 1 and len(set(numbers)) == 1:
            _flag(flags, dataset_id, "STUCK_CHANNEL", "All finite values are identical; this is a diagnostic suspicion only", channel_name=metadata["canonical_name"], source_line_number=values[0][0]["source_line_number"], end_source_line_number=values[-1][0]["source_line_number"], details={"value": numbers[0], "valid_count": len(numbers)})

        if numbers:
            low = min(numbers)
            high = max(numbers)
            for rail, endpoint in (("minimum", low), ("maximum", high)):
                run_start: tuple[dict[str, Any], dict[str, Any]] | None = None
                run_length = 0
                previous_index: int | None = None
                for record in parsed.records:
                    cell = record["values"][channel]
                    is_endpoint = cell["value_status"] == "VALID" and cell["numeric_value"] == endpoint
                    if is_endpoint and (previous_index is None or record["record_index"] == previous_index + 1):
                        if run_start is None:
                            run_start = (record, cell)
                        run_length += 1
                    else:
                        if run_length >= 3 and run_start is not None:
                            _flag(flags, dataset_id, "POSSIBLE_SATURATION", "At least three consecutive samples repeat an observed channel extreme; hardware limits are undocumented", channel_name=metadata["canonical_name"], source_line_number=run_start[0]["source_line_number"], end_source_line_number=parsed.records[previous_index]["source_line_number"] if previous_index is not None else None, timestamp_value=time_values[run_start[0]["record_index"]], details={"extreme": rail, "value": endpoint, "run_length": run_length})
                        run_start = (record, cell) if is_endpoint else None
                        run_length = 1 if is_endpoint else 0
                    previous_index = record["record_index"]
                if run_length >= 3 and run_start is not None:
                    _flag(flags, dataset_id, "POSSIBLE_SATURATION", "At least three consecutive samples repeat an observed channel extreme; hardware limits are undocumented", channel_name=metadata["canonical_name"], source_line_number=run_start[0]["source_line_number"], end_source_line_number=parsed.records[-1]["source_line_number"], timestamp_value=time_values[run_start[0]["record_index"]], details={"extreme": rail, "value": endpoint, "run_length": run_length})

        # A robust step indicator is descriptive only. Do not flag changes across
        # missing samples, resets, or intervals already classified as possible gaps.
        consecutive_differences: list[tuple[dict[str, Any], dict[str, Any], float]] = []
        channel_cells = [record["values"][channel] for record in parsed.records]
        if channel != time_name:
            for index in range(1, len(parsed.records)):
                before = channel_cells[index - 1]["numeric_value"]
                after = channel_cells[index]["numeric_value"]
                delta_t = timebase_rows[index]["delta"]
                if (
                    before is not None
                    and after is not None
                    and timebase_rows[index]["interval_class"] == "NORMAL_INTERVAL"
                    and delta_t is not None
                    and 0 < delta_t <= gap_threshold
                ):
                    consecutive_differences.append((parsed.records[index - 1], parsed.records[index], abs(after - before)))
        nonzero_differences = [item[2] for item in consecutive_differences if item[2] > 0]
        if len(nonzero_differences) >= 3:
            threshold = float(np.quantile(nonzero_differences, 0.995))
            for before_record, after_record, difference in consecutive_differences:
                if difference > threshold:
                    _flag(flags, dataset_id, "LARGE_DISCONTINUITY", "Absolute adjacent change is above the channel's 99.5th percentile of nonzero changes; no sample is removed", channel_name=metadata["canonical_name"], source_line_number=before_record["source_line_number"], end_source_line_number=after_record["source_line_number"], timestamp_value=time_values[after_record["record_index"]], details={"absolute_change": difference, "threshold": threshold, "reference_percentile": 0.995})

        for record in parsed.records:
            cell = record["values"][channel]
            sample_rows.append((
                dataset_id,
                record["record_index"],
                record["source_line_number"],
                record["section_marker"],
                metadata["canonical_name"],
                channel,
                cell["raw_value"],
                cell["numeric_value"],
                cell["value_status"],
                time_values[record["record_index"]],
                source_time_unit or "UNKNOWN",
                metadata.get("unit"),
                metadata["unit_status"],
                metadata["source_sensor"],
                metadata["sensor_class"],
                metadata.get("sensor_axis"),
                metadata["coordinate_frame"],
                metadata["data_type"],
                metadata["data_origin"],
                raw_source_file,
                parsed.source_sha256,
                metadata.get("conversion_applied"),
                metadata["calibration_status"],
            ))

    gps = classify_gps(
        parsed.channels,
        parsed.records,
        timestamp_channel=time_name,
        timestamp_unit=source_time_unit,
    )
    if gps["status"] == "GPS_PRESENT_BUT_INVALID":
        _flag(flags, dataset_id, "GPS_INVALID", "Latitude/longitude channels exist but no sample forms an in-range coordinate pair", details=gps)
    elif gps["status"] == "GPS_COORDINATE_PAIRS_INTERMITTENT":
        _flag(flags, dataset_id, "GPS_COORDINATE_PAIRS_INTERMITTENT", "Some rows have in-range coordinate pairs, but GPS fix quality is unknown", details=gps)

    issue_counts = Counter(issue["kind"] for issue in parsed.parse_issues)
    if parsed.parse_issues:
        _flag(flags, dataset_id, "PARSE_ISSUES", "One or more source lines were not telemetry samples and were retained as parse issues", details={"issue_count": len(parsed.parse_issues), "kinds": dict(sorted(issue_counts.items()))})

    inventory = {
        "schema_version": "1.0",
        "audit_version": "1.0",
        "dataset_id": dataset_id,
        "source_file": raw_source_file,
        "source_sha256": parsed.source_sha256,
        "source_size_bytes": parsed.source_size_bytes,
        "source_encoding": parsed.encoding,
        "delimiter": parsed.delimiter,
        "header_line_number": parsed.header_line_number,
        "header_channels": list(parsed.channels),
        "record_count": len(parsed.records),
        "first_record_source_line_number": parsed.records[0]["source_line_number"],
        "last_record_source_line_number": parsed.records[-1]["source_line_number"],
        "parse_issue_count": len(parsed.parse_issues),
        "parse_issue_counts": dict(sorted(issue_counts.items())),
        "parse_issues": list(parsed.parse_issues),
        "exact_duplicate_blocks": find_exact_duplicate_blocks(parsed),
        "timebase": timebase_summary,
        "gps": gps,
        "channels": channel_metadata,
        "provenance_semantics": {
            "MEASURED": "Value emitted by a recorded sensor or device channel; no later conversion is implied.",
            "DERIVED": "Value computed onboard or from another measured quantity; the derivation may be undocumented.",
            "INFERRED": "A conclusion estimated from one or more observations; not a direct sensor measurement.",
        },
        "quality_flag_rules": {
            "MISSING_VALUES": "At least one explicit blank/NaN token in a numeric channel.",
            "TIMESTAMP_GAP": "Positive adjacent interval greater than gap_factor times the modal positive interval; heuristic only.",
            "TIMESTAMP_BACKWARD_JUMP": "Current timestamp is less than the preceding finite reading; the mechanism is unknown.",
            "DUPLICATE_TIMESTAMP": "Adjacent records have identical timestamps.",
            "NON_MONOTONIC_TIME": "Current timestamp is less than the preceding finite reading.",
            "POSSIBLE_SATURATION": "Three or more adjacent finite samples repeat an observed channel extreme; hardware limits are unknown.",
            "STUCK_CHANNEL": "All finite channel values are identical; sensor failure is not concluded.",
            "LARGE_DISCONTINUITY": "Adjacent finite value change is above that channel's 99.5th percentile of nonzero adjacent changes; the timestamp channel and intervals across gaps/resets/missing samples are excluded; no sample is removed.",
            "UNIT_UNKNOWN": "No supported unit is declared for a channel.",
            "UNIT_ASSUMED": "A unit was explicitly assumed and has not been verified.",
            "TIME_UNIT_UNSUPPORTED": "Timestamp unit is declared but cannot be converted to SI seconds by this audit; sample frequency is unavailable.",
            "FRAME_UNKNOWN": "Coordinate frame or reference datum is not fully documented.",
            "GPS_INVALID": "Latitude/longitude channels exist but no in-range coordinate pair is present.",
            "GPS_COORDINATE_PAIRS_INTERMITTENT": "Some but not all stream records have an in-range coordinate pair; fix quality is unknown.",
            "INSUFFICIENT_METADATA": "Sensor identity or class is absent or explicitly unknown.",
            "INVALID_NUMERIC_VALUES": "A non-empty channel token is nonnumeric or non-finite.",
            "MISSING_TIMESTAMP": "At least one adjacent timestamp is absent or not finite.",
            "PARSE_ISSUES": "The source contains non-sample lines or malformed rows preserved in the inventory.",
        },
    }

    return {
        "inventory": inventory,
        "samples": pd.DataFrame.from_records(sample_rows, columns=SAMPLE_COLUMNS),
        "channel_statistics": pd.DataFrame(channel_summaries),
        "timebase_diagnostics": pd.DataFrame(timebase_rows),
        "segments": segments,
        "sensor_quality_flags": pd.DataFrame(flags, columns=FLAG_COLUMNS),
    }
