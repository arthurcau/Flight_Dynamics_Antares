"""Translate configured launch-angle distributions to RocketPy arguments."""

from math import isfinite

from antares_fd.config.exceptions import ConfigurationError


def launch_angle_distribution(nominal, settings, name):
    settings = settings or {}
    distribution = settings.get("distribution", "normal")
    if distribution == "uniform":
        lower, upper = settings.get("min"), settings.get("max")
        limit = 90 if name == "inclination" else 360
        if (not all(isinstance(v, (int, float)) and isfinite(v)
                    for v in (lower, upper)) or not 0 <= lower < upper <= limit):
            raise ConfigurationError(
                f"flight.{name}: uniform distribution requires 0 <= min < max <= {limit}.")
        if "std" in settings:
            raise ConfigurationError(f"flight.{name}: use min/max, not std, for uniform.")
        # RocketPy calls the numpy sampler with these two positional arguments;
        # numpy.uniform takes (low, high), unlike normal's (mean, std).
        return (lower, upper, "uniform")
    if distribution != "normal" or "min" in settings or "max" in settings:
        raise ConfigurationError(f"flight.{name}: specify distribution: uniform for bounds.")
    std = settings.get("std", 0.0)
    if not isinstance(std, (int, float)) or not isfinite(std) or std < 0:
        raise ConfigurationError(f"flight.{name}.std must be finite and non-negative.")
    return (nominal, std) if std else None
