import re
with open("source/antares_fd/simulation/plotters.py", "r") as f:
    content = f.read()

# 1. Update export_nominal_flight_plots to include combined Accel+Vel+Mach
new_plot_block = """
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
        plt.title("Acceleration, Velocity & Mach vs Time")
        pdf.savefig(fig)
        plt.close(fig)
"""

content = content.replace("        # 3. Acceleration vs Time", new_plot_block + "\n        # Acceleration vs Time")

# 2. Add 3D plot to Monte Carlo
mc_3d_code = """
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
    ax_3d.set_title(f"3D Isometric Dispersion Analysis\\nRun: {run_id}")
    ax_3d.legend()
    
    plot_3d_path = results_dir / f"dispersion_plot_3d_{run_id}.pdf"
    plt.savefig(plot_3d_path, bbox_inches='tight')
    plt.close(fig_3d)
    
    print(f"[Monte Carlo] 3D Dispersion plot saved to {plot_3d_path}")
"""

content = content.replace("    plot_path = results_dir / f\"dispersion_plot_{run_id}.pdf\"\n    plt.savefig(plot_path, bbox_inches='tight')\n    plt.close()", mc_3d_code)

with open("source/antares_fd/simulation/plotters.py", "w") as f:
    f.write(content)
