"""Translate explicit numerical settings and execute a RocketPy flight."""

import numpy as np
from rocketpy import Flight

from antares_fd.config.exceptions import ConfigurationError


SOLVER_OPTIONS = {
    "rtol", "atol", "max_time", "max_time_step", "min_time_step",
    "time_overshoot", "terminate_on_apogee", "verbose", "name",
    "equations_of_motion", "ode_solver", "initial_solution", "simulation_mode",
}


def flight_options(simulation_config):
    """Return supported Flight keyword arguments; never ignore a misspelling."""
    config = dict(simulation_config or {})
    unknown = set(config) - SOLVER_OPTIONS
    if unknown:
        raise ConfigurationError(f"Unsupported simulation options: {sorted(unknown)}")
    for key in ("rtol", "atol", "max_time", "max_time_step", "min_time_step"):
        if key in config:
            values = np.asarray(config[key], dtype=float)
            lower_ok = values >= 0 if key == "min_time_step" else values > 0
            if not np.isfinite(values).all() or not lower_ok.all():
                raise ConfigurationError(f"simulation.{key} must be finite and {'nonnegative' if key == 'min_time_step' else 'positive'}")
    return config


def run_flight(rocket, environment, launch_config, simulation_config):
    """Execute with configured tolerances, preserving RocketPy's defaults otherwise."""
    if not launch_config:
        raise ConfigurationError("launch_config is required for Flight")
    rail = launch_config.get("rail", {})
    length = rail.get("length")
    if length is None or not np.isfinite(length) or length <= 0:
        raise ConfigurationError("launch.rail.length is required and must be positive")
    inclination, heading = rail.get("inclination_deg", 90.0), rail.get("heading_deg", 0.0)
    if inclination is None or not np.isfinite(inclination) or not 0 <= inclination <= 90:
        raise ConfigurationError("launch.rail.inclination_deg must be in [0, 90]")
    if heading is None or not np.isfinite(heading) or not 0 <= heading <= 360:
        raise ConfigurationError("launch.rail.heading_deg is required in [0, 360]")
    for key in ("base_clearance", "roll_angle_deg"):
        if rail.get(key, 0) != 0:
            raise ConfigurationError(f"Nonzero launch.rail.{key} is not implemented")
    for section, entries in launch_config.get("initial_conditions", {}).items():
        if any(value != 0 for value in entries.values()):
            raise ConfigurationError(f"Nonzero launch.initial_conditions.{section}: use simulation.initial_solution")
    ignition = launch_config.get("ignition", {})
    if ignition.get("time", 0) != 0 or ignition.get("ignition_delay", 0) != 0:
        raise ConfigurationError("Delayed ignition is not implemented in the launch builder")
    flight = Flight(rocket=rocket, environment=environment, rail_length=length,
                    inclination=inclination, heading=heading, **flight_options(simulation_config))
    if not np.isfinite(np.asarray(flight.solution, dtype=float)).all():
        raise RuntimeError("Flight integration produced non-finite state values")
    return flight
