import re
with open("source/antares_fd/builders/environment.py", "r") as f:
    content = f.read()

new_code = """
def build_environment_ensemble(environment_config, launch_config) -> list[Environment]:
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
    
    profiles = get_atmospheric_ensemble(lat, lon, elev, target_date_str)
    
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
        
    print(f"[MAGI] Loaded {len(envs)} ensemble members successfully.\\n")
    return envs

"""

content = content + "\n" + new_code

with open("source/antares_fd/builders/environment.py", "w") as f:
    f.write(content)

