"""A current-model reference run must archive exact inputs and explicit labels."""

from pathlib import Path
from dataclasses import dataclass
from types import SimpleNamespace

import json
import shutil
import numpy as np
import pandas as pd

import pytest

from antares_fd.validation.models import load_model_variants
from antares_fd.validation.reference import (
    _archived_environment, _atmosphere_frame, _compare_reference_timeseries,
    collect_reference_inputs, replay_archived_reference, run_current_reference,
)


PROJECT = Path(__file__).resolve().parents[2] / "projects/neblina_1"
MANIFEST = PROJECT / "reconstruction/model_variants.yaml"


def test_reference_inputs_include_curve_and_config_sources():
    relative_paths = [path.relative_to(PROJECT).as_posix() for path in collect_reference_inputs(PROJECT)]
    assert "config/vehicle.yaml" in relative_paths
    assert "config/environment.yaml" in relative_paths
    assert "motors/Yaripo_teste_est_2_2.eng" in relative_paths
    assert "aero/power_on_drag.csv" in relative_paths
    assert "aero/power_off_drag.csv" in relative_paths


def test_replay_comparison_aligns_states_on_shared_time_without_extrapolation():
    original = pd.DataFrame({"time_s": [0.0, 1.0, 2.0], "altitude_agl_m": [0.0, 10.0, 20.0]})
    replay = pd.DataFrame({"time_s": [0.0, 0.9, 1.8], "altitude_agl_m": [0.0, 9.0, 18.0]})

    comparison = _compare_reference_timeseries(original, replay, rtol=1e-9, atol=1e-9)

    assert comparison["matches"] is True
    assert comparison["common_time_samples"] == 2
    assert comparison["source_time_samples_outside_common_domain"] == 1
    assert comparison["maximum_absolute_difference"] == 0.0


def test_archived_magi_humidity_rebuilds_the_same_derived_atmosphere():
    from datetime import datetime, timezone

    from antares_fd.builders.environment import _apply_profile, _base_environment
    from antares_fd.config.loader import load_project_config
    from antares_fd.environment.atmosphere import AtmosphericProfile

    config = load_project_config(PROJECT)
    profile = AtmosphericProfile(
        altitude_asl_m=np.array([495.0, 2000.0]),
        pressure_pa=np.array([95000.0, 80000.0]),
        temperature_k=np.array([292.0, 275.0]),
        wind_u_mps=np.array([2.0, 5.0]),
        wind_v_mps=np.array([-1.0, 3.0]),
        source="synthetic-test",
        source_type="deterministic_forecast",
        model="test-model",
        run_time_utc=None,
        valid_time_utc=datetime(2026, 9, 3, 18, tzinfo=timezone.utc),
        latitude_deg=-21.89,
        longitude_deg=-49.01,
        member_id="control",
        specific_humidity_kg_kg=np.array([0.01, 0.004]),
    )
    original_environment = _apply_profile(_base_environment(config.launch), profile)
    archived = _atmosphere_frame(SimpleNamespace(env=original_environment))
    replay_environment = _archived_environment(config, archived, original_environment.antares_atmosphere)
    replayed = _atmosphere_frame(SimpleNamespace(env=replay_environment))

    assert "specific_humidity_kg_kg" in archived
    pd.testing.assert_frame_equal(archived, replayed, check_exact=True)


def test_non_reference_variant_cannot_be_exported_as_reference(tmp_path):
    preflight = load_model_variants(MANIFEST)["NEBLINA1_PREFLIGHT_RECONSTRUCTION"]
    with pytest.raises(ValueError, match="CURRENT_REFERENCE"):
        run_current_reference(PROJECT, preflight, tmp_path / "run")
    assert not (tmp_path / "run").exists()


def test_reference_refuses_output_outside_ignored_results(tmp_path):
    reference = load_model_variants(MANIFEST)["NEBLINA1_CURRENT_MODEL_REFERENCE"]
    with pytest.raises(ValueError, match="results"):
        run_current_reference(PROJECT, reference, tmp_path / "external")
    assert not (tmp_path / "external").exists()


def test_reference_inputs_reject_paths_outside_project(tmp_path):
    config_dir = tmp_path / "project/config"
    config_dir.mkdir(parents=True)
    (config_dir / "vehicle.yaml").write_text(
        "vehicle:\n  drag:\n    power_on:\n      source_type: file\n      file: ../../outside.csv\n", encoding="utf-8"
    )
    (config_dir / "motor.yaml").write_text("motor: {}\n", encoding="utf-8")
    (tmp_path / "outside.csv").write_text("mach,Cd\n0,1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="outside project"):
        collect_reference_inputs(tmp_path / "project")


def test_reference_export_uses_snapshotted_inputs_and_model_labels(tmp_path, monkeypatch):
    class ProfileFunction:
        def __init__(self, altitude, values):
            self.source = SimpleNamespace(altitude=altitude)
            self.altitude = altitude
            self.values = values

        def __call__(self, altitude):
            return np.interp(altitude, self.altitude, self.values)

    altitude = np.array([495.0, 1500.0])
    env = SimpleNamespace(
        antares_atmosphere={"source_type": "historical_forecast", "source": "synthetic-test"},
        pressure=ProfileFunction(altitude, [95000.0, 85000.0]),
        temperature=ProfileFunction(altitude, [290.0, 280.0]),
        density=ProfileFunction(altitude, [1.1, 1.0]),
        wind_velocity_x=ProfileFunction(altitude, [1.0, 2.0]),
        wind_velocity_y=ProfileFunction(altitude, [0.0, 0.0]),
        speed_of_sound=ProfileFunction(altitude, [340.0, 335.0]),
        dynamic_viscosity=ProfileFunction(altitude, [1.8e-5, 1.7e-5]),
    )
    flight = SimpleNamespace(env=env)
    series = SimpleNamespace(
        time=np.array([0.0, 1.0]), altitude_agl=np.array([0.0, 10.0]),
        altitude_asl=np.array([495.0, 505.0]), velocity_z=np.array([0.0, 20.0]),
        acceleration_z=np.array([0.0, 20.0]), dynamic_pressure=np.array([0.0, 100.0]),
        mach=np.array([0.0, 0.1]), thrust=np.array([100.0, 0.0]), mass=np.array([30.0, 29.0]),
    )

    @dataclass
    class Metrics:
        apogee_agl: float
        timeseries: object
        atmosphere: object
        validation: object

    test_project = tmp_path / "projects/neblina_1"
    for directory in ("config", "aero", "motors"):
        shutil.copytree(PROJECT / directory, test_project / directory)

    def fake_execute(config, project_dir, **kwargs):
        assert project_dir.name == "inputs"
        assert (project_dir / "motors/Yaripo_teste_est_2_2.eng").is_file()
        if kwargs.get("environment") is not None:
            return SimpleNamespace(env=kwargs["environment"])
        return flight

    monkeypatch.setattr("antares_fd.validation.reference.execute_scenario", fake_execute)
    monkeypatch.setattr("antares_fd.validation.reference.extract_flight_metrics", lambda *args, **kwargs: Metrics(10.0, series, None, {"unproven": True}))
    reference = load_model_variants(MANIFEST)["NEBLINA1_CURRENT_MODEL_REFERENCE"]
    destination = run_current_reference(test_project, reference, tmp_path / "results/neblina_1/reference")

    manifest = json.loads((destination / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["data_origin"] == "MODELED"
    assert manifest["validation_status"] == "NOT_YET_VALIDATED"
    assert manifest["source_telemetry_sha256"] is None
    assert "validation" not in json.loads((destination / "flight_metrics.json").read_text(encoding="utf-8"))
    assert pd.read_parquet(destination / "simulated_timeseries.parquet")["altitude_agl_m"].tolist() == [0.0, 10.0]
    assert len(pd.read_parquet(destination / "atmosphere_profile.parquet")) == 2
    with pytest.raises(FileExistsError):
        run_current_reference(test_project, reference, destination)

    replay = replay_archived_reference(destination, tmp_path / "results/neblina_1/replay")
    replay_manifest = json.loads((replay / "manifest.json").read_text(encoding="utf-8"))
    assert replay_manifest["numerical_replay"]["status"] == "PASS_NUMERICAL_REPLAY"
    assert replay_manifest["numerical_replay"]["atmosphere_match"] is True
    assert replay_manifest["data_origin"] == "MODELED"
    assert pd.read_parquet(replay / "atmosphere_profile.parquet").equals(
        pd.read_parquet(destination / "atmosphere_profile.parquet")
    )


def test_replay_rejects_modified_archived_timeseries(tmp_path, monkeypatch):
    import hashlib

    source = tmp_path / "results/neblina_1/reference"
    source.mkdir(parents=True)
    (tmp_path / "projects/neblina_1").mkdir(parents=True)
    inputs = source / "inputs"
    inputs.mkdir()
    input_path = inputs / "config.yaml"
    input_path.write_text("same archived input\n", encoding="utf-8")
    (source / "manifest.json").write_text(json.dumps({
        "status": "REFERENCE_ONLY", "role": "CURRENT_REFERENCE",
        "configuration_hashes": {"config.yaml": hashlib.sha256(input_path.read_bytes()).hexdigest()},
        "output_hashes": {},
    }), encoding="utf-8")
    with pytest.raises(ValueError, match="fails its checksum"):
        replay_archived_reference(source, tmp_path / "results/neblina_1/replay")
    assert not (tmp_path / "results/neblina_1/replay").exists()
