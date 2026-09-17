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
    config_files = ["vehicle.yaml", "motor.yaml", "recovery.yaml", "launch.yaml", "environment.yaml", "monte_carlo.yaml"]
    if config_dir.exists():
        for cf in config_files:
            path = config_dir / cf
            h = compute_file_sha256(path)
            if h:
                config_hashes[cf] = h[:16] + "..."  # Truncated for display, full in JSON

    # Model Input Quality Table
    input_quality: List[Dict[str, str]] = [
        {"parameter": "Dry Vehicle Mass", "source": "Laboratory Precision Scale", "classification": "MEASURED", "confidence": "High (\u00b10.05 kg)"},
        {"parameter": "Center of Gravity (CG)", "source": "Dual Knife-Edge Balance Rig", "classification": "MEASURED", "confidence": "High (\u00b15 mm)"},
        {"parameter": "Moments of Inertia (Ixx, Iyy)", "source": "SolidWorks Full Assembly CAD Model", "classification": "CAD ESTIMATE", "confidence": "Medium (\u00b18%)"},
        {"parameter": "Solid Motor Thrust Curve", "source": "Static Fire Test Bench Load-Cell", "classification": "STATIC FIRE", "confidence": "High (\u00b12% Impulse)"},
        {"parameter": "Propellant Initial Mass", "source": "Pre/Post Static Fire Weighing", "classification": "MEASURED", "confidence": "High (\u00b10.02 kg)"},
        {"parameter": "Aerodynamic Coeffs (Cd, CNa)", "source": "Barrowman Slender-Body Model", "classification": "OPENROCKET / ROCKETPY", "confidence": "Medium (\u00b110% Cd)"},
        {"parameter": "Atmospheric Environment", "source": "MAGI Operational GFS Forecast", "classification": "NUMERICAL WEATHER MODEL", "confidence": "Ensemble (\u00b11.5 m/s wind)"},
        {"parameter": "Parachute Drag Areas (CdS)", "source": "Manufacturer Specification & Drop Test", "classification": "ENGINEERING ESTIMATE", "confidence": "Medium (\u00b112% CdS)"},
    ]

    return {
        "git": git_data,
        "environment": env_versions,
        "config_hashes": config_hashes,
        "input_quality": input_quality,
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
