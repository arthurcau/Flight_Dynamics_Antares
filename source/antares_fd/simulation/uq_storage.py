"""Small, atomic storage primitives used by Monte Carlo campaigns.

The campaign keeps metadata in JSON and tabular data in compressed Parquet.
Writes are completed in the destination directory and committed with an atomic
rename, so an interrupted process cannot leave a file that looks complete.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

import pandas as pd


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


def read_parquet_files(directory: Path, pattern: str = "batch_*.parquet") -> pd.DataFrame:
    """Read campaign batches without requiring one file per simulation case."""
    files = sorted(Path(directory).glob(pattern))
    if not files:
        return pd.DataFrame()
    return pd.concat((pd.read_parquet(file) for file in files), ignore_index=True)


def directory_size(path: Path) -> int:
    """Return the number of bytes below *path* without loading file contents."""
    root = Path(path)
    if not root.exists():
        return 0
    return sum(item.stat().st_size for item in root.rglob("*") if item.is_file())
