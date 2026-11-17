"""Tests for the explicit zero-based RocketPy resume contract."""

import json
from types import SimpleNamespace
import importlib

import pytest
import yaml

from antares_fd.simulation.monte_carlo_failure import _failure_records
from antares_fd.simulation.monte_carlo_resume import restore_jsonl_case_logs


def _write_pair(tmp_path, output_records, input_records, *, blank_lines=False):
    outputs = tmp_path / "mc_sim.outputs.txt"
    inputs = tmp_path / "mc_sim.inputs.txt"
    prefix = "\n" if blank_lines else ""
    outputs.write_text(prefix + "".join(json.dumps(row) + "\n" for row in output_records), encoding="utf-8")
    inputs.write_text(prefix + "".join(json.dumps(row) + "\n" for row in input_records), encoding="utf-8")
    return outputs, inputs


def test_nominal_resume_restores_complete_logs_and_counts_objects_not_lines(tmp_path):
    outputs, inputs = _write_pair(
        tmp_path,
        [{"index": 0, "apogee": 10}, {"index": 1, "apogee": 20}, {"index": 2, "apogee": 30}],
        [{"index": 0, "mass": 1}, {"index": 1, "mass": 2}, {"index": 2, "mass": 3}],
        blank_lines=True,
    )
    mc = SimpleNamespace(outputs_log=[], inputs_log=[], num_of_loaded_sims=99)

    completed = restore_jsonl_case_logs(mc, outputs, inputs, allowed_case_ids={0, 1, 2})

    assert completed == 3
    assert mc.num_of_loaded_sims == 3
    assert [row["case_id"] for row in mc.outputs_log] == [0, 1, 2]
    assert [row["case_id"] for row in mc.inputs_log] == [0, 1, 2]


def test_nominal_resume_restores_partial_prefix_for_append(tmp_path):
    outputs, inputs = _write_pair(
        tmp_path,
        [{"index": 0, "apogee": 10}, {"index": 1, "apogee": 20}],
        [{"index": 0, "mass": 1}, {"index": 1, "mass": 2}],
    )
    mc = SimpleNamespace(outputs_log=[], inputs_log=[], num_of_loaded_sims=0)

    assert restore_jsonl_case_logs(mc, outputs, inputs, allowed_case_ids={0, 1, 2}) == 2
    assert mc.num_of_loaded_sims == 2


@pytest.mark.parametrize(
    "output_records,input_records,error",
    [
        ([{"index": 0}, {"index": 0}], [{"index": 0}, {"index": 0}], "duplicate case ID"),
        ([{"index": 0}, {"index": 2}], [{"index": 0}, {"index": 2}], "non-prefix case IDs"),
        ([{"index": 0}], [{"index": 1}], "same case IDs"),
    ],
)
def test_nominal_resume_rejects_duplicate_gapped_and_unpaired_logs(
    tmp_path, output_records, input_records, error,
):
    outputs, inputs = _write_pair(tmp_path, output_records, input_records)
    mc = SimpleNamespace(outputs_log=[], inputs_log=[], num_of_loaded_sims=0)

    with pytest.raises(ValueError, match=error):
        restore_jsonl_case_logs(mc, outputs, inputs, allowed_case_ids={0, 1, 2})


def test_terminal_failure_classification_keeps_sparse_successes_and_reports_gap():
    mc = SimpleNamespace(outputs_log=[{"index": 0}, {"index": 2}])

    assert [row["case_id"] for row in _failure_records(mc, None, 3)] == [1]


def test_nominal_entrypoint_skips_workers_for_a_fully_restored_campaign(tmp_path, monkeypatch):
    runner = importlib.import_module("antares_fd.simulation.monte_carlo")
    environment_builder = importlib.import_module("antares_fd.builders.environment")
    scenarios = importlib.import_module("antares_fd.simulation.scenarios")
    plotters = importlib.import_module("antares_fd.simulation.plotters")

    campaign_dir = tmp_path / "campaign"
    campaign_dir.mkdir()
    (campaign_dir / "mc_sim.outputs.txt").write_text(
        '{"index": 0, "apogee": 10}\n{"index": 1, "apogee": 20}\n',
        encoding="utf-8",
    )
    (campaign_dir / "mc_sim.inputs.txt").write_text(
        '{"index": 0, "mass": 1}\n{"index": 1, "mass": 2}\n',
        encoding="utf-8",
    )
    monkeypatch.setenv("ANTARES_CAMPAIGN_DIR", str(campaign_dir))
    monkeypatch.setenv("ANTARES_CAMPAIGN_ACTIVE", "1")
    monkeypatch.setenv("ANTARES_CAMPAIGN_RUN_ID", "completed-resume")
    monkeypatch.setenv("ANTARES_MC_SCENARIO", "nominal")

    config = SimpleNamespace(
        monte_carlo={"num_simulations": 2, "random_seed": 17},
        environment={},
        launch={"rail": {"length": 5.2, "inclination_deg": 85.0, "heading_deg": 0.0}},
        motor={},
        vehicle={},
        recovery={},
        simulation={},
    )
    monkeypatch.setattr(scenarios, "apply_scenario", lambda original, _: original)
    monkeypatch.setattr(environment_builder, "build_environment", lambda *_: object())
    monkeypatch.setattr(environment_builder, "build_environment_ensemble", lambda *_: [])
    monkeypatch.setattr(runner, "ProfileStochasticEnvironment", lambda **_: object())
    monkeypatch.setattr(runner, "build_motor", lambda *_: SimpleNamespace(total_impulse=1.0))
    monkeypatch.setattr(runner, "StochasticSolidMotor", lambda *_args, **_kwargs: object())
    vehicle = SimpleNamespace(mass=1.0, motor_position=0.0)
    monkeypatch.setattr(runner, "build_vehicle", lambda *_: vehicle)
    monkeypatch.setattr(runner, "add_recovery_system", lambda *_: None)
    stochastic_vehicle = SimpleNamespace(add_motor=lambda *_args, **_kwargs: None)
    monkeypatch.setattr(runner, "StochasticRocket", lambda *_args, **_kwargs: stochastic_vehicle)
    monkeypatch.setattr(runner, "_transfer_rocket_components", lambda *_: None)
    monkeypatch.setattr(runner, "launch_angle_distribution", lambda nominal, *_: nominal)
    flight = object()
    monkeypatch.setattr(runner, "run_flight", lambda *_: flight)
    monkeypatch.setattr(runner, "StochasticFlight", lambda *_args, **_kwargs: object())

    class CompletedMonteCarlo:
        def __init__(self, *, filename, **_kwargs):
            self.input_file = f"{filename}.inputs.txt"
            self.outputs_log = []
            self.inputs_log = []
            self.errors_log = []
            self.num_of_loaded_sims = 0
            self._MonteCarlo__run_single_simulation = lambda *_args, **_kwargs: None

        def simulate(self, **_kwargs):
            pytest.fail("a complete resume must not resimulate cases")

    monkeypatch.setattr(runner, "ConfiguredMonteCarlo", CompletedMonteCarlo)
    monkeypatch.setattr(
        runner,
        "CampaignManager",
        lambda: pytest.fail("a complete resume must not start a campaign manager"),
    )
    monkeypatch.setattr(runner.subprocess, "check_output", lambda *_args, **_kwargs: b"test\n")
    monkeypatch.setattr(plotters, "plot_monte_carlo_dispersion", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(plotters, "plot_monte_carlo_distributions", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(plotters, "plot_monte_carlo_convergence", lambda *_args, **_kwargs: None)

    restored = runner.execute_monte_carlo(config, tmp_path / "project")

    assert restored.num_of_loaded_sims == 2
    assert [record["case_id"] for record in restored.inputs_log] == [0, 1]
    assert [record["case_id"] for record in restored.outputs_log] == [0, 1]
    manifest = yaml.safe_load((campaign_dir / "manifest.yaml").read_text(encoding="utf-8"))
    assert manifest["run"]["status"] == "completed"
    assert manifest["run"]["completed_cases"] == 2
