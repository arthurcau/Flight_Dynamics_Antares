with open("source/antares_fd/simulation/monte_carlo.py", "r") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "flight=stoch_flight," in line:
        lines.insert(i+1, "        export_list=['apogee', 'apogee_time', 'x_impact', 'y_impact', 'impact_velocity', 'max_mach_number', 't_final', 'out_of_rail_velocity', 'max_dynamic_pressure', 'max_speed'],\n")
        break

with open("source/antares_fd/simulation/monte_carlo.py", "w") as f:
    f.writelines(lines)
