import os
import json
import pandas as pd
from pathlib import Path
import subprocess

def generate_latex_report(config, results_dir: Path, run_id: str):
    print("[Report] Generating LaTeX report...")
    
    # --- 1. Extract Config & Variations ---
    mc_cfg = config.monte_carlo if config.monte_carlo else {}
    
    variations_text = ""
    for category, params in mc_cfg.items():
        if isinstance(params, dict):
            variations_text += f"\\subsection{{{category.capitalize()}}}\n\\begin{{itemize}}\n"
            for param, vals in params.items():
                if isinstance(vals, dict) and "std" in vals:
                    variations_text += f"\\item \\textbf{{{param.replace('_', ' ')}}}: $\\sigma = {vals['std']}$\n"
                elif isinstance(vals, dict) and "factor_std" in vals:
                    variations_text += f"\\item \\textbf{{{param.replace('_', ' ')}}}: factor $\\sigma = {vals['factor_std']}$\n"
                else:
                    variations_text += f"\\item \\textbf{{{param.replace('_', ' ')}}}: {vals}\n"
            variations_text += "\\end{itemize}\n"

    # --- 2. Process Results ---
    outputs_file = results_dir / "mc_sim.outputs.txt"
    results_text = ""
    if outputs_file.exists():
        records = []
        with open(outputs_file, "r") as f:
            for line in f:
                if line.strip():
                    try:
                        records.append(json.loads(line))
                    except:
                        pass
        if records:
            df = pd.DataFrame(records)
            results_text += "\\begin{table}[h!]\n\\centering\n\\begin{tabular}{|l|c|c|}\n\\hline\n"
            results_text += "\\textbf{Parameter} & \\textbf{Mean} & \\textbf{Std Dev} \\\\\n\\hline\n"
            for col in ['apogee', 'apogee_time', 'x_impact', 'y_impact', 'impact_velocity', 'max_mach_number']:
                if col in df.columns:
                    mean_val = df[col].mean()
                    std_val = df[col].std()
                    results_text += f"{col.replace('_', ' ').title()} & {mean_val:.2f} & {std_val:.2f} \\\\\n"
            results_text += "\\hline\n\\end{tabular}\n\\caption{Monte Carlo Summary Statistics}\n\\end{table}\n"
    
    # --- 3. LaTeX Template ---
    latex_content = f"""\\documentclass[12pt,a4paper]{{article}}
\\usepackage[utf8]{{inputenc}}
\\usepackage{{graphicx}}
\\usepackage{{geometry}}
\\usepackage{{hyperref}}
\\usepackage{{booktabs}}
\\geometry{{margin=2cm}}

\\title{{Monte Carlo Flight Dynamics Report}}
\\author{{Antares Flight Dynamics}}
\\date{{\\today}}

\\begin{{document}}

\\maketitle

\\section{{Simulation Setup}}
This report presents the results of the Monte Carlo simulation run \\texttt{{{run_id.replace('_', '\\_')}}}.
A total of {mc_cfg.get('num_simulations', 'Unknown')} simulations were requested with seed {mc_cfg.get('random_seed', 'Unknown')}.

\\section{{Varied Parameters}}
The following stochastic parameters were varied during the campaign:
{variations_text}

\\section{{Results Summary}}
The statistical summary of the landing dispersion and flight parameters is presented below.
{results_text}

\\section{{Visualizations}}
"""

    plot_2d = results_dir / f"dispersion_plot_{run_id}.pdf"
    if plot_2d.exists():
        latex_content += f"""
\\begin{{figure}}[h!]
    \\centering
    \\includegraphics[width=0.8\\textwidth]{{{plot_2d.name}}}
    \\caption{{2D Ground Dispersion with Probability Ellipses}}
\\end{{figure}}
\\clearpage
"""

    plot_3d = results_dir / f"dispersion_plot_3d_{run_id}.pdf"
    if plot_3d.exists():
        latex_content += f"""
\\begin{{figure}}[h!]
    \\centering
    \\includegraphics[width=0.9\\textwidth]{{{plot_3d.name}}}
    \\caption{{3D Isometric View of the Dispersion}}
\\end{{figure}}
"""


    plot_dist = results_dir / f"distributions_{run_id}.pdf"
    if plot_dist.exists():
        latex_content += f"\n\\begin{{figure}}[h!]\n    \\centering\n    \\includegraphics[width=1.0\\textwidth]{{{plot_dist.name}}}\n    \\caption{{Monte Carlo Statistical Distributions}}\n\\end{{figure}}\n"

    latex_content += "\end{document}\n"


    # --- 4. Write and Compile ---
    tex_file = results_dir / f"report_{run_id}.tex"
    with open(tex_file, "w") as f:
        f.write(latex_content)
        
    print(f"[Report] LaTeX source saved to {tex_file}")
    
    # Try to compile
    try:
        subprocess.run(["pdflatex", "-interaction=nonstopmode", tex_file.name], cwd=str(results_dir), check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"[Report] PDF successfully compiled at {results_dir / f'report_{run_id}.pdf'}")
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        if isinstance(e, FileNotFoundError):
            print("[Report] Warning: 'pdflatex' compiler not found on this system. Saving report as .txt fallback...")
        else:
            print(f"[Report] Warning: pdflatex compilation failed. Saving report as .txt fallback...")
        
        txt_file = results_dir / f"report_{run_id}.txt"
        with open(txt_file, "w") as f_txt:
            f_txt.write("MONTE CARLO FLIGHT DYNAMICS REPORT\n")
            f_txt.write("="*40 + "\n\n")
            
            f_txt.write("1. SIMULATION SETUP\n")
            f_txt.write("-" * 20 + "\n")
            f_txt.write(f"Run ID: {run_id}\n")
            f_txt.write(f"Simulations: {mc_cfg.get('num_simulations', 'Unknown')}\n")
            f_txt.write(f"Seed: {mc_cfg.get('random_seed', 'Unknown')}\n\n")
            
            f_txt.write("2. VARIED PARAMETERS\n")
            f_txt.write("-" * 20 + "\n")
            for category, params in mc_cfg.items():
                if isinstance(params, dict):
                    f_txt.write(f"{category.upper()}:\n")
                    for param, vals in params.items():
                        if isinstance(vals, dict) and "std" in vals:
                            f_txt.write(f"  - {param}: std = {vals['std']}\n")
                        elif isinstance(vals, dict) and "factor_std" in vals:
                            f_txt.write(f"  - {param}: factor std = {vals['factor_std']}\n")
                        else:
                            f_txt.write(f"  - {param}: {vals}\n")
            f_txt.write("\n")
            
            f_txt.write("3. RESULTS SUMMARY\n")
            f_txt.write("-" * 20 + "\n")
            if 'df' in locals():
                for col in ['apogee', 'apogee_time', 'x_impact', 'y_impact', 'impact_velocity', 'max_mach_number']:
                    if col in df.columns:
                        mean_val = df[col].mean()
                        std_val = df[col].std()
                        f_txt.write(f"{col.replace('_', ' ').title()}: Mean = {mean_val:.2f} | Std Dev = {std_val:.2f}\n")
            
            f_txt.write("\n(Check the results directory for the PDF dispersion plots)\n")
        
        print(f"[Report] Plain text report saved to {txt_file}")
