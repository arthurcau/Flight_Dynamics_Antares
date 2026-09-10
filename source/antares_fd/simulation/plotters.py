import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
from pathlib import Path
from .statistics import calculate_covariance_ellipse

def plot_monte_carlo_dispersion(outputs_file: Path, results_dir: Path, run_id: str):
    """
    Parses outputs JSONL file to plot the 2D landing dispersion with probability ellipses.
    """
    x_impact = []
    y_impact = []
    
    with outputs_file.open('r') as f:
        for line in f:
            if not line.strip(): continue
            try:
                data = json.loads(line)
                if 'x_impact' in data and 'y_impact' in data:
                    x_impact.append(data['x_impact'])
                    y_impact.append(data['y_impact'])
            except json.JSONDecodeError:
                pass
                
    if len(x_impact) < 2:
        print("[Monte Carlo] Not enough valid impact data to plot dispersion.")
        return
        
    x = np.array(x_impact)
    y = np.array(y_impact)
    
    # If all points are identical (e.g. 0), we can't plot covariance
    if np.all(x == x[0]) and np.all(y == y[0]):
        print("[Monte Carlo] All impacts are at the exact same location. Ellipse plot skipped.")
        return

    plt.figure(figsize=(10, 10))
    plt.scatter(x, y, s=5, alpha=0.5, label='Simulated Impacts', color='blue')
    
    # Plot probability containment ellipses
    probabilities = {
        50: 0.50,
        90: 0.90,
        95: 0.95,
        99: 0.99
    }
    
    colors = ['green', 'orange', 'red', 'purple']
    
    ax = plt.gca()
    
    for (label, p), color in zip(probabilities.items(), colors):
        try:
            ellipse_data = calculate_covariance_ellipse(x, y, p)
            ellipse = Ellipse(
                xy=ellipse_data['center'],
                width=ellipse_data['width'],
                height=ellipse_data['height'],
                angle=ellipse_data['angle'],
                edgecolor=color,
                fc='None',
                lw=2,
                label=f'{label}% Containment (Bivariate Normal)'
            )
            ax.add_patch(ellipse)
        except Exception as e:
            print(f"[Monte Carlo] Warning: Could not plot {label}% ellipse: {e}")
            
    # Mark launch pad (origin)
    plt.plot(0, 0, marker='*', color='black', markersize=12, label='Launch Pad (Origin)')
    
    plt.xlabel("East / x (m)")
    plt.ylabel("North / y (m)")
    plt.title(f"Ground Dispersion Analysis\nRun: {run_id}")
    plt.axis('equal')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    
    plot_path = results_dir / f"dispersion_plot_{run_id}.pdf"
    plt.savefig(plot_path, bbox_inches='tight')
    plt.close()
    
    print(f"[Monte Carlo] Dispersion plot saved to {plot_path}")
