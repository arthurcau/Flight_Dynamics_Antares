"""Propriedades de massa de uma lista explícita de componentes em SI.

A posição axial cresce do bico para a cauda. O tensor usa os eixos do
RocketPy: I11/I22 transversais e I33 longitudinal, com produtos I12/I13/I23.
Motor e propelente ficam fora da massa do veículo para impedir dupla contagem.
"""
from __future__ import annotations

import copy
import math
from typing import Any

import numpy as np

from antares_fd.config.exceptions import ConfigurationError

PROVENANCE = {"MEASURED", "CALCULATED", "ASSUMED", "UNKNOWN"}
KINDS = {"structure", "electronics", "payload", "recovery", "motor", "other"}


def number(value: Any, field: str, *, minimum: float | None = None) -> float:
    """Exija um escalar finito, rejeitando booleanos e limites inferiores inválidos."""
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ConfigurationError(f"{field}: informe um número finito.")
    if minimum is not None and value < minimum:
        raise ConfigurationError(f"{field}: mínimo {minimum}.")
    return float(value)


def validate_components(document: dict, *, complete: bool = False) -> list[str]:
    """Valide a lista de componentes sem transformar ausências em números.

    Em edição, null é aceito e retornado como pendência; complete=True exige
    cobertura COMPLETE e todos os dados necessários à soma de massa e tensor.
    Valores presentes inválidos sempre geram ConfigurationError.
    """
    if not isinstance(document, dict) or str(document.get("schema_version")) != "1":
        raise ConfigurationError("components.schema_version deve ser 1.")
    if document.get("coverage") not in {"COMPLETE", "PARTIAL"}:
        raise ConfigurationError("components.coverage deve ser COMPLETE ou PARTIAL.")
    rows = document.get("components")
    if not isinstance(rows, list) or len(rows) > 10000:
        raise ConfigurationError("components deve ser uma lista com até 10000 itens.")
    pending, seen = [], set()
    if document["coverage"] != "COMPLETE":
        pending.append("O inventário de componentes ainda é parcial.")
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ConfigurationError(f"components[{index}] deve ser um mapeamento.")
        key = row.get("id")
        if not isinstance(key, str) or not key.strip() or key in seen:
            raise ConfigurationError("Cada componente precisa de id único não vazio.")
        seen.add(key)
        if not isinstance(row.get("category", "other"), str) or row.get("category", "other") not in KINDS:
            raise ConfigurationError(f"{key}: categoria desconhecida.")
        provenance = row.get("provenance", {})
        if not isinstance(provenance, dict) or not isinstance(provenance.get("type", "UNKNOWN"), str) or provenance.get("type", "UNKNOWN") not in PROVENANCE:
            raise ConfigurationError(f"{key}: proveniência desconhecida.")
        if not isinstance(row.get("included", True), bool):
            raise ConfigurationError(f"{key}.included deve ser booleano.")
        if row.get("included", True) is not True or row.get("category") == "motor":
            continue
        for field, lower in (("mass_kg", 0), ("axial_position_m", None)):
            if row.get(field) is None:
                pending.append(f"{key}.{field} não informado.")
            else:
                number(row[field], f"{key}.{field}", minimum=lower)
        if row.get("mass_kg") == 0:
            continue
        model = row.get("inertia_model", "provided")
        required = {"provided": [], "point_mass": [], "solid_cylinder": ["length_m", "outer_radius_m"],
                    "hollow_cylinder": ["length_m", "outer_radius_m", "inner_radius_m"],
                    "box": ["length_m", "width_m", "height_m"]}
        if not isinstance(model, str) or model not in required:
            raise ConfigurationError(f"{key}: modelo de inércia desconhecido.")
        geometry = row.get("geometry", {})
        if not isinstance(geometry, dict):
            raise ConfigurationError(f"{key}.geometry deve ser mapeamento.")
        missing_geometry = []
        for field in required[model]:
            if geometry.get(field) is None:
                missing_geometry.append(field)
            else:
                number(geometry[field], f"{key}.geometry.{field}", minimum=0)
        if missing_geometry or (row.get("mass_kg") is None and model != "provided"):
            pending.append(f"{key}: massa ou geometria de inércia incompleta.")
            continue
        try:
            intrinsic_inertia(row)
        except ConfigurationError as exc:
            if row.get("inertia_model", "provided") == "provided" and row.get("inertia_kg_m2") is None:
                pending.append(str(exc))
            else:
                raise
        radial = row.get("radial_position_m", [0, 0])
        if not isinstance(radial, list) or len(radial) != 2:
            raise ConfigurationError(f"{key}.radial_position_m exige dois valores.")
        for value in radial:
            number(value, f"{key}.radial_position_m")
    if complete and (pending or not rows):
        raise ConfigurationError("Inventário incompleto: " + "; ".join(pending or ["lista vazia"]))
    return pending


def intrinsic_inertia(component: dict) -> np.ndarray:
    """Obtenha o tensor local por declaração explícita ou geometria analítica.

    Modelos aceitos: provided, point_mass, solid_cylinder, hollow_cylinder e
    box. O centro local já deve ser o CG; posições não são somadas aqui.
    """
    model = component.get("inertia_model", "provided")
    if model == "provided":
        raw = component.get("inertia_kg_m2")
        if not isinstance(raw, list) or len(raw) != 6:
            raise ConfigurationError(f"{component.get('id')}.inertia_kg_m2 exige seis valores.")
        values = [number(value, "inertia_kg_m2") for value in raw]
        a, b, c, ab, ac, bc = values
        tensor = np.array([[a, ab, ac], [ab, b, bc], [ac, bc, c]], dtype=float)
        eigenvalues = np.linalg.eigvalsh(tensor)
        if eigenvalues.min() < -1e-12 or 2 * eigenvalues.max() > eigenvalues.sum() + 1e-10:
            raise ConfigurationError("Tensor de inércia não representa uma distribuição de massa física.")
        return tensor
    mass = number(component.get("mass_kg"), "mass_kg", minimum=0)
    if model == "point_mass":
        return np.zeros((3, 3))
    geometry = component.get("geometry", {})
    length = number(geometry.get("length_m"), "length_m", minimum=0)
    if model in {"solid_cylinder", "hollow_cylinder"}:
        outer = number(geometry.get("outer_radius_m"), "outer_radius_m", minimum=0)
        inner = number(geometry.get("inner_radius_m", 0), "inner_radius_m", minimum=0)
        if inner > outer or (model == "solid_cylinder" and inner != 0):
            raise ConfigurationError("Raios interno/externo incompatíveis com o modelo.")
        axial = mass * (outer**2 + inner**2) / 2
        transverse = mass * (3 * (outer**2 + inner**2) + length**2) / 12
        return np.diag([transverse, transverse, axial])
    if model == "box":
        width = number(geometry.get("width_m"), "width_m", minimum=0)
        height = number(geometry.get("height_m"), "height_m", minimum=0)
        return np.diag([mass * (height**2 + length**2) / 12,
                        mass * (width**2 + length**2) / 12,
                        mass * (width**2 + height**2) / 12])
    raise ConfigurationError(f"Modelo de inércia não suportado: {model}.")


def mass_properties(document: dict) -> dict:
    """Some massas e tensores pelo teorema dos eixos paralelos, sem incluir motor.

    Exige inventário completo; calcula CG tridimensional e transporta cada
    tensor ao CG agregado. Retorna massa, posição axial, offset radial e seis
    entradas do tensor, mantendo a convenção RocketPy explícita.
    """
    validate_components(document, complete=True)
    rows = [row for row in document["components"]
            if row.get("included", True) and row.get("category") != "motor" and row["mass_kg"] > 0]
    total = math.fsum(row["mass_kg"] for row in rows)
    if total <= 0:
        raise ConfigurationError("A massa sem motor deve ser positiva.")
    positions = [np.array([*row.get("radial_position_m", [0, 0]), row["axial_position_m"]]) for row in rows]
    center = sum((row["mass_kg"] * position for row, position in zip(rows, positions)), np.zeros(3)) / total
    tensor = np.zeros((3, 3))
    for row, position in zip(rows, positions):
        delta = position - center
        tensor += intrinsic_inertia(row) + row["mass_kg"] * (np.dot(delta, delta) * np.eye(3) - np.outer(delta, delta))
    inertia = [tensor[0, 0], tensor[1, 1], tensor[2, 2], tensor[0, 1], tensor[0, 2], tensor[1, 2]]
    return {"mass_without_motor": total, "center_of_mass_without_motor": float(center[2]),
            "radial_center_of_mass_m": center[:2].tolist(),
            "inertia": dict(zip(("I11", "I22", "I33", "I12", "I13", "I23"), map(float, inertia))),
            "component_count": len(rows), "method": "components"}


def resolve_vehicle_mass(vehicle: dict) -> dict:
    """Materialize propriedades agregadas de componentes em uma cópia do veículo.

    Mantém o caminho legado para method diferente de components. Componentes
    não são adicionados novamente como payloads; o agregado é passado ao Rocket.
    CG radial não nulo é rejeitado até existir montagem equivalente no builder.
    """
    result = copy.deepcopy(vehicle)
    if result.get("mass_properties", {}).get("method") != "components":
        return result
    document = {"schema_version": 1, "coverage": result.get("components_coverage", "PARTIAL"),
                "components": result.get("mass_components", [])}
    properties = mass_properties(document)
    if any(abs(value) > 1e-10 for value in properties.pop("radial_center_of_mass_m")):
        raise ConfigurationError("CG radial não nulo exige um modelo explícito de excentricidade.")
    result["mass_properties"] = properties
    result["mass_components"] = []
    return result
