import datetime
from rocketpy import Environment
from antares_fd.config.exceptions import ConfigurationError

def build_environment(environment_config, launch_config) -> Environment:
    """Builds the RocketPy Environment object from configurations."""
    print("Building Environment...")
    
    if not launch_config:
        raise ConfigurationError("launch_config is required to build Environment")
        
    site = launch_config.get("site", {})
    lat = site.get("latitude")
    lon = site.get("longitude")
    elev = site.get("elevation")
    datum = site.get("datum", "SIRGAS2000")
    
    if lat is None or lon is None or elev is None:
        raise ConfigurationError("launch.site requires latitude, longitude, and elevation")
        
    env = Environment(
        latitude=lat,
        longitude=lon,
        elevation=elev,
        datum=datum
    )
    
    dt_config = launch_config.get("datetime", {})
    date_str = dt_config.get("date")
    time_str = dt_config.get("time")
    tz = dt_config.get("timezone", "America/Sao_Paulo")
    
    if date_str and time_str:
        try:
            # Parse YYYY-MM-DD and HH:MM:SS
            year, month, day = map(int, date_str.split('-'))
            hour, minute, second = map(int, time_str.split(':'))
            env.set_date(
                (year, month, day, hour, minute, second),
                timezone=tz
            )
        except ValueError:
            raise ConfigurationError(f"Invalid date/time format. Expected YYYY-MM-DD and HH:MM:SS, got '{date_str}' '{time_str}'")
    else:
        # If date or time is not defined, we might raise an error based on rules
        raise ConfigurationError("launch.datetime.date and time are required")
        
    # Apply atmospheric models from environment_config
    if environment_config:
        env_type = environment_config.get("type", "standard_atmosphere").upper()
        if env_type == "MAGI":
            print("\\n[MAGI] Initializing Advanced Vertical Atmospheric Model...")
            import sys
            from pathlib import Path
            import pandas as pd
            
            # Inject MAGI path
            magi_path = Path(__file__).resolve().parents[3] / "MAGI"
            if str(magi_path) not in sys.path:
                sys.path.insert(0, str(magi_path))
                
            from state_manager import StateManager
            from balthasar import Balthasar
            from casper import CasperProcessor
            from melchior import Melchior
            
            # Run MAGI
            state_mgr = StateManager(cache_dir=str(magi_path / "dados_cache"))
            balthasar = Balthasar(cache_dir=str(magi_path / "dados_cache"), elevation_msl=elev)
            forecast_result, is_real_ensemble = balthasar.fetch_operational_forecast()
            
            target_date_str = environment_config.get("target_date")
            if target_date_str:
                target_date = pd.to_datetime(target_date_str, utc=True)
                if isinstance(forecast_result, list):
                    for df in forecast_result:
                        df['valid_time_utc'] = target_date
                else:
                    forecast_result['valid_time_utc'] = target_date

            state_info = state_mgr.evaluate_state(
                is_online=True, fetch_success=True, 
                is_real_ensemble=is_real_ensemble, variables_complete=True
            )
            
            import numpy as np
            VERTICAL_GRID = np.arange(10, 6000 + 100, 100)
            casper = CasperProcessor(elevation_msl=elev, surface_scenario="OPEN_TERRAIN")
            
            if not is_real_ensemble:
                df_nominal = casper.interpolate_profile(forecast_result, VERTICAL_GRID) if forecast_result is not None else pd.DataFrame()
            else:
                df_nominal = casper.interpolate_profile(forecast_result[0], VERTICAL_GRID) if forecast_result else pd.DataFrame()
                
            if df_nominal.empty:
                print("[MAGI] WARNING: No atmospheric data generated! Reverting to standard atmosphere.")
                env.set_atmospheric_model(type="standard_atmosphere")
                return env

            # Extract lists of coordinates (altitude ASL in meters, value) for RocketPy
            # MAGI provides altitude_agl_m. We need ASL for RocketPy custom_atmosphere:
            alt_asl = df_nominal['altitude_agl_m'].values.astype(float) + elev
            pressure_vals = df_nominal['pressure_pa'].values.astype(float)
            temp_vals = df_nominal['temperature_k'].values.astype(float)
            u_vals = df_nominal['u_east_mps'].values.astype(float)
            v_vals = df_nominal['v_north_mps'].values.astype(float)
            
            # Remove NaNs if any
            mask = ~np.isnan(pressure_vals) & ~np.isnan(temp_vals) & ~np.isnan(u_vals) & ~np.isnan(v_vals)
            
            pressure_array = np.column_stack((alt_asl[mask], pressure_vals[mask])).tolist()
            temperature_array = np.column_stack((alt_asl[mask], temp_vals[mask])).tolist()
            u_array = np.column_stack((alt_asl[mask], u_vals[mask])).tolist()
            v_array = np.column_stack((alt_asl[mask], v_vals[mask])).tolist()
            
            env.set_atmospheric_model(
                type="custom_atmosphere",
                pressure=pressure_array,
                temperature=temperature_array,
                wind_u=u_array,
                wind_v=v_array
            )
            print("[MAGI] Custom atmospheric profiles injected into RocketPy Environment successfully.\\n")
        else:
            env.set_atmospheric_model(type="standard_atmosphere")
    else:
        # RocketPy uses standard atmosphere by default
        env.set_atmospheric_model(type="standard_atmosphere")

    return env
