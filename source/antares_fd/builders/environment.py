"""Build independent, traceable atmospheric environments for each simulation."""

import datetime
from dataclasses import dataclass
from zoneinfo import ZoneInfo

import numpy as np
from rocketpy import Environment, Function

from antares_fd.config.exceptions import ConfigurationError, AtmosphereUnavailableError


@dataclass
class ProfileVariable:
    """Interpolate within coverage; reject upper extrapolation.

    Values below the ground boundary are held at their ground value solely for
    integrator trial steps while locating impact. No upper-air extension occurs.
    """
    altitude: np.ndarray
    values: np.ndarray

    def __call__(self, altitude):
        if np.any(np.asarray(altitude) > self.altitude[-1]):
            raise AtmosphereUnavailableError(f"Flight exceeded atmospheric coverage ({self.altitude[-1]} m ASL)")
        return np.interp(altitude, self.altitude, self.values)


def _base_environment(launch_config):
    if not launch_config:
        raise ConfigurationError("launch_config is required to build Environment")
    site = launch_config.get("site", {})
    lat, lon, elev = (site.get(key) for key in ("latitude", "longitude", "elevation"))
    if any(value is None for value in (lat, lon, elev)) or not np.isfinite([lat, lon, elev]).all():
        raise ConfigurationError("launch.site requires latitude, longitude, and elevation")
    if not -90 <= lat <= 90 or not -180 <= lon <= 180:
        raise ConfigurationError("Invalid launch site coordinates")
    cfg = launch_config.get("datetime", {})
    if not cfg.get("date") or not cfg.get("time"):
        raise ConfigurationError("launch.datetime.date and time are required")
    try:
        date = datetime.datetime.fromisoformat(f"{cfg['date']}T{cfg['time']}")
        date = date.replace(tzinfo=ZoneInfo(cfg.get("timezone", "America/Sao_Paulo")))
    except (ValueError, KeyError) as exc:
        raise ConfigurationError("Invalid date/time format. Expected YYYY-MM-DD and HH:MM:SS with a valid timezone") from exc
    env = Environment(latitude=lat, longitude=lon, elevation=elev, datum=site.get("datum", "SIRGAS2000"))
    env.set_date(date.astimezone(datetime.UTC))
    return env


def _weather_time(config, launch_config, environment):
    date, time = config.get("target_date"), config.get("target_time")
    if date is None:
        return environment.datetime_date.isoformat()
    text = str(date)
    if "T" not in text and " " not in text:
        text += "T" + str(time or launch_config["datetime"]["time"])
    value = datetime.datetime.fromisoformat(text.replace("Z", "+00:00"))
    if value.tzinfo is None:
        value = value.replace(tzinfo=ZoneInfo(launch_config["datetime"].get("timezone", "America/Sao_Paulo")))
    return value.astimezone(datetime.UTC).isoformat()


def _apply_profile(env, profile):
    z = np.asarray(profile.altitude_asl_m)
    if z[0] > env.elevation:
        raise AtmosphereUnavailableError("Atmospheric profile does not cover the launch elevation")
    arrays = {"pressure": np.column_stack((z, profile.pressure_pa)),
              "temperature": np.column_stack((z, profile.temperature_k)),
              "wind_u": np.column_stack((z, profile.wind_u_mps)),
              "wind_v": np.column_stack((z, profile.wind_v_mps))}
    env.set_atmospheric_model(type="custom_atmosphere", **arrays)
    for name, values in (("pressure", profile.pressure_pa), ("temperature", profile.temperature_k),
                         ("wind_velocity_x", profile.wind_u_mps), ("wind_velocity_y", profile.wind_v_mps)):
        setattr(env, name, Function(ProfileVariable(z.copy(), np.asarray(values).copy()), inputs="Height ASL (m)"))
    env.calculate_density_profile()
    if profile.specific_humidity_kg_kg is not None:
        from MAGI.casper import CasperPhysics
        q = Function(ProfileVariable(z.copy(), profile.specific_humidity_kg_kg.copy()))
        # Preserve actual temperature for sound speed/viscosity. Correct only
        # density through the ideal moist-air equation, without replacing T by Tv.
        env.density = env.pressure / (CasperPhysics.R_AIR * env.temperature * (1 + (1 / CasperPhysics.EPSILON - 1) * q))
    env.calculate_speed_of_sound_profile()
    env.calculate_dynamic_viscosity()
    env.max_expected_height = float(z[-1])
    env.antares_atmosphere = {"source": profile.source, "source_type": profile.source_type,
                            "model": profile.model, "valid_time_utc": str(profile.valid_time_utc),
                            "run_time_utc": str(profile.run_time_utc), "member_id": profile.member_id,
                            "altitude_bounds_asl_m": [float(z[0]), float(z[-1])],
                            "density_model": "ideal_moist_air" if profile.specific_humidity_kg_kg is not None else "ideal_dry_air",
                            "sound_speed_model": "RocketPy_dry_air_gamma_approximation", **profile.metadata}
    return env


def _build_environments(environment_config, launch_config, ensemble):
    config = environment_config or {"type": "standard_atmosphere"}
    env = _base_environment(launch_config)
    kind = str(config.get("type", "standard_atmosphere")).lower()
    if kind != "magi":
        if kind != "standard_atmosphere":
            raise ConfigurationError(f"Unsupported environment type: {kind}")
        env.set_atmospheric_model(type="standard_atmosphere")
        env.antares_atmosphere = {"source_type": "standard_atmosphere", "explicit_fallback": False}
        return [env]
    from MAGI.interface import get_atmospheric_profile, get_atmospheric_ensemble
    kwargs = {key: config[key] for key in (
        "cache_dir", "surface_scenario", "max_altitude_agl_m", "vertical_step_m",
        "historical_years", "historical_reference_year", "model"
    ) if key in config}
    target = _weather_time(config, launch_config, env)
    try:
        if ensemble:
            profiles = get_atmospheric_ensemble(env.latitude, env.longitude, env.elevation, target,
                                                config.get("time_window_minutes", 120), config.get("time_step_minutes", 10), **kwargs)
        else:
            profiles = [get_atmospheric_profile(env.latitude, env.longitude, env.elevation, target, **kwargs)]
        if not profiles:
            raise AtmosphereUnavailableError("MAGI returned an empty atmospheric ensemble")
        return [_apply_profile(_base_environment(launch_config), profile) for profile in profiles]
    except (ConfigurationError, ValueError, OSError) as exc:
        fallback = config.get("fallback", {})
        if not fallback.get("enabled", False):
            raise AtmosphereUnavailableError(f"MAGI atmospheric data unavailable: {exc}") from exc
        if fallback.get("type", "standard_atmosphere") != "standard_atmosphere":
            raise ConfigurationError("Only explicitly configured standard_atmosphere fallback is supported") from exc
        env.set_atmospheric_model(type="standard_atmosphere")
        env.antares_atmosphere = {"source_type": "standard_atmosphere", "explicit_fallback": True,
                                "fallback_reason": str(exc), "requested_time_utc": target}
        print(f"[MAGI] Explicit standard-atmosphere fallback: {exc}")
        return [env]


def build_environment(environment_config, launch_config):
    return _build_environments(environment_config, launch_config, ensemble=False)[0]


def build_environment_ensemble(environment_config, launch_config):
    """Return complete profiles, including separately identified time scenarios."""
    return _build_environments(environment_config, launch_config, ensemble=True)
