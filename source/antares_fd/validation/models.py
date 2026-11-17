"""Validated model-variant declarations; this module never changes physics inputs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml


ROLES = {"PREFLIGHT", "AS_FLOWN", "POSTFLIGHT", "CURRENT_REFERENCE"}
STATUSES = {
    "PREFLIGHT": {"COMPLETE", "PARTIALLY_RECONSTRUCTED_PREFLIGHT_MODEL"},
    "AS_FLOWN": {"COMPLETE", "BLOCKED_BY_MISSING_METADATA"},
    "POSTFLIGHT": {"COMPLETE", "NOT_YET_VALIDATED"},
    "CURRENT_REFERENCE": {"REFERENCE_ONLY"},
}
ORIGINS = {
    "MEASURED", "DERIVED", "INFERRED", "ASSUMED", "MODELED", "CALIBRATED",
    "POSTFLIGHT_IDENTIFIED",
}
CHANGE_FIELDS = {
    "parameter", "previous_value", "new_value", "reason", "evidence",
    "uncertainty", "effect_on_fit",
}


@dataclass(frozen=True)
class Evidence:
    claim: str
    origin: str
    source: str


@dataclass(frozen=True)
class ModelVariant:
    id: str
    role: str
    status: str
    runnable: bool
    configuration: str | None
    evidence: tuple[Evidence, ...]
    missing_evidence: tuple[str, ...]
    identified_changes: tuple[Mapping[str, Any], ...]


def _nonempty_text(value: Any, field: str) -> str:
    """Exija texto não vazio para identificar um campo de proveniência.

    Valida o tipo e remove espaços externos; retorna o texto normalizado.
    Ausência ou texto vazio gera ValueError com o nome field.
    """
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be nonempty text")
    return value.strip()


def parse_model_variants(document: Mapping[str, Any]) -> dict[str, ModelVariant]:
    """Validate provenance, status and separation before consumers use a model."""
    if not isinstance(document, Mapping) or document.get("schema_version") != 1:
        raise ValueError("model_variants schema_version must be 1")
    _nonempty_text(document.get("project"), "project")
    entries = document.get("variants")
    if not isinstance(entries, list) or not entries:
        raise ValueError("variants must be a nonempty list")

    variants: dict[str, ModelVariant] = {}
    roles_seen: set[str] = set()
    for entry in entries:
        if not isinstance(entry, Mapping):
            raise ValueError("Each variant must be a mapping")
        model_id = _nonempty_text(entry.get("id"), "variant id")
        if model_id in variants:
            raise ValueError(f"Duplicate variant id: {model_id}")
        role = _nonempty_text(entry.get("role"), f"{model_id}.role")
        if role not in ROLES:
            raise ValueError(f"{model_id}: unsupported role {role}")
        if role in roles_seen:
            raise ValueError(f"Duplicate variant role: {role}")
        roles_seen.add(role)
        status = _nonempty_text(entry.get("status"), f"{model_id}.status")
        if status not in STATUSES[role]:
            raise ValueError(f"{model_id}: status {status} is invalid for {role}")
        runnable = entry.get("runnable")
        if not isinstance(runnable, bool):
            raise ValueError(f"{model_id}.runnable must be boolean")
        if status in {"COMPLETE", "REFERENCE_ONLY"} and not runnable:
            raise ValueError(f"{model_id}: {status} requires runnable=true")
        configuration = entry.get("configuration")
        if configuration is not None:
            configuration = _nonempty_text(configuration, f"{model_id}.configuration")
        if runnable and (status not in {"COMPLETE", "REFERENCE_ONLY"} or not configuration):
            raise ValueError(f"{model_id}: runnable requires a complete or reference configuration")
        if not runnable and configuration is not None:
            raise ValueError(f"{model_id}: non-runnable variant cannot claim a configuration")

        raw_evidence = entry.get("evidence")
        if not isinstance(raw_evidence, list):
            raise ValueError(f"{model_id}.evidence must be a list")
        evidence = []
        for item in raw_evidence:
            if not isinstance(item, Mapping):
                raise ValueError(f"{model_id}.evidence entries must be mappings")
            origin = _nonempty_text(item.get("origin"), f"{model_id}.evidence.origin")
            if origin not in ORIGINS:
                raise ValueError(f"{model_id}: unsupported evidence origin {origin}")
            if role == "PREFLIGHT" and origin in {"CALIBRATED", "POSTFLIGHT_IDENTIFIED"}:
                raise ValueError(f"{model_id}: PREFLIGHT cannot use {origin} evidence")
            evidence.append(Evidence(
                _nonempty_text(item.get("claim"), f"{model_id}.evidence.claim"),
                origin,
                _nonempty_text(item.get("source"), f"{model_id}.evidence.source"),
            ))
        raw_missing = entry.get("missing_evidence")
        if not isinstance(raw_missing, list) or any(not isinstance(x, str) or not x.strip() for x in raw_missing):
            raise ValueError(f"{model_id}.missing_evidence must be a list of nonempty strings")
        if status != "COMPLETE" and not raw_missing:
            raise ValueError(f"{model_id}: incomplete status requires missing_evidence")

        raw_changes = entry.get("identified_changes")
        if not isinstance(raw_changes, list):
            raise ValueError(f"{model_id}.identified_changes must be a list")
        if role != "POSTFLIGHT" and raw_changes:
            raise ValueError(f"{model_id}: only POSTFLIGHT may identify parameters")
        for change in raw_changes:
            if not isinstance(change, Mapping) or not CHANGE_FIELDS <= change.keys():
                raise ValueError(f"{model_id}.identified_changes needs {sorted(CHANGE_FIELDS)}")
            for field in ("parameter", "reason", "evidence", "uncertainty", "effect_on_fit"):
                _nonempty_text(change[field], f"{model_id}.identified_changes.{field}")
        variants[model_id] = ModelVariant(
            id=model_id, role=role, status=status, runnable=runnable,
            configuration=configuration, evidence=tuple(evidence),
            missing_evidence=tuple(x.strip() for x in raw_missing),
            identified_changes=tuple(dict(item) for item in raw_changes),
        )
    return variants


def load_model_variants(path: Path) -> dict[str, ModelVariant]:
    """Read a declared model history without inferring any missing inputs."""
    with Path(path).open("r", encoding="utf-8") as stream:
        document = yaml.safe_load(stream)
    return parse_model_variants(document)
