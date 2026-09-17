"""
Analysis subsystem for Antares Flight Dynamics.
"""

from .metrics import extract_flight_metrics
from .compliance import evaluate_compliance, ComplianceItem
from .sensitivity import analyze_monte_carlo_sensitivity
from .provenance import collect_reproducibility_data, evaluate_model_validity
from .uq import (
    compliance_analysis,
    convergence_table,
    distribution_statistics,
    landing_dispersion,
    probability_confidence_interval,
    quantile_confidence_interval,
    spearman_sensitivity,
)

__all__ = [
    "extract_flight_metrics",
    "evaluate_compliance",
    "ComplianceItem",
    "analyze_monte_carlo_sensitivity",
    "collect_reproducibility_data",
    "evaluate_model_validity",
    "distribution_statistics",
    "convergence_table",
    "quantile_confidence_interval",
    "probability_confidence_interval",
    "landing_dispersion",
    "spearman_sensitivity",
    "compliance_analysis",
]
