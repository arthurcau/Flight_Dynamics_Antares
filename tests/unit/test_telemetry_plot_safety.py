"""The raw plotting utility must preserve source evidence and clock boundaries."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd
import pytest


SCRIPT = Path(__file__).resolve().parents[2] / "projects/neblina_1/simulations/plot_flight_data.py"


def _module():
    spec = importlib.util.spec_from_file_location("neblina_raw_plot", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_plot_uses_acquisition_order_without_stitching_clock_segments(tmp_path: Path) -> None:
    source = tmp_path / "raw.log"
    source.write_text("boot\ntime_ms,bmp1_rel_alt_m\n100,0\n200,1\n10,2\n20,3\n", encoding="utf-8")
    data = _module().load_telemetry(source)

    assert data["record_index"].tolist() == [0, 1, 2, 3]
    assert data["segment"].tolist() == [0, 0, 1, 1]
    assert "plot_time_s" not in data
    assert data["time_ms"].tolist() == [100, 200, 10, 20]


def test_plot_rejects_source_collision_and_existing_artifact(tmp_path: Path) -> None:
    source = tmp_path / "results" / "raw.log"
    source.parent.mkdir(parents=True)
    original = b"boot\ntime_ms,bmp1_rel_alt_m\n100,0\n200,1\n"
    source.write_bytes(original)
    plot = _module()
    data = plot.load_telemetry(source)

    with pytest.raises(ValueError, match="raw source"):
        plot.write_plots(data, source, source_path=source, repo_root=tmp_path)
    assert source.read_bytes() == original

    destination = tmp_path / "results" / "existing.pdf"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(b"prior result")
    with pytest.raises(FileExistsError):
        plot.write_plots(data, destination, source_path=source, repo_root=tmp_path)
    assert destination.read_bytes() == b"prior result"


def test_plot_rejects_output_outside_results(tmp_path: Path) -> None:
    source = tmp_path / "raw.log"
    source.write_text("time_ms,bmp1_rel_alt_m\n100,0\n200,1\n", encoding="utf-8")
    plot = _module()
    data = plot.load_telemetry(source)
    destination = tmp_path / "data" / "plots.pdf"
    with pytest.raises(ValueError, match="results"):
        plot.write_plots(data, destination, source_path=source, repo_root=tmp_path)
    assert not destination.exists()


def test_plot_keeps_clock_boundary_after_missing_time(tmp_path: Path) -> None:
    source = tmp_path / "raw.log"
    source.write_text("boot\ntime_ms,bmp1_rel_alt_m\n100,0\n200,1\nnan,2\n10,3\n", encoding="utf-8")
    data = _module().load_telemetry(source)
    assert data["record_index"].tolist() == [0, 1, 2, 3]
    assert data["segment"].tolist() == [0, 0, 0, 1]
    assert pd.isna(data.loc[2, "time_ms"])
