import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
from pathlib import Path
import matplotlib.backends.backend_pdf

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
    
    if np.all(x == x[0]) and np.all(y == y[0]):
        print("[Monte Carlo] All impacts are at the exact same location. Ellipse plot skipped.")
        return

    plt.figure(figsize=(10, 10))
    plt.scatter(x, y, s=5, alpha=0.5, label='Simulated Impacts', color='blue')
    
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


def euler_from_quaternion(e0, e1, e2, e3):
    """
    Convert a quaternion into euler angles (roll, pitch, yaw)
    roll is rotation around x in radians (counterclockwise)
    pitch is rotation around y in radians (counterclockwise)
    yaw is rotation around z in radians (counterclockwise)
    """
    t0 = +2.0 * (e0 * e1 + e2 * e3)
    t1 = +1.0 - 2.0 * (e1 * e1 + e2 * e2)
    roll_x = np.degrees(np.arctan2(t0, t1))
    
    t2 = +2.0 * (e0 * e2 - e3 * e1)
    t2 = np.clip(t2, -1.0, 1.0)
    pitch_y = np.degrees(np.arcsin(t2))
    
    t3 = +2.0 * (e0 * e3 + e1 * e2)
    t4 = +1.0 - 2.0 * (e2 * e2 + e3 * e3)
    yaw_z = np.degrees(np.arctan2(t3, t4))
    
    return roll_x, pitch_y, yaw_z


def export_nominal_flight_plots(flight, results_dir: Path, project_name: str):
    """
    Exports nominal flight data to multiple PDF charts:
    - 3D Isometric Trajectory
    - Stability margin vs Time
    - Acceleration vs Time
    - Pitch, Roll, Yaw vs Time
    - Angle of Attack vs Time
    - Mach vs Time
    """
    print("Generating comprehensive flight telemetry plots...")
    
    pdf_path = results_dir / f"{project_name}_telemetry_plots.pdf"
    pdf = matplotlib.backends.backend_pdf.PdfPages(pdf_path)
    
    try:
        t = flight.z[:, 0]
        x = flight.x[:, 1]
        y = flight.y[:, 1]
        z = flight.z[:, 1]
        
        # 1. 3D Isometric Trajectory
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')
        ax.plot(x, y, z, label='Rocket Trajectory', color='r', linewidth=2)
        ax.set_xlabel('East (m)')
        ax.set_ylabel('North (m)')
        ax.set_zlabel('Altitude AGL (m)')
        ax.set_title("3D Isometric Trajectory")
        
        # Highlight apogee
        apogee_idx = np.argmax(z)
        ax.scatter(x[apogee_idx], y[apogee_idx], z[apogee_idx], color='blue', s=50, label='Apogee')
        ax.legend()
        pdf.savefig(fig)
        plt.close(fig)
        
        # 2. Stability Margin vs Time
        fig, ax = plt.subplots(figsize=(10, 6))
        # RocketPy static margin might be only up to apogee or full.
        t_sm = flight.static_margin[:, 0]
        sm = flight.static_margin[:, 1]
        ax.plot(t_sm, sm, color='green')
        ax.set_title("Static Margin vs Time")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Static Margin (cal)")
        ax.grid(True)
        # Limit to motor burnout or a bit after, since it diverges after apogee
        t_apogee = flight.apogee_time
        ax.set_xlim(0, t_apogee * 1.5)
        pdf.savefig(fig)
        plt.close(fig)
        
        # 3. Acceleration vs Time
        fig, ax = plt.subplots(figsize=(10, 6))
        t_a = flight.ax[:, 0]
        ax_val = flight.ax[:, 1]
        ay_val = flight.ay[:, 1]
        az_val = flight.az[:, 1]
        a_tot = np.sqrt(ax_val**2 + ay_val**2 + az_val**2)
        ax.plot(t_a, a_tot, label='Total Acceleration', color='purple')
        ax.plot(t_a, az_val, label='Vertical Acceleration (Z)', color='orange', alpha=0.7)
        ax.set_title("Acceleration vs Time")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Acceleration (m/s²)")
        ax.set_xlim(0, t_apogee * 1.5)
        ax.grid(True)
        ax.legend()
        pdf.savefig(fig)
        plt.close(fig)
        
        # 4. Pitch, Roll, Yaw vs Time
        fig, ax = plt.subplots(figsize=(10, 6))
        e0 = flight.e0[:, 1]
        e1 = flight.e1[:, 1]
        e2 = flight.e2[:, 1]
        e3 = flight.e3[:, 1]
        roll, pitch, yaw = euler_from_quaternion(e0, e1, e2, e3)
        t_e = flight.e0[:, 0]
        ax.plot(t_e, pitch, label='Pitch', color='blue')
        ax.plot(t_e, roll, label='Roll', color='red')
        ax.plot(t_e, yaw, label='Yaw', color='green')
        ax.set_title("Euler Angles vs Time")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Angle (degrees)")
        ax.set_xlim(0, t_apogee)
        ax.grid(True)
        ax.legend()
        pdf.savefig(fig)
        plt.close(fig)
        
        # 5. Angle of Attack vs Time
        fig, ax = plt.subplots(figsize=(10, 6))
        t_alpha = flight.angle_of_attack[:, 0]
        alpha = flight.angle_of_attack[:, 1]
        ax.plot(t_alpha, alpha, color='crimson')
        ax.set_title("Angle of Attack vs Time")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Angle of Attack (degrees)")
        ax.set_xlim(0, t_apogee)
        ax.grid(True)
        pdf.savefig(fig)
        plt.close(fig)
        
        # 6. Mach vs Time
        fig, ax = plt.subplots(figsize=(10, 6))
        t_mach = flight.mach_number[:, 0]
        mach = flight.mach_number[:, 1]
        ax.plot(t_mach, mach, color='teal')
        ax.set_title("Mach Number vs Time")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Mach Number")
        ax.set_xlim(0, t_apogee * 1.2)
        ax.grid(True)
        pdf.savefig(fig)
        plt.close(fig)

    except Exception as e:
        print(f"Error generating PDF plots: {e}")
    finally:
        pdf.close()
        print(f"[PDF Export] Telemetry multi-page plot saved to: {pdf_path}")
