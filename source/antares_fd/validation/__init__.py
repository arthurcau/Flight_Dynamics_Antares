"""Explicit model provenance and time-aligned flight comparison contracts."""

from .models import ModelVariant, load_model_variants, parse_model_variants
from .residuals import Alignment, ComparisonBasis, compare_time_series, summarize_residuals

__all__ = [
    "Alignment", "ComparisonBasis", "ModelVariant", "compare_time_series", "load_model_variants",
    "parse_model_variants", "summarize_residuals",
]
