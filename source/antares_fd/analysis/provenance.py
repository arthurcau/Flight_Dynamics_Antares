"""
Provenance, Traceability, Model Quality & Validity Analysis.

Gathers deterministic reproducibility metadata:
- Git repository state (commit, branch, dirty flag)
- Python environment & dependency versions
- Cryptographic SHA-256 hashes of configuration and propulsion files
- Model input source quality classification (Measured vs Estimated)
- Model validity envelope checks
"""

import hashlib
import importlib.metadata
import platform
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:  # pragma: no cover - project configuration requires PyYAML
    yaml = None

from antares_fd.analysis.flight_metrics import FlightMetrics


def compute_file_sha256(filepath: Path) -> Optional[str]:
    """Computes SHA-256 hash of a file if it exists."""
    if not filepath.exists() or not filepath.is_file():
        return None
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def get_git_provenance(repo_dir: Path) -> Dict[str, str]:
    """Extracts git commit, branch, and dirty status."""
    provenance = {
        "commit": "unknown",
        "branch": "unknown",
        "dirty": "unknown",
    }
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(repo_dir),
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(repo_dir),
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        status = subprocess.check_output(
            ["git", "status", "--porcelain"],
            cwd=str(repo_dir),
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        provenance["commit"] = commit
        provenance["branch"] = branch
        provenance["dirty"] = "dirty" if len(status) > 0 else "clean"
    except Exception:
        pass
    return provenance


def _get_package_version(pkg_name: str) -> str:
    """Safely retrieves a package version."""
    try:
        return importlib.metadata.version(pkg_name)
    except Exception:
        try:
            mod = __import__(pkg_name)
            return getattr(mod, "__version__", "unknown")
        except Exception:
            return "unknown"


def _read_yaml(path: Path) -> Dict[str, Any]:
    """Read configuration metadata without inventing missing evidence."""
    if yaml is None or not path.exists():
        return {}
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return {}
    return value if isinstance(value, dict) else {}


def _value_at(data: Dict[str, Any], *keys: str) -> Any:
    value: Any = data
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def _display_value(value: Any) -> str:
    if value is None or value == "":
        return "NOT PROVIDED"
    return str(value)


def _repo_relative(path: Path, project_dir: Path, project_root: Path) -> str:
    """Return a stable path suitable for a report."""
    for base in (project_root, project_dir):
        try:
            return path.resolve().relative_to(base.resolve()).as_posix()
        except ValueError:
            continue
    return path.name


def _provenance_record(parameter: str, value: Any, unit: str, *, source: Any = None,
                       source_type: Any = None, reference: Any = None,
                       revision: Any = None, method: Any = None,
                       uncertainty: Any = None, semantics: Any = None,
                       confidence: Any = None, notes: Any = None) -> Dict[str, str]:
    """Build a row using only explicitly configured provenance."""
    return {
        "parameter": parameter,
        "nominal": _display_value(value),
        "unit": unit,
        "source": _display_value(source),
        "classification": _display_value(source_type).upper() if source_type else "UNKNOWN",
        "reference": _display_value(reference),
        "revision": _display_value(revision),
        "method": _display_value(method),
        "uncertainty": _display_value(uncertainty),
        "uncertainty_semantics": _display_value(semantics),
        "confidence": _display_value(confidence),
        "notes": _display_value(notes),
    }


def _config_input_quality(project_dir: Path, project_root: Path) -> List[Dict[str, str]]:
    """Extract model-input evidence from the project's YAML files."""
    config_dir = project_dir / "config"
    vehicle = _read_yaml(config_dir / "vehicle.yaml")
    motor = _read_yaml(config_dir / "motor.yaml")
    launch = _read_yaml(config_dir / "launch.yaml")
    environment = _read_yaml(config_dir / "environment.yaml")
    recovery = _read_yaml(config_dir / "recovery.yaml")
    vehicle_data = vehicle.get("vehicle", {})
    mass = vehicle_data.get("mass_properties", {})
    vehicle_prov = vehicle_data.get("provenance", {})
    revision = vehicle_data.get("revision")
    rows = [
        _provenance_record("Dry vehicle mass", mass.get("mass_without_motor"), "kg",
                           source=_value_at(vehicle_prov, "mass", "source"),
                           source_type=mass.get("method") or _value_at(vehicle_prov, "mass", "type"),
                           reference=_value_at(vehicle_prov, "mass", "reference"),
                           revision=revision, method=mass.get("method"),
                           semantics="No uncertainty configured; instrument resolution is not inferred as uncertainty."),
        _provenance_record("Center of mass", mass.get("center_of_mass_without_motor"), "m",
                           source=_value_at(vehicle_prov, "center_of_mass", "source"),
                           source_type=_value_at(vehicle_prov, "center_of_mass", "type"),
                           reference=_value_at(vehicle_prov, "center_of_mass", "reference"),
                           revision=revision, semantics="No uncertainty configured."),
    ]
    inertia = mass.get("inertia", {})
    for key in ("I11", "I22", "I33"):
        rows.append(_provenance_record(
            f"Inertia {key}", inertia.get(key), "kg m^2",
            source=inertia.get("source") or _value_at(vehicle_prov, "inertia", "source"),
            source_type=_value_at(vehicle_prov, "inertia", "type"),
            reference=inertia.get("reference") or _value_at(vehicle_prov, "inertia", "reference"),
            revision=revision, semantics="No uncertainty configured."))

    motor_data = motor.get("motor", {})
    thrust_source = motor_data.get("thrust_source")
    thrust_path = None
    if thrust_source:
        configured_path = project_dir / str(thrust_source)
        thrust_path = configured_path if configured_path.exists() else config_dir / str(thrust_source)
    rows.append(_provenance_record(
        "Motor thrust curve", thrust_source, "N vs s",
        source=_repo_relative(thrust_path, project_dir, project_root) if thrust_path else None,
        source_type="CONFIGURED FILE" if thrust_source else None,
        revision=motor_data.get("revision"),
        semantics="No thrust uncertainty configured in motor.yaml."))

    drag = vehicle_data.get("drag", {})
    for mode in ("power_on", "power_off"):
        model = drag.get(mode, {})
        source_file = model.get("file")
        source_path = None
        if source_file:
            configured_path = project_dir / str(source_file)
            source_path = configured_path if configured_path.exists() else config_dir / str(source_file)
        rows.append(_provenance_record(
            f"{mode.replace('_', ' ').title()} drag coefficient",
            source_file or model.get("constant"), "dimensionless / Mach curve",
            source=_repo_relative(source_path, project_dir, project_root) if source_path else model.get("source"),
            source_type=model.get("source_type"), revision=revision,
            method=model.get("interpolation"),
            semantics="No coefficient uncertainty configured in vehicle.yaml."))

    launch_data = launch.get("launch", {})
    site = launch_data.get("site", {})
    launch_prov = launch_data.get("provenance", {})
    rows.extend([
        _provenance_record("Launch coordinates", f"{site.get('latitude')}, {site.get('longitude')}", "deg",
                           source=_value_at(launch_prov, "coordinates", "source"),
                           source_type=_value_at(launch_prov, "coordinates", "type"),
                           reference=_value_at(launch_prov, "coordinates", "reference"),
                           revision=launch_data.get("revision")),
        _provenance_record("Site elevation", site.get("elevation"), "m",
                           source=_value_at(launch_prov, "elevation", "source"),
                           source_type=_value_at(launch_prov, "elevation", "type"),
                           reference=_value_at(launch_prov, "elevation", "reference"),
                           revision=launch_data.get("revision"),
                           semantics="No elevation uncertainty configured in launch.yaml."),
    ])

    environment_data = environment.get("environment", {})
    rows.append(_provenance_record(
        "Atmospheric environment", environment_data.get("type"), "profile",
        source=environment_data.get("source") or environment_data.get("provider"),
        source_type="CONFIGURED ENVIRONMENT TYPE" if environment_data.get("type") else None,
        reference=environment_data.get("forecast_initialization") or environment_data.get("valid_time"),
        semantics="No uncertainty is inferred from the environment type; profile/member provenance is required."))

    for device in recovery.get("recovery", {}).get("devices", []):
        if not isinstance(device, dict):
            continue
        aero = device.get("aerodynamics", {})
        device_prov = device.get("provenance", {})
        cd_prov = device_prov.get("cd_s", {}) if isinstance(device_prov.get("cd_s"), dict) else {}
        rows.append(_provenance_record(
            f"Recovery {device.get('id', 'device')} CdS", aero.get("cd_s"), "m^2",
            source=cd_prov.get("source"), source_type=cd_prov.get("type"),
            reference=cd_prov.get("reference"), revision=recovery.get("recovery", {}).get("revision"),
            semantics="No recovery uncertainty configured in recovery.yaml."))
    return rows


def collect_reproducibility_data(project_dir: Path) -> Dict[str, Any]:
    """
    Collects complete provenance, config hashes, input quality, and validity data.
    """
    project_root = project_dir.resolve().parents[1] if project_dir.name in ["neblina_1", "projects"] else project_dir
    git_data = get_git_provenance(project_root)

    # Software versions
    env_versions = {
        "python_version": platform.python_version(),
        "rocketpy_version": _get_package_version("rocketpy"),
        "reportlab_version": _get_package_version("reportlab"),
        "matplotlib_version": _get_package_version("matplotlib"),
        "os_platform": f"{platform.system()} {platform.release()}",
    }

    # Configuration SHA-256 hashes
    config_dir = project_dir / "config"
    config_hashes: Dict[str, str] = {}
    config_files = ["vehicle.yaml", "motor.yaml", "recovery.yaml", "launch.yaml", "environment.yaml", "monte_carlo.yaml", "uncertainties.yaml"]
    if config_dir.exists():
        for cf in config_files:
            path = config_dir / cf
            h = compute_file_sha256(path)
            if h:
                config_hashes[cf] = h

    data_hashes: Dict[str, str] = {}
    vehicle_data = _read_yaml(config_dir / "vehicle.yaml").get("vehicle", {})
    motor_data = _read_yaml(config_dir / "motor.yaml").get("motor", {})
    referenced_files = {
        "motor_data": motor_data.get("thrust_source"),
        "aero_power_on": _value_at(vehicle_data, "drag", "power_on", "file"),
        "aero_power_off": _value_at(vehicle_data, "drag", "power_off", "file"),
    }
    for label, relative_file in referenced_files.items():
        if not relative_file:
            continue
        configured_path = project_dir / str(relative_file)
        data_path = configured_path if configured_path.exists() else config_dir / str(relative_file)
        digest = compute_file_sha256(data_path)
        if digest:
            data_hashes[_repo_relative(data_path, project_dir, project_root)] = digest

    input_quality = _config_input_quality(project_dir, project_root)

    return {
        "git": git_data,
        "environment": env_versions,
        "config_hashes": config_hashes,
        "data_hashes": data_hashes,
        "input_quality": input_quality,
        "provenance_status": "CONFIGURED_METADATA_ONLY",
    }


def evaluate_model_validity(metrics: FlightMetrics) -> List[Dict[str, str]]:
    """
    Evaluates simulation metrics against physics and aerodynamic model limits.
    """
    if isinstance(metrics, dict):
        max_mach = metrics.get("kinematics", {}).get("max_mach", 0.0)
        max_alpha = metrics.get("aerodynamic_loads", {}).get("max_angle_of_attack_ascent_deg", 0.0)
        apogee_asl = metrics.get("trajectory", {}).get("apogee_asl_m", 0.0)
        v_rail = metrics.get("rail_dynamics", {}).get("rail_exit_velocity_ms", 0.0)
    else:
        max_mach = metrics.max_mach
        max_alpha = metrics.max_angle_of_attack
        apogee_asl = metrics.apogee_asl
        v_rail = metrics.rail_exit_velocity

    validity_checks = [
        {
            "domain": "Aerodynamics",
            "parameter": "Flight Mach Number",
            "simulated": f"{max_mach:.2f} M",
            "validity_limit": "\u2264 0.80 M (Subsonic)",
            "status": "QUALIFIED" if max_mach <= 0.80 else "OUT OF NOMINAL RANGE",
            "note": "Slender-body linear Barrowman equations valid without transonic wave drag corrections.",
        },
        {
            "domain": "Aerodynamics",
            "parameter": "Ascent Angle of Attack",
            "simulated": f"{max_alpha:.2f}\u00b0",
            "validity_limit": "\u2264 10.0\u00b0 (Linear Lift)",
            "status": "QUALIFIED" if max_alpha <= 10.0 else "NON-LINEAR REGIME",
            "note": "Linear normal force slope CNa assumes attached flow without crossflow separation.",
        },
        {
            "domain": "Atmosphere",
            "parameter": "Apogee Altitude ASL",
            "simulated": f"{apogee_asl:.0f} m",
            "validity_limit": "\u2264 30,000 m (GFS Grid)",
            "status": "QUALIFIED" if apogee_asl <= 30000 else "EXCEEDS MODEL CEILING",
            "note": "MAGI weather profile covers entire trajectory domain from ground pad to apogee.",
        },
        {
            "domain": "Launch Dynamics",
            "parameter": "Rail Guide Clearance",
            "simulated": f"{v_rail:.1f} m/s",
            "validity_limit": "\u2265 25.0 m/s",
            "status": "QUALIFIED" if v_rail >= 25.0 else "UNSTABLE CLEARANCE",
            "note": "Rail button release dynamics assume rigid tower alignment and aerodynamic stability.",
        },
    ]
    return validity_checks
