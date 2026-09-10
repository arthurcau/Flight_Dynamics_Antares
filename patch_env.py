import sys

with open('source/antares_fd/builders/environment.py', 'r') as f:
    lines = f.readlines()

out = []
skip = False
for line in lines:
    if "    # Apply atmospheric models from environment_config" in line:
        skip = True
        out.append("    # Apply atmospheric models from environment_config\n")
        out.append("""    if environment_config:
        env_type = environment_config.get("type", "standard_atmosphere").upper()
        if env_type == "MAGI":
            print("\\n[MAGI] Fetching atmospheric profile via MAGI adapter...")
            from MAGI.interface import get_atmospheric_profile
            from antares_fd.config.exceptions import AtmosphereUnavailableError

            target_date_str = environment_config.get("target_date")
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
                print(f"[MAGI] Loaded {profile.source_type} successfully.\\n")
            except Exception as e:
                if fallback_enabled:
                    fallback_type = fallback_cfg.get("type", "standard_atmosphere")
                    print(f"\\n[MAGI] WARNING: Atmospheric fetch failed ({e}). Explicit fallback enabled. Reverting to {fallback_type}.")
                    env.set_atmospheric_model(type=fallback_type)
                else:
                    raise AtmosphereUnavailableError(f"MAGI could not generate a valid atmospheric profile: {e}\\nSimulation aborted.") from e
        else:
            env.set_atmospheric_model(type=env_type.lower())
    else:
        env.set_atmospheric_model(type="standard_atmosphere")

    return env
""")
    if "    return env" in line:
        skip = False
        continue
    
    if not skip:
        out.append(line)

with open('source/antares_fd/builders/environment.py', 'w') as f:
    f.writelines(out)
