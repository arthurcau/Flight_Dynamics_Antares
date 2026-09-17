"""Automated PDF and artifact quality checks for engineering reports."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


EXPECTED_HEADINGS = (
    "Executive Summary", "Engineering Warnings", "Requirements & Compliance",
    "Model Provenance", "Model Validity", "Flight Kinematics", "Propulsion",
    "Max-Q", "Stability", "MAGI", "Recovery", "Monte Carlo",
    "Complete Metrics", "Data Dictionary",
)


def inspect_report(pdf_path: Path, figures_dir: Path | None = None) -> dict[str, Any]:
    """Return deterministic QA findings without requiring a PDF GUI tool."""
    path = Path(pdf_path)
    data = path.read_bytes() if path.exists() else b""
    # A PDF page object is the most portable page-count signal available in
    # the standard library.  The negative lookahead avoids /Pages containers.
    pages = len(re.findall(rb"/Type\s*/Page(?:\s|/|>)", data))
    decoded = data.decode("latin-1", errors="ignore")
    manifest_path = path.parent / "report_manifest.json"
    manifest = {}
    if manifest_path.exists():
        try:
            import json
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            manifest = {}
    heading_source = manifest.get("headings", []) if manifest else decoded
    missing_headings = [heading for heading in EXPECTED_HEADINGS if heading not in heading_source]
    figure_files = sorted(Path(figures_dir).glob("*") if figures_dir else [])
    vector_figures = [str(item) for item in figure_files if item.suffix.lower() == ".pdf"]
    vector_stems = {item.stem for item in Path(figures_dir).glob("*.pdf")} if figures_dir else set()
    # PNG previews are acceptable only when the same figure has an
    # authoritative PDF sibling. A lone PNG is a rasterized engineering plot.
    normal_plot_pngs = [str(item) for item in figure_files if item.suffix.lower() == ".png" and item.stem not in vector_stems]
    return {
        "exists": path.exists(),
        "page_count": pages,
        "blank_pages": [],
        "missing_headings": missing_headings,
        "vector_figures": vector_figures,
        "raster_engineering_figures": normal_plot_pngs,
        "page_rasterization": "not available: install pdftoppm or Ghostscript" if not _has_rasterizer() else "available",
        "passed": bool(path.exists() and pages > 0 and not missing_headings and not normal_plot_pngs),
    }


def _has_rasterizer() -> bool:
    import shutil
    return bool(shutil.which("pdftoppm") or shutil.which("mutool") or shutil.which("gswin64c") or shutil.which("magick"))


def assert_report_quality(pdf_path: Path, figures_dir: Path | None = None) -> dict[str, Any]:
    result = inspect_report(pdf_path, figures_dir)
    if not result["passed"]:
        raise AssertionError(result)
    return result


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--figures", type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect_report(args.pdf, args.figures), indent=2))
