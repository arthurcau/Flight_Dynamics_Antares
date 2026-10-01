"""Descriptive residuals with explicit, evidence-backed clock alignment."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Alignment:
    """Anchor one observed clock segment to a simulation time origin."""

    segment_id: int
    observed_anchor_time_s: float
    simulated_anchor_time_s: float
    event: str
    evidence: str
    uncertainty_s: float

    def __post_init__(self) -> None:
        if not isinstance(self.segment_id, int) or self.segment_id < 0:
            raise ValueError("segment_id must be a nonnegative integer")
        if any(not math.isfinite(value) for value in (
            self.observed_anchor_time_s, self.simulated_anchor_time_s, self.uncertainty_s
        )) or self.uncertainty_s < 0:
            raise ValueError("Alignment times must be finite and uncertainty nonnegative")
        if not self.event.strip() or not self.evidence.strip():
            raise ValueError("Alignment requires an observed event and evidence")


@dataclass(frozen=True)
class ComparisonBasis:
    """Declare the two units and frames before computing any residual."""

    observed_unit: str
    simulated_unit: str
    observed_frame: str
    simulated_frame: str
    observed_unit_status: str
    evidence: str

    def __post_init__(self) -> None:
        fields = (
            self.observed_unit, self.simulated_unit, self.observed_frame,
            self.simulated_frame, self.evidence,
        )
        if any(not isinstance(value, str) or not value.strip() for value in fields):
            raise ValueError("Comparison units, frames and evidence must be nonempty")
        if self.observed_unit_status not in {"DOCUMENTED", "HEADER_LABEL", "UNIT_ASSUMED"}:
            raise ValueError("observed_unit_status must describe the unit evidence")
        if self.observed_unit != self.simulated_unit:
            raise ValueError("Comparison unit mismatch; convert explicitly upstream")
        if (self.observed_frame != self.simulated_frame
                or "UNKNOWN" in self.observed_frame.upper()):
            raise ValueError("Comparison frame mismatch or unknown frame")


def _array(values: Sequence[float], name: str) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    if array.ndim != 1 or array.size == 0:
        raise ValueError(f"{name} must be a nonempty one-dimensional series")
    return array


def compare_time_series(
    observed_time_s: Sequence[float],
    observed_segment_id: Sequence[int],
    observed_values: Sequence[float],
    simulated_time_s: Sequence[float],
    simulated_values: Sequence[float],
    *,
    observed_record_index: Sequence[int],
    alignment: Alignment,
    basis: ComparisonBasis,
    quantity: str,
    observed_origin: str,
) -> pd.DataFrame:
    """Return simulated-minus-observed residuals without crossing clock segments.

    The caller must establish the event anchor independently from telemetry.
    This operation interpolates the simulated series only within its domain.
    It does not infer a launch time, correct timestamps or fill missing samples.
    """
    if observed_origin not in {"MEASURED", "DERIVED"}:
        raise ValueError("observed_origin must be MEASURED or DERIVED")
    if not isinstance(basis, ComparisonBasis):
        raise ValueError("basis must explicitly declare matching units and frames")
    if not isinstance(quantity, str) or not quantity.strip():
        raise ValueError("quantity must be explicitly named with units")
    obs_t = _array(observed_time_s, "observed_time_s")
    obs_y = _array(observed_values, "observed_values")
    sim_t = _array(simulated_time_s, "simulated_time_s")
    sim_y = _array(simulated_values, "simulated_values")
    segments = np.asarray(observed_segment_id)
    record_index = np.asarray(observed_record_index)
    if segments.ndim != 1 or len(segments) != len(obs_t) or len(obs_y) != len(obs_t):
        raise ValueError("Observed time, segment and value series must have equal length")
    if len(sim_y) != len(sim_t) or len(sim_t) < 2:
        raise ValueError("Simulated time and value series need at least two paired samples")
    if (record_index.ndim != 1 or len(record_index) != len(obs_t)
            or not np.issubdtype(record_index.dtype, np.integer)
            or np.any(record_index < 0) or np.any(np.diff(record_index) <= 0)):
        raise ValueError("observed_record_index must preserve unique acquisition order")
    if segments.ndim != 1 or not np.issubdtype(segments.dtype, np.integer):
        raise ValueError("observed_segment_id must contain integer segment_id values")
    if not np.all(segments == alignment.segment_id):
        raise ValueError("Comparison requires a single observed segment matching the alignment")
    if not np.isfinite(obs_t).all() or not np.isfinite(sim_t).all() or not np.isfinite(sim_y).all():
        raise ValueError("Time coordinates and simulated values must be finite")
    if np.isinf(obs_y).any():
        raise ValueError("Observed values may be missing (NaN), but not infinite")
    if np.any(np.diff(obs_t) <= 0) or np.any(np.diff(sim_t) <= 0):
        raise ValueError("Time coordinates must increase strictly in file order")
    model_t = obs_t - alignment.observed_anchor_time_s + alignment.simulated_anchor_time_s
    if model_t[0] < sim_t[0] or model_t[-1] > sim_t[-1]:
        raise ValueError("Comparison would require simulation extrapolation")
    model_y = np.interp(model_t, sim_t, sim_y)
    result = pd.DataFrame({
        "record_index": record_index,
        "observed_time_s": obs_t,
        "segment_id": segments,
        "model_time_s": model_t,
        "observed_value": obs_y,
        "simulated_value": model_y,
        "residual_simulated_minus_observed": model_y - obs_y,
    })
    result.attrs.update({
        "quantity": quantity, "observed_origin": observed_origin,
        "simulated_origin": "MODELED", "alignment_event": alignment.event,
        "alignment_evidence": alignment.evidence,
        "alignment_uncertainty_s": alignment.uncertainty_s,
        "unit": basis.observed_unit, "frame": basis.observed_frame,
        "observed_unit_status": basis.observed_unit_status,
        "basis_evidence": basis.evidence,
    })
    return result


def summarize_residuals(residuals: pd.DataFrame) -> dict[str, float | int | str]:
    """Describe valid residuals; this does not establish model validity."""
    values = residuals["residual_simulated_minus_observed"].to_numpy(dtype=float)
    finite = values[np.isfinite(values)]
    if not len(finite):
        return {"status": "INSUFFICIENT_OBSERVABILITY", "valid_count": 0}
    return {
        "status": "DESCRIPTIVE_ONLY",
        "valid_count": int(len(finite)),
        "mean": float(np.mean(finite)),
        "mae": float(np.mean(np.abs(finite))),
        "rmse": float(np.sqrt(np.mean(finite * finite))),
        "maximum_absolute": float(np.max(np.abs(finite))),
    }
