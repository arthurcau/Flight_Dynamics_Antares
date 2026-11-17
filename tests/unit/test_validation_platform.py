"""Validação local deve rejeitar formas mal tipadas e arquivos físicos corrompidos."""
import pytest

from antares_fd.application.projects import ProjectStore
from antares_fd.application.validation import validate_project


@pytest.mark.parametrize("section,field,value", [
    ("vehicle", "geometry", []), ("vehicle", "mass_properties", None),
    ("vehicle", "drag", "invalid"), ("launch", "site", []),
    ("vehicle", "mass_properties", {"method": []}),
    ("launch", "datetime", None), ("environment", "type", None)
])
def test_invalid_nested_data_becomes_diagnostic(engineering_workspace, section, field, value):
    store = ProjectStore(engineering_workspace)
    data = store.read("reference")
    data["config"][section][section][field] = value
    store.save("reference", data["config"], data["revision"], "Dado mal tipado")
    result = validate_project(engineering_workspace, "reference")
    assert not result["valid"]
    assert any(row["severity"] == "error" for row in result["issues"])


def test_corrupt_thrust_curve_is_rejected_before_weather(engineering_workspace, monkeypatch):
    store = ProjectStore(engineering_workspace)
    data = store.read("reference")
    relative = data["config"]["motor"]["motor"]["thrust_source"]
    (store.path("reference") / relative).write_text("This is not a thrust curve")
    def no_weather(*args, **kwargs):
        """Falhe se a validação tentar adquirir meteorologia."""
        pytest.fail("A validação não deve consultar meteorologia")
    monkeypatch.setattr("antares_fd.builders.environment.build_environment", no_weather)
    result = validate_project(engineering_workspace, "reference")
    assert not result["valid"]
    assert any(row["path"] == "builders" for row in result["issues"])
