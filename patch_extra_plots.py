import sys

with open("source/antares_fd/simulation/plotters.py", "r") as f:
    content = f.read()

new_function = """

def plot_monte_carlo_distributions(outputs_file, results_dir, run_id):
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
                
    if len(records) < 2:
        return
        
    df = pd.DataFrame(records)
    
    # Required columns check
    required = ['apogee', 'out_of_rail_velocity', 'x_impact', 'y_impact', 'max_mach_number', 'impact_velocity']
    if not all(col in df.columns for col in required):
        return
        
    df['impact_distance'] = np.sqrt(df['x_impact']**2 + df['y_impact']**2)
    
    fig = plt.figure(figsize=(18, 12))
    fig.suptitle(f"Monte Carlo Statistical Distributions\\nRun: {run_id}", fontsize=16)
    
    # 1. Apogee Histogram
    ax1 = plt.subplot(2, 3, 1)
    ax1.hist(df['apogee'], bins=30, color='skyblue', edgecolor='black', alpha=0.7)
    mean_ap = df['apogee'].mean()
    std_ap = df['apogee'].std()
    ax1.axvline(mean_ap, color='red', linestyle='dashed', linewidth=2, label=f'Mean: {mean_ap:.1f}m')
    ax1.axvline(mean_ap + std_ap, color='orange', linestyle='dotted', linewidth=2, label=f'+1 Std: {mean_ap + std_ap:.1f}m')
    ax1.axvline(mean_ap - std_ap, color='orange', linestyle='dotted', linewidth=2)
    ax1.set_title('Apogee Distribution')
    ax1.set_xlabel('Apogee (m)')
    ax1.set_ylabel('Frequency')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. Out of Rail Velocity
    ax2 = plt.subplot(2, 3, 2)
    ax2.hist(df['out_of_rail_velocity'], bins=30, color='lightgreen', edgecolor='black', alpha=0.7)
    mean_oor = df['out_of_rail_velocity'].mean()
    ax2.axvline(mean_oor, color='red', linestyle='dashed', linewidth=2, label=f'Mean: {mean_oor:.1f} m/s')
    ax2.axvline(30.0, color='purple', linestyle='solid', linewidth=2, label='Safe Min (30 m/s)') # common rule of thumb
    ax2.set_title('Out of Rail Velocity')
    ax2.set_xlabel('Velocity (m/s)')
    ax2.set_ylabel('Frequency')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. Max Mach Number
    ax3 = plt.subplot(2, 3, 3)
    ax3.hist(df['max_mach_number'], bins=30, color='salmon', edgecolor='black', alpha=0.7)
    mean_mach = df['max_mach_number'].mean()
    ax3.axvline(mean_mach, color='red', linestyle='dashed', linewidth=2, label=f'Mean: {mean_mach:.2f} M')
    ax3.set_title('Maximum Mach Number')
    ax3.set_xlabel('Mach Number')
    ax3.set_ylabel('Frequency')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. Impact Velocity
    ax4 = plt.subplot(2, 3, 4)
    # Impact velocity is often negative (falling down), let's use absolute magnitude
    imp_vel = np.abs(df['impact_velocity'])
    ax4.hist(imp_vel, bins=30, color='mediumpurple', edgecolor='black', alpha=0.7)
    mean_imp = imp_vel.mean()
    ax4.axvline(mean_imp, color='red', linestyle='dashed', linewidth=2, label=f'Mean: {mean_imp:.1f} m/s')
    ax4.set_title('Impact Velocity (Ground Hit)')
    ax4.set_xlabel('Velocity Magnitude (m/s)')
    ax4.set_ylabel('Frequency')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    # 5. Scatter: Apogee vs Impact Distance
    ax5 = plt.subplot(2, 3, (5, 6)) # Spans two columns
    scatter = ax5.scatter(df['apogee'], df['impact_distance'], c=df['max_mach_number'], cmap='viridis', alpha=0.7, edgecolors='black')
    plt.colorbar(scatter, ax=ax5, label='Max Mach Number')
    ax5.set_title('Apogee Altitude vs. Ground Drift Distance')
    ax5.set_xlabel('Apogee (m)')
    ax5.set_ylabel('Drift Distance from Pad (m)')
    ax5.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plot_path = results_dir / f"distributions_{run_id}.pdf"
    plt.savefig(plot_path, bbox_inches='tight')
    plt.close()
    print(f"[Monte Carlo] Additional statistical plots saved to {plot_path}")
"""
content = content + new_function

with open("source/antares_fd/simulation/plotters.py", "w") as f:
    f.write(content)
