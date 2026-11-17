"""Contratos analíticos independentes para massa, transporte de tensor e importação."""
import copy
import gzip
import io
import math
from pathlib import Path
import zipfile

import numpy as np
import pytest

from antares_fd.config.exceptions import ConfigurationError
from antares_fd.design.components import intrinsic_inertia, mass_properties, resolve_vehicle_mass, validate_components
from antares_fd.design.openrocket import parse_openrocket

FIXTURE = Path(__file__).parents[1] / "fixtures/openrocket/reference.xml"


def component(key, mass, position, category="structure"):
    """Defina massas pontuais explicitamente para um cálculo de referência fechado."""
    return {"id": key, "name": key, "mass_kg": mass, "axial_position_m": position,
            "category": category, "inertia_model": "point_mass", "provenance": {"type": "ASSUMED"}}


def test_parallel_axis_and_motor_exclusion_without_double_counting():
    document = {"schema_version": 1, "coverage": "COMPLETE", "components": [
        component("a", 2, 0), component("b", 2, 2), component("motor", 100, 10, "motor")]}
    result = mass_properties(document)
    assert result["mass_without_motor"] == 4
    assert result["center_of_mass_without_motor"] == 1
    assert result["inertia"] == {"I11": 4, "I22": 4, "I33": 0, "I12": 0, "I13": 0, "I23": 0}
    document["components"][1]["axial_position_m"] = 0
    assert mass_properties(document)["inertia"]["I11"] == 0


def test_local_hollow_cylinder_matches_closed_form_and_scales_with_mass():
    row = component("tube", 3, 0)
    row.update(inertia_model="hollow_cylinder", geometry={"length_m": 2, "outer_radius_m": .1, "inner_radius_m": .08})
    tensor = intrinsic_inertia(row)
    assert tensor[2, 2] == pytest.approx(3 * (.1**2 + .08**2) / 2)
    assert tensor[0, 0] == pytest.approx(3 * (3 * (.1**2 + .08**2) + 2**2) / 12)
    row["mass_kg"] *= .95
    np.testing.assert_allclose(intrinsic_inertia(row), tensor * .95)


@pytest.mark.parametrize("inertia", [[-1, 1, 1, 0, 0, 0], [1, 1, 4, 0, 0, 0], [1, 1, 1, 2, 0, 0]])
def test_nonphysical_tensors_are_rejected(inertia):
    with pytest.raises(ConfigurationError):
        intrinsic_inertia({"inertia_model": "provided", "inertia_kg_m2": inertia})


def test_partial_inventory_preserves_unknowns_and_cannot_override_vehicle():
    document = {"schema_version": 1, "coverage": "PARTIAL", "components": [
        {"id": "unknown", "mass_kg": None, "axial_position_m": None, "inertia_kg_m2": None}]}
    assert len(validate_components(document)) == 4
    with pytest.raises(ConfigurationError, match="incompleto"):
        mass_properties(document)
    vehicle = {"mass_properties": {"method": "components"}, "mass_components": document["components"]}
    before = copy.deepcopy(vehicle)
    with pytest.raises(ConfigurationError):
        resolve_vehicle_mass(vehicle)
    assert vehicle == before


def test_openrocket_xml_zip_and_gzip_agree_with_analytical_reference():
    xml = FIXTURE.read_bytes()
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("rocket.ork", xml)
    results = [parse_openrocket(content) for content in (xml, buffer.getvalue(), gzip.compress(xml))]
    body_mass = math.pi * (.05**2 - .045**2) * 1000
    total = body_mass + 4
    for result in results:
        assert result["components"]["coverage"] == "COMPLETE"
        assert result["mass_properties"]["mass_without_motor"] == pytest.approx(total)
        assert result["mass_properties"]["center_of_mass_without_motor"] == pytest.approx((body_mass * .5 + 4 * .25) / total)
        assert result["review_required"] is True
        assert result["motor_configurations_xml"] == []


def test_unsupported_shape_and_subtree_overrides_are_reported_not_silently_lost():
    xml = FIXTURE.read_bytes().replace(b"<bodytube>", b"<bodytube><overridemass>8</overridemass><overridesubcomponentsmass>true</overridesubcomponentsmass>")
    result = parse_openrocket(xml)
    assert result["components"]["coverage"] == "PARTIAL"
    assert result["warnings"]
    unknown = FIXTURE.read_bytes().replace(b"<masscomponent>", b"<tubefinset>").replace(b"</masscomponent>", b"</tubefinset>")
    assert parse_openrocket(unknown)["unsupported"][0]["type"] == "tubefinset"


@pytest.mark.parametrize("content", [b"", b"<!DOCTYPE x [<!ENTITY x SYSTEM 'file:///etc/passwd'>]><openrocket/>", b"<not-openrocket/>", b"garbage"])
def test_invalid_or_external_entity_documents_are_rejected(content):
    with pytest.raises(ValueError):
        parse_openrocket(content)
