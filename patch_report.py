import sys

with open("source/antares_fd/simulation/report.py", "r") as f:
    content = f.read()

new_plot_tex = """
    plot_dist = results_dir / f"distributions_{run_id}.pdf"
    if plot_dist.exists():
        latex_content += f"\\n\\\\begin{{figure}}[h!]\\n    \\\\centering\\n    \\\\includegraphics[width=1.0\\\\textwidth]{{{plot_dist.name}}}\\n    \\\\caption{{Monte Carlo Statistical Distributions}}\\n\\\\end{{figure}}\\n"

    latex_content += "\\end{document}\\n"
"""

content = content.replace("    latex_content += \"\\\\end{document}\\n\"", new_plot_tex)

with open("source/antares_fd/simulation/report.py", "w") as f:
    f.write(content)
