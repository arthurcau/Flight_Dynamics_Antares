"""Scenario stochastic post-processing using common random-number cases."""

from __future__ import annotations

from typing import Any, Mapping

import numpy as np
import pandas as pd

from antares_fd.analysis.uq import distribution_statistics, landing_dispersion, empirical_landing_surface as _empirical_landing_surface


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

    A missing case ID produces an explicit unpaired result. If some cases
    failed in one scenario, the common valid subset is retained and marked
    partial so the report exposes the reduced comparison population.
    """
    if not frames:
        return pd.DataFrame()
    names = list(frames)
    base_name = names[0]
    base = frames[base_name]
    if "case_id" not in base:
        return pd.DataFrame([{"comparison_status": "UNPAIRED / NOT DIRECTLY COMPARABLE"}])
    result = base[["case_id"] + [c for c in columns if c in base]].copy()
    result = result.rename(columns={c: f"{c}_{base_name}" for c in columns if c in result})
    for name in names[1:]:
        other = frames[name]
        if "case_id" not in other:
            return pd.DataFrame([{"comparison_status": "UNPAIRED / NOT DIRECTLY COMPARABLE"}])
        right = other[["case_id"] + [c for c in columns if c in other]].copy()
        right = right.rename(columns={c: f"{c}_{name}" for c in columns if c in right})
        result = result.merge(right, on="case_id", how="inner")
        for column in columns:
            a, b = f"{column}_{base_name}", f"{column}_{name}"
            if a in result and b in result:
                result[f"delta_{name}_minus_{base_name}_{column}"] = pd.to_numeric(result[b], errors="coerce") - pd.to_numeric(result[a], errors="coerce")
    if result.empty:
        return pd.DataFrame([{"comparison_status": "UNPAIRED / NOT DIRECTLY COMPARABLE"}])
    case_sets = [set(pd.to_numeric(frame["case_id"], errors="coerce").dropna().astype(int)) for frame in frames.values()]
    full_population = bool(case_sets) and all(case_set == case_sets[0] for case_set in case_sets[1:])
    result["comparison_status"] = (
        "PAIRED_COMMON_RANDOM_NUMBERS" if full_population
        else "PAIRED_COMMON_RANDOM_NUMBERS_PARTIAL"
    )
    return result


def paired_comparison_statistics(paired: pd.DataFrame) -> pd.DataFrame:
    """Summarize every paired delta using the same empirical statistics."""
    valid_statuses = {"PAIRED_COMMON_RANDOM_NUMBERS", "PAIRED_COMMON_RANDOM_NUMBERS_PARTIAL"}
    if paired.empty or "comparison_status" not in paired or not paired["comparison_status"].isin(valid_statuses).any():
        return pd.DataFrame()
    columns = [column for column in paired.columns if column.startswith("delta_")]
    return distribution_statistics(paired, columns=columns)


def deterministic_scenario_consistency(metrics_by_scenario: Mapping[str, Any], tolerance: Mapping[str, float] | None = None) -> dict[str, Any]:
    """Check ascent metrics against nominal for post-ascent recovery cases."""
    tolerance = dict(tolerance or {"rail_exit_velocity": 1e-6, "rail_exit_time": 1e-6, "max_mach": 1e-6, "max_dynamic_pressure": 1e-3, "apogee_agl": 1e-5})
    nominal = metrics_by_scenario.get("nominal")
    if nominal is None:
        return {"status": "NOT AVAILABLE", "reason": "nominal deterministic metrics are missing", "comparisons": []}
    comparisons = []
    for scenario_id, metrics in metrics_by_scenario.items():
        if scenario_id == "nominal" or metrics is None:
            continue
        if scenario_id not in {"main_at_apogee", "only_reefing"}:
            continue
        deltas = {}
        violations = []
        for field, limit in tolerance.items():
            left = getattr(metrics, field, np.nan)
            right = getattr(nominal, field, np.nan)
            try:
                delta = float(left) - float(right)
            except (TypeError, ValueError):
                delta = np.nan
            deltas[field] = delta
            if np.isfinite(delta) and abs(delta) > limit:
                violations.append(field)
        comparisons.append({"scenario_id": scenario_id, "status": "SCENARIO CONSISTENCY FAILURE" if violations else "CONSISTENT THROUGH ASCENT", "violations": violations, "deltas": deltas})
    return {"status": "PASS" if all(item["status"] == "CONSISTENT THROUGH ASCENT" for item in comparisons) else "SCENARIO CONSISTENCY FAILURE", "comparisons": comparisons, "tolerances": tolerance}


def empirical_landing_surface(outputs: pd.DataFrame, bins: int = 40) -> dict:
    """Return an empirical 2-D occupancy surface, without Gaussian assumptions."""
    return _empirical_landing_surface(outputs, bins=bins)
