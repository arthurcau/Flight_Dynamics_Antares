import datetime
from rocketpy import Environment
from antares_fd.config.exceptions import ConfigurationError

def build_environment(environment_config, launch_config) -> Environment:
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
            print("\n[MAGI] Fetching atmospheric profile via MAGI adapter...")
            from MAGI.interface import get_atmospheric_profile
            from antares_fd.config.exceptions import AtmosphereUnavailableError

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
                print(f"[MAGI] Loaded {profile.source_type} successfully.\n")
            except Exception as e:
                if fallback_enabled:
                    fallback_type = fallback_cfg.get("type", "standard_atmosphere")
                    print(f"\n[MAGI] WARNING: Atmospheric fetch failed ({e}). Explicit fallback enabled. Reverting to {fallback_type}.")
                    env.set_atmospheric_model(type=fallback_type)
                else:
                    raise AtmosphereUnavailableError(f"MAGI could not generate a valid atmospheric profile: {e}\nSimulation aborted.") from e
        else:
            env.set_atmospheric_model(type=env_type.lower())
    else:
        env.set_atmospheric_model(type="standard_atmosphere")

    return env

def build_environment_ensemble(environment_config, launch_config):
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
        
    print("\n[MAGI] Fetching atmospheric ensemble via MAGI adapter...")
    from MAGI.interface import get_atmospheric_ensemble
    target_date_str = environment_config.get("target_date")
    target_time_str = environment_config.get("target_time")
    if target_date_str and target_time_str:
        target_date_str = f"{target_date_str}T{target_time_str}"
    
    time_window_minutes = environment_config.get("time_window_minutes", 120)
    time_step_minutes = environment_config.get("time_step_minutes", 10)
    profiles = get_atmospheric_ensemble(lat, lon, elev, target_date_str, time_window_minutes, time_step_minutes)
    
    envs = []
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
        
    print(f"[MAGI] Loaded {len(envs)} ensemble members successfully.")
    return envs
