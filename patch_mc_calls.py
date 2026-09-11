import sys

for filename in ["source/antares_fd/simulation/monte_carlo.py", "source/antares_fd/simulation/monte_carlo_failure.py"]:
    with open(filename, "r") as f:
        content = f.read()
    
    # Replace the import statement
    content = content.replace("from antares_fd.simulation.plotters import plot_monte_carlo_dispersion", 
                              "from antares_fd.simulation.plotters import plot_monte_carlo_dispersion, plot_monte_carlo_distributions")
                              
    # Add the function call right after plot_monte_carlo_dispersion
    content = content.replace("plot_monte_carlo_dispersion(outputs_file, results_dir, run_id, nominal_flight=flight, all_flights=all_flights)",
                              "plot_monte_carlo_dispersion(outputs_file, results_dir, run_id, nominal_flight=flight, all_flights=all_flights)\n        plot_monte_carlo_distributions(outputs_file, results_dir, run_id)")
                              
    content = content.replace("plot_monte_carlo_dispersion(outputs_file, results_dir, run_id, nominal_flight=flight, nominal_flight_fail=flight_fail, all_flights=all_flights)",
                              "plot_monte_carlo_dispersion(outputs_file, results_dir, run_id, nominal_flight=flight, nominal_flight_fail=flight_fail, all_flights=all_flights)\n        plot_monte_carlo_distributions(outputs_file, results_dir, run_id)")
                              
    with open(filename, "w") as f:
        f.write(content)
