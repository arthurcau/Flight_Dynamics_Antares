import sys

for filename in ["source/antares_fd/simulation/monte_carlo.py", "source/antares_fd/simulation/monte_carlo_failure.py"]:
    with open(filename, "r") as f:
        content = f.read()
    
    content = content.replace(
        "from antares_fd.simulation.plotters import plot_monte_carlo_dispersion, plot_monte_carlo_distributions",
        "from antares_fd.simulation.plotters import plot_monte_carlo_dispersion, plot_monte_carlo_distributions, plot_monte_carlo_convergence"
    )
    
    content = content.replace(
        "plot_monte_carlo_distributions(outputs_file, results_dir, run_id)",
        "plot_monte_carlo_distributions(outputs_file, results_dir, run_id)\n        plot_monte_carlo_convergence(outputs_file, results_dir, run_id)"
    )
    
    with open(filename, "w") as f:
        f.write(content)

# Patch report.py to include convergence plot
with open("source/antares_fd/simulation/report.py", "r") as f:
    rep_content = f.read()
    
rep_content = rep_content.replace(
    "latex_content += \"\\end{document}\\n\"",
    """plot_conv = results_dir / f"convergence_{run_id}.pdf"
    if plot_conv.exists():
        latex_content += f"\\n\\\\begin{{figure}}[h!]\\n    \\\\centering\\n    \\\\includegraphics[width=0.9\\\\textwidth]{{{plot_conv.name}}}\\n    \\\\caption{{Monte Carlo Statistical Convergence (Data Reliability)}}\\n\\\\end{{figure}}\\n"

    latex_content += "\\end{document}\\n"
"""
)

with open("source/antares_fd/simulation/report.py", "w") as f:
    f.write(rep_content)
    
