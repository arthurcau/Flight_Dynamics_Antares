import sys

with open("MAGI/interface.py", "r") as f:
    code = f.read()

code = code.replace(
    "def get_atmospheric_ensemble(latitude, longitude, elevation, target_date_str=None) -> list[AtmosphericProfile]:",
    "def get_atmospheric_ensemble(latitude, longitude, elevation, target_date_str=None, time_window_minutes=120, time_step_minutes=10) -> list[AtmosphericProfile]:"
)

# Change vertical grid resolution to 10m
code = code.replace(
    "VERTICAL_GRID = np.arange(10, 6000 + 100, 100)",
    "VERTICAL_GRID = np.arange(10, 6000 + 10, 10)"
)

# Call balthasar with kwargs
code = code.replace(
    "forecast_result, is_real_ensemble = balthasar.fetch_operational_forecast(latitude, longitude, target_date_str)",
    "forecast_result, is_real_ensemble = balthasar.fetch_operational_forecast(latitude, longitude, target_date_str, time_window_minutes, time_step_minutes)"
)

with open("MAGI/interface.py", "w") as f:
    f.write(code)

