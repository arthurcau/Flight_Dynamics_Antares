"""Plot the raw Neblina flight telemetry log in acquisition order.

The log contains ESP32 boot messages before the CSV header.  This script finds
the header automatically, loads every telemetry column, and writes a PDF with
one overview page and one detailed page per sensor group.  Missing values are
kept as gaps in the curves instead of being interpolated.

Example:
    .venv/bin/python projects/neblina_1/simulations/plot_flight_data.py

Use ``--log`` and ``--output`` to plot a different log or choose a new PDF
destination. The horizontal axis is sample order because clock segments cannot
be stitched into one elapsed-time axis from the available evidence. Review
notes by Cau.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import matplotlib

# The default use case writes files and should work without a display server.
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import pandas as pd

from antares_fd.telemetry.loader import find_csv_header_line, parse_telemetry_log
from antares_fd.telemetry.timebase import segment_timebase


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_LOG = PROJECT_ROOT / "data" / "flight_data" / "Dados de Vôo Neblina - LASC 2026.log"
DEFAULT_RESULTS = PROJECT_ROOT / "results" / "neblina_1"


GROUPS: tuple[tuple[str, tuple[str, ...], str, str], ...] = (
    (
        "Altímetros",
        ("bmp1_rel_alt_m", "bmp2_rel_alt_m"),
        "Altitude relativa calculada a bordo [m]",
        "Altitude",
    ),
    (
        "Acelerômetro MPU1",
        ("mpu1_ax_g", "mpu1_ay_g", "mpu1_az_g"),
        "Leitura bruta do acelerômetro [g]",
        "MPU1 — aceleração",
    ),
    (
        "Giroscópio MPU1",
        ("mpu1_gx_dps", "mpu1_gy_dps", "mpu1_gz_dps"),
        "Velocidade angular [graus/s]",
        "MPU1 — velocidade angular",
    ),
    (
        "Acelerômetro MPU2",
        ("mpu2_ax_g", "mpu2_ay_g", "mpu2_az_g"),
        "Leitura bruta do acelerômetro [g]",
        "MPU2 — aceleração",
    ),
    (
        "Giroscópio MPU2",
        ("mpu2_gx_dps", "mpu2_gy_dps", "mpu2_gz_dps"),
        "Velocidade angular [graus/s]",
        "MPU2 — velocidade angular",
    ),
    (
        "Coordenadas GPS",
        ("gps_lat_deg", "gps_lon_deg"),
        "Latitude/longitude [graus]",
        "GPS — coordenadas",
    ),
    (
        "Altitude GPS",
        ("gps_alt_m",),
        "Altitude [m]",
        "GPS — altitude",
    ),
    (
        "Satélites GPS",
        ("gps_sat",),
        "Contagem [n]",
        "GPS — satélites",
    ),
)


LINE_LABELS = {
    "bmp1_rel_alt_m": "BMP1",
    "bmp2_rel_alt_m": "BMP2",
    "gps_alt_m": "GPS altitude",
    "mpu1_ax_g": "ax",
    "mpu1_ay_g": "ay",
    "mpu1_az_g": "az",
    "mpu1_gx_dps": "gx",
    "mpu1_gy_dps": "gy",
    "mpu1_gz_dps": "gz",
    "mpu2_ax_g": "ax",
    "mpu2_ay_g": "ay",
    "mpu2_az_g": "az",
    "mpu2_gx_dps": "gx",
    "mpu2_gy_dps": "gy",
    "mpu2_gz_dps": "gz",
    "gps_lat_deg": "latitude",
    "gps_lon_deg": "longitude",
    "gps_alt_m": "altitude",
    "gps_sat": "satélites",
}


def find_csv_header(log_path: Path) -> int:
    """Return the zero-based line number of the telemetry CSV header."""
    return find_csv_header_line(log_path, header_channel="time_ms") - 1


def load_telemetry(log_path: Path) -> pd.DataFrame:
    """Load the CSV portion of the raw log without dropping or reordering rows."""
    parsed = parse_telemetry_log(
        log_path,
        header_channel="time_ms",
        timestamp_channel="time_ms",
    )
    data = parsed.to_wide_frame()
    data["record_index"] = [record["record_index"] for record in parsed.records]
    data["source_line_number"] = [record["source_line_number"] for record in parsed.records]
    if "time_ms" not in data.columns:
        raise ValueError("A coluna obrigatória 'time_ms' não foi encontrada.")

    if data.empty:
        raise ValueError(f"Nenhuma amostra numérica encontrada em: {log_path}")

    timebase = segment_timebase(parsed, timestamp_channel="time_ms", seconds_per_unit=0.001)
    data["segment"] = timebase["segment_id"].to_numpy()

    return data


def _segments(data: pd.DataFrame) -> Iterable[tuple[int, pd.DataFrame]]:
    """Yield each contiguous clock segment without joining reset boundaries."""
    for segment_id, segment_data in data.groupby("segment", sort=True):
        yield int(segment_id), segment_data


def plot_group(
    ax: plt.Axes,
    data: pd.DataFrame,
    columns: tuple[str, ...],
    ylabel: str,
) -> None:
    """Plot one group of signals, preserving NaNs and counter resets."""

    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    any_valid_data = False
    boundary_marker_drawn = False

    for column_index, column in enumerate(columns):
        if column not in data:
            continue

        color = colors[column_index % len(colors)]
        label = LINE_LABELS.get(column, column)
        column_has_data = False

        for _, segment_data in _segments(data):
            values = segment_data[column]
            if not values.notna().any():
                continue

            ax.plot(
                segment_data["record_index"],
                values,
                color=color,
                linewidth=0.8,
                label=label if not column_has_data else "_nolegend_",
            )
            column_has_data = True
            any_valid_data = True

        if not column_has_data:
            # The line is intentionally absent: this makes a completely
            # unavailable signal explicit instead of suggesting zero values.
            continue

    boundaries = data.loc[data["segment"].diff().fillna(0).gt(0), "record_index"]
    for boundary in boundaries:
        ax.axvline(
            boundary,
            color="0.45",
            linestyle="--",
            linewidth=0.7,
            alpha=0.7,
            label="salto para trás no relógio" if not boundary_marker_drawn else "_nolegend_",
        )
        boundary_marker_drawn = True

    if not any_valid_data:
        ax.text(
            0.5,
            0.5,
            "Sem dados válidos no log",
            ha="center",
            va="center",
            transform=ax.transAxes,
            color="0.35",
        )

    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.25)
    ax.margins(x=0.01)

    handles, labels = ax.get_legend_handles_labels()
    if handles:
        ax.legend(loc="best", fontsize=8, ncol=min(4, len(handles)))


def make_figure(data: pd.DataFrame, *, overview: bool = False) -> plt.Figure:
    """Build the overview or detailed figure."""

    if overview:
        rows = (len(GROUPS) + 1) // 2
        figure, axes = plt.subplots(rows, 2, figsize=(16, rows * 3.7), sharex=True)
        axes_flat = axes.ravel()
        figure.suptitle("Neblina — telemetria bruta completa", fontsize=16)
    else:
        figure, axis = plt.subplots(figsize=(14, 7.5))
        axes_flat = [axis]

    for axis, group in zip(axes_flat, GROUPS):
        _, columns, ylabel, title = group
        plot_group(axis, data, columns, ylabel)
        axis.set_title(title)

    if overview:
        for axis in axes_flat[len(GROUPS):]:
            axis.set_visible(False)

    if overview:
        for axis in axes_flat:
            axis.set_xlabel("Índice da amostra (ordem de aquisição)")
        figure.tight_layout(rect=(0, 0, 1, 0.96))
    else:
        axes_flat[0].set_xlabel("Índice da amostra (ordem de aquisição)")
        figure.tight_layout()

    return figure


def write_plots(
    data: pd.DataFrame,
    output_path: Path,
    *,
    source_path: Path,
    repo_root: Path | None = None,
) -> Path:
    """Write new plot artifacts while guarding the immutable raw source."""

    repo_root = Path(repo_root or PROJECT_ROOT).resolve()
    results_root = repo_root / "results"
    if results_root.is_symlink():
        raise ValueError("Plot results directory must not be a symlink")
    output_path = Path(output_path)
    if not output_path.is_absolute():
        output_path = repo_root / output_path
    output_path = output_path.resolve()
    resolved_results = results_root.resolve()
    if output_path == resolved_results or not output_path.is_relative_to(resolved_results):
        raise ValueError("Plot artifacts must be written beneath the repository results/ directory")
    source_path = Path(source_path)
    if output_path.resolve() == source_path.resolve():
        raise ValueError("Plot output cannot be the raw source")
    overview_path = output_path.with_name(f"{output_path.stem}_overview.png")
    if overview_path.resolve() == source_path.resolve():
        raise ValueError("Plot overview cannot be the raw source")
    if output_path.exists() or overview_path.exists():
        raise FileExistsError("Plot artifact already exists; choose a new output path")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with PdfPages(output_path) as pdf:
        overview_figure = make_figure(data, overview=True)
        overview_figure.savefig(overview_path, dpi=160)
        pdf.savefig(overview_figure)
        plt.close(overview_figure)

        for group in GROUPS:
            figure = make_figure_for_group(data, group)
            pdf.savefig(figure)
            plt.close(figure)

    return overview_path


def make_figure_for_group(
    data: pd.DataFrame,
    group: tuple[str, tuple[str, ...], str, str],
) -> plt.Figure:
    """Build one detailed PDF page for a sensor group."""

    group_name, columns, ylabel, title = group
    figure, axis = plt.subplots(figsize=(14, 7.5))
    plot_group(axis, data, columns, ylabel)
    axis.set_title(f"Neblina — {title}")
    axis.set_xlabel("Índice da amostra (ordem de aquisição)")
    figure.tight_layout()
    figure.canvas.manager.set_window_title(group_name)
    return figure


def parse_args() -> argparse.Namespace:
    """Parse the optional raw-log and PDF destination paths."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--log",
        type=Path,
        default=DEFAULT_LOG,
        help="caminho do log bruto (padrão: log do Neblina)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="PDF de saída (padrão: novo diretório em results/neblina_1/)",
    )
    return parser.parse_args()


def main() -> None:
    """Load the raw log, preserve its segments, and write new plots."""
    args = parse_args()
    data = load_telemetry(args.log)
    output = args.output or (
        DEFAULT_RESULTS
        / f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')}_raw_telemetry_plots"
        / "neblina_flight_data.pdf"
    )
    overview_path = write_plots(data, output, source_path=args.log)

    reset_count = int(data["segment"].max())
    print(f"Amostras plotadas: {len(data)}")
    print(f"Colunas plotadas: {len(data.columns) - 3}")
    print(f"Saltos para trás do contador time_ms: {reset_count}")
    print(f"PDF: {output}")
    print(f"PNG geral: {overview_path}")


if __name__ == "__main__":
    main()
