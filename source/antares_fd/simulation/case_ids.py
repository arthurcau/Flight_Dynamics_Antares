"""Canonical Monte Carlo case-ID contract.

Antares campaign case IDs are non-negative, zero-based integers. RocketPy's
parallel producer already exports zero-based ``index`` values; the serial
producer exports its incremented monitor count, so the campaign adapter must
normalize that producer at the boundary. Consumers never guess an index base.
"""

from __future__ import annotations

import math
from numbers import Integral, Real
from typing import Any, Iterable, Mapping


CASE_ID_BASE = 0


def normalize_case_id(value: Any, *, context: str = "case ID") -> int:
    """Validate and return a canonical zero-based case ID."""
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{context} must be a zero-based integer")
    if isinstance(value, Integral):
        case_id = int(value)
        if case_id < CASE_ID_BASE:
            raise ValueError(f"{context} must be a non-negative zero-based integer")
        return case_id
    try:
        number = float(value)
    except OverflowError as exc:
        raise ValueError(f"{context} is outside the finite integer range") from exc
    if not math.isfinite(number) or not number.is_integer() or number < CASE_ID_BASE:
        raise ValueError(f"{context} must be a non-negative zero-based integer")
    return int(number)


def canonicalize_case_records(
    records: Iterable[Mapping[str, Any]],
    *,
    allowed_case_ids: set[int] | None = None,
    context: str = "Monte Carlo records",
) -> list[dict[str, Any]]:
    """Copy records with explicit canonical IDs; reject ambiguity and duplicates."""
    normalized: list[dict[str, Any]] = []
    seen: set[int] = set()
    for row_number, record in enumerate(records, start=1):
        if not isinstance(record, Mapping):
            raise ValueError(f"{context} row {row_number} must be an object")
        explicit_id = record.get("case_id")
        exported_index = record.get("index")
        if explicit_id is None and exported_index is None:
            raise ValueError(f"{context} row {row_number} has no case_id or index")
        case_id = normalize_case_id(
            explicit_id if explicit_id is not None else exported_index,
            context=f"{context} row {row_number} case ID",
        )
        if explicit_id is not None and exported_index is not None:
            index_id = normalize_case_id(
                exported_index,
                context=f"{context} row {row_number} exported index",
            )
            if index_id != case_id:
                raise ValueError(
                    f"{context} row {row_number} has conflicting case_id and index"
                )
        if case_id in seen:
            raise ValueError(f"{context} contains duplicate case ID {case_id}")
        if allowed_case_ids is not None and case_id not in allowed_case_ids:
            raise ValueError(f"{context} contains case ID {case_id} outside the sample table")
        seen.add(case_id)
        copied = dict(record)
        copied["case_id"] = case_id
        normalized.append(copied)
    return normalized


def completed_prefix_length(case_ids: Iterable[int], requested: int) -> int:
    """Return a safely resumable completed prefix or fail closed on sparse IDs."""
    requested = int(requested)
    if requested < 0:
        raise ValueError("requested case count must be non-negative")
    ids = {normalize_case_id(case_id) for case_id in case_ids}
    outside = sorted(case_id for case_id in ids if case_id >= requested)
    if outside:
        raise ValueError(
            f"completed case IDs exceed requested range [0, {requested}): {outside[:5]}"
        )
    prefix = set(range(len(ids)))
    if ids != prefix:
        missing = sorted(prefix - ids)
        present = sorted(ids)
        raise ValueError(
            "cannot safely resume Monte Carlo records with non-prefix case IDs; "
            f"present={present[:10]}, missing within prefix={missing[:10]}"
        )
    return len(ids)
