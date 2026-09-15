"""Exploratory offline benchmark; does not modify production configuration.

Run directly with the project's interpreter. Timing excludes weather downloads
and plots. Random samples differ between parallel runs; this is not a numerical
equivalence test. Results are written next to this script.
"""
import cProfile
import argparse
import json
import pstats
from pathlib import Path
from time import perf_counter
from unittest.mock import patch

from test_monte_carlo_failure import FailureCampaignTests, execute_monte_carlo
from rocketpy import MonteCarlo

ORIGINAL_SIMULATE = MonteCarlo.simulate


def run_case(workers, count, compact=False, profile=False):
    fixture = FailureCampaignTests()
    fixture.setUp()
    fixture.config.monte_carlo["num_simulations"] = count
    timings = {}

    def simulate(self, **kwargs):
        kwargs.update(parallel=workers > 1, n_workers=workers)
        if compact:
            kwargs["include_function_data"] = False
        start = perf_counter()
        try:
            return ORIGINAL_SIMULATE(self, **kwargs)
        finally:
            timings["simulate_seconds"] = perf_counter() - start

    profiler = cProfile.Profile() if profile else None
    try:
        with patch.object(MonteCarlo, "simulate", simulate):
            start = perf_counter()
            if profiler:
                profiler.enable()
            mc = execute_monte_carlo(fixture.config, fixture.project)
            if profiler:
                profiler.disable()
            timings["total_seconds"] = perf_counter() - start
        timings.update(workers=workers, count=count, compact=compact,
                       profiled=profile, completed=len(mc.outputs_log))
        timings["input_bytes"] = sum(
            p.stat().st_size for p in fixture.results.glob("*/*.inputs.txt"))
        if profiler:
            with Path(__file__).with_suffix(".profile.txt").open("w") as output:
                pstats.Stats(profiler, stream=output).strip_dirs().sort_stats(
                    "cumulative").print_stats(65)
        print("BENCHMARK", json.dumps(timings), flush=True)
        return timings
    finally:
        fixture.doCleanups()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--large", action="store_true",
                        help="Compare full and compact exports with 60 cases")
    args = parser.parse_args()
    results = []
    cases = (
        (1, 12, False, False), (3, 12, False, False),
        (6, 12, False, False), (6, 12, True, False),
        (1, 2, False, True),
    )
    if args.large:
        cases = ((1, 12, True, False), (6, 60, False, False),
                 (6, 60, True, False))
    for workers, count, compact, profile in cases:
        results.append(run_case(workers, count, compact, profile))
        suffix = ".large.json" if args.large else ".json"
        Path(__file__).with_suffix(suffix).write_text(
            json.dumps(results, indent=2), encoding="utf-8")
