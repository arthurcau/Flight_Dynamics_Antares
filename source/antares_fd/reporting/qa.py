"""Automated PDF and artifact quality checks for engineering reports."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from typing import Any


EXPECTED_HEADINGS = (
    "Executive Summary", "Engineering Warnings", "Requirements & Compliance",
    "Model Provenance", "Model Validity", "Flight Kinematics", "Propulsion",
    "Max-Q", "Stability", "MAGI", "Recovery", "Monte Carlo",
    "Complete Metrics", "Data Dictionary",
)


def render_report_pages(pdf_path: Path, output_dir: Path, dpi: int = 180) -> list[Path]:
    """Render every PDF page for automated visual inspection."""
    pdf_path = Path(pdf_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    prefix = output_dir / "page"
    for old in output_dir.glob("page-*.png"):
        old.unlink(missing_ok=True)
    if shutil.which("pdftoppm"):
        command = [shutil.which("pdftoppm"), "-png", "-r", str(int(dpi)), str(pdf_path), str(prefix)]
    elif shutil.which("mutool"):
        command = [shutil.which("mutool"), "draw", "-r", str(int(dpi)), "-o", str(prefix) + "-%03d.png", str(pdf_path)]
    elif shutil.which("gswin64c"):
        command = [shutil.which("gswin64c"), "-dSAFER", "-dBATCH", "-dNOPAUSE", "-sDEVICE=pngalpha", f"-r{int(dpi)}", f"-sOutputFile={prefix}-%03d.png", str(pdf_path)]
    else:
        try:
            import fitz
        except ImportError:
            return []
        document = fitz.open(pdf_path)
        scale = float(dpi) / 72.0
        matrix = fitz.Matrix(scale, scale)
        pages = []
        for index, page in enumerate(document, start=1):
            target = output_dir / f"page-{index:03d}.png"
            page.get_pixmap(matrix=matrix, alpha=False).save(target)
            pages.append(target)
        return pages
    subprocess.run(command, check=True, capture_output=True)
    return sorted(output_dir.glob("page-*.png"))


def inspect_report(pdf_path: Path, figures_dir: Path | None = None, render_dir: Path | None = None) -> dict[str, Any]:
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
    figure_files = sorted(
        item for item in (Path(figures_dir).rglob("*") if figures_dir else [])
        if item.is_file() and item.resolve() != path.resolve()
    )
    def _portable(item: Path) -> str:
        try:
            return item.resolve().relative_to(Path(figures_dir).resolve()).as_posix()
        except (ValueError, TypeError):
            return item.name

    vector_figures = [_portable(item) for item in figure_files if item.is_file() and item.suffix.lower() == ".pdf"]
    vector_stems = {item.stem for item in figure_files if item.is_file() and item.suffix.lower() == ".pdf"}
    # PNG previews are acceptable only when the same figure has an
    # authoritative PDF sibling. A lone PNG is a rasterized engineering plot.
    normal_plot_pngs = [_portable(item) for item in figure_files if item.is_file() and item.suffix.lower() == ".png" and item.stem not in vector_stems]
    rendered_pages = render_report_pages(path, render_dir) if render_dir and path.exists() else []
    visual_qa_available = not render_dir or bool(rendered_pages)
    blank_pages: list[str] = []
    if rendered_pages:
        try:
            from PIL import Image, ImageStat
            for page in rendered_pages:
                image = Image.open(page).convert("L")
                stat = ImageStat.Stat(image)
                # A page with almost no contrast is an accidental blank page;
                # cover pages and intentional whitespace retain text/graphics.
                if stat.stddev[0] < 1.0:
                    blank_pages.append(str(page))
        except ImportError:
            pass
    return {
        "exists": path.exists(),
        "page_count": pages,
        "blank_pages": blank_pages,
        "missing_headings": missing_headings,
        "vector_figures": vector_figures,
        "raster_engineering_figures": normal_plot_pngs,
        "page_rasterization": "not available: install pdftoppm or Ghostscript" if not _has_rasterizer() else "available",
        "rendered_pages": len(rendered_pages),
        "visual_qa_complete": visual_qa_available,
        "passed": bool(path.exists() and pages > 0 and not missing_headings and not normal_plot_pngs and not blank_pages and visual_qa_available),
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
