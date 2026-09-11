import sys

with open("source/antares_fd/simulation/plotters.py", "r") as f:
    content = f.read()

convergence_func = """

def plot_monte_carlo_convergence(outputs_file, results_dir, run_id):
    import json
    import numpy as np
    import matplotlib.pyplot as plt
    import pandas as pd
    
    records = []
    with open(outputs_file, 'r') as f:
        for line in f:
            if not line.strip(): continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                pass
                
    if len(records) < 5:
        return
        
    df = pd.DataFrame(records)
    
    # Calculate running means and stds
    df['run_mean_apogee'] = df['apogee'].expanding().mean()
    df['run_std_apogee'] = df['apogee'].expanding().std()
    
    df['impact_distance'] = np.sqrt(df['x_impact']**2 + df['y_impact']**2)
    df['run_mean_impact'] = df['impact_distance'].expanding().mean()
    df['run_std_impact'] = df['impact_distance'].expanding().std()
    
    x_axis = np.arange(1, len(df) + 1)
    
    fig = plt.figure(figsize=(14, 10))
    fig.suptitle(f"Monte Carlo Convergence Analysis\\nRun: {run_id}", fontsize=16)
    
    # Apogee Convergence
    ax1 = plt.subplot(2, 2, 1)
    ax1.plot(x_axis, df['run_mean_apogee'], label='Running Mean', color='blue', linewidth=2)
    ax1.fill_between(x_axis, 
                     df['run_mean_apogee'] - df['run_std_apogee'], 
                     df['run_mean_apogee'] + df['run_std_apogee'], 
                     color='blue', alpha=0.2, label='±1 Running Std')
    ax1.set_title('Apogee Convergence')
    ax1.set_xlabel('Number of Simulations')
    ax1.set_ylabel('Apogee (m)')
    ax1.grid(True, linestyle='--', alpha=0.6)
    ax1.legend()
    
    # Impact Distance Convergence
    ax2 = plt.subplot(2, 2, 2)
    ax2.plot(x_axis, df['run_mean_impact'], label='Running Mean', color='green', linewidth=2)
    ax2.fill_between(x_axis, 
                     df['run_mean_impact'] - df['run_std_impact'], 
                     df['run_mean_impact'] + df['run_std_impact'], 
                     color='green', alpha=0.2, label='±1 Running Std')
    ax2.set_title('Ground Drift Distance Convergence')
    ax2.set_xlabel('Number of Simulations')
    ax2.set_ylabel('Drift Distance (m)')
    ax2.grid(True, linestyle='--', alpha=0.6)
    ax2.legend()
    
    # Std Dev Stabilization
    ax3 = plt.subplot(2, 2, (3,4))
    # Normalize standard deviations to percentage of final to view stabilization
    final_ap_std = df['run_std_apogee'].iloc[-1]
    final_imp_std = df['run_std_impact'].iloc[-1]
    
    if final_ap_std > 0 and final_imp_std > 0:
        ap_norm = (df['run_std_apogee'] / final_ap_std - 1.0) * 100
        imp_norm = (df['run_std_impact'] / final_imp_std - 1.0) * 100
        ax3.plot(x_axis, ap_norm, label='Apogee Std. Dev. Variance (%)', color='red', linewidth=2)
        ax3.plot(x_axis, imp_norm, label='Impact Std. Dev. Variance (%)', color='purple', linewidth=2)
        
        ax3.axhline(5.0, color='black', linestyle='--', alpha=0.5, label='±5% Stability Threshold')
        ax3.axhline(-5.0, color='black', linestyle='--', alpha=0.5)
        
        ax3.set_ylim(-20, 20)
        ax3.set_title('Standard Deviation Stabilization (Data Reliability)')
        ax3.set_xlabel('Number of Simulations')
        ax3.set_ylabel('Deviation from Final Std (%)')
        ax3.grid(True, linestyle='--', alpha=0.6)
        ax3.legend()
        
    plt.tight_layout()
    plot_path = results_dir / f"convergence_{run_id}.pdf"
    plt.savefig(plot_path, bbox_inches='tight')
    plt.close()
"""
if "def plot_monte_carlo_convergence" not in content:
    content = content + convergence_func

with open("source/antares_fd/simulation/plotters.py", "w") as f:
    f.write(content)
