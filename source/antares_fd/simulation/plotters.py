import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
from pathlib import Path
import matplotlib.backends.backend_pdf

from .statistics import calculate_covariance_ellipse

def plot_monte_carlo_dispersion(outputs_file: Path, results_dir: Path, run_id: str, nominal_flight=None, nominal_flight_fail=None, all_flights=None):
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
    if all_flights and len(all_flights) > 0:
        try:
            extreme_points = [
                (np.max(x), y[np.argmax(x)]),
                (np.min(x), y[np.argmin(x)]),
                (x[np.argmax(y)], np.max(y)),
                (x[np.argmin(y)], np.min(y))
            ]
            
            plotted_extremes = []
            for ex_x, ex_y in extreme_points:
                best_flight = None
                best_dist = float('inf')
                for flt_data in all_flights:
                    fx, fy = flt_data['x'][-1], flt_data['y'][-1]
                    dist = (fx - ex_x)**2 + (fy - ex_y)**2
                    if dist < best_dist:
                        best_dist = dist
                        best_flight = flt_data
                
                # Plot if found and close enough (margin for float precision)
                if best_flight is not None and best_dist < 10.0:
                    # check if not already in list by identity (since dicts are unhashable, use id)
                    if not any(id(best_flight) == id(p) for p in plotted_extremes):
                        plotted_extremes.append(best_flight)
                        
            for i, flt_data in enumerate(plotted_extremes):
                label = 'Extreme Trajectories' if i == 0 else None
                plt.plot(flt_data['x'], flt_data['y'], color='red', linestyle='--', linewidth=1, label=label, alpha=0.5)
        except Exception as e:
            print(f"[Monte Carlo] Failed to plot extreme trajectories: {e}")

    # Plot nominal trajectory
    if nominal_flight is not None:
        try:
            if nominal_flight_fail is not None:
                t_fail_start = nominal_flight_fail.x[0, 0]
                idx = np.abs(nominal_flight.x[:, 0] - t_fail_start).argmin()
                plt.plot(nominal_flight.x[:idx+1, 1], nominal_flight.y[:idx+1, 1], color='black', linewidth=2, label='Nominal Trajectory', zorder=5)
                plt.plot(nominal_flight_fail.x[:, 1], nominal_flight_fail.y[:, 1], color='magenta', linestyle='-.', linewidth=2, label='Nominal Failure Trajectory', zorder=5)
                plt.scatter([nominal_flight_fail.x[-1, 1]], [nominal_flight_fail.y[-1, 1]], color='magenta', marker='*', s=150, label='Nominal Failure Impact', zorder=6)
            else:
                plt.plot(nominal_flight.x[:, 1], nominal_flight.y[:, 1], color='black', linewidth=2, label='Nominal Trajectory', zorder=5)
                plt.scatter([nominal_flight.x[-1, 1]], [nominal_flight.y[-1, 1]], color='black', marker='*', s=150, label='Nominal Impact', zorder=6)
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
    title_suffix = ""
    if nominal_flight is not None and hasattr(nominal_flight, 'env'):
        env = nominal_flight.env
        d = getattr(env, 'date', getattr(env, 'datetime_date', None))
        if isinstance(d, tuple) and len(d) >= 5:
            title_suffix += f"\nDate: {d[0]:04d}-{d[1]:02d}-{d[2]:02d} {d[3]:02d}:{d[4]:02d}"
        try:
            wd = float(env.wind_direction(10))
            ws = float((env.wind_velocity_x(10)**2 + env.wind_velocity_y(10)**2)**0.5)
            title_suffix += f" | Wind (10m): {ws:.1f} m/s @ {wd:.1f}°"
        except Exception:
            pass
            
    plt.title(f"Ground Dispersion Analysis\nRun: {run_id}{title_suffix}")
    plt.axis('equal')
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Add Nose cone landing site for neblina_1 projects
    if 'neblina_1' in str(results_dir):
        lat_nose = -21.9438267
        lon_nose = -48.9602672
        lat_pad = -21.938982
        lon_pad = -48.950316
        if nominal_flight is not None and hasattr(nominal_flight, 'env'):
            lat_pad = nominal_flight.env.latitude
            lon_pad = nominal_flight.env.longitude
            
        R = 6378137.0
        x_nose = np.radians(lon_nose - lon_pad) * R * np.cos(np.radians(lat_pad))
        y_nose = np.radians(lat_nose - lat_pad) * R
        plt.scatter(x_nose, y_nose, marker='X', color='darkred', s=150, zorder=10, edgecolors='black', label='Nose Cone Landing Site')
        
        lat_fuse = -21.943290
        lon_fuse = -48.960191
        x_fuse = np.radians(lon_fuse - lon_pad) * R * np.cos(np.radians(lat_pad))
        y_fuse = np.radians(lat_fuse - lat_pad) * R
        plt.scatter(x_fuse, y_fuse, marker='P', color='darkorange', s=150, zorder=10, edgecolors='black', label='Fuselage Landing Site')
        
    plt.legend()
    

    plot_path = results_dir / f"dispersion_plot_{run_id}.pdf"
    plt.savefig(plot_path, bbox_inches='tight')
    plt.close()
    
    # Generate 3D Isometric View of the Monte Carlo Dispersion
    fig_3d = plt.figure(figsize=(12, 10))
    ax_3d = fig_3d.add_subplot(111, projection='3d')
    
    # Scatter impacts on Z=0 plane
    ax_3d.scatter(x, y, np.zeros_like(x), s=5, alpha=0.5, label='Simulated Impacts (Z=0)', color='blue')
    
    # Draw ground plane to make ellipses and impacts clearly "on the ground"
    min_x, max_x = np.min(x) - 500, np.max(x) + 500
    min_y, max_y = np.min(y) - 500, np.max(y) + 500
    xx, yy = np.meshgrid(np.linspace(min_x, max_x, 10), np.linspace(min_y, max_y, 10))
    zz = np.zeros_like(xx)
    ax_3d.plot_surface(xx, yy, zz, color='lightgray', alpha=0.3)
    
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
            
    # Plot extreme trajectories in 3D
    try:
        for i, flt_data in enumerate(plotted_extremes):
            label = 'Extreme Trajectories' if i == 0 else None
            if 'z' in flt_data:
                ax_3d.plot(flt_data['x'], flt_data['y'], flt_data['z'], color='red', linestyle='--', linewidth=1, label=label, alpha=0.5)
    except:
        pass
        
    # Plot nominal trajectory in 3D
    max_z = 1000 # default
    if nominal_flight is not None:
        max_z = np.max(nominal_flight.z[:, 1])
        if nominal_flight_fail is not None:
            t_fail_start = nominal_flight_fail.x[0, 0]
            idx = np.abs(nominal_flight.x[:, 0] - t_fail_start).argmin()
            ax_3d.plot(nominal_flight.x[:idx+1, 1], nominal_flight.y[:idx+1, 1], nominal_flight.z[:idx+1, 1], color='black', linewidth=2, label='Nominal Trajectory')
            ax_3d.plot(nominal_flight_fail.x[:, 1], nominal_flight_fail.y[:, 1], nominal_flight_fail.z[:, 1], color='magenta', linestyle='-.', linewidth=2, label='Nominal Failure Trajectory')
            
            # Failure Point (mid-air)
            ax_3d.scatter([nominal_flight_fail.x[0, 1]], [nominal_flight_fail.y[0, 1]], [nominal_flight_fail.z[0, 1]], color='red', marker='X', s=100, label='Failure Point')
            
            # Impact Point (Z=0)
            ax_3d.scatter([nominal_flight_fail.x[-1, 1]], [nominal_flight_fail.y[-1, 1]], [0], color='magenta', marker='*', s=150, label='Nominal Failure Impact')
        else:
            ax_3d.plot(nominal_flight.x[:, 1], nominal_flight.y[:, 1], nominal_flight.z[:, 1], color='black', linewidth=2, label='Nominal Trajectory')
            ax_3d.scatter([nominal_flight.x[-1, 1]], [nominal_flight.y[-1, 1]], [0], color='black', marker='*', s=150, label='Nominal Impact')
            
    ax_3d.set_zlim(0, max_z * 1.1)

    ax_3d.plot([0], [0], [0], marker='*', color='black', markersize=12, label='Launch Pad')
    ax_3d.set_xlabel("East / x (m)")
    ax_3d.set_ylabel("North / y (m)")
    ax_3d.set_zlabel("Altitude / z (m)")
    ax_3d.set_title(f"3D Isometric Dispersion Analysis\nRun: {run_id}{title_suffix}")
    
    if 'neblina_1' in str(results_dir):
        ax_3d.scatter(x_nose, y_nose, 0, marker='X', color='darkred', s=150, zorder=10, edgecolors='black', label='Nose Cone Landing Site')
        ax_3d.scatter(x_fuse, y_fuse, 0, marker='P', color='darkorange', s=150, zorder=10, edgecolors='black', label='Fuselage Landing Site')
        
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
    fig.suptitle(f"Monte Carlo Statistical Distributions\nRun: {run_id}", fontsize=16)
    
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
