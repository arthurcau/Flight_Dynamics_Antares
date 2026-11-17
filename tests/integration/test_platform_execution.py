"""Integração offline da mesma execução usada por terminal e GUI."""
import json
from pathlib import Path

import pytest

from antares_fd.application.projects import ProjectStore
from antares_fd.application.runs import execute_run, list_runs, read_run, verify_run


def test_deterministic_run_preserves_inputs_metrics_and_integrity(engineering_workspace):
    root = engineering_workspace
    result = execute_run(root, "reference", report=False)
    assert result["status"] == "COMPLETE"
    path = root / "results/reference" / result["run_id"]
    metrics = json.loads((path / "master_metrics.json").read_text())
    baseline = json.loads((Path(__file__).parents[1] / "fixtures/reference_project/expected.json").read_text())
    for key, specification in baseline["metrics"].items():
        assert metrics[key] == pytest.approx(specification["value"], abs=specification["absolute_tolerance"]), key
    assert (path / "atmosphere_input.parquet").exists()
    assert (path / "software_provenance.json").exists()
    assert metrics["total_impulse"] > 0
    assert metrics["rail_exit_velocity"] > 0
    assert verify_run(root, "reference", result["run_id"])["valid"]
    view = read_run(root, "reference", result["run_id"])
    assert len(view["series"]["time"]) > 100
    # Edição posterior nunca altera o modelo do resultado anterior.
    store = ProjectStore(root)
    before = store.read("reference")
    snapshot = path / "inputs/projects/reference/config/vehicle.yaml"
    frozen_bytes = snapshot.read_bytes()
    before["config"]["vehicle"]["vehicle"]["mass_properties"]["mass_without_motor"] += 1
    store.save("reference", before["config"], before["revision"], "Nova configuração")
    assert snapshot.read_bytes() == frozen_bytes
    assert verify_run(root, "reference", result["run_id"])["valid"]
    (path / "master_metrics.json").write_text("{}")
    assert not verify_run(root, "reference", result["run_id"])["valid"]


def test_invalid_project_never_creates_a_run(engineering_workspace):
    root = engineering_workspace
    store = ProjectStore(root)
    before = store.read("reference")
    before["config"]["motor"]["motor"]["thrust_source"] = None
    store.save("reference", before["config"], before["revision"], "Motor sem curva")
    with pytest.raises(ValueError, match="Projeto inválido"):
        execute_run(root, "reference", report=False)
    assert not (root / "results").exists()


def test_canonical_mc_uses_the_same_output_root_and_frozen_model(engineering_workspace):
    root = engineering_workspace
    result = execute_run(root, "reference", mode="monte_carlo", samples=1, workers=1, report=False)
    assert result["status"] in {"COMPLETE", "COMPLETE_NOT_CONVERGED"}
    path = root / "results/reference" / result["run_id"]
    manifest = json.loads((path / "manifest.json").read_text())
    assert manifest["requested_samples"] == 1
    assert manifest["completed_scenario_ids"] == ["nominal"]
    assert (path / "scenarios/nominal/outputs.parquet").exists()
    assert (path / "scenarios/nominal/atmospheres/nominal/atmosphere_input.parquet").exists()
    assert verify_run(root, "reference", result["run_id"])["valid"]
    view = read_run(root, "reference", result["run_id"])
    assert view["campaign"]["case_count"] == 1
    assert view["campaign"]["landing"]
    assert view["campaign"]["ecdf"][0]["metric"]
    assert view["metrics"]["apogee_agl"] == pytest.approx(2530.68665, abs=3)
    assert list_runs(root, "reference")[0]["metrics"] == view["metrics"] | {"total_impulse": None}
