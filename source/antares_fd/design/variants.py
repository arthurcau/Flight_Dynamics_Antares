"""Transformações de montagem explícitas, sem efeitos no projeto original."""
from __future__ import annotations

from copy import deepcopy

from antares_fd.config.exceptions import ConfigurationError
from antares_fd.design.components import number, validate_components


def transform_components(document: dict, *, swap: list[str] | None = None, structural_factor: float = 1.0) -> dict:
    """Troque posições axiais e escale massas estruturais em uma cópia do inventário.

    swap contém dois IDs distintos com posições conhecidas. O fator aplica-se
    somente a estruturas incluídas; tensores informados escalam linearmente,
    sob hipótese explícita de geometria conservada. Dados ausentes bloqueiam
    a transformação necessária; nenhum motor/empuxo é inferido ou modificado.
    """
    validate_components(document)
    factor = number(structural_factor, "structural_factor", minimum=1e-12)
    if factor > 2:
        raise ConfigurationError("structural_factor deve ser no máximo 2.")
    result = deepcopy(document)
    rows = result["components"]
    if swap:
        if not isinstance(swap, list) or len(swap) != 2 or swap[0] == swap[1]:
            raise ConfigurationError("Selecione dois IDs de componentes distintos.")
        selected = [next((row for row in rows if row["id"] == key), None) for key in swap]
        if any(row is None for row in selected):
            raise ConfigurationError("Componente da troca não encontrado.")
        first, second = selected
        for row in selected:
            number(row.get("axial_position_m"), row["id"] + ".axial_position_m")
        first["axial_position_m"], second["axial_position_m"] = second["axial_position_m"], first["axial_position_m"]
        for row in selected:
            row["provenance"] = {"type": "ASSUMED", "source": "Troca de posições axiais: " + ", ".join(swap),
                                 "baseline": deepcopy(row.get("provenance", {}))}
    if factor != 1:
        for row in rows:
            if row.get("category") != "structure" or row.get("included", True) is not True:
                continue
            row["mass_kg"] = number(row.get("mass_kg"), row["id"] + ".mass_kg", minimum=0) * factor
            if row.get("inertia_model", "provided") == "provided" and row.get("inertia_kg_m2") is not None:
                row["inertia_kg_m2"] = [value * factor for value in row["inertia_kg_m2"]]
            row["provenance"] = {"type": "ASSUMED", "source": f"Massa estrutural × {factor}; geometria conservada",
                                 "baseline": deepcopy(row.get("provenance", {}))}
    validate_components(result)
    return result
