"""Persistência, migração e catálogo compartilham o contrato entre CLI e GUI."""
import copy
import json
from pathlib import Path

import pytest

from antares_fd import cli
from antares_fd.application.datasets import register_dataset, verify_catalog
from antares_fd.application.projects import ProjectStore, project_revision
from antares_fd.application.validation import migrate_project, validate_project
from antares_fd.application.workspace import ConflictError, contained
from antares_fd.design.openrocket import import_design

FIXTURE = Path(__file__).parents[1] / "fixtures/openrocket/reference.xml"


def test_clone_is_isolated_and_collision_never_overwrites_source(engineering_workspace):
    root = engineering_workspace
    store = ProjectStore(root)
    before = project_revision(store.path("reference"))
    data = store.create("new_vehicle", "reference")
    assert data["id"] == "new_vehicle"
    assert data["config"]["model"]["model"]["baseline"]["revision"] == before
    assert project_revision(store.path("reference")) == before
    assert not (store.path("new_vehicle") / "telemetry").exists()
    with pytest.raises(ConflictError):
        store.create("NEW_VEHICLE", "reference")


def test_revision_conflict_and_restore_include_changed_curve(engineering_workspace):
    store = ProjectStore(engineering_workspace)
    before = store.read("reference")
    relative = "aero/power_on_drag.csv"
    original = (store.path("reference") / relative).read_bytes()
    changed = copy.deepcopy(before["config"])
    changed["vehicle"]["vehicle"]["name"] = "Edited"
    after = store.save("reference", changed, before["revision"], "Teste de edição", assets={relative: b"0, 0.5\n1, 0.6\n"})
    with pytest.raises(ConflictError):
        store.save("reference", changed, before["revision"], "Revisão obsoleta")
    assert store.read("reference")["revision"] == after["revision"]
    restored = store.restore("reference", before["revision"], after["revision"])
    assert restored["config"]["vehicle"]["vehicle"]["name"] == before["name"]
    assert (store.path("reference") / relative).read_bytes() == original
    assert len(store.history("reference")) == 2


@pytest.mark.parametrize("project", ["../outside", "/tmp/outside", "bad/name", "a.b", ""])
def test_project_ids_cannot_escape_workspace(engineering_workspace, project):
    with pytest.raises(ValueError):
        ProjectStore(engineering_workspace).create(project)


def test_symlinks_and_asset_escape_are_rejected_without_mutation(engineering_workspace, tmp_path):
    root = engineering_workspace
    store = ProjectStore(root)
    before = store.read("reference")
    with pytest.raises(ValueError):
        store.save("reference", {}, before["revision"], "Invalid asset", assets={"sources/../../escape": b"bad"})
    assert store.read("reference")["revision"] == before["revision"]
    external = tmp_path / "external"
    external.mkdir()
    (root / "projects/link").symlink_to(external)
    with pytest.raises(ValueError):
        store.path("link")
    with pytest.raises(ValueError):
        contained(root, "projects/link/secret")


def test_explicit_migration_preview_does_not_write(engineering_workspace):
    root = engineering_workspace
    store = ProjectStore(root)
    before = store.read("reference")
    assert migrate_project(root, "reference")["changed"] is False
    assert store.read("reference")["revision"] == before["revision"]
    result = migrate_project(root, "reference", apply=True)
    assert result["changed"] is True
    assert store.read("reference")["stage"] == "DESIGN"
    assert store.read("reference")["config"]["vehicle"] == before["config"]["vehicle"]
    assert migrate_project(root, "reference", apply=True)["changed"] is False


def test_unsupported_schema_is_rejected_without_changing_bytes(engineering_workspace):
    store = ProjectStore(engineering_workspace)
    before = store.read("reference")
    with pytest.raises(ValueError, match="schema"):
        store.save("reference", {"model": {"schema_version": 99}}, before["revision"], "Future schema")
    assert store.read("reference")["revision"] == before["revision"]


def test_catalog_keeps_raw_bytes_and_detects_missing_or_changed_data(engineering_workspace):
    root = engineering_workspace
    path = root / "data/raw.log"
    path.parent.mkdir()
    path.write_bytes(b"original raw evidence\n")
    entry = register_dataset(root, "flight", "data/raw.log", kind="telemetry", owner="Antares", source="Fixture", project="reference")
    assert len(entry["sha256"]) == 64
    assert verify_catalog(root)["datasets"][0]["status"] == "VERIFIED"
    with pytest.raises(ConflictError):
        register_dataset(root, "flight", "data/raw.log", kind="telemetry", owner="Antares", source="Fixture")
    path.write_bytes(b"changed")
    assert verify_catalog(root)["datasets"][0]["status"] == "CHANGED"
    path.unlink()
    assert verify_catalog(root)["datasets"][0]["status"] == "MISSING"


def test_import_preserves_original_and_invalidates_stale_mass_and_drag(engineering_workspace):
    root = engineering_workspace
    store = ProjectStore(root)
    before = store.read("reference")
    original = FIXTURE.read_bytes()
    result = import_design(root, "reference", original, before["revision"])
    assert result["project"]["config"]["model"]["model"]["pending_import"] is True
    assert result["project"]["config"]["vehicle"]["vehicle"]["mass_properties"] == {"method": "components"}
    assert result["project"]["config"]["motor"]["motor"]["thrust_source"] is None
    assert (store.path("reference") / "sources" / (result["report"]["sha256"] + ".ork")).read_bytes() == original
    assert not validate_project(root, "reference")["valid"]
    assert store.history("reference")[0]["revision"] == before["revision"]


def test_validation_and_project_commands_return_json_without_network(engineering_workspace, capsys):
    root = engineering_workspace
    assert cli.main(["--repo-root", str(root), "validate", "reference"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["valid"]
    assert cli.main(["--repo-root", str(root), "project", "new", "derived", "--from", "reference"]) == 0
    assert json.loads(capsys.readouterr().out)["id"] == "derived"
    config = ProjectStore(root).read("derived")
    config["config"]["vehicle"]["vehicle"]["mass_properties"]["mass_without_motor"] = None
    ProjectStore(root).save("derived", config["config"], config["revision"], "Unknown mass")
    assert cli.main(["--repo-root", str(root), "validate", "derived"]) == 1
    assert not json.loads(capsys.readouterr().out)["valid"]
