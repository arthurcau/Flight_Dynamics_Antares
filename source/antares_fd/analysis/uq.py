"""Statistical post processing for saved Monte Carlo result tables.

Functions in this module consume pandas tables and never need RocketPy
objects.  They are deliberately small and composable so reports, CLI tools and
future Award Brief renderers use the same calculations.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd
from scipy import stats


PERCENTILES = (1, 5, 10, 25, 50, 75, 90, 95, 99)


def _numeric(values: Iterable[Any]) -> np.ndarray:
    return pd.to_numeric(pd.Series(values), errors="coerce").dropna().to_numpy(dtype=float)


def distribution_statistics(frame: pd.DataFrame, columns: Sequence[str] | None = None) -> pd.DataFrame:
    """Return one typed row per output and standard engineering percentiles."""
    columns = list(columns or frame.select_dtypes(include="number").columns)
    rows: list[dict[str, Any]] = []
    for column in columns:
        if column not in frame:
            continue
        values = _numeric(frame[column])
        if not len(values):
            continue
        row: dict[str, Any] = {
            "metric": column,
            "count": int(len(values)),
            "mean": float(np.mean(values)),
            "std": float(np.std(values, ddof=1)) if len(values) > 1 else 0.0,
            "min": float(np.min(values)),
            "max": float(np.max(values)),
            "skewness": float(stats.skew(values, bias=False)) if len(values) > 2 else np.nan,
            "kurtosis": float(stats.kurtosis(values, bias=False)) if len(values) > 3 else np.nan,
        }
        row.update({f"p{percentile:02d}": float(np.percentile(values, percentile)) for percentile in PERCENTILES})
        rows.append(row)
    return pd.DataFrame(rows)


def quantile_confidence_interval(values: Iterable[Any], quantile: float, confidence: float = 0.95) -> tuple[float, float]:
    """Exact order-statistics interval for a population quantile.

    The interval is formed from binomial order statistics, which does not
    assume a Gaussian output distribution.  Endpoints are observed sample
    values and therefore have an honest resolution at small sample counts.
    """
    sample = np.sort(_numeric(values))
    if not len(sample):
        return (float("nan"), float("nan"))
    q = float(np.clip(quantile, 0.0, 1.0))
    alpha = 1.0 - float(confidence)
    lower_rank = int(stats.binom.ppf(alpha / 2.0, len(sample), q))
    upper_rank = int(stats.binom.isf(alpha / 2.0, len(sample), q))
    lower_rank = max(1, min(len(sample), lower_rank))
    upper_rank = max(lower_rank, min(len(sample), upper_rank + 1))
    return float(sample[lower_rank - 1]), float(sample[upper_rank - 1])


def probability_confidence_interval(successes: int, trials: int, confidence: float = 0.95) -> tuple[float, float]:
    """Two-sided exact Clopper-Pearson interval for a binomial probability."""
    if trials <= 0:
        return (float("nan"), float("nan"))
    successes = max(0, min(int(successes), int(trials)))
    alpha = 1.0 - float(confidence)
    lower = 0.0 if successes == 0 else float(stats.beta.ppf(alpha / 2.0, successes, trials - successes + 1))
    upper = 1.0 if successes == trials else float(stats.beta.ppf(1.0 - alpha / 2.0, successes + 1, trials - successes))
    return lower, upper


def one_sided_lower_bound(successes: int, trials: int, confidence: float = 0.95) -> float:
    """Exact one-sided lower confidence bound for a compliance probability."""
    if trials <= 0:
        return float("nan")
    successes = max(0, min(int(successes), int(trials)))
    if successes == 0:
        return 0.0
    return float(stats.beta.ppf(1.0 - (1.0 - confidence), successes, trials - successes + 1))


def landing_dispersion(frame: pd.DataFrame, confidence_levels: Sequence[float] = (0.50, 0.80, 0.90, 0.95, 0.99)) -> dict[str, Any]:
    """Calculate ENU covariance and correctly scaled two-dimensional ellipses."""
    east_name = "landing_east" if "landing_east" in frame else "x_impact"
    north_name = "landing_north" if "landing_north" in frame else "y_impact"
    if east_name not in frame or north_name not in frame:
        return {"count": 0, "warning": "landing coordinates unavailable"}
    points = frame[[east_name, north_name]].apply(pd.to_numeric, errors="coerce").dropna().to_numpy(float)
    if not len(points):
        return {"count": 0, "warning": "landing coordinates unavailable"}
    mean = points.mean(axis=0)
    covariance = np.cov(points, rowvar=False, ddof=1) if len(points) > 1 else np.zeros((2, 2))
    covariance = np.asarray(covariance, dtype=float).reshape(2, 2)
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    order = np.argsort(eigenvalues)[::-1]
    eigenvalues = np.maximum(eigenvalues[order], 0.0)
    eigenvectors = eigenvectors[:, order]
    orientation = float(np.degrees(np.arctan2(eigenvectors[1, 0], eigenvectors[0, 0])))
    ellipses = {}
    for level in confidence_levels:
        scale = float(np.sqrt(stats.chi2.ppf(level, df=2)))
        ellipses[str(level)] = {
            "major_axis": float(scale * np.sqrt(eigenvalues[0])),
            "minor_axis": float(scale * np.sqrt(eigenvalues[1])),
            "orientation_deg": orientation,
        }
    warning = None
    if len(points) >= 20:
        radii = np.linalg.norm(points - mean, axis=1)
        if float(stats.skew(radii, bias=False)) > 1.0 or np.linalg.matrix_rank(covariance) < 2:
            warning = "landing cloud may be skewed, multimodal or degenerate; inspect raw points"
    return {
        "count": int(len(points)),
        "mean_east": float(mean[0]),
        "mean_north": float(mean[1]),
        "median_east": float(np.median(points[:, 0])),
        "median_north": float(np.median(points[:, 1])),
        "covariance": covariance.tolist(),
        "ellipses": ellipses,
        "warning": warning,
    }


def convergence_table(frame: pd.DataFrame, checkpoints: Sequence[int], criteria: Mapping[str, Mapping[str, float]], window: int = 3) -> pd.DataFrame:
    """Evaluate output-specific stability using existing result prefixes."""
    rows: list[dict[str, Any]] = []
    checkpoints = sorted({int(point) for point in checkpoints if int(point) > 0})
    for metric, criterion in criteria.items():
        column = criterion.get("column", metric)
        if column not in frame:
            rows.append({"metric": metric, "checkpoint": None, "status": "UNAVAILABLE"})
            continue
        series = _numeric(frame[column])
        values: list[float] = []
        for checkpoint in checkpoints:
            if len(series) < checkpoint:
                continue
            q = criterion.get("quantile")
            if criterion.get("derived") == "landing_ellipse_95_major":
                prefix = frame.iloc[:checkpoint]
                value = float(landing_dispersion(prefix)["ellipses"]["0.95"]["major_axis"])
            else:
                value = float(np.quantile(series[:checkpoint], q)) if q is not None else float(np.mean(series[:checkpoint]))
            values.append(value)
            rows.append({"metric": metric, "checkpoint": checkpoint, "value": value, "status": "PENDING"})
        tolerance = float(criterion.get("relative_change", criterion.get("absolute_change", 0.0)))
        relative = "relative_change" in criterion
        stable = False
        if len(values) >= max(2, window):
            recent = values[-window:]
            changes = []
            for previous, current in zip(recent, recent[1:]):
                denominator = max(abs(previous), np.finfo(float).eps)
                changes.append(abs(current - previous) / denominator if relative else abs(current - previous))
            stable = all(change <= tolerance for change in changes)
        for row in reversed(rows):
            if row.get("metric") != metric:
                break
            row["status"] = "CONVERGED" if stable else "NOT_CONVERGED"
            row["tolerance"] = tolerance
            row["window"] = int(window)
    return pd.DataFrame(rows)


def sensitivity_stability_table(inputs: pd.DataFrame, outputs: pd.DataFrame, checkpoints: Sequence[int], output: str, top_k: int = 5, window: int = 3) -> pd.DataFrame:
    """Track top-driver overlap and rank agreement across existing prefixes."""
    rows: list[dict[str, Any]] = []
    rankings: list[list[str]] = []
    for checkpoint in sorted({int(point) for point in checkpoints if int(point) > 0}):
        if len(outputs) < checkpoint:
            continue
        local = spearman_sensitivity(inputs.iloc[:checkpoint], outputs.iloc[:checkpoint], [output])
        if local.empty:
            continue
        local = local.sort_values("coefficient", key=lambda values: values.abs(), ascending=False)
        ranking = local["input"].tolist()
        rankings.append(ranking)
        rows.append({"metric": f"sensitivity_{output}_top{top_k}", "checkpoint": checkpoint, "top_k": top_k, "top_inputs": ",".join(ranking[:top_k]), "status": "PENDING"})
    stable = False
    if len(rankings) >= max(2, window):
        recent = rankings[-window:]
        overlaps = []
        agreements = []
        for first, second in zip(recent, recent[1:]):
            first_top, second_top = set(first[:top_k]), set(second[:top_k])
            union = first_top | second_top
            overlaps.append(len(first_top & second_top) / len(union) if union else 1.0)
            common = [item for item in first if item in second]
            if len(common) >= 2:
                agreements.append(float(stats.spearmanr([first.index(item) for item in common], [second.index(item) for item in common]).statistic))
        stable = all(value >= 0.8 for value in overlaps) and all(value >= 0.8 for value in agreements)
    for row in rows:
        row["status"] = "CONVERGED" if stable else "NOT_CONVERGED"
    return pd.DataFrame(rows)


def conditional_tail_analysis(inputs: pd.DataFrame, outputs: pd.DataFrame, metric: str, quantile: float = 0.99, upper: bool = True) -> pd.DataFrame:
    """Compare input distributions in an extreme output tail with all cases."""
    if metric not in outputs:
        return pd.DataFrame()
    output_values = pd.to_numeric(outputs[metric], errors="coerce")
    threshold = output_values.quantile(quantile if upper else 1.0 - quantile)
    selected = output_values >= threshold if upper else output_values <= threshold
    numeric = inputs.select_dtypes(include="number")
    rows: list[dict[str, Any]] = []
    for column in numeric.columns:
        if column in {"case_id", "seed"}:
            continue
        full = pd.to_numeric(numeric[column], errors="coerce")
        tail = full[selected].dropna()
        if tail.empty or full.dropna().empty:
            continue
        rows.append({"output": metric, "tail": "upper" if upper else "lower", "quantile": quantile, "threshold": float(threshold), "input": column, "full_mean": float(full.mean()), "tail_mean": float(tail.mean()), "mean_shift": float(tail.mean() - full.mean()), "tail_count": int(len(tail)), "sample_count": int(full.notna().sum())})
    return pd.DataFrame(rows).sort_values("mean_shift", key=lambda values: values.abs(), ascending=False) if rows else pd.DataFrame()


def spearman_sensitivity(inputs: pd.DataFrame, outputs: pd.DataFrame, output_columns: Sequence[str]) -> pd.DataFrame:
    """Return rank correlations as evidence of association, never causality."""
    joined = pd.concat([inputs.reset_index(drop=True), outputs.reset_index(drop=True)], axis=1)
    numeric_inputs = [column for column in inputs.select_dtypes(include="number") if column not in {"case_id", "seed"}]
    rows: list[dict[str, Any]] = []
    for output in output_columns:
        if output not in joined:
            continue
        y = pd.to_numeric(joined[output], errors="coerce")
        for input_name in numeric_inputs:
            x = pd.to_numeric(joined[input_name], errors="coerce")
            valid = x.notna() & y.notna()
            if valid.sum() < 3 or x[valid].nunique() < 2:
                continue
            coefficient, pvalue = stats.spearmanr(x[valid], y[valid])
            rows.append({"input": input_name, "output": output, "method": "spearman", "coefficient": float(coefficient), "p_value": float(pvalue), "sample_count": int(valid.sum())})
    result = pd.DataFrame(rows)
    if not result.empty:
        result["rank"] = result.groupby("output")["coefficient"].transform(lambda values: values.abs().rank(method="min", ascending=False).astype(int))
    return result


def compliance_analysis(frame: pd.DataFrame, requirements: Mapping[str, Mapping[str, Any]], confidence: float = 0.95) -> pd.DataFrame:
    """Evaluate per-case margins and exact probability confidence bounds."""
    rows: list[dict[str, Any]] = []
    for req_id, requirement in requirements.items():
        metric = requirement.get("metric")
        if metric not in frame:
            continue
        values = pd.to_numeric(frame[metric], errors="coerce")
        operator = requirement.get("operator")
        limit = requirement.get("limit")
        if operator == ">=":
            margin = values - float(limit)
        elif operator == "<=":
            margin = float(limit) - values
        elif operator == "between" and isinstance(limit, (list, tuple)):
            margin = np.minimum(values - float(limit[0]), float(limit[1]) - values)
        else:
            continue
        valid = margin.dropna()
        successes = int((valid >= 0).sum())
        trials = int(len(valid))
        lower, upper = probability_confidence_interval(successes, trials, confidence)
        one_sided = one_sided_lower_bound(successes, trials, confidence)
        worst_index = valid.idxmin() if len(valid) else None
        rows.append({
            "requirement": req_id, "metric": metric, "limit": limit, "operator": operator,
            "nominal_margin": None, "p05_margin": float(np.percentile(valid, 5)) if len(valid) else np.nan,
            "p50_margin": float(np.percentile(valid, 50)) if len(valid) else np.nan,
            "p95_margin": float(np.percentile(valid, 95)) if len(valid) else np.nan,
            "probability_satisfied": successes / trials if trials else np.nan,
            "ci_lower": lower, "ci_upper": upper, "one_sided_lower_bound": one_sided,
            "verification_status": "STATISTICALLY_DEMONSTRATED" if one_sided >= float(requirement.get("required_probability", 0.99)) else "NOT_STATISTICALLY_DEMONSTRATED",
            "worst_margin": float(valid.min()) if len(valid) else np.nan,
            "worst_case_id": frame.loc[worst_index, "case_id"] if worst_index is not None and "case_id" in frame else None,
        })
    return pd.DataFrame(rows)
