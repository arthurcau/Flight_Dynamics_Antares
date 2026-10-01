import pandas as pd
import numpy as np
import pytest

from antares_fd.analysis.uq import distribution_statistics
from antares_fd.simulation.monte_carlo_failure import _failure_records
from antares_fd.simulation.case_ids import completed_prefix_length
from antares_fd.simulation.uq_pipeline import _output_frame
from antares_fd.simulation.uncertainty import SamplingPlan, UncertaintyRegistry
from antares_fd.reporting.qa import inspect_report
from antares_fd.analysis.scenario_uq import paired_scenario_comparison, empirical_landing_surface


ROOT = __import__("pathlib").Path(__file__).resolve().parents[2]


def test_output_frame_converts_asl_to_agl_and_normalizes_touchdown_speed():
    samples = pd.DataFrame({"case_id": [0], "site_elevation": [495.0], "seed": [1]})
    frame = _output_frame([{"case_id": 0, "apogee": 3100.0, "impact_velocity": -70.0}], samples)
    assert frame.loc[0, "apogee_asl"] == 3100.0
    assert frame.loc[0, "apogee_agl"] == 2605.0
    assert frame.loc[0, "apogee_agl_elevation_source"] == "LEGACY_DECLARED_SITE_ELEVATION"
    assert frame.loc[0, "touchdown_velocity_signed"] == -70.0
    assert frame.loc[0, "touchdown_velocity"] == 70.0


def test_output_frame_uses_realized_rocketpy_elevation_for_agl():
    samples = pd.DataFrame({
        "case_id": [0, 1],
        "site_elevation": [495.0, 500.0],
        "rocketpy_elevation": [501.0, 489.0],
    })
    records = [
        {"case_id": 0, "apogee": 3100.0},
        {"case_id": 1, "apogee": 3110.0},
    ]

    frame = _output_frame(records, samples)

    assert frame["apogee_agl"].tolist() == [2599.0, 2621.0]
    assert frame["apogee_agl_elevation_source"].tolist() == [
        "ROCKETPY_LOGGED_ELEVATION", "ROCKETPY_LOGGED_ELEVATION",
    ]


def test_output_frame_rejects_missing_realized_elevation_instead_of_using_site_elevation():
    samples = pd.DataFrame({
        "case_id": [0],
        "site_elevation": [495.0],
        "rocketpy_elevation": [np.nan],
    })

    with pytest.raises(ValueError, match="finite per-case elevation"):
        _output_frame([{"case_id": 0, "apogee": 3100.0}], samples)


def test_output_frame_preserves_zero_based_gapped_case_ids():
    samples = pd.DataFrame({"case_id": [0, 1, 2, 3], "site_elevation": [0.0] * 4})
    frame = _output_frame([{"index": 1, "apogee": 10.0}, {"index": 3, "apogee": 30.0}], samples)
    assert frame["case_id"].astype(int).tolist() == [1, 3]


def test_output_frame_rejects_duplicate_case_ids():
    with pytest.raises(ValueError, match="duplicate case ID"):
        _output_frame([{"index": 0}, {"index": 0}], pd.DataFrame({"case_id": [0]}))


def test_failure_records_treat_exported_ids_as_zero_based():
    mc = type("MC", (), {"outputs_log": [{"index": 0}, {"index": 1}]})()
    failures = _failure_records(mc, None, 3)
    assert [record["case_id"] for record in failures] == [2]


def test_resume_accepts_only_a_completed_case_id_prefix():
    assert completed_prefix_length([1, 0], requested=4) == 2
    with pytest.raises(ValueError, match="non-prefix case IDs"):
        completed_prefix_length([0, 2], requested=4)


def test_distribution_statistics_rejects_bad_or_nonfinite_metric_values():
    with pytest.raises(ValueError, match="non-numeric"):
        distribution_statistics(pd.DataFrame({"apogee": [1.0, "bad"]}), ["apogee"])
    with pytest.raises(ValueError, match="non-finite"):
        distribution_statistics(pd.DataFrame({"apogee": [1.0, np.inf]}), ["apogee"])


def test_distribution_statistics_preserves_empty_metric_as_zero_count():
    summary = distribution_statistics(pd.DataFrame({"apogee": pd.Series([np.nan, np.nan])}), ["apogee"])
    assert summary.loc[0, "count"] == 0
    assert pd.isna(summary.loc[0, "mean"])


def test_output_frame_rejects_non_numeric_metrics_before_artifact_writing():
    with pytest.raises(ValueError, match="not numeric"):
        _output_frame([{"index": 0, "apogee": "bad"}], pd.DataFrame({"case_id": [0]}))


def test_sampling_plan_declared_nominals_are_not_nan():
    registry = UncertaintyRegistry(ROOT / "projects/neblina_1/config/uncertainties.yaml")
    samples = SamplingPlan(registry, 8, seed=7, env_ensemble_size=2).samples
    assert samples["vehicle_mass"].notna().all()
    assert samples["site_elevation"].notna().all()


def test_campaign_selection_rule_keeps_failure_campaign_explicit():
    names = ["monte_carlo_failure", "monte_carlo"]
    ordered = sorted(names, key=lambda name: 0 if "failure" not in name else 1)
    assert ordered == ["monte_carlo", "monte_carlo_failure"]


def test_missing_report_is_reported_as_failed(tmp_path):
    result = inspect_report(tmp_path / "missing.pdf")
    assert result["passed"] is False
    assert result["page_count"] == 0


def test_scenario_uq_uses_paired_case_ids_and_empirical_surface():
    nominal = pd.DataFrame({"case_id": [0, 1], "apogee_agl": [100.0, 110.0], "landing_distance": [10.0, 12.0]})
    failure = pd.DataFrame({"case_id": [0, 1], "apogee_agl": [100.0, 108.0], "landing_distance": [14.0, 18.0], "landing_east": [1.0, 2.0], "landing_north": [3.0, 4.0]})
    paired = paired_scenario_comparison({"nominal": nominal, "failure": failure})
    assert paired["comparison_status"].iloc[0] == "PAIRED_COMMON_RANDOM_NUMBERS"
    assert paired["delta_failure_minus_nominal_landing_distance"].tolist() == [4.0, 6.0]
    surface = empirical_landing_surface(failure, bins=4)
    assert surface["status"] == "AVAILABLE"
    assert surface["method"] == "empirical_2d_histogram"
