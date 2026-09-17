import pandas as pd

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
    assert frame.loc[0, "touchdown_velocity_signed"] == -70.0
    assert frame.loc[0, "touchdown_velocity"] == 70.0


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
