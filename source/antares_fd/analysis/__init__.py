"""
Analysis subsystem for Antares Flight Dynamics.
"""

from .metrics import extract_flight_metrics
from .compliance import evaluate_compliance, ComplianceItem
from .sensitivity import analyze_monte_carlo_sensitivity
from .provenance import collect_reproducibility_data, evaluate_model_validity

__all__ = [
    "extract_flight_metrics",
    "evaluate_compliance",
    "ComplianceItem",
    "analyze_monte_carlo_sensitivity",
    "collect_reproducibility_data",
    "evaluate_model_validity",
]
