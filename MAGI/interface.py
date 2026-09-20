"""Validated interface between MAGI profiles and the flight-dynamics package."""

from pathlib import Path

import numpy as np
import pandas as pd

from antares_fd.config.exceptions import ConfigurationError
from antares_fd.environment.atmosphere import AtmosphericProfile
from MAGI.balthasar import Balthasar
from MAGI.casper import CasperProcessor, MagiSchema


def _process_df_to_profile(frame, elevation, latitude, longitude):
    MagiSchema.validate(frame)
    accepted = {"VALID", "HYDROSTATIC_WARNING", "SYNTHETIC_SURFACE_LAYER"}
    if not frame.quality_flag.isin(accepted).all():
        raise ConfigurationError(f"MAGI profile rejected by quality control: {sorted(set(frame.quality_flag))}")
    def value(column, default=None):
        item = frame[column].iloc[0] if column in frame else default
        return default if pd.isna(item) else item

    meta = {
        **frame.attrs,
        "quality_flags": sorted(set(frame.quality_flag)),
        "retrieved_at_utc": str(value("retrieved_at_utc", "unknown")),
    }
    for col in ("historical_reference_year", "target_date_utc", "historical_surrogate_notice"):
        if col in frame:
            meta[col] = str(value(col))

    return AtmosphericProfile(
        altitude_asl_m=frame.altitude_msl_m.to_numpy(dtype=float),
        pressure_pa=frame.pressure_pa.to_numpy(dtype=float),
        temperature_k=frame.temperature_k.to_numpy(dtype=float),
        wind_u_mps=frame.u_east_mps.to_numpy(dtype=float),
        wind_v_mps=frame.v_north_mps.to_numpy(dtype=float),
        source=value("data_source", "unknown"),
        source_type=value("data_type", "unknown"),
        model=value("model_name"),
        run_time_utc=value("generation_time_utc"),
        valid_time_utc=value("valid_time_utc"),
        latitude_deg=latitude,
        longitude_deg=longitude,
        member_id=value("ensemble_member"),
        specific_humidity_kg_kg=frame.specific_humidity_kg_kg.to_numpy(dtype=float),
        metadata=meta,
    )


def get_atmospheric_ensemble(latitude, longitude, elevation, target_date_str=None,
                             time_window_minutes=120, time_step_minutes=10, *,
                             cache_dir=None, surface_scenario="OPEN_TERRAIN",
                             max_altitude_agl_m=6000, vertical_step_m=10,
                             historical_years=None, historical_reference_year=None,
                             model=None):
    """Return an atmospheric ensemble (multi-year historical archive or temporal scenarios)."""
    if max_altitude_agl_m <= 0 or vertical_step_m <= 0:
        raise ConfigurationError("MAGI vertical extent and step must be positive")
    cache = Path(cache_dir) if cache_dir is not None else Path(__file__).parent / "dados_cache"
    balthasar = Balthasar(cache_dir=cache, elevation_msl=elevation, model=model)
    raw, _ = balthasar.fetch_operational_forecast(
        latitude, longitude, target_date_str,
        time_window_minutes, time_step_minutes,
        historical_years=historical_years,
        historical_reference_year=historical_reference_year,
        is_ensemble=True,
    )
    frames = raw if isinstance(raw, list) else [raw]
    if not frames or any(frame.empty for frame in frames):
        raise ConfigurationError("MAGI returned no complete atmospheric profiles")
    grid = np.unique(np.r_[np.arange(0, max_altitude_agl_m, vertical_step_m), max_altitude_agl_m])
    processor = CasperProcessor(elevation_msl=elevation, surface_scenario=surface_scenario)
    return [_process_df_to_profile(processor.interpolate_profile(frame, grid), elevation, latitude, longitude)
            for frame in frames]


def get_atmospheric_profile(latitude, longitude, elevation, target_date_str=None, *,
                            cache_dir=None, surface_scenario="OPEN_TERRAIN",
                            max_altitude_agl_m=6000, vertical_step_m=10,
                            historical_years=None, historical_reference_year=None,
                            model=None, **kwargs):
    """Return the nominal profile at the requested time (or representative historical reference year)."""
    if max_altitude_agl_m <= 0 or vertical_step_m <= 0:
        raise ConfigurationError("MAGI vertical extent and step must be positive")
    cache = Path(cache_dir) if cache_dir is not None else Path(__file__).parent / "dados_cache"
    balthasar = Balthasar(cache_dir=cache, elevation_msl=elevation, model=model)
    raw, _ = balthasar.fetch_operational_forecast(
        latitude, longitude, target_date_str,
        time_window_minutes=0, time_step_minutes=10,
        historical_years=historical_years,
        historical_reference_year=historical_reference_year,
        is_ensemble=False,
    )
    frame = raw if not isinstance(raw, list) else raw[0]
    if frame is None or frame.empty:
        raise ConfigurationError("MAGI returned an empty atmospheric profile")
    grid = np.unique(np.r_[np.arange(0, max_altitude_agl_m, vertical_step_m), max_altitude_agl_m])
    processor = CasperProcessor(elevation_msl=elevation, surface_scenario=surface_scenario)
    return _process_df_to_profile(processor.interpolate_profile(frame, grid), elevation, latitude, longitude)
