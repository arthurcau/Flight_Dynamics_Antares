import re
with open("source/antares_fd/simulation/monte_carlo.py", "r") as f:
    content = f.read()

content = content.replace("elevation=config.environment.get(\"elevation_std\", None),\n        wind_velocity_x_factor=config.environment.get(\"wind_velocity_x_factor_std\", None),", "elevation=config.environment.get(\"elevation_std\", None)")

with open("source/antares_fd/simulation/monte_carlo.py", "w") as f:
    f.write(content)
