import re
with open("source/antares_fd/simulation/monte_carlo.py", "r") as f:
    content = f.read()

# Fix build_recovery error and env error
content = content.replace("nominal_rocket = build_recovery(config.recovery, nominal_rocket)", "add_recovery_system(nominal_rocket, config.recovery)")
content = content.replace("flight = Flight(rocket, env,", "flight = Flight(rocket, nominal_env,")

with open("source/antares_fd/simulation/monte_carlo.py", "w") as f:
    f.write(content)
