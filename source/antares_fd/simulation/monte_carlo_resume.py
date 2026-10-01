"""Strict RocketPy JSONL restore and resume-prefix validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from antares_fd.simulation.case_ids import (
    canonicalize_case_records,
    completed_prefix_length,
    normalize_case_id,
)
from antares_fd.storage import read_jsonl_objects


def restore_jsonl_case_logs(
    monte_carlo: Any,
    outputs_path: Path,
    inputs_path: Path,
    *,
    allowed_case_ids: set[int],
) -> int:
    """Restore RocketPy logs and its resume counter from validated case IDs.

    JSONL physical line counts are deliberately ignored: blank lines do not
    represent simulations. Input and output records must pair by unique,
    zero-based case ID, and successful outputs must form a prefix so RocketPy's
    append API resumes at the next correct index.
    """
    allowed = {
        normalize_case_id(case_id, context="allowed Monte Carlo case ID")
        for case_id in allowed_case_ids
    }
    if allowed != set(range(len(allowed))):
        raise ValueError("allowed Monte Carlo case IDs must form a zero-based range")

    outputs = canonicalize_case_records(
        read_jsonl_objects(Path(outputs_path), missing_ok=True),
        allowed_case_ids=allowed,
        context="RocketPy output log",
    )
    inputs = canonicalize_case_records(
        read_jsonl_objects(Path(inputs_path), missing_ok=True),
        allowed_case_ids=allowed,
        context="RocketPy input log",
    )
    output_ids = {record["case_id"] for record in outputs}
    input_ids = {record["case_id"] for record in inputs}
    if output_ids != input_ids:
        raise ValueError(
            "RocketPy input/output logs do not contain the same case IDs; "
            "refusing an unsafe resume"
        )
    completed = completed_prefix_length(output_ids, len(allowed))

    monte_carlo.outputs_log = outputs
    monte_carlo.inputs_log = inputs
    monte_carlo.num_of_loaded_sims = completed
    return completed
