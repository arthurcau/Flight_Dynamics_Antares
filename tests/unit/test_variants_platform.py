"""Provas independentes das transformações de montagem e proteção de hipóteses."""
from copy import deepcopy

import pytest

from antares_fd.config.exceptions import ConfigurationError
from antares_fd.design.components import mass_properties
from antares_fd.design.variants import transform_components


def inventory():
    """Monte payload, eletrônica e gaiola com CGs pontuais e massas conhecidas."""
    return {"schema_version": 1, "coverage": "COMPLETE", "components": [
        {"id": "payload", "category": "payload", "mass_kg": 4, "axial_position_m": .4, "inertia_model": "point_mass"},
        {"id": "electronics", "category": "electronics", "mass_kg": 1, "axial_position_m": 1.4, "inertia_model": "point_mass"},
        {"id": "cage", "category": "structure", "mass_kg": 2, "axial_position_m": 1.4, "inertia_model": "point_mass"}
    ]}


def test_swap_and_structural_saving_do_not_discount_payload_or_electronics():
    document = inventory()
    original = deepcopy(document)
    changed = transform_components(document, swap=["payload", "electronics"], structural_factor=.95)
    assert document == original
    values = {row["id"]: row for row in changed["components"]}
    assert values["payload"]["mass_kg"] == 4
    assert values["electronics"]["mass_kg"] == 1
    assert values["cage"]["mass_kg"] == pytest.approx(1.9)
    expected_center = (4 * 1.4 + 1 * .4 + 1.9 * 1.4) / 6.9
    properties = mass_properties(changed)
    assert properties["mass_without_motor"] == pytest.approx(6.9)
    assert properties["center_of_mass_without_motor"] == pytest.approx(expected_center)


def test_partial_data_never_mutates_source_when_transform_fails():
    document = inventory()
    document["coverage"] = "PARTIAL"
    document["components"][-1]["mass_kg"] = None
    original = deepcopy(document)
    with pytest.raises(ConfigurationError):
        transform_components(document, swap=["payload", "electronics"], structural_factor=.95)
    assert document == original
