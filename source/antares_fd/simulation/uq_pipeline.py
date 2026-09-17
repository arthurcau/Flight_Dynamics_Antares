"""Finalize compact campaign artifacts from RocketPy's scalar logs."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd
import yaml

from antares_fd.analysis.uq import (
    compliance_analysis,
    convergence_table,
    distribution_statistics,
    landing_dispersion,
    quantile_confidence_interval,
    spearman_sensitivity,
    sensitivity_stability_table,
    conditional_tail_analysis,
)
from antares_fd.simulation.uq_campaign import MonteCarloCampaign
from antares_fd.simulation.uq_storage import write_json_atomic, write_parquet_atomic
from antares_fd.simulation.uq_storage import directory_size


def _read_json_lines(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not path.exists():
        return records
    with path.open("r", encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except (TypeError, json.JSONDecodeError):
                continue
            if isinstance(record, dict):
                records.append(record)
    return records


def _output_frame(records: list[dict[str, Any]], samples: pd.DataFrame | None) -> pd.DataFrame:
    frame = pd.DataFrame(records)
    if frame.empty:
        return frame
    if "case_id" not in frame:
        frame["case_id"] = frame.get("index", np.arange(len(frame)))
    frame["case_id"] = pd.to_numeric(frame["case_id"], errors="coerce").astype("Int64")
    aliases = {
        "apogee_time": "apogee_time", "x_impact": "landing_east",
        "y_impact": "landing_north", "impact_velocity": "touchdown_velocity",
        "max_mach_number": "max_mach", "max_dynamic_pressure": "max_dynamic_pressure",
        "out_of_rail_velocity": "rail_exit_velocity", "max_speed": "max_velocity",
        "t_final": "flight_duration",
    }
    for old, new in aliases.items():
        if old in frame and new not in frame:
            frame[new] = frame[old]
    # RocketPy exports ``apogee`` as altitude above sea level.  Keep that
    # source value and derive AGL from the exact elevation used by the case.
    # The previous alias copied ASL into an AGL column, creating an apparent
    # ~495 m nominal/Monte-Carlo discrepancy.
    if "apogee" in frame:
        elevation = pd.Series(0.0, index=frame.index)
        if samples is not None and "site_elevation" in samples:
            elevation = pd.to_numeric(samples.set_index("case_id")["site_elevation"], errors="coerce").reindex(frame["case_id"].tolist()).reset_index(drop=True)
            elevation.index = frame.index
        elif "rocketpy_elevation" in frame:
            elevation = pd.to_numeric(frame["rocketpy_elevation"], errors="coerce").fillna(0.0)
        frame["apogee_asl"] = pd.to_numeric(frame["apogee"], errors="coerce")
        frame["apogee_agl"] = frame["apogee_asl"] - elevation.fillna(0.0)
    if "max_acceleration" in frame and "max_total_acceleration" not in frame:
        frame["max_total_acceleration"] = pd.to_numeric(frame["max_acceleration"], errors="coerce") / 9.80665
    if "landing_east" in frame and "landing_north" in frame:
        frame["landing_distance"] = np.hypot(frame["landing_east"], frame["landing_north"])
    if "touchdown_velocity" in frame:
        frame["touchdown_velocity_signed"] = pd.to_numeric(frame["touchdown_velocity"], errors="coerce")
        frame["touchdown_velocity"] = frame["touchdown_velocity_signed"].abs()
    if samples is not None and "seed" not in frame and "seed" in samples:
        seed_map = samples.set_index("case_id")["seed"]
        frame["seed"] = frame["case_id"].map(seed_map)
    return frame


def _input_frame(samples: pd.DataFrame, records: list[dict[str, Any]] | None) -> pd.DataFrame:
    """Combine declared samples with the exact scalar values RocketPy used."""
    if not records:
        return samples
    normalized_records = []
    for record in records:
        normalized_records.append({
            key: json.dumps(value, ensure_ascii=False, separators=(",", ":"), default=str)
            if isinstance(value, (dict, list, tuple)) else value
            for key, value in record.items()
        })
    actual = pd.DataFrame(normalized_records)
    if actual.empty:
        return samples
    if "case_id" not in actual:
        actual["case_id"] = actual.get("index", np.arange(len(actual)))
    actual["case_id"] = pd.to_numeric(actual["case_id"], errors="coerce").astype("Int64")
    actual = actual.rename(columns={column: f"rocketpy_{column}" for column in actual.columns if column != "case_id"})
    if samples.empty:
        return actual
    result = samples.set_index("case_id")
    actual = actual.set_index("case_id")
    for column in actual.columns:
        if column not in result:
            result[column] = pd.Series(actual[column], index=actual.index, dtype=actual[column].dtype).reindex(result.index)
        else:
            common = result.index.intersection(actual.index)
            result.loc[common, column] = actual.loc[common, column].to_numpy()
    return result.reset_index()


def _requirements(project_dir: Path) -> dict[str, dict[str, Any]]:
    path = Path(project_dir) / "config" / "requirements.yaml"
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data.get("requirements", {})


def _representative_cases(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty or "case_id" not in frame:
        return pd.DataFrame()
    selections: list[dict[str, Any]] = []
    metrics = {
        "lowest_apogee": ("apogee_agl", "min"), "highest_apogee": ("apogee_agl", "max"),
        "worst_rail_exit": ("rail_exit_velocity", "min"), "worst_touchdown_velocity": ("touchdown_velocity", "max"),
        "furthest_landing": ("landing_distance", "max"),
    }
    for label, (column, operation) in metrics.items():
        if column not in frame:
            continue
        values = pd.to_numeric(frame[column], errors="coerce")
        if values.notna().any():
            index = values.idxmin() if operation == "min" else values.idxmax()
            selections.append({"selection": label, "case_id": int(frame.loc[index, "case_id"]), "metric": column, "value": float(values.loc[index])})
    for percentile in (5, 50, 95):
        if "apogee_agl" in frame:
            values = pd.to_numeric(frame["apogee_agl"], errors="coerce")
            target = float(np.percentile(values.dropna(), percentile))
            index = (values - target).abs().idxmin()
            selections.append({"selection": f"apogee_p{percentile:02d}", "case_id": int(frame.loc[index, "case_id"]), "metric": "apogee_agl", "value": float(values.loc[index])})
    return pd.DataFrame(selections).drop_duplicates(subset=["selection", "case_id"])


def finalize_campaign_analysis(
    campaign: MonteCarloCampaign,
    project_dir: Path,
    output_records: list[dict[str, Any]] | None = None,
    input_records: list[dict[str, Any]] | None = None,
    failure_records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build all cheap statistical artifacts from saved scalar data."""
    samples = pd.read_parquet(campaign.samples_path) if campaign.samples_path.exists() else pd.DataFrame()
    if input_records is None:
        input_records = _read_json_lines(campaign.path / "mc_sim.inputs.txt")
    samples = _input_frame(samples, input_records)
    write_parquet_atomic(samples, campaign.samples_path)
    if output_records is None:
        output_records = _read_json_lines(campaign.path / "mc_sim.outputs.txt")
    outputs = _output_frame(output_records, samples)
    write_parquet_atomic(outputs, campaign.path / "outputs.parquet")
    if not list(campaign.batches_path.glob("batch_*.parquet")):
        campaign.write_batch(0, outputs)

    failures = pd.DataFrame(failure_records or [])
    write_parquet_atomic(failures, campaign.path / "failures.parquet")
    statistics = distribution_statistics(outputs)
    write_parquet_atomic(statistics, campaign.path / "statistics.parquet")

    criteria = {
        "apogee_p05": {"column": "apogee_agl", "quantile": 0.05, "relative_change": 0.005},
        "apogee_p50": {"column": "apogee_agl", "quantile": 0.50, "relative_change": 0.002},
        "apogee_p95": {"column": "apogee_agl", "quantile": 0.95, "relative_change": 0.005},
        "landing_ellipse_95_major": {"column": "landing_distance", "derived": "landing_ellipse_95_major", "relative_change": 0.01},
        "touchdown_velocity_p95": {"column": "touchdown_velocity", "quantile": 0.95, "relative_change": 0.01},
    }
    settings = campaign.settings
    configured = settings.get("convergence", {})
    checkpoints = configured.get("checkpoints", [50, 100, 200, 500, 1000, 2000, 5000, 7500, 10000, 12500, 15000, 17500, 20000]) if isinstance(configured, Mapping) else [len(outputs)]
    convergence = convergence_table(outputs, [point for point in checkpoints if point <= len(outputs)], criteria, int(configured.get("window", 3)) if isinstance(configured, Mapping) else 3)
    stability = sensitivity_stability_table(samples, outputs, [point for point in checkpoints if point <= len(outputs)], "apogee_agl", top_k=5, window=int(configured.get("window", 3)) if isinstance(configured, Mapping) else 3)
    if not stability.empty:
        convergence = pd.concat([convergence, stability], ignore_index=True)
    write_parquet_atomic(convergence, campaign.path / "convergence.parquet")
    write_parquet_atomic(stability, campaign.path / "sensitivity_stability.parquet")

    confidence_rows = []
    for metric in ("apogee_agl", "landing_distance", "touchdown_velocity"):
        if metric not in outputs:
            continue
        values = pd.to_numeric(outputs[metric], errors="coerce").dropna()
        p05_ci = quantile_confidence_interval(values, 0.05)
        p50_ci = quantile_confidence_interval(values, 0.50)
        p95_ci = quantile_confidence_interval(values, 0.95)
        confidence_rows.append({"metric": metric, "sample_count": len(values), "p05": float(np.percentile(values, 5)), "p05_ci_low": p05_ci[0], "p05_ci_high": p05_ci[1], "p50": float(np.percentile(values, 50)), "p50_ci_low": p50_ci[0], "p50_ci_high": p50_ci[1], "p95": float(np.percentile(values, 95)), "p95_ci_low": p95_ci[0], "p95_ci_high": p95_ci[1]})
    confidence = pd.DataFrame(confidence_rows)
    write_parquet_atomic(confidence, campaign.path / "confidence.parquet")

    sensitivity = spearman_sensitivity(samples, outputs, ["apogee_agl", "landing_distance", "touchdown_velocity", "max_dynamic_pressure"])
    write_parquet_atomic(sensitivity, campaign.path / "sensitivity.parquet")
    tail_frames = [conditional_tail_analysis(samples, outputs, metric) for metric in ("touchdown_velocity", "rail_exit_velocity", "landing_distance", "apogee_agl")]
    tail_analysis = pd.concat([item for item in tail_frames if not item.empty], ignore_index=True) if any(not item.empty for item in tail_frames) else pd.DataFrame()
    write_parquet_atomic(tail_analysis, campaign.path / "tail_analysis.parquet")
    compliance = compliance_analysis(outputs, _requirements(project_dir))
    write_parquet_atomic(compliance, campaign.path / "compliance.parquet")

    landing = landing_dispersion(outputs)
    representatives = _representative_cases(outputs)
    write_parquet_atomic(representatives, campaign.path / "representative_cases.parquet")
    convergence_status = bool(not convergence.empty and (convergence["status"] == "CONVERGED").all())
    warnings: list[str] = []
    if not samples.empty:
        for column in samples.columns:
            if column not in {"case_id", "seed"} and samples[column].isna().all():
                warnings.append(f"uncertainty '{column}' has no declared nominal and was not sampled")
    if len(failures):
        warnings.append("simulation failures were recorded and excluded from statistics")
        policy = campaign.settings.get("failure_policy", {})
        limit = float(policy.get("max_failure_fraction", 1.0)) if isinstance(policy, Mapping) else 1.0
        if len(failures) / max(len(outputs) + len(failures), 1) > limit:
            warnings.append("simulation failure rate exceeds the configured campaign policy")
    convergence_required = bool(campaign.settings.get("convergence", True))
    if convergence_required and not convergence_status and len(outputs) >= campaign.min_samples:
        warnings.append("one or more required output metrics did not converge")
    if landing.get("warning"):
        warnings.append(landing["warning"])
    sensitivity_status = bool(stability.empty or (stability["status"] == "CONVERGED").all())
    status = "FAILED" if len(outputs) < campaign.target_samples else ("COMPLETE_NOT_CONVERGED" if convergence_required and (not convergence_status or not sensitivity_status) else "COMPLETE")
    summary = {
        "campaign_id": campaign.campaign_id, "status": status,
        "requested": campaign.target_samples, "successful": int(len(outputs)), "failed": int(len(failures)),
        "convergence": {"required_metrics_converged": convergence_status and sensitivity_status, "sensitivity_ranking_converged": sensitivity_status}, "apogee": {},
        "landing": landing, "warnings": warnings,
        "artifacts": {name: name for name in ("inputs.parquet", "outputs.parquet", "statistics.parquet", "convergence.parquet", "confidence.parquet", "sensitivity.parquet", "sensitivity_stability.parquet", "tail_analysis.parquet", "compliance.parquet", "representative_cases.parquet")},
    }
    if not statistics.empty:
        apogee = statistics[statistics["metric"] == "apogee_agl"]
        if not apogee.empty:
            summary["apogee"] = {key: float(apogee.iloc[0][key]) for key in ("p05", "p50", "p95") if key in apogee}
    _write_plot_artifacts(campaign.path / "plots", outputs, convergence, sensitivity, compliance)
    write_json_atomic({
        "campaign_id": campaign.campaign_id,
        "input_table_bytes": campaign.samples_path.stat().st_size if campaign.samples_path.exists() else 0,
        "output_table_bytes": (campaign.path / "outputs.parquet").stat().st_size,
        "campaign_disk_bytes": directory_size(campaign.path),
        "successful_cases": len(outputs), "failed_cases": len(failures),
        "elapsed_seconds": time.perf_counter() - campaign.started_monotonic,
        "cases_per_second": len(outputs) / max(time.perf_counter() - campaign.started_monotonic, np.finfo(float).eps),
        "batch_count": len(list(campaign.batches_path.glob("batch_*.parquet"))),
    }, campaign.path / "performance.json")
    write_json_atomic(summary, campaign.path / "summary.json")
    campaign.write_manifest(summary["status"], samples, {"successful_samples": len(outputs), "failed_samples": len(failures), "warnings": warnings})
    return summary


def _write_plot_artifacts(directory: Path, outputs: pd.DataFrame, convergence: pd.DataFrame, sensitivity: pd.DataFrame, compliance: pd.DataFrame) -> None:
    """Create a small, fixed set of review plots from canonical tables."""
    if outputs.empty:
        return
    try:
        import matplotlib.pyplot as plt
        from antares_fd.reporting.theme import save_figure
    except ImportError:
        return
    directory.mkdir(parents=True, exist_ok=True)
    if "apogee_agl" in outputs:
        fig, axis = plt.subplots(figsize=(7, 4))
        values = pd.to_numeric(outputs["apogee_agl"], errors="coerce").dropna()
        axis.hist(values, bins=30, color="#2563eb", alpha=0.8)
        axis.axvline(values.quantile(0.05), color="#dc2626", linestyle="--", label="P05")
        axis.axvline(values.quantile(0.50), color="#111827", linestyle="-", label="P50")
        axis.axvline(values.quantile(0.95), color="#dc2626", linestyle="--", label="P95")
        axis.set(xlabel="Apogee AGL (m)", ylabel="Cases", title="Apogee distribution")
        axis.legend(); fig.tight_layout(); save_figure(fig, directory / "apogee_distribution.pdf", preview=False); plt.close(fig)
    if {"landing_east", "landing_north"}.issubset(outputs.columns):
        fig, axis = plt.subplots(figsize=(7, 5))
        axis.scatter(outputs["landing_east"], outputs["landing_north"], s=8, alpha=0.35, rasterized=True)
        axis.scatter([0], [0], marker="*", color="black")
        axis.set(xlabel="East (m)", ylabel="North (m)", title="Landing dispersion")
        axis.axis("equal"); fig.tight_layout(); save_figure(fig, directory / "landing_dispersion.pdf", preview=False); plt.close(fig)
    if "touchdown_velocity" in outputs:
        fig, axis = plt.subplots(figsize=(7, 4))
        axis.hist(pd.to_numeric(outputs["touchdown_velocity"], errors="coerce").dropna(), bins=30, color="#7c3aed", alpha=0.8)
        axis.axvline(0, color="black", linewidth=1); axis.set(xlabel="Touchdown velocity (m/s)", ylabel="Cases", title="Touchdown distribution")
        fig.tight_layout(); save_figure(fig, directory / "touchdown_distribution.pdf", preview=False); plt.close(fig)
    if not convergence.empty and "value" in convergence:
        figure, axis = plt.subplots(figsize=(7, 4))
        apogee = convergence[convergence["metric"] == "apogee_p50"]
        if not apogee.empty:
            axis.plot(apogee["checkpoint"], apogee["value"], marker="o")
        axis.set(xlabel="Cases", ylabel="P50 apogee (m)", title="Apogee convergence")
        figure.tight_layout(); save_figure(figure, directory / "convergence_apogee.pdf", preview=False); plt.close(figure)
    if not sensitivity.empty:
        apogee = sensitivity[sensitivity["output"] == "apogee_agl"].sort_values("coefficient")
        if not apogee.empty:
            figure, axis = plt.subplots(figsize=(7, 4)); axis.barh(apogee["input"], apogee["coefficient"], color="#0891b2")
            axis.set(xlabel="Spearman rho", title="Apogee sensitivity (association)"); figure.tight_layout(); save_figure(figure, directory / "sensitivity_apogee.pdf", preview=False); plt.close(figure)
    if not compliance.empty:
        figure, axis = plt.subplots(figsize=(7, 4)); axis.bar(compliance["requirement"], compliance["probability_satisfied"], color="#16a34a")
        axis.set_ylim(0, 1.05); axis.set_ylabel("Probability satisfied"); axis.tick_params(axis="x", rotation=45)
        figure.tight_layout(); save_figure(figure, directory / "compliance_probability.pdf", preview=False); plt.close(figure)
        margin_columns = [column for column in ("p05_margin", "p50_margin", "p95_margin") if column in compliance]
        if margin_columns:
            figure, axis = plt.subplots(figsize=(7, 4))
            axis.axhline(0, color="black", linewidth=1)
            for _, row in compliance.iterrows():
                axis.plot([row["requirement"]] * len(margin_columns), [row[column] for column in margin_columns], "o-")
            axis.set_ylabel("Requirement margin"); axis.tick_params(axis="x", rotation=45)
            figure.tight_layout(); save_figure(figure, directory / "requirement_margins.pdf", preview=False); plt.close(figure)
