"""Strict, non-mutating parsing for CSV telemetry logs with text preambles."""

from __future__ import annotations

import csv
import hashlib
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


class TelemetryParseError(ValueError):
    """Raised when a telemetry source cannot be parsed without guessing."""


@dataclass(frozen=True)
class ParsedTelemetry:
    """Parsed numeric samples plus source locations and explicit parse issues."""

    source_path: Path
    source_sha256: str
    source_size_bytes: int
    header_line_number: int
    channels: tuple[str, ...]
    records: tuple[dict[str, Any], ...]
    parse_issues: tuple[dict[str, Any], ...]
    encoding: str
    delimiter: str

    def to_wide_frame(self) -> pd.DataFrame:
        """Return numeric columns for display or analysis, retaining missing values."""

        return pd.DataFrame(
            [{name: record["values"][name]["numeric_value"] for name in self.channels} for record in self.records],
            columns=self.channels,
        )


def _sha256(path: Path) -> str:
    """Calcule a identidade binária SHA-256 do registro bruto de telemetria.

    Lê o arquivo em blocos sem normalizar linhas ou valores; retorna digest
    hexadecimal e propaga falhas de leitura para preservar rastreabilidade.
    """
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def find_csv_header_line(
    source_path: Path,
    *,
    header_channel: str,
    encoding: str = "utf-8",
    delimiter: str = ",",
) -> int:
    """Find a header whose first field exactly matches the configured channel."""

    source_path = Path(source_path)
    try:
        with source_path.open("r", encoding=encoding, errors="strict", newline="") as stream:
            for line_number, line in enumerate(stream, start=1):
                try:
                    fields = next(csv.reader([line], delimiter=delimiter, strict=True))
                except csv.Error:
                    continue
                if fields and fields[0].strip() == header_channel:
                    return line_number
    except (OSError, UnicodeError) as exc:
        raise TelemetryParseError(f"Cannot read telemetry source {source_path}: {exc}") from exc
    raise TelemetryParseError(f"CSV header beginning with {header_channel!r} not found in {source_path}")


def parse_telemetry_log(
    source_path: Path,
    *,
    header_channel: str,
    timestamp_channel: str,
    expected_channels: tuple[str, ...] | list[str] | None = None,
    encoding: str = "utf-8",
    delimiter: str = ",",
    missing_tokens: tuple[str, ...] = ("", "nan", "NaN", "NAN"),
    section_markers: tuple[str, ...] | list[str] = (),
) -> ParsedTelemetry:
    """Parse numeric CSV rows without editing the source or hiding bad rows.

    Lines with the wrong width, empty lines, and non-data text remain visible in
    ``parse_issues`` with their one-based source line number and original text.
    Numeric tokens are retained alongside their parsed floating-point form.
    """

    source_path = Path(source_path)
    if not source_path.is_file():
        raise TelemetryParseError(f"Telemetry source does not exist or is not a file: {source_path}")

    digest_before = _sha256(source_path)
    size_bytes = source_path.stat().st_size
    header_line = find_csv_header_line(
        source_path,
        header_channel=header_channel,
        encoding=encoding,
        delimiter=delimiter,
    )
    records: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    channels: list[str] = []
    marker_values = {marker.casefold(): marker for marker in section_markers}
    active_section: str | None = None

    try:
        with source_path.open("r", encoding=encoding, errors="strict", newline="") as stream:
            for line_number, raw_line in enumerate(stream, start=1):
                if line_number < header_line:
                    continue
                try:
                    fields = next(csv.reader([raw_line], delimiter=delimiter, strict=True))
                except csv.Error as exc:
                    issues.append({"source_line_number": line_number, "kind": "CSV_SYNTAX_ERROR", "raw_line": raw_line.rstrip("\r\n"), "detail": str(exc)})
                    continue

                if line_number == header_line:
                    channels = [field.strip() for field in fields]
                    if len(set(channels)) != len(channels):
                        raise TelemetryParseError(f"Duplicate channel names in header at line {line_number}")
                    if timestamp_channel not in channels:
                        raise TelemetryParseError(f"Required timestamp channel {timestamp_channel!r} is absent from the header")
                    if expected_channels is not None and tuple(channels) != tuple(expected_channels):
                        raise TelemetryParseError(
                            "Telemetry header does not match the declared schema: "
                            f"expected {list(expected_channels)!r}, found {channels!r}"
                        )
                    continue

                stripped = raw_line.strip()
                marker = marker_values.get(stripped.casefold())
                if marker is not None:
                    active_section = marker
                    issues.append({"source_line_number": line_number, "kind": "SECTION_MARKER", "raw_line": stripped, "detail": marker})
                    continue
                if not stripped:
                    issues.append({"source_line_number": line_number, "kind": "EMPTY_LINE", "raw_line": "", "detail": "Blank line outside a telemetry sample"})
                    continue
                if len(fields) != len(channels):
                    issues.append({"source_line_number": line_number, "kind": "ROW_WIDTH_MISMATCH", "raw_line": raw_line.rstrip("\r\n"), "detail": f"Expected {len(channels)} fields; found {len(fields)}"})
                    continue

                values: dict[str, dict[str, Any]] = {}
                for channel, raw_value in zip(channels, fields, strict=True):
                    token = raw_value.strip()
                    if token in missing_tokens:
                        values[channel] = {"raw_value": raw_value, "numeric_value": None, "value_status": "MISSING"}
                        continue
                    try:
                        number = float(token)
                    except ValueError:
                        values[channel] = {"raw_value": raw_value, "numeric_value": None, "value_status": "NON_NUMERIC"}
                        issues.append({"source_line_number": line_number, "kind": "NON_NUMERIC_VALUE", "raw_line": raw_line.rstrip("\r\n"), "detail": f"{channel}={token!r}"})
                        continue
                    if not math.isfinite(number):
                        values[channel] = {"raw_value": raw_value, "numeric_value": None, "value_status": "NON_FINITE"}
                        issues.append({"source_line_number": line_number, "kind": "NON_FINITE_VALUE", "raw_line": raw_line.rstrip("\r\n"), "detail": f"{channel}={token!r}"})
                        continue
                    values[channel] = {"raw_value": raw_value, "numeric_value": number, "value_status": "VALID"}

                records.append(
                    {
                        "record_index": len(records),
                        "source_line_number": line_number,
                        "section_marker": active_section,
                        "values": values,
                    }
                )
    except (OSError, UnicodeError, csv.Error) as exc:
        raise TelemetryParseError(f"Failed while parsing telemetry source {source_path}: {exc}") from exc

    if not channels:
        raise TelemetryParseError(f"CSV header was not read from {source_path}")
    if not records:
        raise TelemetryParseError(f"No correctly shaped telemetry records found in {source_path}")

    digest_after = _sha256(source_path)
    if digest_after != digest_before:
        raise TelemetryParseError(f"Telemetry source changed while being read: {source_path}")

    return ParsedTelemetry(
        source_path=source_path.resolve(),
        source_sha256=digest_before,
        source_size_bytes=size_bytes,
        header_line_number=header_line,
        channels=tuple(channels),
        records=tuple(records),
        parse_issues=tuple(issues),
        encoding=encoding,
        delimiter=delimiter,
    )
