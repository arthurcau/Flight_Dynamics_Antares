"""Dataset configuration, artifact writing, verification, and human report."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from antares_fd.analysis.provenance import get_git_provenance
from antares_fd.storage import write_json_atomic, write_parquet_atomic

from .audit import audit_dataset
from .loader import parse_telemetry_log


PARQUET_ARTIFACTS = (
    "telemetry_samples.parquet",
    "channel_statistics.parquet",
    "timebase_diagnostics.parquet",
    "telemetry_segments.parquet",
    "sensor_quality_flags.parquet",
)
JSON_ARTIFACTS = ("telemetry_inventory.json", "sensor_calibration_manifest.json")
REPORT_NAME = "telemetry_quality_report.md"
MANIFEST_NAME = "telemetry_manifest.json"


class TelemetryArtifactError(RuntimeError):
    """Raised when generated telemetry artifacts fail integrity validation."""


def _sha256(path: Path) -> str:
    """Calcule SHA-256 de um artefato de telemetria sem modificá-lo.

    Lê blocos binários e retorna o digest hexadecimal para verificação
    de integridade e vinculação ao registro bruto.
    """
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_metadata(metadata_path: Path) -> dict[str, Any]:
    """Carregue e valide os metadados YAML da auditoria de telemetria.

    Lê metadata_path, exige o contrato esperado e retorna o mapeamento.
    Campos de calibração ausentes não são preenchidos com estimativas.
    """
    try:
        with metadata_path.open("r", encoding="utf-8") as stream:
            metadata = yaml.safe_load(stream)
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise ValueError(f"Cannot read telemetry metadata {metadata_path}: {exc}") from exc
    if not isinstance(metadata, dict):
        raise ValueError(f"Telemetry metadata must be a YAML mapping: {metadata_path}")
    raw = metadata.get("raw_data")
    if not isinstance(raw, dict) or not raw.get("path"):
        raise ValueError("Telemetry metadata must declare raw_data.path")
    required_top = ("dataset_id", "header_channel", "timestamp_channel", "channels")
    missing_top = [key for key in required_top if key not in metadata]
    if missing_top:
        raise ValueError(f"Telemetry metadata is missing required fields: {missing_top}")
    entries = metadata["channels"]
    if not isinstance(entries, list) or not entries:
        raise ValueError("Telemetry metadata channels must be a non-empty list")
    required_channel_fields = (
        "canonical_name",
        "raw_channel_name",
        "unit",
        "unit_status",
        "unit_source",
        "source_sensor",
        "sensor_class",
        "sensor_axis",
        "coordinate_frame",
        "data_type",
        "data_origin",
        "calibration_status",
        "conversion_applied",
        "is_timestamp_channel",
    )
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ValueError(f"Telemetry channel metadata at index {index} must be a mapping")
        missing = [key for key in required_channel_fields if key not in entry]
        if missing:
            raise ValueError(f"Telemetry channel metadata at index {index} is missing fields: {missing}")
        if entry["data_origin"] not in {"MEASURED", "DERIVED", "INFERRED"}:
            raise ValueError(f"Unsupported data_origin for {entry.get('raw_channel_name')}: {entry['data_origin']}")
        if entry["unit_status"] not in {"HEADER_LABEL", "DOCUMENTED", "UNIT_ASSUMED", "UNKNOWN"}:
            raise ValueError(f"Unsupported unit_status for {entry.get('raw_channel_name')}: {entry['unit_status']}")
        if entry["unit"] is None and entry["unit_status"] != "UNKNOWN":
            raise ValueError(f"Channel {entry['raw_channel_name']} has no unit but is not marked UNKNOWN")
        if entry["unit"] is not None and entry["unit_status"] == "UNKNOWN":
            raise ValueError(f"Channel {entry['raw_channel_name']} declares a unit while unit_status is UNKNOWN")
    raw_names = [entry["raw_channel_name"] for entry in entries]
    canonical_names = [entry["canonical_name"] for entry in entries]
    if len(set(raw_names)) != len(raw_names) or len(set(canonical_names)) != len(canonical_names):
        raise ValueError("Telemetry channel raw and canonical names must be unique")
    return metadata


def _write_text_atomic(text: str, path: Path) -> None:
    """Publique um documento de texto sem expor gravação parcial.

    Escreve UTF-8 em arquivo temporário no diretório de destino e usa
    substituição atômica. Em falha, remove o temporário e propaga o erro.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def _calibration_manifest(
    metadata: dict[str, Any], *, source_sha256: str, metadata_sha256: str
) -> dict[str, Any]:
    """Record the calibration knowledge boundary without assuming constants."""

    sensors: dict[str, dict[str, Any]] = {}
    for entry in metadata["channels"]:
        sensor_name = entry["source_sensor"]
        sensor = sensors.setdefault(
            sensor_name,
            {
                "source_sensor": sensor_name,
                "model": "UNKNOWN",
                "confidence": "HEADER_ONLY",
                "evidence": ["source_header", "dataset_metadata"],
                "channels": [],
            },
        )
        sensor["channels"].append(
            {
                "canonical_name": entry["canonical_name"],
                "raw_channel_name": entry["raw_channel_name"],
                "sensor_class": entry["sensor_class"],
                "sensor_axis": entry["sensor_axis"],
                "unit": entry["unit"],
                "unit_status": entry["unit_status"],
                "scale": "UNKNOWN",
                "offset": "UNKNOWN",
                "range": "UNKNOWN",
                "coordinate_frame": entry["coordinate_frame"],
                "calibration_status": entry["calibration_status"],
                "source_evidence": entry["unit_source"],
            }
        )
    return {
        "schema_version": "1.0",
        "dataset_id": metadata["dataset_id"],
        "source_sha256": source_sha256,
        "metadata_sha256": metadata_sha256,
        "status": "BLOCKED_BY_MISSING_METADATA",
        "unknown_fields_policy": "UNKNOWN means no sensor-specific evidence is declared; no calibration is applied",
        "sensors": list(sensors.values()),
    }


def _markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    """Formate cabeçalhos e linhas em uma tabela Markdown.

    Converte as células com o formatador local e inclui a linha separadora.
    Retorna texto para o relatório sem alterar os dados canônicos.
    """
    def cell(value: Any) -> str:
        """Escape uma célula para não quebrar a estrutura Markdown.

        Converte value em texto e neutraliza separadores e quebras de linha.
        O retorno é usado somente na apresentação do relatório.
        """
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return "—"
        return str(value).replace("|", "\\|").replace("\n", " ")

    output = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    output.extend("| " + " | ".join(cell(value) for value in row) + " |" for row in rows)
    return "\n".join(output)


def _render_report(output_dir: Path) -> str:
    """Render Markdown only from the canonical JSON and Parquet artifacts."""

    inventory = json.loads((output_dir / "telemetry_inventory.json").read_text(encoding="utf-8"))
    stats = pd.read_parquet(output_dir / "channel_statistics.parquet")
    timebase = pd.read_parquet(output_dir / "timebase_diagnostics.parquet")
    flags = pd.read_parquet(output_dir / "sensor_quality_flags.parquet")
    tb = inventory["timebase"]
    gps = inventory["gps"]
    gps_window = (
        f"{gps['first_in_range_coordinate_pair_timestamp']}–{gps['last_in_range_coordinate_pair_timestamp']} {gps['timestamp_unit']}"
        if gps.get("in_range_coordinate_pair_count", 0)
        else "none recorded"
    )
    effective_hz = tb["effective_sample_frequency_hz"]
    median_hz = tb["median_interval_frequency_hz"]
    frequency_text = (
        f"effective {effective_hz:.6g} Hz; median-interval {median_hz:.6g} Hz"
        if effective_hz is not None and median_hz is not None
        else "not computed because the timestamp unit is unknown or unsupported"
    )
    seconds_per_unit = tb["seconds_per_timestamp_unit"]
    clock_scale = f"1 {tb['time_unit']} = {seconds_per_unit:g} s" if seconds_per_unit is not None else "unavailable"
    issue_counts = inventory["parse_issue_counts"]
    records = [
        [
            row["canonical_channel_name"],
            row["sensor_class"],
            row["data_origin"],
            row["unit"] if row["unit"] is not None else "UNIT_UNKNOWN",
            row["unit_status"],
            row["coordinate_frame"],
            row["valid_count"],
            row["missing_count"],
            f"{row['missing_fraction']:.3%}",
            row["minimum"],
            row["maximum"],
        ]
        for row in stats.to_dict(orient="records")
    ]
    flag_counts = (
        flags.groupby("quality_flag", dropna=False).size().sort_values(ascending=False).to_dict()
        if not flags.empty
        else {}
    )
    interval_classes = timebase["interval_class"].value_counts().to_dict()
    sections = inventory.get("sections", [])
    section_lines = [f"- `{section['name']}`: {section['record_count']} records" for section in sections]
    if not section_lines:
        section_lines = ["- No section labels were declared in the dataset metadata."]
    duplicate_lines = [
        (
            f"- {block['record_count']} raw-token-identical rows: records "
            f"{block['duplicate_start_record_index']}–{block['duplicate_end_record_index']} "
            f"(source lines {block['duplicate_start_source_line_number']}–{block['duplicate_end_source_line_number']}) "
            f"repeat records {block['original_start_record_index']}–{block['original_end_record_index']} "
            f"(source lines {block['original_start_source_line_number']}–{block['original_end_source_line_number']}); "
            f"mechanism UNKNOWN."
        )
        for block in inventory.get("exact_duplicate_blocks", [])
    ]
    if not duplicate_lines:
        duplicate_lines = ["- No exact repeated marked section was detected."]
    file_rows = [
        [item["path"], item["role"], item["format"], item["size_bytes"], item["sha256"] or "—", item["status"]]
        for item in inventory.get("files", [])
    ]
    warnings = [f"- `{name}`: {count}" for name, count in sorted(flag_counts.items())]
    if not warnings:
        warnings = ["- No quality flags were triggered by the configured checks."]
    parse_lines = [f"- `{kind}`: {count}" for kind, count in sorted(issue_counts.items())]
    if not parse_lines:
        parse_lines = ["- No parser issues."]
    absent = inventory.get("channel_families_not_represented", [])
    absent_text = ", ".join(f"`{value}`" for value in absent) if absent else "None identified from the channel metadata."

    lines = [
        f"# Telemetry quality report: {inventory['dataset_id']}",
        "",
        "> This is a data-integrity audit. It does not reconstruct flight events or interpret flight dynamics.",
        "",
        "## Dataset",
        "",
        f"- Source: `{inventory['source_file']}`",
        f"- SHA-256: `{inventory['source_sha256']}`",
        f"- Size: {inventory['source_size_bytes']} bytes",
        f"- CSV header: line {inventory['header_line_number']}; {len(inventory['header_channels'])} channels",
        f"- Parsed records: {inventory['record_count']}; parser issues: {inventory['parse_issue_count']}",
        "",
        "## Files and source sections",
        "",
        _markdown_table(["File", "Role", "Format", "Bytes", "SHA-256", "Status"], file_rows),
        "",
        *section_lines,
        "",
        "Parser issues are retained in `telemetry_inventory.json`; they are not included as sample rows:",
        *parse_lines,
        "",
        "Exact duplicate block evidence (all records are retained):",
        *duplicate_lines,
        "",
        "## Channels",
        "",
        _markdown_table(
            ["Channel", "Class", "Origin", "Unit", "Unit status", "Frame", "Valid", "Missing", "Missing fraction", "Minimum", "Maximum"],
            records,
        ),
        "",
        f"Channel families not represented in this file: {absent_text}",
        "",
        "Units come from the source header or project metadata and are not independently calibrated here. Values were not converted.",
        "MEASURED / DERIVED / INFERRED origins, calibration state, source sensor, and axis details are preserved in the machine-readable channel metadata.",
        "Sensor calibration, mounting orientation, and undocumented reference frames remain unknown.",
        "",
        "## Timebase",
        "",
        f"- First/last file-order timestamps: {tb['initial_timestamp']} / {tb['final_timestamp']} {tb['time_unit']}",
        f"- Minimum/maximum timestamp: {tb['minimum_timestamp']} / {tb['maximum_timestamp']} {tb['time_unit']}",
        f"- Timestamp unit: {tb['time_unit']} ({tb['time_unit_status']}); SI scale for frequency: {clock_scale}.",
        f"- Modal interval: {tb['nominal_interval']} {tb['time_unit']}; median positive interval: {tb['median_positive_interval']} {tb['time_unit']}",
        f"- Sampling frequency: {frequency_text}",
        f"- Backward clock jumps (mechanism unknown): {tb['timestamp_backward_jump_count']}; duplicate adjacent timestamps: {tb['duplicate_timestamp_count']}; possible gaps: {tb['gap_count']}",
        f"- File-order clock segments: {tb['segment_count']}; global corrected time: {tb['global_corrected_time_status']}.",
        f"- Gap rule: {tb['gap_detection_rule']}; threshold: {tb['gap_threshold']} {tb['time_unit']}; estimated missing slots: {tb['estimated_missing_samples_across_gaps']}; aggregate excess duration: {tb['total_gap_duration_excess_over_nominal']} {tb['time_unit']}.",
        f"- Interval classifications: {json.dumps(interval_classes, sort_keys=True)}",
        "",
        "Gap detection uses the modal positive interval across this stream. Multiple cadence regimes can make this heuristic over- or under-inclusive; timestamps were not corrected.",
        "",
        "## Sensor status",
        "",
        f"- GPS: **{gps['status']}**; in-range latitude/longitude pairs: {gps['in_range_coordinate_pair_count']} of {gps['record_count']} records; fix quality {gps['fix_quality_status']}.",
        f"- GPS in-range coordinate timestamp window: {gps_window}; contiguous intervals: {len(gps.get('coordinate_pair_intervals', []))}; transitions: {gps.get('coordinate_pair_transition_count', 0)}.",
        "- GPS channels and timestamps are retained even where coordinate values are missing.",
        "- Sensor classes and axes reflect the source header and metadata only; no sensor orientation or calibration is inferred.",
        "",
        "## Quality warnings",
        "",
        *warnings,
        "",
        "`POSSIBLE_SATURATION`, `STUCK_CHANNEL`, and `LARGE_DISCONTINUITY` are signal-shape diagnostics. They do not establish a sensor fault or a physically invalid value.",
        "",
        "## Known limitations",
        "",
        "- Channel values and timestamps were not converted, filtered, interpolated, synchronized, or corrected. Intervals remain in the declared source time unit; frequency is computed only when that unit has a supported SI scale.",
        "- No sensor datasheets, calibration records, mounting transforms, GPS fix-quality fields, or clock synchronization model were present in the declared metadata.",
        "- No static/pre-flight bias window was identified; the source section marker was preserved without assigning a flight phase.",
        "- The two BMP-labeled channels contain relative-altitude values; raw pressure samples are not present in this file.",
        "- Parse issue lines remain traceable by original source line and are not interpreted as samples.",
        "",
        "## Next steps",
        "",
        "Phase 2 — Sensor Calibration, Time Alignment and Flight Event Reconstruction.",
        "",
    ]
    return "\n".join(lines)


def verify_artifact_set(output_dir: Path) -> dict[str, Any]:
    """Verify manifest checksums, Parquet readability, columns, and row counts."""

    output_dir = Path(output_dir)
    manifest_path = output_dir / MANIFEST_NAME
    if not manifest_path.is_file():
        raise TelemetryArtifactError(f"Telemetry artifact manifest is missing: {manifest_path}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TelemetryArtifactError(f"Telemetry artifact manifest is unreadable: {exc}") from exc
    for name, expected in manifest.get("artifacts", {}).items():
        path = output_dir / name
        if not path.is_file():
            raise TelemetryArtifactError(f"Declared telemetry artifact is missing: {path}")
        actual_hash = _sha256(path)
        if actual_hash != expected["sha256"]:
            raise TelemetryArtifactError(f"Checksum mismatch for telemetry artifact {path.name}")
        if path.stat().st_size != expected["size_bytes"]:
            raise TelemetryArtifactError(f"Size mismatch for telemetry artifact {path.name}")
        if path.suffix == ".parquet":
            try:
                frame = pd.read_parquet(path)
            except Exception as exc:
                raise TelemetryArtifactError(f"Corrupt or unreadable Parquet artifact {path.name}: {exc}") from exc
            if list(frame.columns) != expected["columns"] or len(frame) != expected["row_count"]:
                raise TelemetryArtifactError(f"Schema or row-count mismatch for telemetry artifact {path.name}")
        elif path.suffix == ".json":
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise TelemetryArtifactError(f"Corrupt JSON artifact {path.name}: {exc}") from exc
    expected_names = set(PARQUET_ARTIFACTS) | set(JSON_ARTIFACTS) | {REPORT_NAME}
    if set(manifest.get("artifacts", {})) != expected_names:
        raise TelemetryArtifactError("Telemetry manifest artifact list is incomplete or unexpected")
    return manifest


def audit_project(
    project_dir: Path,
    *,
    repo_root: Path,
    metadata_path: Path | None = None,
    source_path: Path | None = None,
    output_dir: Path | None = None,
) -> Path:
    """Run a configured audit and atomically publish its complete artifact set."""

    project_dir = Path(project_dir).resolve()
    repo_root = Path(repo_root).resolve()
    metadata_path = Path(metadata_path or project_dir / "telemetry" / "metadata" / "dataset.yaml").resolve()
    metadata_hash = _sha256(metadata_path)
    metadata = _load_metadata(metadata_path)
    if _sha256(metadata_path) != metadata_hash:
        raise TelemetryArtifactError("Telemetry metadata changed while being read")
    source = Path(source_path or (repo_root / metadata["raw_data"]["path"])).resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Declared telemetry source is unavailable: {source}")
    raw_source_file = source.relative_to(repo_root).as_posix() if source.is_relative_to(repo_root) else str(source)
    parsed = parse_telemetry_log(
        source,
        header_channel=metadata["header_channel"],
        timestamp_channel=metadata["timestamp_channel"],
        expected_channels=[entry["raw_channel_name"] for entry in metadata["channels"]],
        encoding=metadata.get("raw_data", {}).get("encoding", "utf-8"),
        delimiter=metadata.get("raw_data", {}).get("delimiter", ","),
        missing_tokens=tuple(metadata.get("raw_data", {}).get("missing_tokens", ["", "nan", "NaN", "NAN"])),
        section_markers=tuple(metadata.get("section_markers", [])),
    )
    audited = audit_dataset(
        parsed,
        dataset_id=metadata["dataset_id"],
        channel_metadata=metadata["channels"],
        raw_source_file=raw_source_file,
        gap_factor=float(metadata.get("gap_factor", 1.5)),
    )

    inventory = audited["inventory"]
    sections: dict[str, int] = {}
    for record in parsed.records:
        section = record["section_marker"] or "BEFORE_DECLARED_SECTION_MARKER"
        sections[section] = sections.get(section, 0) + 1
    inventory["sections"] = [
        {"name": name, "record_count": count}
        for name, count in sections.items()
    ]
    represented = {entry["sensor_class"] for entry in metadata["channels"]}
    candidate_families = ["magnetometer", "temperature", "raw_pressure", "battery/system_voltage", "event/deployment", "GPS_fix_quality"]
    inventory["channel_families_not_represented"] = [name for name in candidate_families if name not in represented]
    raw_data = metadata["raw_data"]
    inventory["files"] = [
        {
            "path": raw_source_file,
            "role": "raw_telemetry",
            "format": raw_data.get("format", source.suffix.lstrip(".").lower()),
            "size_bytes": parsed.source_size_bytes,
            "sha256": parsed.source_sha256,
            "record_count": len(parsed.records),
            "record_count_status": "PARSED",
            "encoding": parsed.encoding,
            "delimiter": parsed.delimiter,
            "header_line_number": parsed.header_line_number,
            "channels": list(parsed.channels),
            "time_representation": raw_data.get("time_representation", "not documented"),
            "status": "PRESENT",
        }
    ]
    related_files: list[dict[str, Any]] = []
    for declared in metadata.get("related_files", []):
        related_path = Path(declared["path"])
        if not related_path.is_absolute():
            related_path = (repo_root / related_path).resolve()
        exists = related_path.is_file()
        if not exists and declared.get("required", False):
            raise FileNotFoundError(f"Required related telemetry file is unavailable: {related_path}")
        file_record = {
            "path": related_path.relative_to(repo_root).as_posix() if related_path.is_relative_to(repo_root) else str(related_path),
            "role": declared["role"],
            "format": related_path.suffix.lstrip(".").lower() or "unknown",
            "size_bytes": related_path.stat().st_size if exists else None,
            "sha256": _sha256(related_path) if exists else None,
            "record_count": None,
            "record_count_status": "NOT_APPLICABLE_NON_TELEMETRY_FILE",
            "status": "PRESENT" if exists else "DECLARED_BUT_ABSENT",
        }
        related_files.append(file_record)
        inventory["files"].append(file_record)

    if output_dir is None:
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ_telemetry_audit")
        output_dir = repo_root / "results" / project_dir.name / run_id
    else:
        output_dir = Path(output_dir)
        if not output_dir.is_absolute():
            output_dir = (repo_root / output_dir).resolve()
    output_dir = Path(output_dir).resolve()
    results_root = repo_root / "results"
    if (
        results_root.is_symlink()
        or output_dir == results_root.resolve()
        or not output_dir.is_relative_to(results_root.resolve())
    ):
        raise ValueError("Telemetry audit output must be a new directory beneath the repository's ignored results area")
    if output_dir.exists():
        raise FileExistsError(f"Refusing to overwrite existing telemetry audit output: {output_dir}")
    if source.is_relative_to(output_dir):
        raise ValueError("Telemetry audit output directory must not contain the raw source file")
    for name in (*PARQUET_ARTIFACTS, *JSON_ARTIFACTS, REPORT_NAME, MANIFEST_NAME):
        if (output_dir / name).resolve() == source:
            raise ValueError("Telemetry audit artifact path would overwrite the raw source file")

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    stage_dir = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.", suffix=".staging", dir=output_dir.parent))
    try:
        write_json_atomic(inventory, stage_dir / "telemetry_inventory.json")
        write_json_atomic(
            _calibration_manifest(
                metadata,
                source_sha256=parsed.source_sha256,
                metadata_sha256=metadata_hash,
            ),
            stage_dir / "sensor_calibration_manifest.json",
        )
        for filename, table_key in (
            ("telemetry_samples.parquet", "samples"),
            ("channel_statistics.parquet", "channel_statistics"),
            ("timebase_diagnostics.parquet", "timebase_diagnostics"),
            ("telemetry_segments.parquet", "segments"),
            ("sensor_quality_flags.parquet", "sensor_quality_flags"),
        ):
            write_parquet_atomic(audited[table_key], stage_dir / filename)

        # Read back every table before publishing; report content is derived from
        # these canonical files, not from the in-memory analysis object.
        for filename in PARQUET_ARTIFACTS:
            try:
                pd.read_parquet(stage_dir / filename)
            except Exception as exc:
                raise TelemetryArtifactError(f"Generated Parquet artifact failed read-back: {filename}: {exc}") from exc
        if _sha256(source) != parsed.source_sha256:
            raise TelemetryArtifactError("Raw telemetry checksum changed before artifact publication")
        if _sha256(metadata_path) != metadata_hash:
            raise TelemetryArtifactError("Telemetry metadata changed during audit")
        for file_record in related_files:
            if file_record["status"] == "PRESENT":
                related_path = repo_root / file_record["path"] if not Path(file_record["path"]).is_absolute() else Path(file_record["path"])
                if not related_path.is_file() or _sha256(related_path) != file_record["sha256"]:
                    raise TelemetryArtifactError(f"Related source artifact changed during audit: {file_record['path']}")
        _write_text_atomic(_render_report(stage_dir), stage_dir / REPORT_NAME)

        files = [*JSON_ARTIFACTS, *PARQUET_ARTIFACTS, REPORT_NAME]
        artifact_manifest: dict[str, dict[str, Any]] = {}
        for filename in files:
            artifact_path = stage_dir / filename
            details: dict[str, Any] = {"sha256": _sha256(artifact_path), "size_bytes": artifact_path.stat().st_size}
            if artifact_path.suffix == ".parquet":
                frame = pd.read_parquet(artifact_path)
                details["columns"] = list(frame.columns)
                details["row_count"] = len(frame)
            artifact_manifest[filename] = details

        try:
            package_version = importlib.metadata.version("antares-fd")
        except importlib.metadata.PackageNotFoundError:
            package_version = "unknown"
        manifest = {
            "schema_version": "1.0",
            "audit_version": "1.1",
            "dataset_id": metadata["dataset_id"],
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "source_file": raw_source_file,
            "source_sha256": parsed.source_sha256,
            "source_size_bytes": parsed.source_size_bytes,
            "metadata_file": metadata_path.relative_to(repo_root).as_posix() if metadata_path.is_relative_to(repo_root) else str(metadata_path),
            "metadata_sha256": metadata_hash,
            "related_files": related_files,
            "software": {"package": "antares-fd", "version": package_version, "python": platform.python_version()},
            "git": get_git_provenance(repo_root),
            "artifacts": artifact_manifest,
        }
        write_json_atomic(manifest, stage_dir / MANIFEST_NAME)
        verify_artifact_set(stage_dir)
        os.replace(stage_dir, output_dir)
    except Exception:
        shutil.rmtree(stage_dir, ignore_errors=True)
        raise

    if _sha256(source) != parsed.source_sha256:
        raise TelemetryArtifactError("Raw telemetry checksum changed during audit publication")
    return output_dir
