import sys

with open("source/antares_fd/builders/environment.py", "r") as f:
    code = f.read()

code = code.replace(
    "profiles = get_atmospheric_ensemble(lat, lon, elev, target_date_str)",
    """time_window_minutes = environment_config.get("time_window_minutes", 120)
    time_step_minutes = environment_config.get("time_step_minutes", 10)
    profiles = get_atmospheric_ensemble(lat, lon, elev, target_date_str, time_window_minutes, time_step_minutes)"""
)

with open("source/antares_fd/builders/environment.py", "w") as f:
    f.write(code)

