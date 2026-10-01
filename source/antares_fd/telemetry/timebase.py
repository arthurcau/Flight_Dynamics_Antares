"""File-order clock segmentation without an inferred inter-segment timeline."""

from __future__ import annotations

import math

import pandas as pd

from .loader import ParsedTelemetry


SEGMENT_COLUMNS = (
    "record_index",
    "source_line_number",
    "segment_id",
    "raw_time",
    "segment_elapsed_s",
)


def segment_timebase(
    parsed: ParsedTelemetry,
    *,
    timestamp_channel: str,
    seconds_per_unit: float | None,
) -> pd.DataFrame:
    """Retain acquisition order and restart local elapsed time at a clock decrease.

    The first finite clock reading in a segment is its local origin. A missing
    clock value remains in that segment with an unavailable elapsed time. The
    next finite value is compared with the preceding finite reading, so an
    intervening missing value cannot conceal an observed backward jump.
    Neither reset downtime nor a globally continuous clock is inferred.
    """

    if timestamp_channel not in parsed.channels:
        raise ValueError(f"Timestamp channel {timestamp_channel!r} is absent from the parsed header")
    if seconds_per_unit is not None and (
        not math.isfinite(seconds_per_unit) or seconds_per_unit <= 0
    ):
        raise ValueError("seconds_per_unit must be finite and positive")

    rows: list[dict[str, int | float | None]] = []
    segment_id = 0
    previous_finite_time: float | None = None
    segment_origin: float | None = None
    for record in parsed.records:
        raw_time = record["values"][timestamp_channel]["numeric_value"]
        if raw_time is not None:
            if previous_finite_time is not None and raw_time < previous_finite_time:
                segment_id += 1
                segment_origin = raw_time
            elif segment_origin is None:
                segment_origin = raw_time
            previous_finite_time = raw_time
        elapsed = (
            (raw_time - segment_origin) * seconds_per_unit
            if raw_time is not None and segment_origin is not None and seconds_per_unit is not None
            else None
        )
        rows.append(
            {
                "record_index": record["record_index"],
                "source_line_number": record["source_line_number"],
                "segment_id": segment_id,
                "raw_time": raw_time,
                "segment_elapsed_s": elapsed,
            }
        )
    return pd.DataFrame.from_records(rows, columns=SEGMENT_COLUMNS)
