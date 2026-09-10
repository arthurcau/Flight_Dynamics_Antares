with open("source/antares_fd/simulation/monte_carlo.py", "r") as f:
    lines = f.readlines()

new_lines = []
skip = False
for i, line in enumerate(lines):
    if "stoch_env = StochasticEnvironment(" in line:
        new_lines.append(line)
        new_lines.append("        environment=nominal_env,\n")
        new_lines.append("        **env_kwargs\n")
        new_lines.append("    )\n")
        skip = True
    elif skip and "    # 2. Motor" in line:
        skip = False
        new_lines.append(line)
    elif not skip:
        new_lines.append(line)

with open("source/antares_fd/simulation/monte_carlo.py", "w") as f:
    f.writelines(new_lines)
