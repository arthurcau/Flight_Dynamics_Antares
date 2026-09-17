import datetime
from rocketpy import Environment
from antares_fd.config.exceptions import ConfigurationError, AtmosphereUnavailableError

# Cache for MAGI calls to avoid redundant API connections during campaign loops
_ENVIRONMENT_CACHE = {}
_ENSEMBLE_CACHE = {}

def _get_cache_key(environment_config, launch_config, is_ensemble=False):
    # Safely creates a string key for caching based on configuration dicts
    env_str = str(sorted(environment_config.items())) if environment_config else ""
    launch_str = str(sorted(launch_config.items())) if launch_config else ""
    return f"{env_str}_{launch_str}_{is_ensemble}"

def build_environment(environment_config, launch_config) -> Environment:
    global _ENVIRONMENT_CACHE
    cache_key = _get_cache_key(environment_config, launch_config)
    
    if cache_key in _ENVIRONMENT_CACHE:
        print("[MAGI] Using cached nominal atmospheric profile.")
        # We need to return a distinct Environment object to avoid modifications
        # bleeding across simulations, but reproducing the arrays is what matters.
        # However, deepcopying Environment might fail depending on Cython/Fortran inner dependencies.
        # Actually returning a new Environment with the cached arrays is safest.
        cached_profile = _ENVIRONMENT_CACHE[cache_key]
        if isinstance(cached_profile, str): # Fallback happened
             pass # logic handled below by re-creating Env
    
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
            year, month, day = map(int, date_str.split('-'))
            hour, minute, second = map(int, time_str.split(':'))
            env.set_date((year, month, day, hour, minute, second), timezone=tz)
        except ValueError:
            raise ConfigurationError(f"Invalid date/time format. Expected YYYY-MM-DD and HH:MM:SS, got '{date_str}' '{time_str}'")
    else:
        raise ConfigurationError("launch.datetime.date and time are required")
        
    if environment_config:
        env_type = environment_config.get("type", "standard_atmosphere").upper()
        if env_type == "MAGI":
            if cache_key in _ENVIRONMENT_CACHE:
                cached_data = _ENVIRONMENT_CACHE[cache_key]
                if isinstance(cached_data, dict):
                    # Cache hit! Reuse the arrays directly inside a new Environment.
                    env.set_atmospheric_model(
                        type="custom_atmosphere",
                        pressure=cached_data["pressure"],
                        temperature=cached_data["temperature"],
                        wind_u=cached_data["wind_u"],
                        wind_v=cached_data["wind_v"]
                    )
                    return env

            print("\n[MAGI] Fetching atmospheric profile via MAGI adapter...")
            from MAGI.interface import get_atmospheric_profile

            target_date_str = environment_config.get("target_date")
            target_time_str = environment_config.get("target_time")
            if target_date_str and target_time_str:
                target_date_str = f"{target_date_str}T{target_time_str}"
            fallback_cfg = environment_config.get("fallback", {})
            fallback_enabled = fallback_cfg.get("enabled", False)

            try:
                profile = get_atmospheric_profile(lat, lon, elev, target_date_str)
                
                pressure_array = [[z, p] for z, p in zip(profile.altitude_asl_m, profile.pressure_pa)]
                temperature_array = [[z, t] for z, t in zip(profile.altitude_asl_m, profile.temperature_k)]
                u_array = [[z, u] for z, u in zip(profile.altitude_asl_m, profile.wind_u_mps)]
                v_array = [[z, v] for z, v in zip(profile.altitude_asl_m, profile.wind_v_mps)]
                
                env.set_atmospheric_model(
                    type="custom_atmosphere",
                    pressure=pressure_array,
                    temperature=temperature_array,
                    wind_u=u_array,
                    wind_v=v_array
                )
                
                # Save arrays to cache
                _ENVIRONMENT_CACHE[cache_key] = {
                    "pressure": pressure_array,
                    "temperature": temperature_array,
                    "wind_u": u_array,
                    "wind_v": v_array
                }
                
                print(f"[MAGI] Loaded {profile.source_type} successfully.\n")
            except Exception as e:
                if fallback_enabled:
                    fallback_type = fallback_cfg.get("type", "standard_atmosphere")
                    print(f"\n[MAGI] WARNING: Atmospheric fetch failed ({e}). Explicit fallback enabled. Reverting to {fallback_type}.")
                    env.set_atmospheric_model(type=fallback_type)
                    _ENVIRONMENT_CACHE[cache_key] = fallback_type # Cache the fallback signal
                else:
                    raise AtmosphereUnavailableError(f"MAGI could not generate a valid atmospheric profile: {e}\nSimulation aborted.") from e
        else:
            env.set_atmospheric_model(type=env_type.lower())
    else:
        env.set_atmospheric_model(type="standard_atmosphere")

    return env

def build_environment_ensemble(environment_config, launch_config):
    global _ENSEMBLE_CACHE
    cache_key = _get_cache_key(environment_config, launch_config, is_ensemble=True)
    
    print("Building Environment Ensemble...")
    if not launch_config:
        raise ConfigurationError("launch_config is required")
        
    site = launch_config.get("site", {})
    lat = site.get("latitude")
    lon = site.get("longitude")
    elev = site.get("elevation")
    datum = site.get("datum", "SIRGAS2000")
    
    dt_config = launch_config.get("datetime", {})
    date_str = dt_config.get("date")
    time_str = dt_config.get("time")
    tz = dt_config.get("timezone", "America/Sao_Paulo")
    
    env_type = environment_config.get("type", "standard_atmosphere").upper()
    if env_type != "MAGI":
        print("[Monte Carlo] MAGI not enabled, returning single nominal environment for stochastic noise.")
        return [build_environment(environment_config, launch_config)]
        
    if cache_key in _ENSEMBLE_CACHE:
        print("[MAGI] Using cached atmospheric ensemble.")
        cached_envs_data = _ENSEMBLE_CACHE[cache_key]
        envs = []
        for data in cached_envs_data:
            env = Environment(latitude=lat, longitude=lon, elevation=elev, datum=datum)
            if date_str and time_str:
                year, month, day = map(int, date_str.split('-'))
                hour, minute, second = map(int, time_str.split(':'))
                env.set_date((year, month, day, hour, minute, second), timezone=tz)
            env.set_atmospheric_model(
                type="custom_atmosphere",
                pressure=data["pressure"],
                temperature=data["temperature"],
                wind_u=data["wind_u"],
                wind_v=data["wind_v"]
            )
            envs.append(env)
        return envs

    print("\n[MAGI] Fetching atmospheric ensemble via MAGI adapter...")
    from MAGI.interface import get_atmospheric_ensemble
    target_date_str = environment_config.get("target_date")
    target_time_str = environment_config.get("target_time")
    if target_date_str and target_time_str:
        target_date_str = f"{target_date_str}T{target_time_str}"
    
    time_window_minutes = environment_config.get("time_window_minutes", 120)
    time_step_minutes = environment_config.get("time_step_minutes", 10)
    fallback_cfg = environment_config.get("fallback", {})
    fallback_enabled = fallback_cfg.get("enabled", False)

    try:
        profiles = get_atmospheric_ensemble(lat, lon, elev, target_date_str, time_window_minutes, time_step_minutes)
    except Exception as e:
        if fallback_enabled:
            fallback_type = fallback_cfg.get("type", "standard_atmosphere")
            print(f"\n[MAGI] WARNING: Atmospheric ensemble fetch failed ({e}). Explicit fallback enabled. Reverting to single {fallback_type}.")
            return [build_environment(environment_config, launch_config)]
        raise AtmosphereUnavailableError(f"MAGI could not generate a valid atmospheric ensemble: {e}\nSimulation aborted.") from e
    
    envs = []
    cached_data_list = []
    
    for profile in profiles:
        env = Environment(latitude=lat, longitude=lon, elevation=elev, datum=datum)
        if date_str and time_str:
            year, month, day = map(int, date_str.split('-'))
            hour, minute, second = map(int, time_str.split(':'))
            env.set_date((year, month, day, hour, minute, second), timezone=tz)
            
        pressure_array = [[z, p] for z, p in zip(profile.altitude_asl_m, profile.pressure_pa)]
        temperature_array = [[z, t] for z, t in zip(profile.altitude_asl_m, profile.temperature_k)]
        u_array = [[z, u] for z, u in zip(profile.altitude_asl_m, profile.wind_u_mps)]
        v_array = [[z, v] for z, v in zip(profile.altitude_asl_m, profile.wind_v_mps)]
        
        env.set_atmospheric_model(
            type="custom_atmosphere",
            pressure=pressure_array,
            temperature=temperature_array,
            wind_u=u_array,
            wind_v=v_array
        )
        envs.append(env)
        cached_data_list.append({
            "pressure": pressure_array,
            "temperature": temperature_array,
            "wind_u": u_array,
            "wind_v": v_array
        })
        
    _ENSEMBLE_CACHE[cache_key] = cached_data_list
    print(f"[MAGI] Loaded {len(envs)} ensemble members successfully.")
    return envs
