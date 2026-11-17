"""Validação central sem rede e diagnóstico de instalação para CLI e GUI."""
from __future__ import annotations

from datetime import datetime
import importlib.metadata
import importlib.util
import math
from pathlib import Path
import platform
import sys
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import yaml

from antares_fd.application.projects import ProjectStore
from antares_fd.application.workspace import contained
from antares_fd.config.exceptions import ConfigurationError
from antares_fd.design.components import mass_properties, number, validate_components


def validate_project(root: Path, project_id: str) -> dict:
    """Liste erros e avisos de um projeto sem adquirir atmosfera nem integrar voo.

    Campos desconhecidos da versão futura são rejeitados pelo schema_version;
    ausências, limites físicos e arquivos referenciados são indicados por caminho.
    Assunções são permitidas e continuam visíveis como avisos de proveniência.
    """
    issues = []
    def issue(path, message, severity="error"):
        """Acrescente um diagnóstico estruturado sem ocultar erros de outros campos."""
        issues.append({"path": path, "message": str(message), "severity": severity})
    try:
        store = ProjectStore(root)
        data = store.read(project_id)
        project = store.path(project_id)
    except (ValueError, OSError, yaml.YAMLError) as exc:
        return {"valid": False, "issues": [{"path": "project", "message": str(exc), "severity": "error"}]}
    config = data["config"]
    for name, document in config.items():
        if str(document.get("schema_version", "1")) not in {"1", "1.0"}:
            issue(name + ".schema_version", "Versão não suportada; faça migração explícita.")
    sections = {}
    for name in ("vehicle", "motor", "launch", "recovery", "environment"):
        document = config.get(name, {})
        value = document.get(name, document)
        if not isinstance(value, dict) or not value:
            issue(name, "Seção obrigatória ausente ou inválida.")
            value = {}
        sections[name] = value
    vehicle, motor, launch = (sections[name] for name in ("vehicle", "motor", "launch"))
    for section, paths in ((vehicle, ("geometry", "mass_properties", "mass_properties.inertia", "drag", "drag.power_on", "drag.power_off", "staging", "motor_mount", "provenance")),
                           (launch, ("site", "rail", "datetime"))):
        for path in paths:
            parent = section
            keys = path.split(".")
            for key in keys[:-1]:
                parent = parent[key]
            value = parent.get(keys[-1], {})
            if not isinstance(value, dict):
                issue(path, "O campo deve ser um mapeamento.")
                value = {}
            parent[keys[-1]] = value
    def scalar(mapping, key, prefix, minimum=None):
        """Valide um campo escalar preservando a localização no diagnóstico."""
        try:
            return number(mapping.get(key), prefix + "." + key, minimum=minimum)
        except ConfigurationError as exc:
            issue(prefix + "." + key, exc)
            return None
    geometry = vehicle.get("geometry", {})
    diameter = scalar(geometry, "reference_diameter", "vehicle.geometry", 1e-12)
    length = scalar(geometry, "total_length", "vehicle.geometry", 1e-12)
    props = vehicle.get("mass_properties", {})
    if props.get("method") is not None and (not isinstance(props["method"], str) or props["method"] not in {"manual", "measured", "components"}):
        issue("vehicle.mass_properties.method", "Use components ou propriedades agregadas (manual/measured).")
    component_document = config.get("components")
    if props.get("method") == "components":
        try:
            if component_document is None:
                component_document = {"schema_version": 1, "coverage": vehicle.get("components_coverage", "PARTIAL"),
                                      "components": vehicle.get("mass_components", [])}
            props = mass_properties(component_document)
            if any(abs(x) > 1e-10 for x in props["radial_center_of_mass_m"]):
                issue("components", "CG radial não nulo não é representado pelo builder atual.")
        except ConfigurationError as exc:
            issue("components", exc)
            props = {}
    elif component_document is not None:
        try:
            for pending in validate_components(component_document):
                issue("components", pending, "warning")
        except ConfigurationError as exc:
            issue("components", exc)
    scalar(props, "mass_without_motor", "vehicle.mass_properties", 1e-12)
    center = scalar(props, "center_of_mass_without_motor", "vehicle.mass_properties", 0)
    if length is not None and center is not None and center > length:
        issue("vehicle.mass_properties.center_of_mass_without_motor", "CG fora do comprimento declarado.")
    inertia = props.get("inertia", {})
    for key in ("I11", "I22", "I33"):
        scalar(inertia, key, "vehicle.mass_properties.inertia", 0)
    for kind in ("power_on", "power_off"):
        drag = vehicle.get("drag", {}).get(kind, {})
        if drag.get("source_type") == "file":
            try:
                if not contained(project, drag.get("file") or "__missing__", exists=True).is_file():
                    raise ValueError("A curva deve ser um arquivo.")
            except (ValueError, OSError) as exc:
                issue("vehicle.drag." + kind, exc)
        elif drag.get("source_type") == "constant":
            scalar(drag, "constant", "vehicle.drag." + kind, 0)
        else:
            issue("vehicle.drag." + kind, "Declare source_type file ou constant.")
    for section in ("air_brakes", "body_sections", "payloads"):
        if vehicle.get(section):
            issue("vehicle." + section, "Recurso ainda não suportado pelo builder; registre a massa no inventário.")
    if vehicle.get("staging", {}).get("enabled"):
        issue("vehicle.staging", "Separação de estágios exige modelo de evento não implementado.")
    for key in ("dry_mass", "grain_number", "grain_density", "grain_outer_radius", "grain_initial_height", "nozzle_radius", "throat_radius"):
        scalar(motor, key, "motor", 1e-12)
    for key in ("center_of_dry_mass_position", "grains_center_of_mass_position", "grain_separation", "grain_initial_inner_radius"):
        scalar(motor, key, "motor", 0)
    if isinstance(motor.get("grain_number"), (int, float)) and not isinstance(motor["grain_number"], bool):
        if int(motor["grain_number"]) != motor["grain_number"]:
            issue("motor.grain_number", "A quantidade de grãos deve ser inteira.")
    outer, inner = motor.get("grain_outer_radius"), motor.get("grain_initial_inner_radius")
    if isinstance(outer, (int, float)) and isinstance(inner, (int, float)) and inner >= outer:
        issue("motor.grain_initial_inner_radius", "Raio interno deve ser menor que o externo.")
    if diameter and isinstance(outer, (int, float)) and 2 * outer > diameter:
        issue("motor.grain_outer_radius", "O diâmetro dos grãos excede o diâmetro de referência do veículo.")
    dry = motor.get("dry_inertia")
    if not isinstance(dry, list) or len(dry) not in (3, 6) or any(not isinstance(v, (float, int)) or not math.isfinite(v) for v in dry):
        issue("motor.dry_inertia", "Informe três ou seis valores finitos.")
    source = motor.get("thrust_source")
    if isinstance(source, str):
        try:
            if not contained(project, source, exists=True).is_file():
                raise ValueError("Fonte de empuxo deve ser um arquivo.")
        except (ValueError, OSError) as exc:
            issue("motor.thrust_source", exc)
    elif not isinstance(source, (int, float)) or isinstance(source, bool):
        issue("motor.thrust_source", "Informe a curva de empuxo; não é derivada da geometria externa.")
    else:
        scalar(motor, "thrust_source", "motor", 1e-12)
    if vehicle.get("motor_mount", {}).get("enabled"):
        scalar(vehicle["motor_mount"], "position", "vehicle.motor_mount", 0)
    site, rail, date = (launch.get(name, {}) for name in ("site", "rail", "datetime"))
    for key in ("latitude", "longitude", "elevation"):
        value = scalar(site, key, "launch.site")
        limit = {"latitude": 90, "longitude": 180}.get(key)
        if value is not None and limit and abs(value) > limit:
            issue("launch.site." + key, "Coordenada fora do intervalo geográfico.")
    scalar(rail, "length", "launch.rail", 1e-12)
    for key, maximum in (("inclination_deg", 90), ("heading_deg", 360)):
        value = scalar(rail, key, "launch.rail", 0)
        if value is not None and value > maximum:
            issue("launch.rail." + key, f"Máximo: {maximum} graus.")
    try:
        datetime.fromisoformat(str(date["date"]) + "T" + str(date["time"]))
        ZoneInfo(date.get("timezone", "America/Sao_Paulo"))
    except (KeyError, ValueError, TypeError, ZoneInfoNotFoundError) as exc:
        issue("launch.datetime", "Informe data, hora e fuso válidos: " + str(exc))
    environment_type = str(sections["environment"].get("type", "")).lower()
    if environment_type not in {"magi", "standard_atmosphere"}:
        issue("environment.type", "Use MAGI ou standard_atmosphere.")
    if environment_type == "magi":
        issue("environment", "Disponibilidade e cobertura MAGI serão verificadas durante a execução.", "warning")
    try:
        from antares_fd.builders.recovery import add_recovery_system
        class RecoveryCollector:
            """Receptor sem estado físico para verificar parâmetros de recuperação."""
            def add_parachute(self, **kwargs):
                """Aceite parâmetros já validados sem instalar um paraquedas real."""
                return None
        add_recovery_system(RecoveryCollector(), sections["recovery"], verbose=False)
    except (ConfigurationError, TypeError, ValueError, AttributeError) as exc:
        issue("recovery", exc)
    for key in ("mass", "center_of_mass", "inertia", "aerodynamics"):
        evidence = vehicle.get("provenance", {}).get(key, {})
        if not isinstance(evidence, dict) or not evidence.get("source"):
            issue("vehicle.provenance." + key, "Origem não documentada; hipótese pendente de rastreabilidade.", "warning")
    model = config.get("model", {}).get("model", {})
    if not isinstance(model.get("stage", "DESIGN"), str) or model.get("stage", "DESIGN") not in {"DESIGN", "AS_BUILT", "AS_FLOWN"}:
        issue("model.stage", "Estado de modelo inválido.")
    if model.get("pending_import"):
        issue("model.pending_import", "Importação OpenRocket precisa de revisão antes da simulação.")
    if not any(row["severity"] == "error" for row in issues):
        try:
            from antares_fd.config import load_project_config
            from antares_fd.builders import build_motor, build_vehicle
            parsed = load_project_config(project)
            motor_model = build_motor(parsed.motor, project)
            build_vehicle(parsed.vehicle, motor_model, project, verbose=False)
        except (ConfigurationError, ValueError, TypeError, KeyError, AttributeError, OSError, IndexError) as exc:
            issue("builders", "Entradas locais rejeitadas antes da aquisição meteorológica: " + str(exc))
    return {"valid": not any(row["severity"] == "error" for row in issues), "issues": issues,
            "project": data["id"], "revision": data["revision"], "stage": data["stage"]}


def doctor(root: Path) -> dict:
    """Inspecione instalação, ferramentas e diretórios sem baixar dados ou executar voos."""
    versions, issues = {}, []
    for distribution in ("rocketpy", "numpy", "scipy", "pandas", "pyarrow", "PyYAML", "matplotlib",
                         "multiprocess", "netCDF4", "Pillow", "requests", "scikit-learn", "xarray", "reportlab", "staticmap"):
        try:
            versions[distribution] = importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError:
            issues.append("Dependência ausente: " + distribution)
    if sys.version_info < (3, 12):
        issues.append("Python 3.12 ou superior é necessário.")
    if not (Path(root) / "projects").is_dir():
        issues.append("A raiz precisa conter projects/.")
    if versions.get("rocketpy") and not versions["rocketpy"].startswith("1.13."):
        issues.append("RocketPy fora da série 1.13 testada; revisar adaptadores antes de executar.")
    lock = Path(root) / f"requirements-py{sys.version_info.major}{sys.version_info.minor}.lock"
    return {"healthy": not issues, "python": platform.python_version(), "executable": sys.executable,
            "platform": platform.platform(), "versions": versions, "issues": issues,
            "lockfile": lock.name if lock.exists() else None,
            "optional": {"pytest": importlib.util.find_spec("pytest") is not None}}


def migrate_project(root: Path, project_id: str, *, apply: bool = False) -> dict:
    """Adicione metadados v1 a projetos legados por migração explícita e reversível.

    A execução padrão é preview. Nenhum dado físico é modificado; apply=True
    usa a revisão esperada do serviço e preserva a configuração anterior.
    """
    store = ProjectStore(root)
    data = store.read(project_id)
    if "model" in data["config"]:
        return {"changed": False, "message": "Metadados já presentes.", "revision": data["revision"]}
    document = {"schema_version": 1, "model": {"name": data["name"], "stage": "DESIGN",
                "notes": "Migração de metadados; condições as-built/as-flown não foram presumidas."}}
    if apply:
        store.save(project_id, {"model": document}, data["revision"], "Migração explícita de metadados v1")
    return {"changed": apply, "preview": document, "revision": data["revision"]}
