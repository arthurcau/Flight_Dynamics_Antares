"""Catálogo institucional de evidências: hashes, localização, responsáveis e verificação."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import yaml

from antares_fd.application.projects import read_mapping
from antares_fd.application.workspace import ConflictError, contained, identifier, sha256, workspace_lock

KINDS = {"openrocket", "mass_properties", "motor_test", "calibration", "telemetry", "atmosphere", "campaign", "other"}


def read_catalog(root: Path) -> dict:
    """Leia metadados versionáveis sem tentar baixar ou substituir os arquivos brutos."""
    path = contained(root, "catalog/datasets.yaml")
    catalog = read_mapping(path) if path.exists() else {"schema_version": 1, "datasets": []}
    if catalog.get("schema_version") != 1 or not isinstance(catalog.get("datasets"), list):
        raise ValueError("Catálogo deve declarar schema_version 1 e datasets como lista.")
    for row in catalog["datasets"]:
        if not isinstance(row, dict) or any(not isinstance(row.get(key), str) for key in ("id", "path", "sha256", "owner", "source", "kind")):
            raise ValueError("Entrada de catálogo incompleta ou inválida.")
    return catalog


def register_dataset(root: Path, dataset_id: str, relative: str, *, kind: str,
                     owner: str, source: str, project: str | None = None) -> dict:
    """Registre uma evidência local por hash e responsável, sem mover ou editar sua origem.

    O arquivo precisa estar contido no workspace. Mesmo ID com conteúdo diferente
    é recusado; a verificação futura pode ocorrer mesmo com o bruto indisponível.
    """
    identifier(dataset_id)
    if kind not in KINDS or not isinstance(owner, str) or not owner.strip() or not isinstance(source, str) or not source.strip():
        raise ValueError("Informe tipo, responsável e origem da evidência.")
    path = contained(root, relative, exists=True)
    if not path.is_file():
        raise ValueError("O dataset deve ser um arquivo.")
    if project:
        from antares_fd.application.projects import ProjectStore
        project = ProjectStore(root).path(project).name
    entry = {"id": dataset_id, "kind": kind, "owner": owner.strip(), "source": source.strip(),
             "project": project, "path": path.relative_to(Path(root).resolve()).as_posix(),
             "sha256": sha256(path), "size_bytes": path.stat().st_size,
             "registered_utc": datetime.now(timezone.utc).isoformat()}
    with workspace_lock(root, "datasets"):
        catalog = read_catalog(root)
        if any(row["id"] == dataset_id for row in catalog["datasets"]):
            raise ConflictError("ID já registrado. Crie uma nova revisão de evidência.")
        catalog["datasets"].append(entry)
        destination = contained(root, "catalog/datasets.yaml")
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(".tmp")
        temporary.write_text(yaml.safe_dump(catalog, allow_unicode=True, sort_keys=False), encoding="utf-8")
        temporary.replace(destination)
    return entry


def verify_catalog(root: Path) -> dict:
    """Classifique cada evidência como VERIFIED, MISSING ou CHANGED pelo conteúdo local."""
    rows = []
    for entry in read_catalog(root)["datasets"]:
        try:
            path = contained(root, entry["path"], exists=True)
            status = "VERIFIED" if sha256(path) == entry["sha256"] else "CHANGED"
        except FileNotFoundError:
            status = "MISSING"
        except (OSError, ValueError):
            status = "INVALID"
        rows.append({**entry, "status": status})
    return {"valid": all(row["status"] == "VERIFIED" for row in rows), "datasets": rows}
