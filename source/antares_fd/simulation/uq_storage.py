"""Small, atomic storage primitives used by Monte Carlo campaigns.

The campaign keeps metadata in JSON and tabular data in compressed Parquet.
Writes are completed in the destination directory and committed with an atomic
rename, so an interrupted process cannot leave a file that looks complete.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from antares_fd.storage import write_json_atomic, write_parquet_atomic


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
