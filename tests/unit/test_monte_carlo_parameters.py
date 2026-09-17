import unittest
from types import SimpleNamespace

import numpy as np
from rocketpy.stochastic.stochastic_model import StochasticModel

from antares_fd.config.exceptions import ConfigurationError
from antares_fd.simulation.monte_carlo_parameters import launch_angle_distribution


class LaunchAngleTests(unittest.TestCase):
    def test_rocketpy_samples_uniform_bounds_not_gaussian_tails(self):
        for name, nominal, lower, upper in (("inclination", 80, 70, 90),
                                            ("heading", 240, 230, 250)):
            argument = launch_angle_distribution(nominal, {
                "distribution": "uniform", "min": lower, "max": upper}, name)
            model = StochasticModel(SimpleNamespace(**{name: nominal}), seed=42,
                                    **{name: argument})
            values = np.array([next(model.dict_generator())[name] for _ in range(10_000)])
            self.assertTrue(np.all((values >= lower) & (values <= upper)))
            self.assertAlmostEqual(values.mean(), nominal, delta=0.2)
            self.assertAlmostEqual(values.std(), (upper - lower) / np.sqrt(12), delta=0.1)

    def test_legacy_std_and_invalid_bounds(self):
        self.assertEqual(launch_angle_distribution(80, {"std": 5}, "inclination"), (80, 5))
        self.assertIsNone(launch_angle_distribution(80, {}, "inclination"))
        for settings in ({"min": 70, "max": 90},
                         {"distribution": "uniform", "min": 70, "max": 95},
                         {"distribution": "uniform", "min": 70},
                         {"distribution": "uniform", "min": 70, "max": 90, "std": 5}):
            with self.subTest(settings=settings), self.assertRaises(ConfigurationError):
                launch_angle_distribution(80, settings, "inclination")
