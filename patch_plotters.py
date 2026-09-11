import sys

with open("source/antares_fd/simulation/plotters.py", "r") as f:
    content = f.read()

replacement = """    # Scatter impacts on Z=0 plane
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
"""

# Now find the block to replace in plotters.py
start_marker = "    # Scatter impacts on Z=0 plane\n    ax_3d.scatter(x, y, np.zeros_like(x), s=5, alpha=0.5, label='Simulated Impacts (Z=0)', color='blue')"
end_marker = "    ax_3d.plot([0], [0], [0], marker='*', color='black', markersize=12, label='Launch Pad')"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx != -1 and end_idx != -1:
    new_content = content[:start_idx] + replacement + "\n" + content[end_idx:]
    with open("source/antares_fd/simulation/plotters.py", "w") as f:
        f.write(new_content)
    print("Patched plotters.py successfully.")
else:
    print("Could not find markers to patch plotters.py")

