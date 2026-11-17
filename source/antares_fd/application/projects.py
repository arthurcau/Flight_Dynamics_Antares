"""Criação, leitura e revisão de projetos com controle de alterações concorrentes."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import getpass
import json
from pathlib import Path
import shutil
import uuid

import yaml

from antares_fd.application.workspace import ConflictError, contained, identifier, sha256, workspace_lock
from antares_fd.storage import write_json_atomic

CONFIG_FILES = {"vehicle", "motor", "launch", "recovery", "environment", "simulation",
                "monte_carlo", "uncertainties", "requirements", "model", "components", "design"}
STAGES = {"DESIGN", "AS_BUILT", "AS_FLOWN"}


def read_mapping(path: Path) -> dict:
    """Leia um YAML pequeno com raiz mapping e rejeite números não finitos.

    O limite de 2 MiB protege o editor de configuração; documentos muito grandes
    devem ser divididos em assets. Árvores cíclicas não pertencem ao contrato.
    """
    if path.stat().st_size > 2 * 1024 * 1024:
        raise ValueError(f"Configuração muito grande: {path.name}.")
    value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(value, dict):
        raise ValueError(f"{path.name}: a raiz deve ser um mapeamento.")
    json.dumps(value, allow_nan=False, default=str)
    return value


def input_files(project: Path) -> list[Path]:
    """Liste entradas de projeto, recusando links e excluindo saídas e revisões."""
    files = []
    for name in ("config", "aero", "motors", "sources"):
        directory = contained(project, name)
        if directory.exists():
            for path in sorted(directory.rglob("*")):
                safe = contained(project, path.relative_to(project))
                if safe.is_file():
                    files.append(safe)
    return files


def project_revision(project: Path) -> str:
    """Identifique o conteúdo das entradas, incluindo curvas e fontes importadas."""
    records = {path.relative_to(project).as_posix(): sha256(path) for path in input_files(project)}
    return hashlib.sha256(json.dumps(records, sort_keys=True).encode()).hexdigest()


class ProjectStore:
    """API local de projetos; edição preserva snapshot e exige revisão esperada."""

    def __init__(self, root: Path):
        """Associe o serviço à raiz existente do repositório, sem criar um projeto."""
        self.root = Path(root).resolve()
        self.projects = contained(self.root, "projects", exists=True)

    def path(self, project_id: str) -> Path:
        """Resolva um projeto por ID ignorando capitalização, sem seguir symlinks."""
        identifier(project_id)
        for path in self.projects.iterdir():
            if path.name.lower() == project_id.lower():
                safe = contained(self.projects, path.name, exists=True)
                if safe.is_dir() and (safe / "config").is_dir():
                    return safe
        raise FileNotFoundError(f"Projeto não encontrado: {project_id}.")

    def list(self) -> list[dict]:
        """Retorne identificadores, nomes e estados; um projeto inválido não oculta os outros."""
        rows = []
        for path in sorted(self.projects.iterdir()):
            if path.name.startswith(".") or path.is_symlink() or not (path / "config").is_dir():
                continue
            try:
                data = self.read(path.name)
                rows.append({key: data[key] for key in ("id", "name", "stage", "revision")})
            except (ValueError, OSError, yaml.YAMLError) as exc:
                rows.append({"id": path.name, "name": path.name, "stage": "INVALID", "error": str(exc)})
        return rows

    def read(self, project_id: str) -> dict:
        """Leia configurações e fingerprint do projeto, preservando campos desconhecidos."""
        project = self.path(project_id)
        with workspace_lock(self.root, project.name):
            return self._read(project)

    def _read(self, project: Path) -> dict:
        """Leia uma revisão coerente enquanto o chamador mantém o lock do projeto."""
        config = {}
        for path in sorted((project / "config").glob("*.yaml")):
            if path.stem in CONFIG_FILES:
                config[path.stem] = read_mapping(contained(project, path.relative_to(project), exists=True))
        vehicle = config.get("vehicle", {}).get("vehicle", {})
        model = config.get("model", {}).get("model", {})
        if not isinstance(vehicle, dict) or not isinstance(model, dict):
            raise ValueError("vehicle e model devem ser mapeamentos.")
        result = {"id": project.name, "name": vehicle.get("name", project.name),
                  "stage": model.get("stage", "DESIGN"), "revision": project_revision(project), "config": config}
        if isinstance(vehicle.get("mass_properties"), dict) and vehicle["mass_properties"].get("method") == "components":
            from antares_fd.config.exceptions import ConfigurationError
            from antares_fd.design.components import mass_properties
            try:
                result["derived_mass_properties"] = mass_properties(config.get("components", {}))
            except ConfigurationError:
                result["derived_mass_properties"] = None
        return result

    def create(self, project_id: str, source: str = "00_Copy_This") -> dict:
        """Crie um projeto por cópia isolada das entradas, sem telemetria ou resultados.

        Nomes existentes nunca são sobrescritos. A origem e sua revisão ficam no
        model.yaml, e a nova montagem começa no estado DESIGN.
        """
        identifier(project_id)
        with workspace_lock(self.root, "projects"):
            if any(path.name.lower() == project_id.lower() for path in self.projects.iterdir()):
                raise ConflictError("Já existe um projeto com este nome.")
            origin = self.path(source)
            source_revision = project_revision(origin)
            stage = self.projects / (".new-" + uuid.uuid4().hex)
            stage.mkdir()
            try:
                for path in input_files(origin):
                    relative = path.relative_to(origin)
                    target = stage / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(path, target)
                if project_revision(origin) != source_revision or project_revision(stage) != source_revision:
                    raise ConflictError("A origem mudou durante a cópia; crie novamente após a edição.")
                vehicle_path = stage / "config/vehicle.yaml"
                vehicle = read_mapping(vehicle_path)
                vehicle["vehicle"].update(name=project_id, project=project_id, revision="0.1", status="development")
                vehicle_path.write_text(yaml.safe_dump(vehicle, sort_keys=False, allow_unicode=True), encoding="utf-8")
                model = {"schema_version": 1, "model": {"stage": "DESIGN", "name": project_id,
                         "baseline": {"project": origin.name, "revision": source_revision},
                         "notes": "Entradas herdadas: revisar dados e hipóteses antes de simular."}}
                (stage / "config/model.yaml").write_text(yaml.safe_dump(model, sort_keys=False, allow_unicode=True), encoding="utf-8")
                (stage / "README.md").write_text(
                    f"# {project_id}\n\nModelo de projeto derivado de `{origin.name}`.\n\n"
                    f"Revisão de origem: `{source_revision}`.\n\n"
                    "Use `antares-fd validate` antes de `antares-fd run`.\n"
                    "Configurações herdadas não constituem medições deste foguete.\n", encoding="utf-8")
                stage.rename(self.projects / project_id)
            finally:
                if stage.exists():
                    shutil.rmtree(stage)
        return self.read(project_id)

    def history(self, project_id: str) -> list[dict]:
        """Liste revisões preservadas pelo serviço em ordem de gravação."""
        project = self.path(project_id)
        directory = contained(project, "revisions")
        rows = []
        if directory.exists():
            for path in sorted(directory.glob("*/revision.json")):
                if path.parent.name.startswith("."):
                    continue
                rows.append(json.loads(contained(project, path.relative_to(project)).read_text(encoding="utf-8")))
        return sorted(rows, key=lambda row: row["created_utc"], reverse=True)

    def _snapshot(self, project: Path, revision: str, note: str) -> None:
        """Preserve as entradas anteriores à edição com hashes; não sobrescreva uma revisão."""
        destination = contained(project, "revisions/" + revision)
        if destination.exists():
            return
        stage = contained(project, "revisions/." + uuid.uuid4().hex)
        stage.mkdir(parents=True)
        try:
            hashes = {}
            for path in input_files(project):
                relative = path.relative_to(project)
                target = stage / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
                hashes[relative.as_posix()] = sha256(target)
            if project_revision(stage) != revision or project_revision(project) != revision:
                raise ConflictError("As entradas mudaram durante a preservação da revisão.")
            write_json_atomic({"revision": revision, "note": note, "files": hashes, "local_author": getpass.getuser(),
                               "created_utc": datetime.now(timezone.utc).isoformat()}, stage / "revision.json")
            stage.rename(destination)
        finally:
            if stage.exists():
                shutil.rmtree(stage)

    def save(self, project_id: str, config: dict, expected_revision: str, note: str = "Edição local", *, assets: dict | None = None, replace_config: bool = False) -> dict:
        """Grave uma edição otimista e preserve a revisão anterior.

        Valida os documentos antes da primeira escrita; em falha de gravação
        restaura os bytes anteriores. O lock serializa CLI e GUI no workspace.
        """
        if not isinstance(config, dict) or set(config) - CONFIG_FILES:
            raise ValueError("Documento de configuração ou seção desconhecida.")
        if not isinstance(note, str) or not note.strip() or len(note) > 2000:
            raise ValueError("Descreva a alteração em até 2000 caracteres.")
        for name, document in config.items():
            if not isinstance(document, dict):
                raise ValueError(f"{name}: informe um mapeamento.")
            json.dumps(document, allow_nan=False)
            if str(document.get("schema_version", "1")) not in {"1", "1.0"}:
                raise ValueError(f"{name}: versão de schema não suportada.")
        if "components" in config:
            from antares_fd.design.components import validate_components
            validate_components(config["components"])
        model = config.get("model", {}).get("model", {})
        if not isinstance(model, dict) or not isinstance(model.get("stage", "DESIGN"), str) or model.get("stage", "DESIGN") not in STAGES:
            raise ValueError("Estado deve ser DESIGN, AS_BUILT ou AS_FLOWN.")
        project = self.path(project_id)
        checked_assets = {}
        if assets is not None and not isinstance(assets, dict):
            raise ValueError("Assets devem ser um mapeamento.")
        for relative, content in (assets or {}).items():
            if not isinstance(relative, str) or not Path(relative).parts or Path(relative).parts[0] not in {"sources", "motors", "aero"} or not isinstance(content, bytes) or len(content) > 16 * 1024 * 1024:
                raise ValueError("Asset inválido ou maior que 16 MiB.")
            checked_assets[contained(project, relative)] = content
        project_id = project.name
        with workspace_lock(self.root, identifier(project_id)):
            project = self.path(project_id)
            current = project_revision(project)
            if expected_revision != current:
                raise ConflictError("O projeto mudou desde sua leitura. Recarregue antes de salvar.")
            self._snapshot(project, current, note)
            previous = {}
            try:
                if replace_config:
                    for path in (project / "config").glob("*.yaml"):
                        if path.stem in CONFIG_FILES and path.stem not in config:
                            previous[path] = path.read_bytes()
                            path.unlink()
                for path, content in checked_assets.items():
                    contained(project, path.relative_to(project))
                    previous[path] = path.read_bytes() if path.exists() else None
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(content)
                for name, document in config.items():
                    path = contained(project, f"config/{name}.yaml")
                    previous[path] = path.read_bytes() if path.exists() else None
                    temporary = path.with_name("." + path.name + ".tmp")
                    temporary.write_text(yaml.safe_dump(document, sort_keys=False, allow_unicode=True), encoding="utf-8")
                    temporary.replace(path)
            except Exception:
                for path, content in previous.items():
                    if content is None:
                        path.unlink(missing_ok=True)
                    else:
                        path.write_bytes(content)
                raise
        return self.read(project_id)

    def restore(self, project_id: str, revision: str, expected_revision: str) -> dict:
        """Restaure uma revisão de configuração preservando o estado atual como histórico.

        Verifica hashes das entradas arquivadas. Assets não são apagados; uma
        revisão antiga de YAML pode voltar a apontar para seus arquivos originais.
        """
        if not re_full_hash(revision):
            raise ValueError("Revisão deve ser um SHA-256.")
        project = self.path(project_id)
        snapshot = contained(project, "revisions/" + revision, exists=True)
        manifest = json.loads((snapshot / "revision.json").read_text(encoding="utf-8"))
        for relative, digest in manifest["files"].items():
            if sha256(contained(snapshot, relative, exists=True)) != digest:
                raise ValueError("Revisão arquivada falhou na verificação de integridade.")
        config = {path.stem: read_mapping(path) for path in (snapshot / "config").glob("*.yaml") if path.stem in CONFIG_FILES}
        assets = {relative: contained(snapshot, relative, exists=True).read_bytes()
                  for relative in manifest["files"] if Path(relative).parts[0] in {"motors", "aero", "sources"}}
        return self.save(project_id, config, expected_revision, "Restauração de " + revision,
                         assets=assets, replace_config=True)


def re_full_hash(value: str) -> bool:
    """Identifique uma impressão digital SHA-256 hexadecimal de 64 caracteres."""
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)
