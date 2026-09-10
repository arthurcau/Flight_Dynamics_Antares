import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
from pathlib import Path
import matplotlib.backends.backend_pdf

from .statistics import calculate_covariance_ellipse

def plot_monte_carlo_dispersion(outputs_file: Path, results_dir: Path, run_id: str, nominal_flight=None, all_flights=None):
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
    
    # Plot extreme trajectories first (so they are in the background)
    if all_flights and len(all_flights) == len(x):
        try:
            idx_max_x = np.argmax(x)
            idx_min_x = np.argmin(x)
            idx_max_y = np.argmax(y)
            idx_min_y = np.argmin(y)
            extreme_indices = list(set([idx_max_x, idx_min_x, idx_max_y, idx_min_y]))
            
            for i, idx in enumerate(extreme_indices):
                flt = all_flights[idx]
                label = 'Extreme Trajectories' if i == 0 else None
                plt.plot(flt.x[:, 1], flt.y[:, 1], color='red', linestyle='--', linewidth=1, label=label, alpha=0.5)
        except Exception as e:
            print(f"[Monte Carlo] Failed to plot extreme trajectories: {e}")

    # Plot nominal trajectory
    if nominal_flight is not None:
        try:
            plt.plot(nominal_flight.x[:, 1], nominal_flight.y[:, 1], color='black', linewidth=2, label='Nominal Trajectory', zorder=5)
            plt.scatter([nominal_flight.x[:, 1][-1]], [nominal_flight.y[:, 1][-1]], color='black', marker='*', s=150, label='Nominal Impact', zorder=6)
        except Exception as e:
            print(f"[Monte Carlo] Failed to plot nominal trajectory: {e}")

    plt.scatter(x, y, s=15, alpha=0.7, label='Simulated Impacts', color='blue', zorder=4)
    
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
    
    # Generate 3D Isometric View of the Monte Carlo Dispersion
    fig_3d = plt.figure(figsize=(12, 10))
    ax_3d = fig_3d.add_subplot(111, projection='3d')
    
    # Scatter impacts on Z=0 plane
    ax_3d.scatter(x, y, np.zeros_like(x), s=5, alpha=0.5, label='Simulated Impacts (Z=0)', color='blue')
    
    # Draw ellipses in 3D (Z=0)
    for (label, p), color in zip(probabilities.items(), colors):
        try:
            ellipse_data = calculate_covariance_ellipse(x, y, p)
            cx, cy = ellipse_data['center']
            w, h = ellipse_data['width'], ellipse_data['height']
            ang = np.radians(ellipse_data['angle'])
            
            # Parametric ellipse in 2D
            t = np.linspace(0, 2*np.pi, 100)
            x_ell = cx + (w/2)*np.cos(t)*np.cos(ang) - (h/2)*np.sin(t)*np.sin(ang)
            y_ell = cy + (w/2)*np.cos(t)*np.sin(ang) + (h/2)*np.sin(t)*np.cos(ang)
            z_ell = np.zeros_like(x_ell)
            
            ax_3d.plot(x_ell, y_ell, z_ell, color=color, lw=2, label=f'{label}% Containment')
        except Exception as e:
            pass
            
    ax_3d.plot([0], [0], [0], marker='*', color='black', markersize=12, label='Launch Pad')
    ax_3d.set_xlabel("East / x (m)")
    ax_3d.set_ylabel("North / y (m)")
    ax_3d.set_zlabel("Altitude / z (m)")
    ax_3d.set_title(f"3D Isometric Dispersion Analysis\nRun: {run_id}")
    ax_3d.legend()
    
    plot_3d_path = results_dir / f"dispersion_plot_3d_{run_id}.pdf"
    plt.savefig(plot_3d_path, bbox_inches='tight')
    plt.close(fig_3d)
    
    print(f"[Monte Carlo] 3D Dispersion plot saved to {plot_3d_path}")

    
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


def export_nominal_flight_plots(flight, results_dir: Path, project_name: str, scenario_name: str = "nominal"):
    """
    Exports nominal flight data to multiple PDF charts:
    - 3D Isometric Trajectory
    - Top-Down 2D Trajectory
    - Side Views (X-Z and Y-Z)
    - Stability margin vs Time
    - Acceleration vs Time
    - Pitch, Roll, Yaw vs Time
    - Angle of Attack vs Time
    - Mach vs Time
    """
    print(f"Generating comprehensive flight telemetry plots for scenario: {scenario_name}...")
    
    pdf_path = results_dir / f"{project_name}_{scenario_name}_telemetry_plots.pdf"
    pdf = matplotlib.backends.backend_pdf.PdfPages(pdf_path)
    
    try:
        events = []
        events.append((0, "Launch"))
        events.append((flight.out_of_rail_time, "Liftoff"))
        events.append((flight.rocket.motor.burn_out_time, "Burnout"))
        events.append((flight.apogee_time, "Apogee"))
        for t_event, p_event in flight.parachute_events:
            events.append((t_event, f"{p_event.name} Trigger"))
            events.append((t_event + p_event.lag, f"{p_event.name} Open"))

        def add_event_markers(ax):
            max_t = ax.get_xlim()[1]
            y_min, y_max = ax.get_ylim()
            for t, label in events:
                if t > max_t: continue
                ax.axvline(x=t, color='grey', linestyle='--', alpha=0.6, linewidth=1)
                ax.text(t, y_min + 0.95*(y_max - y_min), f" {label}", rotation=90, va='top', ha='left', fontsize=8, color='grey')

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
        ax.set_title(f"[{scenario_name}] 3D Isometric Trajectory")
        
        # Highlight apogee and launchpad
        apogee_idx = np.argmax(z)
        ax.scatter(x[apogee_idx], y[apogee_idx], z[apogee_idx], color='blue', s=50, label='Apogee')
        ax.scatter(x[0], y[0], z[0], color='black', marker='*', s=100, label='Launchpad')
        ax.legend()
        pdf.savefig(fig)
        plt.close(fig)
        # 1.1 Top-Down 2D Trajectory (X-Y)
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.plot(x, y, label='Trajectory', color='r', linewidth=2)
        ax.scatter(x[apogee_idx], y[apogee_idx], color='blue', s=50, label='Apogee')
        ax.scatter(x[0], y[0], color='black', marker='*', s=150, label='Launchpad')
        ax.set_xlabel('East (m)')
        ax.set_ylabel('North (m)')
        ax.set_title(f"[{scenario_name}] Top-Down Trajectory (X-Y Plane)")
        ax.axis('equal')
        ax.grid(True)
        ax.legend()
        pdf.savefig(fig)
        plt.close(fig)

        # 1.2 Side Views (X-Z and Y-Z)
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        ax1.plot(x, z, color='r', linewidth=2)
        ax1.scatter(x[apogee_idx], z[apogee_idx], color='blue', s=50, label='Apogee')
        ax1.scatter(x[0], z[0], color='black', marker='*', s=150, label='Launchpad')
        ax1.set_xlabel('East (m)')
        ax1.set_ylabel('Altitude AGL (m)')
        ax1.set_title(f"[{scenario_name}] Side View (East-Altitude)")
        ax1.grid(True)
        ax1.legend()
        
        ax2.plot(y, z, color='r', linewidth=2)
        ax2.scatter(y[apogee_idx], z[apogee_idx], color='blue', s=50, label='Apogee')
        ax2.scatter(y[0], z[0], color='black', marker='*', s=150, label='Launchpad')
        ax2.set_xlabel('North (m)')
        ax2.set_ylabel('Altitude AGL (m)')
        ax2.set_title(f"[{scenario_name}] Side View (North-Altitude)")
        ax2.grid(True)
        ax2.legend()
        pdf.savefig(fig)
        plt.close(fig)

        # 2. Stability Margin vs Time
        fig, ax = plt.subplots(figsize=(10, 6))
        # RocketPy static margin might be only up to apogee or full.
        t_sm = flight.static_margin[:, 0]
        sm = flight.static_margin[:, 1]
        ax.plot(t_sm, sm, color='green')
        ax.set_title(f"[{scenario_name}] Static Margin vs Time")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Static Margin (cal)")
        ax.grid(True)
        # Limit to motor burnout or a bit after, since it diverges after apogee
        t_apogee = flight.apogee_time
        ax.set_xlim(0, t_apogee * 1.5)
        add_event_markers(ax)
        pdf.savefig(fig)
        plt.close(fig)
        

        # 3. Acceleration, Velocity, and Mach vs Time (Combined)
        fig, ax1 = plt.subplots(figsize=(10, 6))
        
        t = flight.ax[:, 0]
        a_tot = np.sqrt(flight.ax[:, 1]**2 + flight.ay[:, 1]**2 + flight.az[:, 1]**2)
        v_tot = flight.speed[:, 1]
        
        color1 = 'tab:red'
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Acceleration (m/s²)', color=color1)
        ax1.plot(t, a_tot, color=color1, label='Total Acceleration')
        ax1.tick_params(axis='y', labelcolor=color1)
        ax1.set_xlim(0, flight.apogee_time * 1.5)
        
        ax2 = ax1.twinx()  
        color2 = 'tab:blue'
        ax2.set_ylabel('Velocity (m/s)', color=color2)
        ax2.plot(t, v_tot, color=color2, linestyle='--', label='Velocity')
        ax2.tick_params(axis='y', labelcolor=color2)
        
        ax3 = ax1.twinx()
        ax3.spines['right'].set_position(('outward', 60))
        color3 = 'tab:green'
        ax3.set_ylabel('Mach Number', color=color3)
        ax3.plot(flight.mach_number[:, 0], flight.mach_number[:, 1], color=color3, linestyle=':', label='Mach Number')
        ax3.tick_params(axis='y', labelcolor=color3)
        
        fig.tight_layout()
        plt.title(f"[{scenario_name}] Acceleration, Velocity & Mach vs Time")
        add_event_markers(ax1)
        pdf.savefig(fig)
        plt.close(fig)

        # Acceleration vs Time
        fig, ax = plt.subplots(figsize=(10, 6))
        t_a = flight.ax[:, 0]
        ax_val = flight.ax[:, 1]
        ay_val = flight.ay[:, 1]
        az_val = flight.az[:, 1]
        a_tot = np.sqrt(ax_val**2 + ay_val**2 + az_val**2)
        ax.plot(t_a, a_tot, label='Total Acceleration', color='purple')
        ax.plot(t_a, az_val, label='Vertical Acceleration (Z)', color='orange', alpha=0.7)
        ax.set_title(f"[{scenario_name}] Acceleration vs Time")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Acceleration (m/s²)")
        ax.set_xlim(0, t_apogee * 1.5)
        ax.grid(True)
        ax.legend()
        add_event_markers(ax)
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
        ax.set_title(f"[{scenario_name}] Euler Angles vs Time")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Angle (degrees)")
        ax.set_xlim(0, t_apogee)
        ax.grid(True)
        ax.legend()
        add_event_markers(ax)
        pdf.savefig(fig)
        plt.close(fig)
        
        # 5. Angle of Attack vs Time
        fig, ax = plt.subplots(figsize=(10, 6))
        t_alpha = flight.angle_of_attack[:, 0]
        alpha = flight.angle_of_attack[:, 1]
        ax.plot(t_alpha, alpha, color='crimson')
        ax.set_title(f"[{scenario_name}] Angle of Attack vs Time")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Angle of Attack (degrees)")
        ax.set_xlim(0, t_apogee)
        ax.grid(True)
        add_event_markers(ax)
        pdf.savefig(fig)
        plt.close(fig)
        
        # 6. Mach vs Time
        fig, ax = plt.subplots(figsize=(10, 6))
        t_mach = flight.mach_number[:, 0]
        mach = flight.mach_number[:, 1]
        ax.plot(t_mach, mach, color='teal')
        ax.set_title(f"[{scenario_name}] Mach Number vs Time")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Mach Number")
        ax.set_xlim(0, t_apogee * 1.2)
        ax.grid(True)
        add_event_markers(ax)
        pdf.savefig(fig)
        plt.close(fig)

    except Exception as e:
        print(f"Error generating PDF plots: {e}")
    finally:
        pdf.close()
        print(f"[PDF Export] Telemetry multi-page plot saved to: {pdf_path}")
