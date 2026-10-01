from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest
import yaml

from antares_fd.telemetry.artifacts import TelemetryArtifactError, audit_project, verify_artifact_set
from antares_fd.telemetry.audit import audit_dataset, classify_gps
from antares_fd.telemetry.loader import TelemetryParseError, parse_telemetry_log
from antares_fd.telemetry.timebase import segment_timebase


HEADER = ("time_ms", "accel_x", "constant", "gps_lat_deg", "gps_lon_deg", "mystery")


def _channel_metadata() -> list[dict]:
    definitions = {
        "time_ms": ("system_clock", "system_clock", None, "NOT_APPLICABLE", "ms", "HEADER_LABEL", "MEASURED", True),
        "accel_x": ("accelerometer A", "accelerometer", "x", "UNKNOWN", "g", "HEADER_LABEL", "MEASURED", False),
        "constant": ("device status", "system", None, "NOT_APPLICABLE", "count", "HEADER_LABEL", "MEASURED", False),
        "gps_lat_deg": ("GPS", "gps", None, "GEODETIC_DATUM_UNKNOWN", "deg", "HEADER_LABEL", "MEASURED", False),
        "gps_lon_deg": ("GPS", "gps", None, "GEODETIC_DATUM_UNKNOWN", "deg", "HEADER_LABEL", "MEASURED", False),
        "mystery": ("sensor unknown", "unknown", None, "UNKNOWN", None, "UNKNOWN", "DERIVED", False),
    }
    result = []
    for channel in HEADER:
        sensor, sensor_class, axis, frame, unit, unit_status, origin, is_time = definitions[channel]
        result.append(
            {
                "canonical_name": channel,
                "raw_channel_name": channel,
                "unit": unit,
                "unit_status": unit_status,
                "unit_source": "synthetic_header" if unit else None,
                "source_sensor": sensor,
                "sensor_class": sensor_class,
                "sensor_axis": axis,
                "coordinate_frame": frame,
                "data_type": "float64",
                "data_origin": origin,
                "calibration_status": "UNKNOWN",
                "conversion_applied": None,
                "is_timestamp_channel": is_time,
            }
        )
    return result


def _write_log(path: Path, rows: list[list[str]], extra: str = "") -> bytes:
    text = "firmware boot\n" + ",".join(HEADER) + "\n"
    text += "\n".join(",".join(row) for row in rows) + "\n"
    if extra:
        text += extra
    path.write_bytes(text.encode("utf-8"))
    return path.read_bytes()


def _rows() -> list[list[str]]:
    return [
        ["0", "-2", "7", "nan", "nan", "1"],
        ["100", "-2", "7", "91", "181", "2"],
        ["200", "-2", "7", "44", "-70", "3"],
        ["800", "0", "7", "nan", "nan", "4"],
        ["50", "1", "7", "nan", "nan", "5"],
        ["150", "2", "7", "nan", "nan", "6"],
        ["150", "3", "7", "nan", "nan", "7"],
    ]


def _parse_and_audit(tmp_path: Path):
    raw_path = tmp_path / "synthetic.log"
    _write_log(raw_path, _rows(), extra="\nfooter\n")
    parsed = parse_telemetry_log(
        raw_path,
        header_channel="time_ms",
        timestamp_channel="time_ms",
        expected_channels=HEADER,
        section_markers=(),
    )
    audited = audit_dataset(
        parsed,
        dataset_id="synthetic",
        channel_metadata=_channel_metadata(),
        raw_source_file="synthetic.log",
    )
    return raw_path, parsed, audited


def test_parser_preserves_schema_raw_tokens_and_source_file_bytes(tmp_path: Path) -> None:
    raw_path = tmp_path / "synthetic.log"
    before = _write_log(raw_path, _rows(), extra="\nfooter\n")
    parsed = parse_telemetry_log(
        raw_path,
        header_channel="time_ms",
        timestamp_channel="time_ms",
        expected_channels=HEADER,
    )

    assert parsed.channels == HEADER
    assert parsed.header_line_number == 2
    assert parsed.records[0]["values"]["accel_x"]["raw_value"] == "-2"
    assert parsed.records[0]["values"]["gps_lat_deg"]["value_status"] == "MISSING"
    assert [issue["kind"] for issue in parsed.parse_issues] == ["EMPTY_LINE", "ROW_WIDTH_MISMATCH"]
    assert parsed.source_sha256 == hashlib.sha256(before).hexdigest()
    assert raw_path.read_bytes() == before


def test_timebase_detects_gaps_backward_jumps_duplicates_and_non_monotonic_time(tmp_path: Path) -> None:
    _, _, audited = _parse_and_audit(tmp_path)
    intervals = audited["timebase_diagnostics"]["interval_class"].tolist()
    flags = audited["sensor_quality_flags"]["quality_flag"].tolist()

    assert "TIMESTAMP_GAP" in intervals
    assert "TIMESTAMP_BACKWARD_JUMP" in intervals
    assert "DUPLICATE_TIMESTAMP" in intervals
    assert "TIMESTAMP_GAP" in flags
    assert "TIMESTAMP_BACKWARD_JUMP" in flags
    assert "NON_MONOTONIC_TIME" in flags
    assert "DUPLICATE_TIMESTAMP" in flags
    assert audited["inventory"]["timebase"]["timestamp_backward_jump_count"] == 1
    assert audited["inventory"]["timebase"]["segment_count"] == 2
    assert audited["inventory"]["timebase"]["duplicate_timestamp_count"] == 1


def test_segment_timebase_preserves_file_order_without_cross_reset_stitching(tmp_path: Path) -> None:
    raw_path = tmp_path / "clock.log"
    rows = [
        ["100", "0", "7", "nan", "nan", "1"],
        ["200", "0", "7", "nan", "nan", "2"],
        ["", "0", "7", "nan", "nan", "3"],
        ["50", "0", "7", "nan", "nan", "4"],
        ["50", "0", "7", "nan", "nan", "5"],
        ["70", "0", "7", "nan", "nan", "6"],
    ]
    _write_log(raw_path, rows)
    parsed = parse_telemetry_log(raw_path, header_channel="time_ms", timestamp_channel="time_ms")

    segments = segment_timebase(parsed, timestamp_channel="time_ms", seconds_per_unit=0.001)

    assert segments["record_index"].tolist() == list(range(6))
    assert segments["source_line_number"].tolist() == [3, 4, 5, 6, 7, 8]
    assert segments["segment_id"].tolist() == [0, 0, 0, 1, 1, 1]
    assert segments["raw_time"].iloc[3] == 50
    assert segments["segment_elapsed_s"].iloc[[0, 1, 3, 4, 5]].tolist() == pytest.approx([0, 0.1, 0, 0, 0.02])
    assert pd.isna(segments["segment_elapsed_s"].iloc[2])
    assert "corrected_monotonic_time" not in segments.columns


def test_audit_and_segments_agree_on_backward_jump_across_missing_clock(tmp_path: Path) -> None:
    raw_path = tmp_path / "clock_gap.log"
    rows = [
        ["100", "0", "7", "nan", "nan", "1"],
        ["200", "0", "7", "nan", "nan", "2"],
        ["", "0", "7", "nan", "nan", "3"],
        ["50", "0", "7", "nan", "nan", "4"],
        ["70", "0", "7", "nan", "nan", "5"],
    ]
    _write_log(raw_path, rows)
    parsed = parse_telemetry_log(raw_path, header_channel="time_ms", timestamp_channel="time_ms")

    audited = audit_dataset(
        parsed,
        dataset_id="clock_gap",
        channel_metadata=_channel_metadata(),
        raw_source_file="clock_gap.log",
    )

    diagnostics = audited["timebase_diagnostics"]
    assert diagnostics["interval_class"].tolist() == [
        "FIRST_SAMPLE", "TIMESTAMP_GAP", "TIME_VALUE_MISSING", "TIMESTAMP_BACKWARD_JUMP", "NORMAL_INTERVAL"
    ]
    assert diagnostics.iloc[3]["previous_source_line_number"] == 4
    assert diagnostics.iloc[3]["delta"] == -150
    assert audited["segments"]["segment_id"].tolist() == [0, 0, 0, 1, 1]
    assert audited["inventory"]["timebase"]["timestamp_backward_jump_count"] == 1
    assert audited["inventory"]["timebase"]["segment_count"] == 2
    assert "timestamp_reset_count" not in audited["inventory"]["timebase"]


def test_segment_elapsed_is_unavailable_without_documented_clock_scale(tmp_path: Path) -> None:
    raw_path = tmp_path / "clock.log"
    _write_log(raw_path, _rows())
    parsed = parse_telemetry_log(raw_path, header_channel="time_ms", timestamp_channel="time_ms")

    segments = segment_timebase(parsed, timestamp_channel="time_ms", seconds_per_unit=None)

    assert segments["segment_id"].tolist() == [0, 0, 0, 0, 1, 1, 1]
    assert segments["segment_elapsed_s"].isna().all()


def test_channel_statistics_flag_missing_stuck_saturation_and_unknown_metadata(tmp_path: Path) -> None:
    _, _, audited = _parse_and_audit(tmp_path)
    stats = audited["channel_statistics"].set_index("raw_channel_name")
    flags = audited["sensor_quality_flags"]
    flag_pairs = set(zip(flags["quality_flag"], flags["channel_name"], strict=True))

    assert stats.loc["accel_x", "valid_count"] == 7
    assert stats.loc["gps_lat_deg", "missing_count"] == 5
    assert stats.loc["constant", "unique_finite_values"] == 1
    assert ("POSSIBLE_SATURATION", "accel_x") in flag_pairs
    assert ("STUCK_CHANNEL", "constant") in flag_pairs
    assert ("UNIT_UNKNOWN", "mystery") in flag_pairs
    assert ("FRAME_UNKNOWN", "accel_x") in flag_pairs
    assert stats.loc["mystery", "data_origin"] == "DERIVED"


def test_assumed_units_are_explicitly_flagged(tmp_path: Path) -> None:
    _, parsed, _ = _parse_and_audit(tmp_path)
    metadata = _channel_metadata()
    metadata[-1]["unit"] = "device-unit"
    metadata[-1]["unit_status"] = "UNIT_ASSUMED"
    audited = audit_dataset(
        parsed,
        dataset_id="synthetic",
        channel_metadata=metadata,
        raw_source_file="synthetic.log",
    )

    flags = audited["sensor_quality_flags"]
    assert ((flags["quality_flag"] == "UNIT_ASSUMED") & (flags["channel_name"] == "mystery")).any()


def test_timebase_uses_declared_units_and_does_not_invent_frequency(tmp_path: Path) -> None:
    _, parsed, _ = _parse_and_audit(tmp_path)
    seconds_metadata = _channel_metadata()
    seconds_metadata[0]["unit"] = "s"
    seconds = audit_dataset(
        parsed,
        dataset_id="seconds_clock",
        channel_metadata=seconds_metadata,
        raw_source_file="synthetic.log",
    )
    unknown_metadata = _channel_metadata()
    unknown_metadata[0]["unit"] = None
    unknown_metadata[0]["unit_status"] = "UNKNOWN"
    unknown = audit_dataset(
        parsed,
        dataset_id="unknown_clock",
        channel_metadata=unknown_metadata,
        raw_source_file="synthetic.log",
    )
    unsupported_metadata = _channel_metadata()
    unsupported_metadata[0]["unit"] = "device_tick"
    unsupported_metadata[0]["unit_status"] = "DOCUMENTED"
    unsupported = audit_dataset(
        parsed,
        dataset_id="unsupported_clock",
        channel_metadata=unsupported_metadata,
        raw_source_file="synthetic.log",
    )

    assert seconds["inventory"]["timebase"]["nominal_interval"] == 100
    assert seconds["inventory"]["timebase"]["time_unit"] == "s"
    assert seconds["inventory"]["timebase"]["effective_sample_frequency_hz"] == pytest.approx(4 / 900)
    assert unknown["inventory"]["timebase"]["effective_sample_frequency_hz"] is None
    assert unknown["inventory"]["timebase"]["frequency_status"].startswith("UNAVAILABLE")
    assert ((unknown["sensor_quality_flags"]["quality_flag"] == "UNIT_UNKNOWN") & (unknown["sensor_quality_flags"]["channel_name"] == "time_ms")).any()
    assert unsupported["inventory"]["timebase"]["effective_sample_frequency_hz"] is None
    assert ((unsupported["sensor_quality_flags"]["quality_flag"] == "TIME_UNIT_UNSUPPORTED") & (unsupported["sensor_quality_flags"]["channel_name"] == "time_ms")).any()


def test_gps_status_distinguishes_invalid_partial_absent_and_usable() -> None:
    absent = classify_gps(["time_ms"], [])
    invalid_records = [
        {"values": {"gps_lat_deg": {"numeric_value": None}, "gps_lon_deg": {"numeric_value": None}}}
    ]
    invalid = classify_gps(["gps_lat_deg", "gps_lon_deg"], invalid_records)
    mixed_records = [
        {"values": {"gps_lat_deg": {"numeric_value": 45.0}, "gps_lon_deg": {"numeric_value": -70.0}}},
        {"values": {"gps_lat_deg": {"numeric_value": None}, "gps_lon_deg": {"numeric_value": None}}},
    ]
    partial = classify_gps(["gps_lat_deg", "gps_lon_deg"], mixed_records)
    usable = classify_gps(["gps_lat_deg", "gps_lon_deg"], mixed_records[:1])

    assert absent["status"] == "GPS_CHANNEL_ABSENT"
    assert invalid["status"] == "GPS_PRESENT_BUT_INVALID"
    assert partial["status"] == "GPS_COORDINATE_PAIRS_INTERMITTENT"
    assert usable["status"] == "GPS_COORDINATE_PAIRS_ALL_ROWS"
    assert usable["in_range_coordinate_pair_count"] == 1
    assert usable["fix_quality_status"] == "UNKNOWN_NOT_RECORDED"


def test_large_discontinuity_flag_uses_robust_threshold_and_skips_time_channel(tmp_path: Path) -> None:
    rows = []
    for index in range(12):
        accel = "1000" if index == 6 else str(index)
        rows.append([str(index * 100), accel, "7", "nan", "nan", str(index)])
    raw_path = tmp_path / "spike.log"
    _write_log(raw_path, rows)
    parsed = parse_telemetry_log(raw_path, header_channel="time_ms", timestamp_channel="time_ms", expected_channels=HEADER)
    audited = audit_dataset(
        parsed,
        dataset_id="spike",
        channel_metadata=_channel_metadata(),
        raw_source_file="spike.log",
    )
    flags = audited["sensor_quality_flags"]
    jumps = flags.loc[flags["quality_flag"] == "LARGE_DISCONTINUITY"]

    assert 0 < len(jumps) <= 2
    assert "time_ms" not in jumps["channel_name"].tolist()
    assert set(jumps["channel_name"]) == {"accel_x"}


def test_schema_mismatch_fails_loudly(tmp_path: Path) -> None:
    raw_path = tmp_path / "synthetic.log"
    _write_log(raw_path, _rows())
    with pytest.raises(TelemetryParseError, match="does not match the declared schema"):
        parse_telemetry_log(
            raw_path,
            header_channel="time_ms",
            timestamp_channel="time_ms",
            expected_channels=("time_ms", "other"),
        )


def test_marked_duplicate_block_is_reported_without_dropping_records(tmp_path: Path) -> None:
    raw_path = tmp_path / "repeated.log"
    first = ["100", "1", "7", "nan", "nan", "1"]
    second = ["200", "2", "7", "nan", "nan", "2"]
    text = "boot\n" + ",".join(HEADER) + "\n"
    text += ",".join(first) + "\n" + ",".join(second) + "\n"
    text += ",".join(["300", "3", "7", "nan", "nan", "3"]) + "\n"
    text += "DADOS DE VÔO\n" + ",".join(first) + "\n" + ",".join(second) + "\n"
    raw_path.write_text(text, encoding="utf-8")
    parsed = parse_telemetry_log(
        raw_path,
        header_channel="time_ms",
        timestamp_channel="time_ms",
        section_markers=("DADOS DE VÔO",),
    )

    audited = audit_dataset(
        parsed,
        dataset_id="duplicate_section",
        channel_metadata=_channel_metadata(),
        raw_source_file="repeated.log",
    )

    assert len(parsed.records) == 5
    assert len(audited["samples"]) == 5 * len(HEADER)
    assert audited["inventory"]["exact_duplicate_blocks"] == [
        {
            "original_start_record_index": 0,
            "original_end_record_index": 1,
            "original_start_source_line_number": 3,
            "original_end_source_line_number": 4,
            "duplicate_start_record_index": 3,
            "duplicate_end_record_index": 4,
            "duplicate_start_source_line_number": 7,
            "duplicate_end_source_line_number": 8,
            "record_count": 2,
            "section_marker": "DADOS DE VÔO",
            "comparison": "RAW_TOKENS_ALL_CHANNELS_IN_FILE_ORDER",
            "mechanism": "UNKNOWN",
        }
    ]


def test_identical_input_produces_deterministic_audit_tables(tmp_path: Path) -> None:
    _, _, first = _parse_and_audit(tmp_path)
    _, _, second = _parse_and_audit(tmp_path)

    for key in ("samples", "channel_statistics", "timebase_diagnostics", "sensor_quality_flags"):
        pd.testing.assert_frame_equal(first[key], second[key])
    assert first["inventory"] == second["inventory"]


def _write_project_fixture(root: Path) -> tuple[Path, Path, Path]:
    project = root / "projects" / "fixture"
    metadata_path = project / "telemetry" / "metadata" / "dataset.yaml"
    source_path = root / "data" / "fixture.log"
    output_dir = root / "results" / "fixture" / "audit"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    _write_log(source_path, _rows(), extra="\nfooter\n")
    metadata = {
        "dataset_id": "fixture_dataset",
        "header_channel": "time_ms",
        "timestamp_channel": "time_ms",
        "gap_factor": 1.5,
        "raw_data": {"path": "data/fixture.log", "format": "csv_with_text_preamble", "encoding": "utf-8", "delimiter": ","},
        "channels": _channel_metadata(),
    }
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(yaml.safe_dump(metadata, sort_keys=False), encoding="utf-8")
    return project, source_path, output_dir


def test_artifacts_are_machine_readable_verifiable_and_do_not_change_raw(tmp_path: Path) -> None:
    project, source_path, output_dir = _write_project_fixture(tmp_path)
    raw_before = source_path.read_bytes()
    expected_sha = hashlib.sha256(raw_before).hexdigest()

    result = audit_project(project, repo_root=tmp_path, output_dir=output_dir)
    manifest = verify_artifact_set(result)
    inventory = json.loads((result / "telemetry_inventory.json").read_text(encoding="utf-8"))
    samples = pd.read_parquet(result / "telemetry_samples.parquet")
    report = (result / "telemetry_quality_report.md").read_text(encoding="utf-8")
    gps = inventory["gps"]

    assert manifest["source_sha256"] == expected_sha
    assert inventory["source_sha256"] == expected_sha
    assert len(samples) == len(_rows()) * len(HEADER)
    assert (samples["raw_channel_name"] == "accel_x").sum() == len(_rows())
    assert "GPS_COORDINATE_PAIRS_INTERMITTENT" in report
    assert "Timebase" in report and "Known limitations" in report
    assert gps["first_in_range_coordinate_pair_timestamp"] == 200
    assert gps["last_in_range_coordinate_pair_timestamp"] == 200
    assert len(gps["coordinate_pair_intervals"]) == 1
    assert gps["in_range_coordinate_pair_count"] == 1
    assert "200.0–200.0 ms" in report
    segments = pd.read_parquet(result / "telemetry_segments.parquet")
    assert len(segments) == len(_rows())
    assert segments["segment_id"].tolist() == [0, 0, 0, 0, 1, 1, 1]
    assert segments["segment_elapsed_s"].iloc[4] == 0
    calibration = json.loads((result / "sensor_calibration_manifest.json").read_text(encoding="utf-8"))
    assert calibration["source_sha256"] == expected_sha
    assert calibration["status"] == "BLOCKED_BY_MISSING_METADATA"
    accel = next(sensor for sensor in calibration["sensors"] if sensor["source_sensor"] == "accelerometer A")
    assert accel["model"] == "UNKNOWN"
    assert accel["channels"][0]["scale"] == "UNKNOWN"
    assert accel["channels"][0]["coordinate_frame"] == "UNKNOWN"
    assert source_path.read_bytes() == raw_before

    (result / "channel_statistics.parquet").write_bytes(b"corrupt")
    with pytest.raises(TelemetryArtifactError, match="Checksum mismatch"):
        verify_artifact_set(result)


@pytest.mark.parametrize("relative_output", ["data/derived", "projects/fixture/report"])
def test_audit_rejects_output_outside_ignored_results_without_touching_raw(
    tmp_path: Path, relative_output: str
) -> None:
    project, source_path, _ = _write_project_fixture(tmp_path)
    raw_before = source_path.read_bytes()
    destination = tmp_path / relative_output

    with pytest.raises(ValueError, match="ignored results"):
        audit_project(project, repo_root=tmp_path, output_dir=destination)

    assert not destination.exists()
    assert source_path.read_bytes() == raw_before
