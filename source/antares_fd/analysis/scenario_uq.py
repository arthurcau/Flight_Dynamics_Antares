"""Scenario stochastic post-processing using common random-number cases."""

from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd

from antares_fd.analysis.uq import distribution_statistics, landing_dispersion


SCENARIO_OUTPUTS = (
    "apogee_agl", "apogee_asl", "apogee_time", "rail_exit_velocity",
    "rail_exit_time", "max_velocity", "max_mach", "max_total_acceleration",
    "max_dynamic_pressure", "max_angle_of_attack", "angle_of_attack_at_max_q",
    "static_margin_rail_exit", "static_margin_max_q", "static_margin_burnout",
    "minimum_static_margin", "maximum_static_margin", "drogue_deployment_time",
    "drogue_deployment_altitude", "main_deployment_time", "main_deployment_altitude",
    "descent_rate", "touchdown_velocity", "touchdown_energy", "flight_duration",
    "landing_east", "landing_north", "landing_distance", "landing_azimuth",
)


def summarize_scenario(scenario_id: str, outputs: pd.DataFrame, failures: pd.DataFrame | None = None) -> dict:
    """Return the complete applicable scalar summary for one scenario."""
    failures = failures if failures is not None else pd.DataFrame()
    statistics = distribution_statistics(outputs) if not outputs.empty else pd.DataFrame()
    result = {
        "scenario_id": scenario_id,
        "count": int(len(outputs)),
        "successful": int(len(outputs)),
        "failed": int(len(failures)),
        "failure_rate": float(len(failures) / max(len(outputs) + len(failures), 1)),
        "statistics": statistics.to_dict("records"),
        "landing": landing_dispersion(outputs) if {"landing_east", "landing_north"}.issubset(outputs.columns) else {"status": "NOT APPLICABLE"},
        "not_applicable": [column for column in SCENARIO_OUTPUTS if column not in outputs.columns],
    }
    return result


def paired_scenario_comparison(frames: Mapping[str, pd.DataFrame], columns: tuple[str, ...] = ("apogee_agl", "flight_duration", "landing_distance", "touchdown_velocity", "touchdown_energy")) -> pd.DataFrame:
    """Calculate paired deltas for shared case IDs.

    A missing case ID or mismatched sample population produces an explicit
    unpaired result rather than a misleading comparison.
    """
    if not frames:
        return pd.DataFrame()
    names = list(frames)
    base_name = names[0]
    base = frames[base_name]
    if "case_id" not in base:
        return pd.DataFrame([{"comparison_status": "UNPAIRED / NOT DIRECTLY COMPARABLE"}])
    result = None
    for name in names[1:]:
        other = frames[name]
        if "case_id" not in other:
            return pd.DataFrame([{"comparison_status": "UNPAIRED / NOT DIRECTLY COMPARABLE"}])
        left = base[["case_id"] + [c for c in columns if c in base]].copy()
        right = other[["case_id"] + [c for c in columns if c in other]].copy()
        joined = left.merge(right, on="case_id", suffixes=(f"_{base_name}", f"_{name}"), how="inner")
        for column in columns:
            a, b = f"{column}_{base_name}", f"{column}_{name}"
            if a in joined and b in joined:
                joined[f"delta_{name}_minus_{base_name}_{column}"] = joined[b] - joined[a]
        result = joined if result is None else result.merge(joined, on="case_id", how="inner")
    if result is None or result.empty:
        return pd.DataFrame([{"comparison_status": "UNPAIRED / NOT DIRECTLY COMPARABLE"}])
    result["comparison_status"] = "PAIRED_COMMON_RANDOM_NUMBERS"
    return result


def empirical_landing_surface(outputs: pd.DataFrame, bins: int = 40) -> dict:
    """Return an empirical 2-D occupancy surface, without Gaussian assumptions."""
    if not {"landing_east", "landing_north"}.issubset(outputs.columns):
        return {"status": "NOT APPLICABLE"}
    x = pd.to_numeric(outputs["landing_east"], errors="coerce").dropna().to_numpy()
    y = pd.to_numeric(outputs["landing_north"], errors="coerce").dropna().to_numpy()
    if len(x) < 2:
        return {"status": "INSUFFICIENT DATA"}
    density, x_edges, y_edges = np.histogram2d(x, y, bins=bins, density=True)
    return {"status": "AVAILABLE", "method": "empirical_2d_histogram", "density": density.tolist(), "east_edges": x_edges.tolist(), "north_edges": y_edges.tolist(), "sample_count": int(len(x))}
