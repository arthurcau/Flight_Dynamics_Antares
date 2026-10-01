"""Publish auditable observed-flight products from one verified telemetry audit."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from antares_fd.analysis.provenance import get_git_provenance
from antares_fd.simulation.uq_storage import write_json_atomic, write_parquet_atomic
from antares_fd.telemetry.artifacts import verify_artifact_set

from .observations import build_observed_section


PROCESSING_VERSION = "1.1"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _plot_altitude(frame: pd.DataFrame, events: dict, output: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figure, ax = plt.subplots(figsize=(10, 5))
    for name in ("bmp1_rel_alt_m", "bmp2_rel_alt_m"):
        ax.plot(frame["section_elapsed_s"], frame[name], label=name, linewidth=1.3)
    peak = events["recorded_relative_altitude_peak"]
    if peak["status"] == "DIRECTLY_RECORDED_EXTREMUM":
        ax.axvline(
            peak["section_elapsed_s"], color="orange", linestyle="--", alpha=0.8,
            label="recorded relative-altitude extremum",
        )
    ax.set(xlabel="Time since first marked sample [s]", ylabel="Onboard relative altitude [m]",
           title="Recorded altitude in the marked flight section")
    ax.grid(alpha=0.25)
    ax.legend()
    figure.tight_layout()
    figure.savefig(output, dpi=150)
    plt.close(figure)


def process_audit_section(
    audit_dir: Path,
    *,
    repo_root: Path,
    section_marker: str,
    output_dir: Path | None = None,
) -> Path:
    """Produce a new, separate result directory without altering source evidence."""

    audit_dir = Path(audit_dir).resolve()
    repo_root = Path(repo_root).resolve()
    audit_manifest = verify_artifact_set(audit_dir)
    source = Path(audit_manifest["source_file"])
    if not source.is_absolute():
        source = repo_root / source
    source = source.resolve()
    if not source.is_file() or _sha256(source) != audit_manifest["source_sha256"]:
        raise ValueError("Raw telemetry source is missing or differs from the verified audit")

    samples = pd.read_parquet(audit_dir / "telemetry_samples.parquet")
    segments = pd.read_parquet(audit_dir / "telemetry_segments.parquet")
    diagnostics = pd.read_parquet(audit_dir / "timebase_diagnostics.parquet")
    inventory = json.loads((audit_dir / "telemetry_inventory.json").read_text(encoding="utf-8"))
    frame, events, summary = build_observed_section(
        samples, segments, section_marker=section_marker,
        timebase_diagnostics=diagnostics,
        duplicate_blocks=inventory.get("exact_duplicate_blocks", []),
    )
    if output_dir is None:
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ_observed_reconstruction")
        output_dir = repo_root / "results" / "neblina_1" / run_id
    else:
        output_dir = Path(output_dir)
        if not output_dir.is_absolute():
            output_dir = repo_root / output_dir
    output_dir = output_dir.resolve()
    if not output_dir.is_relative_to(repo_root / "results"):
        raise ValueError("Reconstruction artifacts must be written below the repository results/ directory")
    if output_dir.exists():
        raise FileExistsError(f"Refusing to overwrite reconstruction output: {output_dir}")
    if source.is_relative_to(output_dir):
        raise ValueError("Reconstruction output may not contain the raw source")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.", suffix=".staging", dir=output_dir.parent))
    try:
        summary.update({
            "dataset_id": audit_manifest["dataset_id"],
            "source_sha256": audit_manifest["source_sha256"],
            "audit_manifest_sha256": _sha256(audit_dir / "telemetry_manifest.json"),
            "time_alignment": "SEGMENT_LOCAL_ONLY",
            "filtering": "NONE",
            "calibration": "NONE_APPLIED",
            "pressure_altitude_status": "NOT_APPLICABLE_NO_RAW_PRESSURE",
            "cd_identification_status": "INSUFFICIENT_OBSERVABILITY",
            "exact_duplicate_blocks": [
                block for block in inventory.get("exact_duplicate_blocks", [])
                if block.get("section_marker") == section_marker
                and block.get("duplicate_start_record_index") == summary["first_record_index"]
                and block.get("duplicate_end_record_index") == summary["last_record_index"]
            ],
        })
        write_parquet_atomic(frame, stage / "observed_section.parquet")
        write_json_atomic(events, stage / "observed_events.json")
        write_json_atomic(summary, stage / "observed_summary.json")
        _plot_altitude(frame, events, stage / "relative_altitude.png")
        files = ("observed_section.parquet", "observed_events.json", "observed_summary.json", "relative_altitude.png")
        manifest = {
            "schema_version": "1.0",
            "processing_version": PROCESSING_VERSION,
            "methodology_version": "observed_section_1.1",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "source_sha256": audit_manifest["source_sha256"],
            "audit_manifest_sha256": _sha256(audit_dir / "telemetry_manifest.json"),
            "input_artifacts": {name: audit_manifest["artifacts"][name]["sha256"] for name in ("telemetry_samples.parquet", "telemetry_segments.parquet")},
            "software": {"python": platform.python_version(), "pandas": pd.__version__},
            "git": get_git_provenance(repo_root),
            "artifacts": {name: {"sha256": _sha256(stage / name), "size_bytes": (stage / name).stat().st_size} for name in files},
        }
        write_json_atomic(manifest, stage / "reconstruction_manifest.json")
        if _sha256(source) != audit_manifest["source_sha256"]:
            raise ValueError("Raw telemetry changed during reconstruction")
        os.replace(stage, output_dir)
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return output_dir
