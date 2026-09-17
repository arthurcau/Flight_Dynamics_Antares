"""Independent tests for the statistical campaign layer."""

from pathlib import Path
import json
import zipfile

import numpy as np
import pandas as pd
import yaml

from antares_fd.analysis.uq import (
    conditional_tail_analysis,
    convergence_table,
    landing_dispersion,
    probability_confidence_interval,
)
from antares_fd.simulation.uq_campaign import MonteCarloCampaign
from antares_fd.simulation.uncertainty import SamplingPlan, UncertaintyRegistry
from antares_fd.simulation.uq_storage import write_parquet_atomic
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
