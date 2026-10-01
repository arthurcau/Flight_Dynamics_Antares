"""Archive a current RocketPy model run without claiming preflight validation."""

from __future__ import annotations

import dataclasses
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import shutil
import tempfile
import time
from datetime import datetime, timezone
from typing import Any

import numpy as np
import pandas as pd

from antares_fd.config import load_project_config
from antares_fd.config.input_files import collect_project_model_inputs
from antares_fd.analysis.metrics import extract_flight_metrics
from antares_fd.analysis.provenance import get_git_provenance
from antares_fd.simulation.orchestrator import execute_scenario
from antares_fd.simulation.uq_storage import write_json_atomic, write_parquet_atomic

from .models import ModelVariant


PROCESSING_VERSION = "current-model-reference-v3"
# Backward-compatible name retained for callers of the original reference API.
collect_reference_inputs = collect_project_model_inputs


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _snapshot_inputs(project_dir: Path, snapshot_dir: Path) -> dict[str, str]:
    """Copy inputs once; reject concurrent edits while preparing the snapshot."""
    hashes: dict[str, str] = {}
    for source in collect_project_model_inputs(project_dir):
        relative = source.relative_to(project_dir)
        before = _sha256(source)
        target = snapshot_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        after = _sha256(source)
        copied = _sha256(target)
        if before != after or copied != before:
            raise RuntimeError(f"Model input changed during snapshot: {relative}")
        hashes[relative.as_posix()] = copied
    return hashes


def _timeseries_frame(metrics: Any) -> pd.DataFrame:
    series = metrics.timeseries
    names = {
        "time_s": "time", "altitude_agl_m": "altitude_agl",
        "altitude_asl_m": "altitude_asl", "vertical_velocity_mps": "velocity_z",
        "vertical_acceleration_mps2": "acceleration_z",
        "dynamic_pressure_pa": "dynamic_pressure", "mach": "mach",
        "thrust_n": "thrust", "mass_kg": "mass",
    }
    frame = pd.DataFrame({name: np.asarray(getattr(series, attr), dtype=float) for name, attr in names.items()})
    if not np.isfinite(frame.to_numpy()).all() or np.any(np.diff(frame["time_s"]) <= 0):
        raise ValueError("RocketPy reference timeseries contains non-finite or non-increasing values")
    return frame


def _atmosphere_frame(flight: Any) -> pd.DataFrame:
    """Read the full interpolated MAGI grid directly, with no synthetic fallback."""
    env = flight.env
    provenance = getattr(env, "antares_atmosphere", None)
    if not isinstance(provenance, dict) or provenance.get("source_type") == "standard_atmosphere":
        raise ValueError("Current reference requires a non-fallback MAGI atmospheric profile")
    grid_source = getattr(getattr(env.pressure, "source", None), "altitude", None)
    if grid_source is None:
        raise ValueError("MAGI pressure grid is unavailable for archival")
    altitude = np.asarray(grid_source, dtype=float)
    if altitude.ndim != 1 or len(altitude) < 2 or np.any(np.diff(altitude) <= 0):
        raise ValueError("MAGI altitude grid is invalid")
    columns = {
        "altitude_asl_m": altitude,
        "pressure_pa": np.asarray(env.pressure(altitude), dtype=float),
        "temperature_k": np.asarray(env.temperature(altitude), dtype=float),
        "density_kg_m3": np.asarray(env.density(altitude), dtype=float),
        "wind_east_mps": np.asarray(env.wind_velocity_x(altitude), dtype=float),
        "wind_north_mps": np.asarray(env.wind_velocity_y(altitude), dtype=float),
        "speed_of_sound_mps": np.asarray(env.speed_of_sound(altitude), dtype=float),
        "dynamic_viscosity_pa_s": np.asarray(env.dynamic_viscosity(altitude), dtype=float),
    }
    humidity = getattr(env, "antares_specific_humidity_kg_kg", None)
    if humidity is not None:
        columns["specific_humidity_kg_kg"] = np.asarray(humidity, dtype=float)
    frame = pd.DataFrame(columns)
    if not np.isfinite(frame.to_numpy()).all():
        raise ValueError("MAGI atmosphere contains non-finite values")
    return frame


def _plain(value: Any) -> Any:
    if dataclasses.is_dataclass(value):
        return {field.name: _plain(getattr(value, field.name)) for field in dataclasses.fields(value)}
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    if isinstance(value, np.ndarray):
        return _plain(value.tolist())
    if isinstance(value, np.generic):
        return _plain(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("Model artifact contains a non-finite scalar")
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if hasattr(value, "isoformat"):
        return value.isoformat()
    raise TypeError(f"Cannot serialize model provenance value of type {type(value).__name__}")


def _git_metadata(root: Path) -> dict[str, Any]:
    return get_git_provenance(root)


def _results_output_path(project_dir: Path, output_dir: Path) -> Path:
    project_root = project_dir.parents[1]
    results_root = project_root / "results"
    if results_root.is_symlink():
        raise ValueError("Reference artifacts require a non-symlink repository results/ directory")
    output_dir = Path(output_dir)
    if not output_dir.is_absolute():
        output_dir = project_root / output_dir
    output_dir = output_dir.resolve()
    if output_dir == results_root.resolve() or not output_dir.is_relative_to(results_root.resolve()):
        raise ValueError("Reference artifacts must be written below the repository results/ directory")
    if output_dir.exists():
        raise FileExistsError(f"Reference output already exists: {output_dir}")
    return output_dir


def _archived_environment(config: Any, atmosphere: pd.DataFrame, provenance: dict[str, Any]) -> Any:
    """Rebuild archived MAGI inputs through the same RocketPy profile builder."""
    from antares_fd.builders.environment import _apply_profile, _base_environment
    from antares_fd.environment.atmosphere import AtmosphericProfile

    required = (
        "altitude_asl_m", "pressure_pa", "temperature_k", "density_kg_m3",
        "wind_east_mps", "wind_north_mps", "speed_of_sound_mps", "dynamic_viscosity_pa_s",
    )
    if any(name not in atmosphere for name in required):
        raise ValueError("Archived atmosphere lacks one or more required physical fields")
    z = atmosphere["altitude_asl_m"].to_numpy(dtype=float)
    if len(z) < 2 or not np.isfinite(atmosphere[list(required)].to_numpy(dtype=float)).all():
        raise ValueError("Archived atmosphere contains too few or non-finite values")
    if np.any(np.diff(z) <= 0):
        raise ValueError("Archived atmosphere altitude must increase strictly")
    if z[0] > float(config.launch["site"]["elevation"]):
        raise ValueError("Archived atmosphere does not cover launch elevation")

    humidity = None
    if "specific_humidity_kg_kg" in atmosphere:
        humidity = atmosphere["specific_humidity_kg_kg"].to_numpy(dtype=float)
    density_model = provenance.get("density_model")
    if humidity is None and density_model != "ideal_dry_air":
        # Historical moist-air archives did not save humidity. Preserve their
        # sampled derived curves, but mark this replay as approximate.
        from rocketpy import Function

        from antares_fd.builders.environment import ProfileVariable

        env = _base_environment(config.launch)
        arrays = {
            "pressure": np.column_stack((z, atmosphere["pressure_pa"].to_numpy(dtype=float))),
            "temperature": np.column_stack((z, atmosphere["temperature_k"].to_numpy(dtype=float))),
            "wind_u": np.column_stack((z, atmosphere["wind_east_mps"].to_numpy(dtype=float))),
            "wind_v": np.column_stack((z, atmosphere["wind_north_mps"].to_numpy(dtype=float))),
        }
        env.set_atmospheric_model(type="custom_atmosphere", **arrays)
        for attribute, column in (
            ("pressure", "pressure_pa"), ("temperature", "temperature_k"),
            ("density", "density_kg_m3"), ("wind_velocity_x", "wind_east_mps"),
            ("wind_velocity_y", "wind_north_mps"), ("speed_of_sound", "speed_of_sound_mps"),
            ("dynamic_viscosity", "dynamic_viscosity_pa_s"),
        ):
            env_function = Function(
                ProfileVariable(z.copy(), atmosphere[column].to_numpy(dtype=float).copy()),
                inputs="Height ASL (m)",
            )
            setattr(env, attribute, env_function)
        env.max_expected_height = float(z[-1])
        env.antares_atmosphere = dict(provenance)
        env.antares_replay_method = (
            "LEGACY_MOIST_PROFILE_APPROXIMATION"
            if density_model == "ideal_moist_air"
            else "DERIVED_PROFILE_RECONSTRUCTION_UNVERIFIED"
        )
        return env

    valid_time = provenance.get("valid_time_utc")
    if isinstance(valid_time, str):
        valid_time = datetime.fromisoformat(valid_time.replace("Z", "+00:00"))
    run_time = provenance.get("run_time_utc")
    if isinstance(run_time, str):
        run_time = None if run_time in {"", "None", "unknown"} else datetime.fromisoformat(run_time.replace("Z", "+00:00"))
    reserved_metadata = {
        "source", "source_type", "model", "valid_time_utc", "run_time_utc", "member_id",
        "altitude_bounds_asl_m", "density_model", "sound_speed_model",
    }
    profile = AtmosphericProfile(
        altitude_asl_m=z.copy(),
        pressure_pa=atmosphere["pressure_pa"].to_numpy(dtype=float),
        temperature_k=atmosphere["temperature_k"].to_numpy(dtype=float),
        wind_u_mps=atmosphere["wind_east_mps"].to_numpy(dtype=float),
        wind_v_mps=atmosphere["wind_north_mps"].to_numpy(dtype=float),
        source=str(provenance.get("source", "UNKNOWN")),
        source_type=str(provenance.get("source_type", "UNKNOWN")),
        model=provenance.get("model"),
        run_time_utc=run_time,
        valid_time_utc=valid_time or datetime.fromtimestamp(0, timezone.utc),
        latitude_deg=float(config.launch["site"]["latitude"]),
        longitude_deg=float(config.launch["site"]["longitude"]),
        member_id=provenance.get("member_id"),
        specific_humidity_kg_kg=humidity,
        metadata={key: value for key, value in provenance.items() if key not in reserved_metadata},
    )
    env = _apply_profile(_base_environment(config.launch), profile)
    env.antares_replay_method = "MAGI_INPUT_PROFILE_REBUILT"
    return env


def _execute_reference_products(
    project_dir: Path,
    variant: ModelVariant,
    stage: Path,
    snapshot: Path,
    input_hashes: dict[str, str],
    *,
    environment: Any | None = None,
) -> tuple[dict[str, Any], Any]:
    config = load_project_config(snapshot)
    if str(config.environment.get("type", "")).lower() != "magi" or config.environment.get("fallback", {}).get("enabled"):
        raise ValueError("Current reference requires configured MAGI with fallback disabled")
    simulation_started = time.perf_counter()
    flight = execute_scenario(
        config, snapshot, print_summary=False, export_kml=False, environment=environment,
    )
    simulation_wall_seconds = time.perf_counter() - simulation_started
    metrics = extract_flight_metrics(flight, config=config, project_dir=project_dir)
    series = _timeseries_frame(metrics)
    atmosphere = _atmosphere_frame(flight)
    write_parquet_atomic(series, stage / "simulated_timeseries.parquet")
    write_parquet_atomic(atmosphere, stage / "atmosphere_profile.parquet")
    scalar_metrics = {
        field.name: _plain(getattr(metrics, field.name))
        for field in dataclasses.fields(metrics)
        if field.name not in {"timeseries", "atmosphere", "validation"}
    }
    write_json_atomic(scalar_metrics, stage / "flight_metrics.json")
    try:
        rocketpy_version = importlib.metadata.version("rocketpy")
    except importlib.metadata.PackageNotFoundError:
        rocketpy_version = "unknown"
    manifest = {
        "schema_version": 1,
        "variant_id": variant.id,
        "role": variant.role,
        "status": "REFERENCE_ONLY",
        "data_origin": "MODELED",
        "validation_status": "NOT_YET_VALIDATED",
        "source_telemetry_sha256": None,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "processing_version": PROCESSING_VERSION,
        "methodology_version": "explicit-model-variants-with-magi-replay-inputs-v2",
        "git": _git_metadata(project_dir.parents[1]),
        "software_versions": {"python": platform.python_version(), "rocketpy": rocketpy_version},
        "configuration_hashes": input_hashes,
        "runtime": {"rocketpy_simulation_wall_seconds": simulation_wall_seconds},
        "atmosphere_provenance": _plain(flight.env.antares_atmosphere),
        "excluded_metric": {"validation": "No measured landing coordinates with provenance are available for comparison"},
        "output_hashes": {
            name: _sha256(stage / name)
            for name in ("simulated_timeseries.parquet", "atmosphere_profile.parquet", "flight_metrics.json")
        },
    }
    write_json_atomic(manifest, stage / "manifest.json")
    return manifest, flight


def run_current_reference(project_dir: Path, variant: ModelVariant, output_dir: Path) -> Path:
    """Run a labeled current-model reference from copied inputs.

    This is a model execution, not comparison to flight evidence. The call
    refuses to publish a partial output and never falls back to standard air.
    """
    if variant.role != "CURRENT_REFERENCE" or variant.status != "REFERENCE_ONLY" or not variant.runnable:
        raise ValueError("Only a runnable CURRENT_REFERENCE variant may use this exporter")
    if variant.configuration != "project_current_yaml":
        raise ValueError("Unsupported current-reference configuration source")
    project_dir = Path(project_dir).resolve()
    output_dir = _results_output_path(project_dir, output_dir)
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.", dir=output_dir.parent))
    try:
        snapshot = stage / "inputs"
        input_hashes = _snapshot_inputs(project_dir, snapshot)
        _execute_reference_products(project_dir, variant, stage, snapshot, input_hashes)
        os.replace(stage, output_dir)
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return output_dir


def _compare_reference_timeseries(
    original: pd.DataFrame,
    replay: pd.DataFrame,
    *,
    rtol: float,
    atol: float,
) -> dict[str, Any]:
    """Compare states at common physical times, without extrapolation."""
    if list(original.columns) != list(replay.columns) or "time_s" not in original:
        return {
            "matches": False,
            "reason": "trajectory schemas differ",
            "common_time_samples": 0,
            "channels": {},
        }
    source_time = original["time_s"].to_numpy(dtype=float)
    replay_time = replay["time_s"].to_numpy(dtype=float)
    in_common_domain = (source_time >= replay_time[0]) & (source_time <= replay_time[-1])
    common_time = source_time[in_common_domain]
    if not len(common_time):
        return {
            "matches": False,
            "reason": "trajectories have no common sampled time",
            "common_time_samples": 0,
            "channels": {},
        }

    channels: dict[str, dict[str, Any]] = {}
    all_differences: list[np.ndarray] = []
    matches = True
    for column in original.columns:
        if column == "time_s":
            continue
        expected = original[column].to_numpy(dtype=float)[in_common_domain]
        observed = np.interp(common_time, replay_time, replay[column].to_numpy(dtype=float))
        difference = np.abs(expected - observed)
        if not np.isfinite(difference).all():
            matches = False
            channels[column] = {"status": "NONFINITE_COMPARISON"}
            continue
        maximum_index = int(np.argmax(difference))
        channels[column] = {
            "sample_count": int(len(difference)),
            "maximum_absolute_difference": float(difference[maximum_index]),
            "maximum_difference_time_s": float(common_time[maximum_index]),
            "root_mean_square_difference": float(np.sqrt(np.mean(difference**2))),
            "maximum_difference_reference_value": float(expected[maximum_index]),
            "maximum_difference_replay_value": float(observed[maximum_index]),
        }
        all_differences.append(difference)
        matches = matches and bool(np.all(difference <= atol + rtol * np.abs(expected)))

    flattened = np.concatenate(all_differences) if all_differences else np.array([], dtype=float)
    if len(flattened):
        global_index = int(np.argmax(flattened))
        channel_counts = [len(item) for item in all_differences]
        channel_offsets = np.cumsum([0, *channel_counts])
        channel_index = int(np.searchsorted(channel_offsets[1:], global_index, side="right"))
        channel_name = [name for name in channels if "maximum_absolute_difference" in channels[name]][channel_index]
        sample_index = global_index - int(channel_offsets[channel_index])
        max_difference_time = float(common_time[sample_index])
        maximum_difference = float(flattened[global_index])
    else:
        channel_name = None
        max_difference_time = None
        maximum_difference = None
    return {
        "matches": bool(matches),
        "reason": None,
        "alignment": "linear interpolation of replay states onto source times within shared time domain; no extrapolation",
        "common_time_samples": int(len(common_time)),
        "common_time_bounds_s": [float(common_time[0]), float(common_time[-1])],
        "source_time_samples_outside_common_domain": int((~in_common_domain).sum()),
        "index_paired_time_maximum_difference_s": float(
            np.max(np.abs(source_time[:min(len(source_time), len(replay_time))] - replay_time[:min(len(source_time), len(replay_time))]))
        ),
        "maximum_absolute_difference": maximum_difference,
        "maximum_difference_channel": channel_name,
        "maximum_difference_time_s": max_difference_time,
        "channels": channels,
    }


def replay_archived_reference(archive_dir: Path, output_dir: Path) -> Path:
    """Repeat a current-model run with the exact archived input and MAGI tables."""
    archive_dir = Path(archive_dir).resolve()
    archive_manifest_path = archive_dir / "manifest.json"
    manifest = json.loads(archive_manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status") != "REFERENCE_ONLY" or manifest.get("role") != "CURRENT_REFERENCE":
        raise ValueError("Archived source is not a CURRENT_REFERENCE artifact")
    project_root = archive_dir.parents[2]
    project_dir = project_root / "projects" / "neblina_1"
    if not project_dir.is_dir():
        raise ValueError("Cannot locate the project checkout associated with this archive")
    output_dir = _results_output_path(project_dir, output_dir)
    input_dir = archive_dir / "inputs"
    expected_hashes = manifest.get("configuration_hashes", {})
    if not expected_hashes:
        raise ValueError("Archive contains no frozen model input hashes")
    for relative, expected in expected_hashes.items():
        source = (input_dir / relative).resolve()
        if not source.is_relative_to(input_dir.resolve()) or not source.is_file() or _sha256(source) != expected:
            raise ValueError(f"Archived model input is missing or changed: {relative}")
    expected_outputs = manifest.get("output_hashes", {})
    required_outputs = (
        "simulated_timeseries.parquet", "atmosphere_profile.parquet", "flight_metrics.json",
    )
    for name in required_outputs:
        artifact_path = archive_dir / name
        if not artifact_path.is_file() or _sha256(artifact_path) != expected_outputs.get(name):
            raise ValueError(f"Archived reference artifact is missing or fails its checksum: {name}")
    profile_path = archive_dir / "atmosphere_profile.parquet"
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.", dir=output_dir.parent))
    try:
        snapshot = stage / "inputs"
        shutil.copytree(input_dir, snapshot)
        atmosphere = pd.read_parquet(profile_path)
        config = load_project_config(snapshot)
        archived_environment = _archived_environment(
            config, atmosphere, manifest["atmosphere_provenance"],
        )
        input_hashes = {
            relative: _sha256(snapshot / relative) for relative in expected_hashes
        }
        if input_hashes != expected_hashes:
            raise ValueError("Copied model inputs do not match the original reference manifest")
        variant = ModelVariant(
            id=str(manifest["variant_id"]), role="CURRENT_REFERENCE", status="REFERENCE_ONLY",
            runnable=True, configuration="project_current_yaml", evidence=(),
            missing_evidence=(), identified_changes=(),
        )
        replay_manifest, _ = _execute_reference_products(
            project_dir, variant, stage, snapshot, input_hashes,
            environment=archived_environment,
        )
        original_series = pd.read_parquet(archive_dir / "simulated_timeseries.parquet")
        replay_series = pd.read_parquet(stage / "simulated_timeseries.parquet")
        series_comparison = _compare_reference_timeseries(
            original_series, replay_series, rtol=1e-9, atol=1e-9,
        )
        series_match = bool(series_comparison["matches"])
        original_atmosphere = pd.read_parquet(profile_path)
        replay_atmosphere = pd.read_parquet(stage / "atmosphere_profile.parquet")
        atmosphere_match = (
            list(original_atmosphere.columns) == list(replay_atmosphere.columns)
            and original_atmosphere.shape == replay_atmosphere.shape
            and np.allclose(original_atmosphere.to_numpy(), replay_atmosphere.to_numpy(), rtol=1e-9, atol=1e-9)
        )
        original_metrics = json.loads((archive_dir / "flight_metrics.json").read_text(encoding="utf-8"))
        replay_metrics = json.loads((stage / "flight_metrics.json").read_text(encoding="utf-8"))
        metric_differences = {}
        metrics_match = original_metrics.keys() == replay_metrics.keys()
        for key in original_metrics.keys() & replay_metrics.keys():
            left, right = original_metrics[key], replay_metrics[key]
            if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                metric_differences[key] = float(right - left)
                metrics_match = metrics_match and bool(np.isclose(left, right, rtol=1e-9, atol=1e-9))
            else:
                metrics_match = metrics_match and left == right
        source_code_snapshot = manifest.get("git", {}).get("working_tree_snapshot_sha256")
        replay_code_snapshot = replay_manifest.get("git", {}).get("working_tree_snapshot_sha256")
        if not source_code_snapshot or not replay_code_snapshot:
            code_provenance_status = "SOURCE_CODE_SNAPSHOT_UNAVAILABLE"
            code_snapshot_match = None
        else:
            code_snapshot_match = source_code_snapshot == replay_code_snapshot
            code_provenance_status = "MATCH" if code_snapshot_match else "MISMATCH"
        comparison = {
            "status": "PASS_NUMERICAL_REPLAY" if series_match and atmosphere_match and metrics_match else "NUMERICAL_REPLAY_MISMATCH",
            "code_provenance_status": code_provenance_status,
            "code_snapshot_match": code_snapshot_match,
            "timeseries_match": bool(series_match),
            "timeseries_comparison": series_comparison,
            "atmosphere_match": bool(atmosphere_match),
            "scalar_metrics_match": bool(metrics_match),
            "timeseries_max_absolute_difference": series_comparison["maximum_absolute_difference"],
            "atmosphere_max_absolute_difference": (
                float(np.max(np.abs(original_atmosphere.to_numpy() - replay_atmosphere.to_numpy())))
                if original_atmosphere.shape == replay_atmosphere.shape and original_atmosphere.size else None
            ),
            "scalar_metric_differences": metric_differences,
            "tolerance": {"rtol": 1e-9, "atol": 1e-9},
            "comparison_source": str(archive_dir.name),
            "data_origin": "MODELED",
            "environment_replay_method": getattr(archived_environment, "antares_replay_method", "UNKNOWN"),
        }
        write_json_atomic(comparison, stage / "replay_comparison.json")
        replay_manifest["numerical_replay"] = comparison
        replay_manifest["replay_of_manifest_sha256"] = _sha256(archive_manifest_path)
        replay_manifest["output_hashes"]["replay_comparison.json"] = _sha256(stage / "replay_comparison.json")
        write_json_atomic(replay_manifest, stage / "manifest.json")
        os.replace(stage, output_dir)
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return output_dir
