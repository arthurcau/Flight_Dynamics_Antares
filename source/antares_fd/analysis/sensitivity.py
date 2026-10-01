"""
Monte Carlo Statistical & Sensitivity Analysis.

Computes distributions, percentiles, and input-output correlations
(Tornado analysis) from Monte Carlo campaigns.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from scipy import stats

from antares_fd.analysis.uq import finite_numeric_series, summarize_finite_values
from antares_fd.storage import read_jsonl_objects


def analyze_monte_carlo_sensitivity(
    outputs_file: Path,
    inputs_file: Optional[Path] = None,
    target_metric: str = "apogee",
) -> Dict[str, Any]:
    """
    Analyzes outputs and stochastic inputs to produce statistical summaries and sensitivity correlations.

    Args:
        outputs_file: Path to mc_sim.outputs.txt.
        inputs_file: Optional Path to mc_sim.inputs.txt.
        target_metric: Primary metric for sensitivity analysis ('apogee' or 'impact_distance').

    Returns:
        Structured dictionary containing distribution statistics, percentiles, and sensitivity ranking.
    """
    if not outputs_file.exists():
        return {}

    # 1. Load outputs
    out_records = read_jsonl_objects(outputs_file)

    if not out_records:
        return {}

    df_out = pd.DataFrame(out_records)
    if "x_impact" in df_out.columns and "y_impact" in df_out.columns:
        df_out["impact_distance"] = np.sqrt(df_out["x_impact"]**2 + df_out["y_impact"]**2)

    # 2. Extract distribution statistics & percentiles
    metrics_to_summarize = [
        "apogee", "out_of_rail_velocity", "impact_velocity", "impact_distance",
        "max_mach_number", "max_dynamic_pressure", "t_final", "apogee_time"
    ]

    summary_stats: Dict[str, Dict[str, float]] = {}
    percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]

    for col in metrics_to_summarize:
        if col not in df_out.columns:
            continue
        aligned = finite_numeric_series(df_out[col], col)
        series = aligned[np.isfinite(aligned)]
        if len(series) == 0:
            continue
        count, mean, standard_deviation = summarize_finite_values(aligned, col)

        pct_dict = {f"p{p}": float(np.percentile(series, p)) for p in percentiles}
        summary_stats[col] = {
            "count": count,
            "mean": float(mean),
            "std": float(standard_deviation) if standard_deviation is not None else float("nan"),
            "min": float(series.min()),
            "max": float(series.max()),
            **pct_dict,
        }

    # 3. Sensitivity Correlation (if inputs available)
    sensitivity_ranking: List[Dict[str, Any]] = []

    if inputs_file is not None:
        in_records = read_jsonl_objects(inputs_file)
        if len(in_records) != len(out_records):
            raise ValueError(
                "Monte Carlo input/output record counts differ: "
                f"{len(in_records)} inputs vs {len(out_records)} outputs"
            )
        if in_records:
            # Flatten numeric inputs
            flat_inputs: List[Dict[str, float]] = []
            for row in in_records:
                flat_row = {}
                for k, v in row.items():
                    if isinstance(v, (int, float)) and not isinstance(v, bool):
                        if k != "index":
                            flat_row[k] = float(v)
                flat_inputs.append(flat_row)

            df_in = pd.DataFrame(flat_inputs)

            if target_metric in df_out.columns:
                target_series = finite_numeric_series(df_out[target_metric], target_metric)
                for param in df_in.columns:
                    param_series = finite_numeric_series(df_in[param], param)
                    valid = np.isfinite(param_series) & np.isfinite(target_series)
                    paired_x = param_series[valid]
                    paired_y = target_series[valid]
                    if len(paired_x) >= 3 and np.std(paired_x) > 1e-8 and np.std(paired_y) > 0:
                        r_pearson, p_val = stats.pearsonr(paired_x, paired_y)
                        r_spearman, _ = stats.spearmanr(paired_x, paired_y)
                        if not np.isnan(r_pearson):
                            sensitivity_ranking.append({
                                "parameter": param,
                                "pearson_r": float(r_pearson),
                                "spearman_rho": float(r_spearman),
                                "abs_correlation": float(abs(r_pearson)),
                                "p_value": float(p_val),
                                "sample_count": int(len(paired_x)),
                            })

                sensitivity_ranking.sort(key=lambda x: x["abs_correlation"], reverse=True)

    return {
        "num_cases": len(df_out),
        "statistics": summary_stats,
        "sensitivity_target": target_metric,
        "sensitivity_ranking": sensitivity_ranking,
    }
