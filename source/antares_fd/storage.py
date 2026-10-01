"""Atomic JSON and Parquet writers shared by simulation and telemetry."""

from __future__ import annotations

import json
import math
import os
import tempfile
from pathlib import Path
from typing import Any, Iterator

import pandas as pd


def _validate_finite_json_values(value: Any) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("non-finite numeric value")
    if isinstance(value, int) and not isinstance(value, bool):
        try:
            representable = math.isfinite(float(value))
        except OverflowError:
            representable = False
        if not representable:
            raise ValueError("non-finite numeric value")
    if isinstance(value, dict):
        for nested_value in value.values():
            _validate_finite_json_values(nested_value)
    elif isinstance(value, list):
        for nested_value in value:
            _validate_finite_json_values(nested_value)


def iter_jsonl_objects(path: Path, *, missing_ok: bool = False) -> Iterator[dict[str, Any]]:
    """Yield ordered JSONL objects and fail on malformed or non-finite records.

    Blank lines are ignored. Every nonblank line must contain one JSON object;
    numeric values must be representable as finite Python floats. Errors
    include the source path and physical line number so partial analyses cannot
    silently omit a damaged record.
    """
    path = Path(path)
    if not path.exists():
        if missing_ok:
            return
        raise FileNotFoundError(path)

    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON") from exc
            if not isinstance(record, dict):
                raise ValueError(f"{path}:{line_number}: expected a JSON object")
            try:
                _validate_finite_json_values(record)
            except ValueError as exc:
                raise ValueError(f"{path}:{line_number}: {exc}") from exc
            yield record


def read_jsonl_objects(path: Path, *, missing_ok: bool = False) -> list[dict[str, Any]]:
    """Read every JSONL record using the strict shared validation contract."""
    return list(iter_jsonl_objects(path, missing_ok=missing_ok))


def _temporary_path(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    os.close(handle)
    return Path(name)


def write_parquet_atomic(frame: pd.DataFrame, path: Path, compression: str = "zstd") -> Path:
    """Write *frame* to Parquet and atomically replace *path*."""
    path = Path(path)
    temporary = _temporary_path(path)
    try:
        frame.to_parquet(temporary, engine="pyarrow", compression=compression, index=False)
        os.replace(temporary, path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return path


def write_json_atomic(value: Any, path: Path) -> Path:
    """Write a small JSON document with an atomic commit."""
    path = Path(path)
    temporary = _temporary_path(path)
    try:
        with temporary.open("w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, ensure_ascii=False, default=str)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return path
