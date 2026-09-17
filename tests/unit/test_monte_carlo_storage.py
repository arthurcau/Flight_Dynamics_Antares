"""Verify bounded retention without losing extreme paths or numerical detail."""

import random
import unittest
from concurrent.futures import ThreadPoolExecutor

import numpy as np

from antares_fd.simulation.monte_carlo_storage import TrajectoryStore


class TrajectoryStoreTests(unittest.TestCase):
    def test_many_paths_preserve_extrema_and_full_precision_with_bounded_storage(self):
        rng = np.random.default_rng(81)
        endpoints = rng.normal(size=(1500, 2))
        store = TrajectoryStore(seed=12)
        for index, (x, y) in enumerate(endpoints):
            path = {"x": np.linspace(0, x, 201), "y": np.linspace(0, y, 201),
                    "z": np.sin(np.linspace(0, np.pi, 201)), "case": index}
            store.append(path)
            self.assertLessEqual(len(store.snapshot()["trajectories"]), 9)
        snapshot = store.snapshot()
        self.assertEqual(snapshot["seen"], 1500)
        paths = {path["case"]: path for path in snapshot["trajectories"]}
        for column in (0, 1):
            for extreme in (np.argmin, np.argmax):
                index = int(extreme(endpoints[:, column]))
                self.assertIn(index, paths)
                self.assertEqual(len(paths[index]["x"]), 201)
                np.testing.assert_array_equal(paths[index]["x"],
                                              np.linspace(0, endpoints[index, 0], 201))
        self.assertEqual(len(snapshot["samples"]), 5)
        self.assertEqual(len({p["case"] for p in snapshot["samples"]}), 5)

    def test_sampling_does_not_change_physics_random_stream(self):
        store = TrajectoryStore(seed=3)
        before = random.getstate()
        for i in range(100):
            store.append({"x": [0, i], "y": [0, -i], "z": [0, 0]})
        self.assertEqual(random.getstate(), before)
        self.assertEqual(TrajectoryStore().snapshot()["trajectories"], [])

    def test_concurrent_offers_are_atomic(self):
        store = TrajectoryStore()
        def append(i):
            store.append({"x": [i], "y": [-i], "case": i})
        with ThreadPoolExecutor(max_workers=6) as executor:
            list(executor.map(append, range(1000)))
        snapshot = store.snapshot()
        self.assertEqual(snapshot["seen"], 1000)
        cases = {p["case"] for p in snapshot["trajectories"]}
        self.assertTrue({0, 999}.issubset(cases))
        self.assertLessEqual(len(cases), 9)
