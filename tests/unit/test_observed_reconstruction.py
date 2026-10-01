"""Synthetic contracts for conservative reconstruction from audited samples."""

from __future__ import annotations

import pandas as pd
import pytest

from antares_fd.reconstruction.observations import build_observed_section


def _fixtures() -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for index, (time_ms, a, b) in enumerate(((1000, 0, 1), (1100, 10, 11), (1200, 20, 21), (1300, 15, 16))):
        for channel, value in (("time_ms", time_ms), ("bmp1_rel_alt_m", a), ("bmp2_rel_alt_m", b)):
            rows.append({
                "record_index": index,
                "source_line_number": index + 10,
                "section_marker": "FLIGHT",
                "raw_channel_name": channel,
                "numeric_value": value,
                "data_origin": "MEASURED" if channel == "time_ms" else "DERIVED",
            })
    segments = pd.DataFrame({
        "record_index": [0, 1, 2, 3],
        "source_line_number": [10, 11, 12, 13],
        "segment_id": [0, 0, 0, 0],
        "raw_time": [1000, 1100, 1200, 1300],
        "segment_elapsed_s": [0, 0.1, 0.2, 0.3],
    })
    return pd.DataFrame(rows), segments


def test_observed_section_preserves_lineage_and_reports_interval_rate() -> None:
    samples, segments = _fixtures()
    diagnostics = pd.DataFrame({
        "record_index": [0, 1, 2, 3],
        "interval_class": ["FIRST_SAMPLE", "NORMAL_INTERVAL", "NORMAL_INTERVAL", "TIMESTAMP_GAP"],
    })
    duplicate_blocks = [{
        "original_start_record_index": 20,
        "original_end_record_index": 23,
        "duplicate_start_record_index": 0,
        "duplicate_end_record_index": 3,
        "mechanism": "UNKNOWN",
    }]
    frame, events, summary = build_observed_section(
        samples, segments, section_marker="FLIGHT",
        timebase_diagnostics=diagnostics, duplicate_blocks=duplicate_blocks,
    )

    assert frame["record_index"].tolist() == [0, 1, 2, 3]
    assert frame["source_line_number"].tolist() == [10, 11, 12, 13]
    assert frame["raw_time"].tolist() == [1000, 1100, 1200, 1300]
    assert frame["bmp1_interval_rate_mps"].iloc[1] == pytest.approx(100)
    assert frame["bmp1_interval_rate_mps"].iloc[3] == pytest.approx(-50)
    assert events["recorded_relative_altitude_peak"]["record_index"] == 2
    assert events["recorded_relative_altitude_peak"]["status"] == "DIRECTLY_RECORDED_EXTREMUM"
    assert events["recorded_relative_altitude_peak"]["confidence"] == "HIGH_FOR_RECORDED_SAMPLE_VALUES"
    assert events["apogee_candidate"]["status"] == "INSUFFICIENT_OBSERVABILITY"
    assert "time_bracket_s" not in events["apogee_candidate"]
    assert events["apogee_candidate"]["timestamp"] is None
    assert events["liftoff"]["time_uncertainty"] == "NOT_QUANTIFIABLE"
    assert frame["is_exact_duplicate_copy"].tolist() == [True] * 4
    assert frame["duplicate_of_record_index"].tolist() == [20, 21, 22, 23]
    assert frame["duplicate_mechanism"].tolist() == ["UNKNOWN"] * 4
    assert frame["interval_quality"].tolist()[-1] == "LONG_INTERVAL_RETAINED"
    assert summary["altitude_origin"] == "DERIVED_ONBOARD"


def test_observed_section_refuses_cross_segment_time_alignment() -> None:
    samples, segments = _fixtures()
    segments.loc[3, "segment_id"] = 1
    with pytest.raises(ValueError, match="multiple clock segments"):
        build_observed_section(samples, segments, section_marker="FLIGHT")


def test_observed_section_does_not_infer_apogee_without_post_peak_sample() -> None:
    samples, segments = _fixtures()
    samples = samples[samples["record_index"] < 3]
    segments = segments.iloc[:3]
    _, events, _ = build_observed_section(samples, segments, section_marker="FLIGHT")
    assert events["apogee_candidate"]["status"] == "INSUFFICIENT_OBSERVABILITY"


def test_duplicate_lineage_is_unknown_when_no_duplicate_block_is_declared() -> None:
    samples, segments = _fixtures()
    frame, _, summary = build_observed_section(samples, segments, section_marker="FLIGHT")
    assert frame["is_exact_duplicate_copy"].tolist() == [False] * 4
    assert frame["duplicate_of_record_index"].isna().all()
    assert summary["duplicate_copy_record_count"] == 0
