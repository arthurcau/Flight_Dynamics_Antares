"""Regression tests for canonical scenario overrides and paired UQ."""

from pathlib import Path

import pandas as pd

from antares_fd.analysis.scenario_uq import deterministic_scenario_consistency, paired_comparison_statistics, paired_scenario_comparison
from antares_fd.config.loader import load_project_config
from antares_fd.simulation.scenarios import apply_scenario, REQUIRED_SCENARIOS
from antares_fd.simulation.uq_campaign import StochasticScenarioCampaign


ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "projects" / "neblina_1"


def test_required_scenario_overrides_are_canonical_and_non_mutating():
    config = load_project_config(PROJECT)
    original = config.recovery["devices"][0]["enabled"]

    main = apply_scenario(config, "main_at_apogee")
    assert main.scenario_id == "main_at_apogee"
    devices = {item["id"]: item for item in main.recovery["devices"]}
    assert devices["drogue"]["enabled"] is False
    assert devices["main"]["trigger"]["type"] == "apogee"

    reefed = apply_scenario(config, "only_reefing")
    reef_devices = {item["id"]: item for item in reefed.recovery["devices"]}
    assert reef_devices["drogue"]["aerodynamics"]["cd_s"] == 6.7171 * 0.15
    assert config.recovery["devices"][0]["enabled"] == original
    assert tuple(REQUIRED_SCENARIOS) == ("nominal", "main_at_apogee", "only_reefing")


def test_paired_comparison_uses_common_case_ids_for_all_scenarios():
    frames = {
        "nominal": pd.DataFrame({"case_id": [0, 1], "apogee_agl": [100, 110], "landing_distance": [10, 20]}),
        "main_at_apogee": pd.DataFrame({"case_id": [0, 1], "apogee_agl": [100, 110], "landing_distance": [12, 24]}),
        "only_reefing": pd.DataFrame({"case_id": [0, 1], "apogee_agl": [100, 110], "landing_distance": [11, 22]}),
    }
    paired = paired_scenario_comparison(frames, columns=("apogee_agl", "landing_distance"))
    assert len(paired) == 2
    assert paired["comparison_status"].eq("PAIRED_COMMON_RANDOM_NUMBERS").all()
    assert paired["delta_main_at_apogee_minus_nominal_landing_distance"].tolist() == [2, 4]
    stats = paired_comparison_statistics(paired)
    assert set(stats["metric"]) == {
        "delta_main_at_apogee_minus_nominal_apogee_agl",
        "delta_main_at_apogee_minus_nominal_landing_distance",
        "delta_only_reefing_minus_nominal_apogee_agl",
        "delta_only_reefing_minus_nominal_landing_distance",
    }


def test_paired_comparison_marks_partial_population_after_case_failure():
    frames = {
        "nominal": pd.DataFrame({"case_id": [0, 1], "apogee_agl": [100, 110]}),
        "main_at_apogee": pd.DataFrame({"case_id": [0], "apogee_agl": [100]}),
    }
    paired = paired_scenario_comparison(frames, columns=("apogee_agl",))
    assert len(paired) == 1
    assert paired["comparison_status"].iloc[0] == "PAIRED_COMMON_RANDOM_NUMBERS_PARTIAL"
    assert not paired_comparison_statistics(paired).empty


def test_post_ascent_scenario_consistency_is_checked():
    from types import SimpleNamespace

    nominal = SimpleNamespace(rail_exit_velocity=25.0, rail_exit_time=1.0, max_mach=0.8, max_dynamic_pressure=1000.0, apogee_agl=2000.0)
    same = SimpleNamespace(rail_exit_velocity=25.0, rail_exit_time=1.0, max_mach=0.8, max_dynamic_pressure=1000.0, apogee_agl=2000.0)
    different = SimpleNamespace(rail_exit_velocity=26.0, rail_exit_time=1.0, max_mach=0.8, max_dynamic_pressure=1000.0, apogee_agl=2000.0)
    assert deterministic_scenario_consistency({"nominal": nominal, "main_at_apogee": same})["status"] == "PASS"
    result = deterministic_scenario_consistency({"nominal": nominal, "only_reefing": different})
    assert result["status"] == "SCENARIO CONSISTENCY FAILURE"
    assert "rail_exit_velocity" in result["comparisons"][0]["violations"]


def test_multi_scenario_campaign_owns_one_shared_sample_table(tmp_path):
    campaign = StochasticScenarioCampaign("demo", tmp_path, master_seed=4, profile="debug")
    samples = campaign.ensure_samples(None)
    assert len(samples) == 50
    assert campaign.samples_path == campaign.path / "samples" / "inputs.parquet"
    assert campaign.scenario("nominal").path == campaign.path / "scenarios" / "nominal"
    assert campaign.scenario("main_at_apogee").samples_path == campaign.samples_path
