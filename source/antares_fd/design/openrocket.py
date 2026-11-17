"""Leitura conservadora de OpenRocket: conserva fonte e identifica lacunas.

Referências: especificação .ork e savers oficiais do OpenRocket. O parser não
executa Java nem presume equivalência de aerodinâmica, recuperação ou motores.
"""
from __future__ import annotations

import copy
import gzip
import hashlib
import io
import math
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

from antares_fd.application.projects import ProjectStore
from antares_fd.design.components import mass_properties, validate_components
from antares_fd.config.exceptions import ConfigurationError

MAX_BYTES = 16 * 1024 * 1024
CYLINDERS = {"bodytube", "innertube", "tubecoupler", "centeringring", "bulkhead", "engineblock"}
ASSEMBLIES = {"rocket", "stage"}
EXTERNAL = {"nosecone", "bodytube", "transition", "trapezoidfinset", "ellipticalfinset"}
SUPPORTED = CYLINDERS | ASSEMBLIES | {"masscomponent", "nosecone", "transition", "trapezoidfinset", "ellipticalfinset", "parachute", "shockcord", "railbutton", "launchlug"}


def design_xml(content: bytes) -> bytes:
    """Leia XML, ZIP ou GZip com limites de expansão e sem extrair arquivos.

    Rejeita DTD/entities, múltiplos candidatos, arquivos cifrados, profundidade
    e nós excessivos. Nenhum nome do ZIP é usado como caminho de escrita.
    """
    if not content or len(content) > MAX_BYTES:
        raise ValueError("Arquivo OpenRocket vazio ou maior que 16 MiB.")
    stream = io.BytesIO(content)
    if zipfile.is_zipfile(stream):
        with zipfile.ZipFile(stream) as archive:
            if len(archive.infolist()) > 500 or sum(item.file_size for item in archive.infolist()) > MAX_BYTES:
                raise ValueError("Arquivo compactado excede os limites de expansão.")
            candidates = [item for item in archive.infolist() if Path(item.filename).name == "rocket.ork"]
            if not candidates:
                candidates = [item for item in archive.infolist() if item.filename.endswith((".ork", ".xml"))]
            if len(candidates) != 1 or candidates[0].flag_bits & 1:
                raise ValueError("O ZIP deve conter um único documento de projeto não cifrado.")
            content = archive.read(candidates[0])
    elif content.startswith(b"\x1f\x8b"):
        with gzip.GzipFile(fileobj=stream) as archive:
            content = archive.read(MAX_BYTES + 1)
    if len(content) > MAX_BYTES or b"<!DOCTYPE" in content.upper() or b"<!ENTITY" in content.upper():
        raise ValueError("XML com DTD/entities ou tamanho não permitido.")
    return content


def numeric(element: ET.Element, name: str, default=None):
    """Leia um número explícito; auto e expressões desconhecidas permanecem ausentes."""
    text = element.findtext(name)
    if text is None:
        return default
    try:
        value = float(text)
    except ValueError:
        return None
    return value if math.isfinite(value) else None


def absolute_start(element, parent_start, parent_length, previous_end, length):
    """Resolva posição top/bottom/middle/after/absolute mantendo offsets em metros.

    Referências que exigem comprimentos ausentes retornam None. Geometria de
    pods, clusters ou estágios paralelos é tratada como não suportada.
    """
    position = element.find("axialoffset")
    if position is None:
        position = element.find("position")
    if position is None:
        method = "after" if element.tag in EXTERNAL | ASSEMBLIES else "top"
        offset = 0.0
    else:
        method = position.get("method", position.get("type", "top")).lower()
        try:
            offset = float(position.text or 0)
        except ValueError:
            return None
    if not math.isfinite(offset):
        return None
    if method == "absolute":
        return offset
    if method == "after":
        return None if previous_end is None else previous_end + offset
    if parent_start is None:
        return None
    if method == "top":
        return parent_start + offset
    if method in {"bottom", "middle"} and parent_length is not None and length is not None:
        fraction = 1 if method == "bottom" else 0.5
        return parent_start + (parent_length - length) * fraction + offset
    return None


def component_row(element, key, parent, start, length):
    """Extraia componente, overrides e material sem fabricar propriedades ausentes.

    Cilindros com raio, comprimento e densidade explícitos recebem massa e
    tensor analíticos. Outras formas preservam campos, exigindo revisão antes
    de usar o inventário como uma montagem completa.
    """
    material = element.find("material")
    mass = numeric(element, "overridemass", numeric(element, "mass"))
    density = None
    if material is not None and material.get("type") == "bulk":
        try:
            density = float(material.get("density", "nan"))
        except ValueError:
            density = None
        if density is not None and (not math.isfinite(density) or density <= 0):
            density = None
    outer = numeric(element, "outerradius", numeric(element, "radius", numeric(element, "packedradius")))
    inner = numeric(element, "innerradius")
    thickness = numeric(element, "thickness")
    if element.tag == "bulkhead":
        inner = 0
    if element.tag == "masscomponent" and outer is not None:
        inner = 0
    if inner is None and outer is not None and thickness is not None:
        inner = outer - thickness
    model = "provided"
    geometry = {"length_m": length, "outer_radius_m": outer, "inner_radius_m": inner}
    if element.tag in CYLINDERS | {"masscomponent"} and None not in (length, outer, inner) and 0 <= inner <= outer and length >= 0:
        if mass is None and density is not None:
            mass = math.pi * (outer**2 - inner**2) * length * density
        if mass is not None:
            model = "hollow_cylinder"
    local_cg = numeric(element, "overridecg", length / 2 if length is not None and model != "provided" else None)
    position = start + local_cg if start is not None and local_cg is not None else None
    radial = numeric(element, "radialposition", 0)
    angle = math.radians(numeric(element, "radialdirection", 0) or 0)
    row = {"id": key, "parent_id": parent, "name": element.findtext("name", element.tag),
           "category": "structure" if element.tag in CYLINDERS | EXTERNAL else "other",
           "included": element.tag not in ASSEMBLIES, "mass_kg": mass, "axial_position_m": position,
           "radial_position_m": [radial * math.cos(angle), radial * math.sin(angle)] if radial is not None else [0, 0],
           "inertia_model": model, "inertia_kg_m2": None, "geometry": geometry,
           "provenance": {"type": "CALCULATED" if model != "provided" else "UNKNOWN", "source": "OpenRocket"},
           "source_type": element.tag, "start_m": start,
           "source_fields": {child.tag: {"text": child.text, "attributes": child.attrib} for child in element if child.tag != "subcomponents"},
           "material": {"name": material.text, **material.attrib} if material is not None else None}
    return row


def parse_openrocket(content: bytes) -> dict:
    """Extraia uma árvore .ork com relatório de cobertura e identidade SHA-256.

    Preserva todos os componentes, inclusive não suportados. Overrides de
    assembleia, múltiplas instâncias, formas sem tensor e posições ambíguas
    impedem a marcação COMPLETE. A curva de empuxo não é inferida.
    """
    digest = hashlib.sha256(content).hexdigest()
    try:
        root = ET.fromstring(design_xml(content))
    except (ET.ParseError, zipfile.BadZipFile, OSError) as exc:
        raise ValueError("Arquivo OpenRocket inválido: " + str(exc)) from exc
    if root.tag != "openrocket" or root.find("rocket") is None:
        raise ValueError("Documento não contém um foguete OpenRocket.")
    stack, node_count = [(root, 0)], 0
    while stack:
        node, depth = stack.pop()
        node_count += 1
        if node_count > 10000 or depth > 64:
            raise ValueError("Árvore XML excede limites de nós/profundidade.")
        stack.extend((child, depth + 1) for child in node)
    rows, warnings, unsupported, ids = [], [], [], set()
    rocket = root.find("rocket")
    def visit(element, parent, parent_start, parent_length, previous_end):
        """Percorra a montagem e mantenha a referência local de cada componente."""
        key = element.findtext("id") or f"ork-{len(rows):04d}"
        if key in ids:
            raise ValueError("IDs duplicados no documento OpenRocket.")
        ids.add(key)
        length = numeric(element, "length", numeric(element, "packedlength"))
        if element.tag == "trapezoidfinset":
            length = numeric(element, "rootchord")
        start = 0.0 if element.tag == "rocket" else absolute_start(element, parent_start, parent_length, previous_end, length)
        row = component_row(element, key, parent, start, length)
        if element.tag not in SUPPORTED:
            unsupported.append({"id": key, "type": element.tag, "name": row["name"]})
        override_flags = ("overridesubcomponents", "overridesubcomponentsmass", "overridesubcomponentscg")
        if any(element.findtext(flag, "false").lower() == "true" for flag in override_flags):
            warnings.append(f"{row['name']}: override de assembleia requer verificação no OpenRocket.")
        if numeric(element, "instancecount", numeric(element, "fincount", 1)) != 1:
            warnings.append(f"{row['name']}: múltiplas instâncias não agregadas automaticamente.")
        if element.find("overridecd") is not None:
            warnings.append(f"{row['name']}: override de Cd preservado, sem conversão automática em curva.")
        if element.tag in ASSEMBLIES and any(element.find(tag) is not None for tag in ("overridemass", "overridecg")):
            warnings.append(f"{row['name']}: massa/CG de assembleia não aplicados aos filhos automaticamente.")
        rows.append(row)
        end = None if start is None or length is None else start + length
        child_previous = start
        for child in element.findall("subcomponents/*"):
            child_end = visit(child, key, start, length, child_previous)
            if child.tag in EXTERNAL | ASSEMBLIES:
                child_previous = child_end
                if child_end is not None:
                    end = max(end or child_end, child_end)
        return end
    visit(rocket, None, 0, None, 0)
    document = {"schema_version": 1, "coverage": "PARTIAL", "components": rows}
    pending = validate_components(document)
    # A única pendência inicial pode ser a própria flag PARTIAL.
    if len(pending) == 1 and not unsupported and not warnings and any(row["included"] for row in rows):
        document["coverage"] = "COMPLETE"
    properties = None
    if document["coverage"] == "COMPLETE":
        try:
            properties = mass_properties(document)
        except ConfigurationError as exc:
            document["coverage"] = "PARTIAL"
            warnings.append(str(exc))
    motors = [ET.tostring(element, encoding="unicode") for element in rocket.findall(".//motormount")]
    return {"name": rocket.findtext("name", "Importação OpenRocket"), "sha256": digest,
            "creator": root.get("creator"), "format_version": root.get("version"),
            "components": document, "mass_properties": properties, "unsupported": unsupported,
            "warnings": warnings, "pending": pending[1:], "motor_configurations_xml": motors,
            "review_required": True,
            "limitations": ["Curvas Cd(Mach) e empuxo exigem fontes independentes.",
                            "Importação não prova equivalência numérica com OpenRocket."]}


def import_design(root: Path, project_id: str, content: bytes, expected_revision: str) -> dict:
    """Importe um .ork preservando seus bytes e exigindo revisão explícita do modelo.

    Geometria externa suportada é mapeada para o builder. Propriedades antigas
    de massa e montagem do motor não são reutilizadas após a importação.
    """
    report = parse_openrocket(content)
    store = ProjectStore(root)
    data = store.read(project_id)
    config = copy.deepcopy(data["config"])
    vehicle = config["vehicle"]["vehicle"]
    vehicle["mass_properties"] = {"method": "components"}
    vehicle["mass_components"] = []
    vehicle["payloads"] = []
    vehicle["body_sections"] = []
    vehicle["fin_sets"], vehicle["tails"] = [], []
    vehicle["nose"] = {"enabled": False}
    vehicle["rail_guides"] = {"enabled": False}
    vehicle["motor_mount"] = {"enabled": True, "position": None}
    ends, radii = [], []
    for row in report["components"]["components"]:
        fields = row["source_fields"]
        element = ET.Element("component")
        for key, value in fields.items():
            ET.SubElement(element, key, value["attributes"]).text = value["text"]
        start, geometry = row["start_m"], row["geometry"]
        if row["source_type"] in {"bodytube", "nosecone", "transition"}:
            if start is not None and geometry["length_m"] is not None:
                ends.append(start + geometry["length_m"])
            radius = numeric(element, "radius", numeric(element, "aftradius"))
            if radius is not None:
                radii.append(radius)
        if row["source_type"] == "nosecone":
            kind = element.findtext("shape", "")
            kind = {"haack": "vonkarman", "conical": "conical", "ogive": "ogive", "ellipsoid": "elliptical"}.get(kind)
            if kind and not (element.findtext("shape") == "haack" and numeric(element, "shapeparameter", 0) != 0):
                vehicle["nose"] = {"enabled": True, "type": kind, "length": geometry["length_m"], "position": start}
            else:
                report["warnings"].append("Perfil de nariz exige conversão manual.")
        if row["source_type"] == "trapezoidfinset":
            vehicle["fin_sets"].append({"enabled": True, "name": row["name"], "type": "trapezoidal",
                "number": numeric(element, "fincount", numeric(element, "instancecount")), "position": start,
                "root_chord": numeric(element, "rootchord"), "tip_chord": numeric(element, "tipchord"),
                "span": numeric(element, "height"), "sweep_length": numeric(element, "sweeplength"),
                "cant_angle_deg": numeric(element, "cant", 0)})
    vehicle["geometry"]["total_length"] = max(ends) if ends else None
    vehicle["geometry"]["reference_diameter"] = 2 * max(radii) if radii else None
    for state in ("power_on", "power_off"):
        vehicle["drag"][state] = {"source_type": "file", "file": None, "extrapolation": "forbidden", "interpolation": "linear"}
    config["components"] = report["components"]
    model = config.setdefault("model", {"schema_version": 1, "model": {"stage": "DESIGN"}})["model"]
    model.update(pending_import=True, openrocket={"sha256": report["sha256"], "creator": report["creator"]})
    motor = config["motor"]["motor"]
    motor.update(thrust_source=None, dry_inertia=None, nozzle_position=None)
    source = "sources/" + report["sha256"] + ".ork"
    report_path = "sources/" + report["sha256"] + ".import.json"
    import json
    updated = store.save(project_id, config, expected_revision, "Importação OpenRocket com revisão pendente",
                         assets={source: content, report_path: json.dumps(report, ensure_ascii=False, indent=2).encode()})
    return {"project": updated, "report": report}
