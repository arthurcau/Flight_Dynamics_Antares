"""Offline Windows benchmark of real flights, disk use and process-tree RAM.

Use --source to compare a saved pre-change orchestrator with the current one.
Weather downloads and plotting are mocked; the two flight integrations, exports
and reload of logs are real. Parallel draws differ between runs. No extra
packages are needed for the Windows memory counters.
"""

import argparse
import ctypes
from ctypes import wintypes
import importlib.util
import json
import os
from pathlib import Path
import sys
from threading import Event, Thread
from time import perf_counter
from unittest.mock import patch

import multiprocess
from rocketpy import MonteCarlo

from test_monte_carlo_failure import FailureCampaignTests, execute_monte_carlo


class MemoryCounters(ctypes.Structure):
    _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
        (name, ctypes.c_size_t) for name in (
            "PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage",
            "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage",
            "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage")]


def memory_reader():
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    kernel.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = (wintypes.HANDLE,)
    psapi.GetProcessMemoryInfo.argtypes = (
        wintypes.HANDLE, ctypes.POINTER(MemoryCounters), wintypes.DWORD)

    def read(pid):
        handle = kernel.OpenProcess(0x0400 | 0x0010, False, pid)
        if not handle:
            return 0, 0
        try:
            counters = MemoryCounters()
            counters.cb = ctypes.sizeof(counters)
            if not psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
                return 0, 0
            return counters.WorkingSetSize, counters.PeakWorkingSetSize
        finally:
            kernel.CloseHandle(handle)

    return read


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=24)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    execute = execute_monte_carlo
    if args.source:
        sys.path.insert(0, str(args.source.resolve().parent))
        spec = importlib.util.spec_from_file_location("baseline", args.source)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        execute = module.execute_monte_carlo

    fixture = FailureCampaignTests()
    fixture.setUp()
    fixture.config.monte_carlo["num_simulations"] = args.count
    # Keep the same input distributions when separately implementing the
    # user's launch-angle request. This benchmark isolates storage changes.
    fixture.config.monte_carlo["flight"] = {
        "inclination": {"std": 5.0}, "heading": {"std": 10.0}}
    original_simulate = MonteCarlo.simulate
    result = {"count": args.count, "workers": args.workers,
              "source": str(args.source) if args.source else "current"}

    def simulate(mc, **kwargs):
        kwargs.update(parallel=args.workers > 1, n_workers=args.workers)
        start = perf_counter()
        try:
            return original_simulate(mc, **kwargs)
        finally:
            result["simulate_seconds"] = perf_counter() - start

    read_memory = memory_reader()
    stop = Event()
    peaks = {}
    tree_peak = 0
    trace = []
    started = perf_counter()

    def sample():
        nonlocal tree_peak
        total = 0
        for pid in [os.getpid()] + [p.pid for p in multiprocess.active_children()]:
            current, peak = read_memory(pid)
            total += current
            peaks[pid] = max(peaks.get(pid, 0), peak)
        tree_peak = max(tree_peak, total)
        if not trace or perf_counter() - started - trace[-1][0] >= 10:
            trace.append([round(perf_counter() - started, 2), round(total / 2**20, 2)])

    def monitor():
        while not stop.wait(0.1):
            sample()

    watcher = Thread(target=monitor, daemon=True)
    watcher.start()
    try:
        with patch.object(MonteCarlo, "simulate", simulate):
            mc = execute(fixture.config, fixture.project)
        result["total_seconds"] = perf_counter() - started
        result["completed"] = len(mc.outputs_log)
        result["input_bytes"] = Path(mc.input_file).stat().st_size
        result["output_bytes"] = Path(mc.output_file).stat().st_size
        result["retained_trajectories"] = len(fixture.dispersion.call_args.kwargs["all_flights"])
        result["manifest_storage"] = fixture.manifest().get("storage")
    finally:
        stop.set()
        watcher.join()
        sample()
        result["peak_tree_working_set_mib"] = tree_peak / 2**20
        result["peak_parent_working_set_mib"] = peaks.get(os.getpid(), 0) / 2**20
        result["peak_child_working_set_mib"] = max(
            (v for pid, v in peaks.items() if pid != os.getpid()), default=0) / 2**20
        result["memory_trace_seconds_mib"] = trace
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print("BENCHMARK", json.dumps(result), flush=True)
        fixture.doCleanups()


if __name__ == "__main__":
    main()
