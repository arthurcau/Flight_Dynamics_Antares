"""Solid motor construction with explicit validation of the thrust curve."""

from pathlib import Path

import numpy as np
from rocketpy import SolidMotor
from rocketpy.motors.motor import Motor

from antares_fd.config.exceptions import ConfigurationError


def _thrust_source(source, project_dir):
    if not isinstance(source, str):
        return source
    path = Path(project_dir) / source
    if not path.is_file():
        raise ConfigurationError(f"Motor thrust file not found: {path}")
    if path.suffix.lower() != ".eng":
        return str(path)

    # RocketPy inserts (0, 0) when reading RASP files. Some measured files
    # already contain that point. Remove only the redundant origin; preserve
    # every measured sample and never modify the source file.
    _, _, points = Motor.import_eng(str(path))
    points = np.asarray(points, dtype=float)
    if len(points) > 1 and np.array_equal(points[:2], [[0, 0], [0, 0]]):
        points = points[1:]
    if (len(points) < 2 or not np.isfinite(points).all()
            or np.any(np.diff(points[:, 0]) <= 0) or np.any(points[:, 1] < 0)):
        raise ConfigurationError(f"Invalid thrust curve in {path}: require finite, increasing times and nonnegative thrust.")
    return points


def build_motor(config, project_dir: Path):
    """Build a SolidMotor; reject missing data and non-finite mass/impulse."""
    if not config:
        raise ConfigurationError("motor configuration is missing. A motor.yaml file is required.")
    if config.get("type", "solid").lower() != "solid":
        raise ConfigurationError(f"Unsupported motor type: {config.get('type')}")
    required = (
        "thrust_source", "dry_mass", "dry_inertia",
        "center_of_dry_mass_position", "grains_center_of_mass_position",
        "grain_number", "grain_separation", "grain_density", "grain_outer_radius",
        "grain_initial_inner_radius", "grain_initial_height", "nozzle_radius", "throat_radius",
    )
    missing = [key for key in required if config.get(key) is None]
    if missing:
        raise ConfigurationError(f"Failed to build SolidMotor: required motor fields: {', '.join(missing)}")
    kwargs = {key: config[key] for key in required}
    if config.get("burn_time") is not None:
        kwargs["burn_time"] = config["burn_time"]
    for key in ("interpolation_method", "coordinate_system_orientation", "nozzle_position"):
        if key in config:
            kwargs[key] = config[key]
    try:
        kwargs["thrust_source"] = _thrust_source(config["thrust_source"], project_dir)
        motor = SolidMotor(**kwargs)
        times = np.unique(np.r_[motor.thrust.source[:, 0], motor.burn_time])
        values = np.r_[motor.total_impulse, motor.propellant_initial_mass,
                       motor.thrust(times), motor.propellant_mass(times),
                       motor.total_mass_flow_rate(times)]
        if not np.isfinite(values).all() or motor.total_impulse <= 0:
            raise ValueError("thrust, impulse and propellant mass/flow must be finite; impulse must be positive")
    except (TypeError, ValueError, IndexError) as exc:
        raise ConfigurationError(f"Failed to build SolidMotor: {exc}") from exc
    return motor
