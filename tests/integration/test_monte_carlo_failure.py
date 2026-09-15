"""Offline regression tests for failure campaigns and Windows worker startup."""
import shutil
import sys
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source"))
sys.path.insert(0, str(ROOT))

import yaml
from rocketpy import Environment
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
        self.assertEqual(self.manifest()["run"]["status"], "completed")
        trajectories = self.dispersion.call_args.kwargs["all_flights"]
        self.assertIsInstance(trajectories, list)
        self.assertEqual(len(trajectories), 2)

    def test_silent_worker_failure_is_reported(self):
        with patch("antares_fd.simulation.monte_carlo_failure.MonteCarlo.simulate"):
            with self.assertRaisesRegex(RuntimeError, "0/2 simulations exported"):
                execute_monte_carlo(self.config, self.project)
        self.assertEqual(self.manifest()["run"]["status"], "failed")
        self.dispersion.assert_not_called()


if __name__ == "__main__":
    unittest.main()
