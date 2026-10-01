"""Offline regression tests for failure campaigns and Windows worker startup."""
import shutil
import sys
import tempfile
import json
import os
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source"))
sys.path.insert(0, str(ROOT))

import yaml
import numpy as np
from rocketpy import Environment, MonteCarlo
from antares_fd.config.loader import load_project_config
from antares_fd.simulation.monte_carlo_failure import execute_monte_carlo


class FailureCampaignTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        root = Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        self.project = root / "projects" / "neblina_1"
        for folder in ("config", "aero", "motors"):
            shutil.copytree(ROOT / "projects" / "neblina_1" / folder,
                            self.project / folder)
        self.config = load_project_config(self.project)
        self.config.monte_carlo["num_simulations"] = 2
        self.results = root / "results" / "neblina_1"
        environment = Environment(latitude=-21.938982, longitude=-48.950316,
                                  elevation=600)
        self.stack.enter_context(patch(
            "antares_fd.builders.environment.build_environment",
            return_value=environment))
        self.stack.enter_context(patch(
            "antares_fd.builders.environment.build_environment_ensemble",
            return_value=[environment]))
        self.dispersion = self.stack.enter_context(patch(
            "antares_fd.simulation.plotters.plot_monte_carlo_dispersion"))
        for name in ("plot_monte_carlo_distributions", "plot_monte_carlo_convergence"):
            self.stack.enter_context(patch(f"antares_fd.simulation.plotters.{name}"))

    def manifest(self):
        return yaml.safe_load(next(self.results.glob("*/manifest.yaml")).read_text())

    def test_parallel_campaign_exports_results_and_trajectories(self):
        mc = execute_monte_carlo(self.config, self.project)
        self.assertEqual(len(mc.outputs_log), 2)
        self.assertEqual({row["index"] for row in mc.outputs_log}, {0, 1})
        self.assertEqual(self.manifest()["run"]["status"], "completed")
        trajectories = self.dispersion.call_args.kwargs["all_flights"]
        self.assertIsInstance(trajectories, list)
        self.assertEqual(len(trajectories), 2)
        self.assertLess(Path(mc.input_file).stat().st_size, 100_000)
        self.assertEqual(len(mc.inputs_log), 2)
        self.assertEqual(self.manifest()["storage"]["trajectories_seen"], 2)
        self.assertFalse(self.manifest()["storage"]["include_function_data"])
        self.assertEqual(len(self.dispersion.call_args.kwargs["sample_flights"]), 2)

    def test_silent_worker_failure_is_reported(self):
        with patch.dict(os.environ, {"ANTARES_MC_WORKERS": "1"}), patch(
            "antares_fd.simulation.monte_carlo_failure.MonteCarlo.simulate"
        ):
            with self.assertRaisesRegex(RuntimeError, "0/2 simulations exported"):
                execute_monte_carlo(self.config, self.project)
        self.assertEqual(self.manifest()["run"]["status"], "failed")
        self.dispersion.assert_not_called()

    def test_campaign_mode_writes_terminal_canonical_scenario_manifest(self):
        campaign_id = "campaign_manifest_contract"
        campaign_dir = self.results / campaign_id
        environment = {
            "ANTARES_CAMPAIGN_DIR": str(campaign_dir),
            "ANTARES_CAMPAIGN_ACTIVE": "1",
            "ANTARES_CAMPAIGN_RUN_ID": campaign_id,
            "ANTARES_COMPACT_OUTPUTS": "1",
            "ANTARES_MC_SCENARIO": "nominal",
            "ANTARES_MC_TARGET": "1",
            "ANTARES_MC_PROFILE": "debug",
            "ANTARES_MC_WORKERS": "1",
            "ANTARES_MC_MAX": "1",
        }
        with patch.dict(os.environ, environment):
            mc = execute_monte_carlo(self.config, self.project)

        manifest_path = campaign_dir / "scenarios" / "nominal" / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(len(mc.outputs_log), 1)
        self.assertEqual(mc.outputs_log[0]["case_id"], 0)
        self.assertEqual(mc.outputs_log[0]["index"], 0)
        self.assertIn(manifest["status"], {"COMPLETE", "COMPLETE_NOT_CONVERGED"})
        self.assertEqual(manifest["successful_samples"], 1)
        self.assertEqual(manifest["failed_samples"], 0)

    def test_compact_export_preserves_flight_metrics_and_trajectory_points(self):
        # Identical physical inputs isolate storage from random sampling.
        for group in self.config.monte_carlo.values():
            if isinstance(group, dict):
                for parameter in group.values():
                    if isinstance(parameter, dict):
                        for key in ("std", "factor_std"):
                            if key in parameter:
                                parameter[key] = 0.0
        self.config.monte_carlo["flight"] = {
            "inclination": {"std": 0}, "heading": {"std": 0}}
        self.config.monte_carlo["num_simulations"] = 1
        second_project = self.project.with_name("neblina_compact")
        shutil.copytree(self.project, second_project)
        original_simulate = MonteCarlo.simulate
        campaigns, trajectories = [], []
        for full, project in ((True, self.project), (False, second_project)):
            def simulate(mc, **kwargs):
                kwargs.update(parallel=False, include_function_data=full)
                return original_simulate(mc, **kwargs)
            with patch.dict(os.environ, {"ANTARES_MC_WORKERS": "1"}), patch.object(MonteCarlo, "simulate", simulate):
                campaigns.append(execute_monte_carlo(self.config, project))
                trajectories.append(self.dispersion.call_args.kwargs["all_flights"][0])
        self.assertEqual(campaigns[0].outputs_log, campaigns[1].outputs_log)
        for axis in ("x", "y", "z"):
            np.testing.assert_array_equal(trajectories[0][axis], trajectories[1][axis])
        self.assertGreater(Path(campaigns[0].input_file).stat().st_size,
                           100 * Path(campaigns[1].input_file).stat().st_size)


if __name__ == "__main__":
    unittest.main()
