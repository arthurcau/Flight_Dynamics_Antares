"""Independent tests for the statistical campaign layer."""

from pathlib import Path
import json
import warnings
import zipfile
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import yaml
import pytest

from antares_fd.analysis.uq import (
    conditional_tail_analysis,
    convergence_table,
    landing_dispersion,
    probability_confidence_interval,
)
from antares_fd.simulation.uq_campaign import MonteCarloCampaign, _git_metadata
from antares_fd.simulation.uncertainty import SamplingPlan, UncertaintyRegistry
from antares_fd.simulation.uq_storage import write_parquet_atomic
from antares_fd.simulation.uq_pipeline import finalize_campaign_analysis
from antares_fd.simulation.uq_pipeline import _uncertainty_frame


ROOT = Path(__file__).resolve().parents[2]


def test_sampling_plan_is_case_deterministic_and_typed():
    registry = UncertaintyRegistry(ROOT / "projects/neblina_1/config/uncertainties.yaml")
    first = SamplingPlan(registry, 12, seed=123, env_ensemble_size=3).samples
    second = SamplingPlan(registry, 12, seed=123, env_ensemble_size=3).samples
    pd.testing.assert_frame_equal(first, second)
    assert first["case_id"].tolist() == list(range(12))
    assert first["seed"].is_unique


def test_probability_bounds_cover_edge_cases():
    assert probability_confidence_interval(0, 10)[0] == 0.0
    assert probability_confidence_interval(10, 10)[1] == 1.0
    low, high = probability_confidence_interval(9, 10)
    assert 0.0 < low < high < 1.0


def test_landing_ellipse_uses_two_dimensional_chi_square():
    frame = pd.DataFrame({"landing_east": [-1.0, 1.0, 0.0, 0.0], "landing_north": [0.0, 0.0, -1.0, 1.0]})
    result = landing_dispersion(frame)
    expected = np.sqrt(5.991464547107979 * (2.0 / 3.0))
    assert np.isclose(result["ellipses"]["0.95"]["major_axis"], expected)
    assert np.isclose(result["ellipses"]["0.95"]["minor_axis"], expected)


def test_convergence_requires_the_configured_window():
    frame = pd.DataFrame({"apogee_agl": [100.0] * 300})
    result = convergence_table(frame, [50, 100, 200, 300], {"apogee_p50": {"column": "apogee_agl", "quantile": 0.5, "relative_change": 0.001}}, window=3)
    assert result.iloc[-1]["status"] == "CONVERGED"


def test_campaign_batches_are_atomic_and_resume_by_case_id(tmp_path):
    campaign = MonteCarloCampaign("demo", tmp_path, master_seed=8, profile="debug")
    batch = pd.DataFrame({"case_id": [0, 1], "apogee_agl": [100.0, 120.0]})
    campaign.write_batch(0, batch)
    assert campaign.completed_case_ids() == {0, 1}
    assert not list(campaign.batches_path.glob("*.tmp"))


def test_campaign_resume_does_not_silently_skip_a_bad_batch(tmp_path):
    campaign = MonteCarloCampaign("demo", tmp_path, profile="debug")
    write_parquet_atomic(pd.DataFrame({"apogee_agl": [100.0]}), campaign.batches_path / "batch_00000.parquet")

    with pytest.raises(ValueError, match="Cannot read campaign batch"):
        campaign.completed_case_ids()


def test_new_campaign_ids_do_not_reuse_an_existing_path(monkeypatch, tmp_path):
    class FixedDateTime:
        @staticmethod
        def now(_tz=None):
            return datetime(2026, 9, 27, 12, 0, 0, 123456, tzinfo=timezone.utc)

    monkeypatch.setattr("antares_fd.simulation.uq_campaign.datetime", FixedDateTime)
    first = MonteCarloCampaign("demo", tmp_path, master_seed=8, profile="debug")
    second = MonteCarloCampaign("demo", tmp_path, master_seed=8, profile="debug")

    assert first.campaign_id != second.campaign_id
    assert first.root_path != second.root_path


def test_campaign_configuration_snapshot_is_created_and_immutable(tmp_path):
    project = tmp_path / "projects/demo"
    config_dir = project / "config"
    config_dir.mkdir(parents=True)
    source = config_dir / "vehicle.yaml"
    source.write_text("mass: 10\n", encoding="utf-8")
    campaign = MonteCarloCampaign("demo", tmp_path, profile="debug")

    snapshot_hashes = campaign.snapshot_config(project)
    snapshot = campaign.root_path / "config_snapshot/config/vehicle.yaml"
    assert snapshot_hashes["config/vehicle.yaml"]
    assert snapshot.read_text(encoding="utf-8") == "mass: 10\n"

    source.write_text("mass: 11\n", encoding="utf-8")
    with pytest.raises(ValueError, match="changed after snapshot"):
        campaign.snapshot_config(project)
    assert snapshot.read_text(encoding="utf-8") == "mass: 10\n"


def test_campaign_snapshot_includes_referenced_model_files_and_git_fingerprint(tmp_path):
    project = tmp_path / "projects/demo"
    config_dir = project / "config"
    config_dir.mkdir(parents=True)
    (project / "motors").mkdir()
    (project / "aero").mkdir()
    (config_dir / "motor.yaml").write_text(
        "motor:\n  thrust_source: motors/test.eng\n", encoding="utf-8",
    )
    (config_dir / "vehicle.yaml").write_text(
        "vehicle:\n  drag:\n    power_on:\n      source_type: file\n      file: aero/on.csv\n"
        "    power_off:\n      source_type: file\n      file: aero/off.csv\n", encoding="utf-8",
    )
    (project / "motors/test.eng").write_text("motor curve\n", encoding="utf-8")
    (project / "aero/on.csv").write_text("mach,cd\n0,0.5\n", encoding="utf-8")
    (project / "aero/off.csv").write_text("mach,cd\n0,0.6\n", encoding="utf-8")
    campaign = MonteCarloCampaign("demo", tmp_path, profile="debug")

    hashes = campaign.snapshot_config(project)
    expected = {
        "config/motor.yaml", "config/vehicle.yaml", "motors/test.eng",
        "aero/on.csv", "aero/off.csv",
    }
    assert set(hashes) == expected
    for relative, digest in hashes.items():
        snapshot = campaign.root_path / "config_snapshot" / relative
        assert snapshot.is_file()
        assert len(digest) == 64

    provenance = _git_metadata(ROOT)
    assert len(provenance["working_tree_snapshot_sha256"]) == 64


def test_campaign_snapshot_rejects_model_inputs_outside_project(tmp_path):
    project = tmp_path / "projects/demo"
    config_dir = project / "config"
    config_dir.mkdir(parents=True)
    (config_dir / "motor.yaml").write_text(
        "motor:\n  thrust_source: ../outside.eng\n", encoding="utf-8",
    )
    (project.parent / "outside.eng").write_text("external motor curve\n", encoding="utf-8")
    campaign = MonteCarloCampaign("demo", tmp_path, profile="debug")

    with pytest.raises(ValueError, match="outside project"):
        campaign.snapshot_config(project)


def test_uncertainty_artifact_preserves_distribution_and_provenance():
    frame = _uncertainty_frame(ROOT / "projects/neblina_1/config/uncertainties.yaml")
    assert {"parameter", "distribution", "unit", "source_type", "correlation_group"}.issubset(frame.columns)
    mass = frame.loc[frame["parameter"] == "vehicle_mass"].iloc[0]
    assert mass["unit"] == "kg"
    assert mass["distribution"] == "normal"
    assert mass["source_type"] == "LEGACY_ASSUMPTION"
    assert "mass_properties.mass_without_motor" in mass["nominal_yaml_path"]


def test_tail_analysis_and_archive_preserve_integrity_metadata(tmp_path):
    inputs = pd.DataFrame({"case_id": range(10), "wind": np.arange(10, dtype=float)}, index=np.arange(100, 110))
    outputs = pd.DataFrame({"case_id": range(9, -1, -1), "touchdown_velocity": np.arange(9, -1, -1, dtype=float)}, index=np.arange(200, 210))
    tail = conditional_tail_analysis(inputs, outputs, "touchdown_velocity", quantile=0.8)
    assert tail.iloc[0]["tail_count"] == 2
    campaign = MonteCarloCampaign("demo", tmp_path, profile="debug")
    campaign.write_manifest("COMPLETE")
    campaign.write_batch(0, outputs)
    archive_path = campaign.archive()
    manifest = json.loads((campaign.path / "manifest.json").read_text(encoding="utf-8"))
    assert "artifact_hashes" in manifest
    with zipfile.ZipFile(archive_path) as archive:
        assert "manifest.json" in archive.namelist()
        assert all(".tmp" not in name for name in archive.namelist())


def test_campaign_archive_refuses_missing_or_corrupt_manifest(tmp_path):
    missing = MonteCarloCampaign("demo", tmp_path, campaign_id="missing_manifest")
    with pytest.raises(FileNotFoundError, match="manifest"):
        missing.archive()
    assert not missing.path.with_suffix(".zip").exists()

    corrupt = MonteCarloCampaign("demo", tmp_path, campaign_id="corrupt_manifest")
    (corrupt.path / "manifest.json").write_text("{broken", encoding="utf-8")
    with pytest.raises(ValueError, match="manifest"):
        corrupt.archive()
    assert not corrupt.path.with_suffix(".zip").exists()

    active = MonteCarloCampaign("demo", tmp_path, campaign_id="active_campaign")
    active.write_manifest("RUNNING")
    with pytest.raises(ValueError, match="terminal status"):
        active.archive()
    assert not active.path.with_suffix(".zip").exists()


def test_campaign_archive_refuses_external_and_existing_destinations(tmp_path):
    campaign = MonteCarloCampaign("demo", tmp_path, campaign_id="archive_destinations")
    campaign.write_manifest("COMPLETE")
    outside = tmp_path / "outside.zip"
    with pytest.raises(ValueError, match="results"):
        campaign.archive(outside)
    with pytest.raises(ValueError, match="outside its source"):
        campaign.archive(campaign.path / "nested.zip")

    archive_path = campaign.archive()
    with pytest.raises(FileExistsError, match="already exists"):
        campaign.archive()
    assert archive_path.is_file()


def test_campaign_archive_preserves_failure_status_and_rejects_symlinked_artifacts(tmp_path):
    failed = MonteCarloCampaign("demo", tmp_path, campaign_id="failed_campaign")
    failed.write_manifest("FAILED", extra={"failure": {"type": "RuntimeError"}})
    archive_path = failed.archive()
    with zipfile.ZipFile(archive_path) as archive:
        manifest = json.loads(archive.read("manifest.json"))
    assert manifest["status"] == "FAILED"
    assert manifest["failure"]["type"] == "RuntimeError"

    linked = MonteCarloCampaign("demo", tmp_path, campaign_id="linked_campaign")
    linked.write_manifest("COMPLETE")
    external = tmp_path / "external.txt"
    external.write_text("outside campaign", encoding="utf-8")
    (linked.path / "external.txt").symlink_to(external)
    with pytest.raises(ValueError, match="symlinked artifacts"):
        linked.archive()
    assert not linked.path.with_suffix(".zip").exists()


@pytest.mark.parametrize("project,campaign_id", [("../outside", "run"), ("demo", "../outside"), ("demo", "/tmp/run")])
def test_campaign_identifiers_cannot_escape_results(tmp_path, project, campaign_id):
    with pytest.raises(ValueError, match="path component"):
        MonteCarloCampaign(project, tmp_path, campaign_id=campaign_id)


def test_campaign_refuses_symlinked_results_project_directory(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    project_results = tmp_path / "results/demo"
    project_results.parent.mkdir(parents=True)
    project_results.symlink_to(outside, target_is_directory=True)

    with pytest.raises(ValueError, match="symlink"):
        MonteCarloCampaign("demo", tmp_path, campaign_id="run")


def test_conditional_tail_analysis_excludes_nonfinite_inputs_without_warning():
    inputs = pd.DataFrame({"case_id": range(4), "mass_kg": [np.inf, 1.0, 3.0, 5.0]})
    outputs = pd.DataFrame({"case_id": range(4), "apogee_agl": [10.0, 20.0, 30.0, 40.0]})

    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        result = conditional_tail_analysis(inputs, outputs, "apogee_agl", quantile=0.5)

    mass = result.loc[result["input"] == "mass_kg"].iloc[0]
    assert mass["sample_count"] == 3
    assert mass["tail_mean"] == 4.0
    assert mass["mean_shift"] == 1.0


def test_finalizer_records_all_null_metrics_as_not_applicable(tmp_path):
    campaign = MonteCarloCampaign("demo", tmp_path, master_seed=8, profile="debug")
    write_parquet_atomic(pd.DataFrame({"case_id": [0], "seed": [12]}), campaign.samples_path)

    finalize_campaign_analysis(
        campaign,
        tmp_path / "projects/demo",
        output_records=[{"index": 0, "apogee": None}],
        input_records=[],
        failure_records=[],
    )

    statistics = pd.read_parquet(campaign.path / "statistics.parquet").set_index("metric")
    assert statistics.loc["apogee", "count"] == 0
    assert pd.isna(statistics.loc["apogee", "mean"])
    confidence = pd.read_parquet(campaign.path / "quantile_confidence.parquet")
    apogee = confidence.loc[confidence["metric"] == "apogee"]
    assert len(apogee) == 9
    assert apogee["sample_count"].eq(0).all()
    assert apogee["estimate"].isna().all()
