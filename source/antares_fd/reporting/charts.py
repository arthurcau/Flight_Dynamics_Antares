"""
Chart Generation for Antares Engineering Reports.

Generates standardized, publication-grade figures for nominal flights
and Monte Carlo campaigns. Every metric and boundary line aligns with
the centralized analysis single-source-of-truth.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for headless reporting
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
import numpy as np
import pandas as pd
import json

from .theme import setup_matplotlib_theme
from antares_fd.simulation.statistics import calculate_covariance_ellipse


def _get_flight_events(flight: Any) -> List[tuple[float, str]]:
    """Extracts key event timestamps from flight."""
    events = [(0.0, "Launch")]
    if hasattr(flight, "out_of_rail_time"):
        events.append((float(flight.out_of_rail_time), "Rail Exit"))
    if hasattr(flight, "rocket") and hasattr(flight.rocket, "motor"):
        events.append((float(flight.rocket.motor.burn_out_time), "Burnout"))
    if hasattr(flight, "apogee_time"):
        events.append((float(flight.apogee_time), "Apogee"))
    if hasattr(flight, "parachute_events"):
        for t_p, p_obj in flight.parachute_events:
            events.append((float(t_p), f"{p_obj.name} Trigger"))
            lag = getattr(p_obj, "lag", 0.0)
            if lag > 0.05:
                events.append((float(t_p + lag), f"{p_obj.name} Open"))
    if hasattr(flight, "t_final"):
        events.append((float(flight.t_final), "Touchdown"))
    events.sort(key=lambda x: x[0])
    return events


def _add_event_lines(ax, events: List[tuple[float, str]], max_t: Optional[float] = None, color: str = "#64748B"):
    """Annotates vertical event lines on an axes."""
    xlim = ax.get_xlim()
    t_limit = max_t if max_t is not None else xlim[1]
    y_min, y_max = ax.get_ylim()
    for t_ev, label in events:
        if t_ev <= t_limit and t_ev >= xlim[0]:
            ax.axvline(x=t_ev, color=color, linestyle="--", alpha=0.5, linewidth=0.8)
            ax.text(
                t_ev, y_min + 0.96 * (y_max - y_min),
                f" {label}", rotation=90, va="top", ha="left",
                fontsize=6.5, color=color, weight="medium"
            )


def generate_mass_and_propulsion_chart(flight: Any, output_path: Path) -> Path:
    """
    Generates high-density Mass & Propulsion diagnostics:
    - Motor Thrust and Instantaneous T/W vs Time
    - Vehicle Total Mass and Propellant Mass vs Time
    - Cumulative Impulse vs Time
    """
    setup_matplotlib_theme()
    rocket = flight.rocket
    motor = rocket.motor
    g0 = 9.80665

    t_bo = float(motor.burn_out_time)
    t_eval = np.linspace(0, t_bo * 1.15, 300)

    thrust_vals = np.array([float(motor.thrust(t)) if t <= t_bo else 0.0 for t in t_eval])
    mass_vals = np.array([float(rocket.total_mass(t)) for t in t_eval])
    prop_init = float(getattr(motor, "propellant_initial_mass", mass_vals[0] - mass_vals[-1]))
    dry_mass = float(rocket.mass)
    prop_vals = np.maximum(0.0, mass_vals - dry_mass)

    tw_vals = thrust_vals / (mass_vals * g0)
    dt = t_eval[1] - t_eval[0]
    cum_impulse = np.cumsum(thrust_vals) * dt

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(7.5, 5.2), sharex=True)

    # 1. Thrust & Instantaneous T/W
    ax1.plot(t_eval, thrust_vals, color="#EA580C", linewidth=1.6, label="Motor Thrust (N)")
    ax1.fill_between(t_eval, thrust_vals, color="#EA580C", alpha=0.15)
    ax1.set_ylabel("Thrust (N)", color="#EA580C")
    ax1.tick_params(axis="y", labelcolor="#EA580C")
    ax1.set_ylim(bottom=0)

    ax1_tw = ax1.twinx()
    ax1_tw.plot(t_eval, tw_vals, color="#2563EB", linestyle="--", linewidth=1.3, label="Thrust-to-Weight (T/W)")
    ax1_tw.set_ylabel("T/W Ratio (-)", color="#2563EB")
    ax1_tw.tick_params(axis="y", labelcolor="#2563EB")
    ax1_tw.set_ylim(bottom=0)
    ax1.set_title("Propulsion Dynamics & Mass Depletion Profile", fontsize=9.5)

    # 2. Total Mass & Propellant Mass
    ax2.plot(t_eval, mass_vals, color="#0B2545", linewidth=1.6, label="Total Vehicle Mass (kg)")
    ax2.plot(t_eval, prop_vals, color="#D97706", linestyle="-.", linewidth=1.4, label="Remaining Propellant (kg)")
    ax2.axhline(dry_mass, color="#64748B", linestyle=":", linewidth=1.0, label=f"Dry Mass ({dry_mass:.2f} kg)")
    ax2.set_ylabel("Mass (kg)")
    ax2.legend(loc="upper right", fontsize=7.5)
    ax2.set_ylim(bottom=0)

    # 3. Cumulative Impulse
    ax3.plot(t_eval, cum_impulse, color="#059669", linewidth=1.6, label="Cumulative Impulse (N·s)")
    total_imp = float(getattr(motor, "total_impulse", cum_impulse[-1]))
    ax3.axhline(total_imp, color="#059669", linestyle="--", linewidth=1.0, label=f"Total Impulse: {total_imp:.0f} N·s")
    ax3.set_ylabel("Impulse (N·s)")
    ax3.set_xlabel("Burn Time (s)")
    ax3.legend(loc="lower right", fontsize=7.5)
    ax3.set_xlim(0, t_bo * 1.15)

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    return output_path


def generate_kinematics_chart(flight: Any, output_path: Path, metrics: Optional[Dict[str, Any]] = None) -> Path:
    """
    Generates 3-panel Trajectory & Ascent Kinematics chart:
    - Altitude AGL with key milestone markers
    - Speed (m/s) and Mach number
    - Total Acceleration and Vertical Acceleration (Ascent Phase)
    """
    setup_matplotlib_theme()
    events = _get_flight_events(flight)
    t_apogee = float(flight.apogee_time)
    t_cutoff = t_apogee * 1.15  # Ascent & coast phase focus

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(7.5, 6.0), sharex=True)

    # 1. Altitude AGL
    t_z = flight.z[:, 0]
    elev = float(flight.env.elevation)
    z_agl = flight.z[:, 1] - elev
    mask_z = t_z <= t_cutoff
    ax1.plot(t_z[mask_z], z_agl[mask_z], color="#0B2545", linewidth=1.6, label="Altitude AGL (m)")
    ax1.set_ylabel("Altitude AGL (m)")
    ax1.set_title("Trajectory & Ascent Flight Kinematics (Boost & Coast Phase)", fontsize=9.5)
    ax1.legend(loc="upper left", fontsize=7.5)
    _add_event_lines(ax1, events, t_cutoff)

    # 2. Speed & Mach Number
    t_v = flight.speed[:, 0]
    v_vals = flight.speed[:, 1]
    mask_v = t_v <= t_cutoff
    ax2.plot(t_v[mask_v], v_vals[mask_v], color="#007ACC", linewidth=1.5, label="Velocity (m/s)")
    ax2.set_ylabel("Velocity (m/s)", color="#007ACC")
    ax2.tick_params(axis="y", labelcolor="#007ACC")

    ax2_mach = ax2.twinx()
    t_m = flight.mach_number[:, 0]
    m_vals = flight.mach_number[:, 1]
    mask_m = t_m <= t_cutoff
    ax2_mach.plot(t_m[mask_m], m_vals[mask_m], color="#D97706", linestyle="--", linewidth=1.3, label="Mach")
    ax2_mach.set_ylabel("Mach Number (-)", color="#D97706")
    ax2_mach.tick_params(axis="y", labelcolor="#D97706")
    _add_event_lines(ax2, events, t_cutoff)

    # 3. Acceleration
    t_a = flight.ax[:, 0]
    a_tot = np.sqrt(flight.ax[:, 1]**2 + flight.ay[:, 1]**2 + flight.az[:, 1]**2)
    a_tot_g = a_tot / 9.80665
    az_g = flight.az[:, 1] / 9.80665
    mask_a = t_a <= t_cutoff

    ax3.plot(t_a[mask_a], a_tot_g[mask_a], color="#DC2626", linewidth=1.5, label="Total Accel (g)")
    ax3.plot(t_a[mask_a], az_g[mask_a], color="#9333EA", linestyle=":", linewidth=1.2, label="Vertical Accel Z (g)")

    # Explicit peak ascent acceleration callout
    if metrics:
        max_ascent_g = metrics.get("kinematics", {}).get("max_total_acceleration", np.max(a_tot_g[mask_a]))
        t_max_a = metrics.get("kinematics", {}).get("time_max_ascent_accel_s", t_a[mask_a][np.argmax(a_tot_g[mask_a])])
        ax3.annotate(
            f"Peak Ascent: {max_ascent_g:.1f} g\nat {t_max_a:.2f} s",
            xy=(t_max_a, max_ascent_g),
            xytext=(t_max_a + 1.2, max_ascent_g * 0.9),
            arrowprops=dict(facecolor="#DC2626", shrink=0.08, width=1, headwidth=4),
            fontsize=7, weight="bold", color="#DC2626"
        )

    ax3.set_ylabel("Acceleration (g)")
    ax3.set_xlabel("Time (s)")
    ax3.legend(loc="upper right", fontsize=7.5)
    _add_event_lines(ax3, events, t_cutoff)

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    return output_path


def generate_propulsion_and_loads_chart(flight: Any, output_path: Path, metrics: Optional[Dict[str, Any]] = None) -> Path:
    """
    Generates Dynamic Pressure (Max Q) and Bending load Q * alpha (strictly post rail exit).
    """
    setup_matplotlib_theme()
    events = _get_flight_events(flight)
    t_apogee = float(flight.apogee_time)
    t_liftoff = float(flight.out_of_rail_time)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7.5, 4.8), sharex=True)

    # 1. Dynamic Pressure Q
    t_q = flight.dynamic_pressure[:, 0]
    q_vals = flight.dynamic_pressure[:, 1] / 1000.0  # kPa
    mask_q = t_q <= t_apogee * 1.1

    ax1.plot(t_q[mask_q], q_vals[mask_q], color="#0284C7", linewidth=1.6, label="Dynamic Pressure Q (kPa)")
    ax1.set_ylabel("Dynamic Pressure (kPa)")
    ax1.set_ylim(bottom=0)

    # Callout Max Q
    max_q_idx = int(np.argmax(q_vals[mask_q]))
    max_q_val = q_vals[mask_q][max_q_idx]
    max_q_time = t_q[mask_q][max_q_idx]
    ax1.plot(max_q_time, max_q_val, marker="o", color="#DC2626", markersize=6)
    ax1.annotate(
        f"Max Q: {max_q_val:.1f} kPa\nat {max_q_time:.2f} s",
        xy=(max_q_time, max_q_val),
        xytext=(max_q_time + 1.2, max_q_val * 0.88),
        arrowprops=dict(facecolor="#DC2626", shrink=0.08, width=1, headwidth=4),
        fontsize=7.5, weight="bold", color="#DC2626"
    )
    ax1.set_title("Aerodynamic Loading & Post-Rail Bending Moment Proxy", fontsize=9.5)
    _add_event_lines(ax1, events, t_apogee * 1.1)

    # 2. Aerodynamic Bending Moment (Q * alpha) - STRICTLY POST-RAIL EXIT
    t_alpha = flight.angle_of_attack[:, 0]
    alpha_vals = flight.angle_of_attack[:, 1]
    post_rail_mask = (t_q >= t_liftoff) & (t_q <= t_apogee * 1.1)

    t_post = t_q[post_rail_mask]
    q_post = q_vals[post_rail_mask] * 1000.0  # Pa
    alpha_post = np.interp(t_post, t_alpha, alpha_vals)
    qa_post = (q_post * np.abs(alpha_post)) / 1000.0  # kPa*deg

    ax2.plot(t_post, qa_post, color="#7C3AED", linewidth=1.6, label=r"$Q \cdot \alpha$ (Post-Rail Flight)")
    ax2.fill_between(t_post, qa_post, color="#7C3AED", alpha=0.15)
    ax2.set_ylabel(r"$Q \cdot \alpha$ (kPa·deg)", color="#7C3AED")
    ax2.set_xlabel("Time (s)")
    ax2.set_ylim(bottom=0)

    # Annotate peak Q*alpha
    if len(qa_post) > 0:
        max_qa_idx = int(np.argmax(qa_post))
        max_qa_val = qa_post[max_qa_idx]
        max_qa_time = t_post[max_qa_idx]
        ax2.plot(max_qa_time, max_qa_val, marker="^", color="#7C3AED", markersize=6)
        ax2.annotate(
            f"Peak Q·α: {max_qa_val:.1f} kPa·deg\nat {max_qa_time:.2f} s",
            xy=(max_qa_time, max_qa_val),
            xytext=(max_qa_time + 1.2, max_qa_val * 0.85),
            arrowprops=dict(facecolor="#7C3AED", shrink=0.08, width=1, headwidth=4),
            fontsize=7, weight="bold", color="#7C3AED"
        )

    _add_event_lines(ax2, events, t_apogee * 1.1)

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    return output_path


def generate_stability_and_attitude_chart(flight: Any, output_path: Path, metrics: Optional[Dict[str, Any]] = None) -> Path:
    """
    Generates CG/CP migration, Static Margin corridor, and Angle of Attack.
    Explicitly highlights Rail Exit, Max Q, Burnout, and Apogee milestones.
    """
    setup_matplotlib_theme()
    events = _get_flight_events(flight)
    t_apogee = float(flight.apogee_time)
    t_cutoff = t_apogee * 1.15
    rocket = flight.rocket

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7.5, 5.0), sharex=True)

    # 1. CG and CP Positions from nose tip
    t_eval = np.linspace(0, t_cutoff, 250)
    cg_vals = [float(rocket.center_of_mass(t)) for t in t_eval]
    cp_vals = [float(rocket.cp_position(t)) for t in t_eval]

    ax1.plot(t_eval, cp_vals, color="#DC2626", linewidth=1.6, label="Center of Pressure (CP)")
    ax1.plot(t_eval, cg_vals, color="#2563EB", linewidth=1.6, label="Center of Gravity (CG)")
    ax1.fill_between(t_eval, cg_vals, cp_vals, color="#10B981", alpha=0.15, label="Static Margin Span (CG → CP)")
    ax1.set_ylabel("Position from Nose (m)")
    ax1.set_xlim(0, t_cutoff)
    ax1.legend(loc="upper right", fontsize=7.5)
    ax1.set_title("Static Stability Envelope & Aerodynamic Center Migration", fontsize=9.5)
    _add_event_lines(ax1, events, t_cutoff)

    # 2. Static Margin (calibers)
    t_sm = flight.static_margin[:, 0]
    sm_vals = flight.static_margin[:, 1]
    mask_sm = t_sm <= t_cutoff

    ax2.plot(t_sm[mask_sm], sm_vals[mask_sm], color="#059669", linewidth=1.6, label="Static Margin (cal)")
    ax2.axhspan(1.5, 3.5, color="#10B981", alpha=0.15, label="Preferred Range (1.5 - 3.5 cal)")
    ax2.axhline(1.0, color="#DC2626", linestyle="--", linewidth=1.1, label="Min Stability Limit (1.0 cal)")

    # Highlight Static Margin at Max-Q
    if metrics:
        sm_mq = metrics.get("aerodynamic_loads", {}).get("static_margin_at_max_q_cal")
        t_mq = metrics.get("aerodynamic_loads", {}).get("time_max_dynamic_pressure_s")
        if sm_mq and t_mq:
            ax2.plot(t_mq, sm_mq, marker="s", color="#D97706", markersize=6)
            ax2.annotate(
                f"SM at Max-Q: {sm_mq:.2f} cal\n(t = {t_mq:.1f} s)",
                xy=(t_mq, sm_mq),
                xytext=(t_mq + 1.2, sm_mq - 0.5),
                arrowprops=dict(facecolor="#D97706", shrink=0.08, width=1, headwidth=4),
                fontsize=7, weight="bold", color="#D97706"
            )

    ax2.set_ylabel("Static Margin (cal)", color="#059669")
    ax2.set_xlabel("Time (s)")
    ax2.set_ylim(0, max(5.0, float(np.max(sm_vals[mask_sm])) + 0.5))
    ax2.legend(loc="upper right", fontsize=7.5)
    _add_event_lines(ax2, events, t_cutoff)

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    return output_path


def generate_full_atmosphere_chart(flight: Any, output_path: Path) -> Path:
    """
    Generates a full-page 4-panel Atmospheric Profile based on MAGI data:
    - Wind Speed vs Altitude AGL
    - Wind Direction vs Altitude AGL
    - Density and Speed of Sound vs Altitude AGL
    - Wind Hodograph (U-East vs V-North)
    """
    setup_matplotlib_theme()
    env = flight.env
    elev = float(env.elevation)
    z_max = float(flight.apogee) if hasattr(flight, "apogee") else 4000.0
    z_eval = np.linspace(elev, z_max * 1.1, 200)
    z_agl = z_eval - elev

    u_east = []
    v_north = []
    wind_speeds = []
    wind_dirs = []
    densities = []
    sound_speeds = []

    for z in z_eval:
        try:
            wx = float(env.wind_velocity_x(z))
            wy = float(env.wind_velocity_y(z))
            spd = float(np.hypot(wx, wy))
            direction = float(np.degrees(np.arctan2(wx, wy)) % 360)
            rho = float(env.density(z))
            c = float(env.speed_of_sound(z))
        except Exception:
            wx, wy = 0.0, 0.0
            spd, direction = 0.0, 0.0
            rho, c = 1.2, 340.0
        u_east.append(wx)
        v_north.append(wy)
        wind_speeds.append(spd)
        wind_dirs.append(direction)
        densities.append(rho)
        sound_speeds.append(c)

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(7.5, 6.2))

    # 1. Wind Speed vs Altitude
    ax1.plot(wind_speeds, z_agl, color="#1D4ED8", linewidth=1.6)
    ax1.set_xlabel("Wind Speed (m/s)")
    ax1.set_ylabel("Altitude AGL (m)")
    ax1.set_title("Wind Velocity Magnitude", fontsize=9)
    ax1.set_xlim(left=0)

    # 2. Wind Direction vs Altitude
    ax2.plot(wind_dirs, z_agl, color="#D97706", linewidth=1.6)
    ax2.set_xlabel("Wind Direction (°Azimuth)")
    ax2.set_ylabel("Altitude AGL (m)")
    ax2.set_title("Wind Direction Heading", fontsize=9)
    ax2.set_xlim(0, 360)

    # 3. Density & Speed of Sound
    ax3.plot(densities, z_agl, color="#047857", linewidth=1.6, label=r"Density $\rho$ (kg/m³)")
    ax3.set_xlabel(r"Air Density (kg/m³)", color="#047857")
    ax3.set_ylabel("Altitude AGL (m)")
    ax3.tick_params(axis="x", labelcolor="#047857")

    ax3_c = ax3.twiny()
    ax3_c.plot(sound_speeds, z_agl, color="#7C3AED", linestyle="--", linewidth=1.3, label="Sound Speed (m/s)")
    ax3_c.set_xlabel("Speed of Sound (m/s)", color="#7C3AED")
    ax3_c.tick_params(axis="x", labelcolor="#7C3AED")
    ax3.set_title("Atmospheric Thermodynamics & Acoustics", fontsize=9)

    # 4. Wind Hodograph (U vs V)
    ax4.plot(u_east, v_north, color="#0B2545", linewidth=1.4, marker="o", markersize=2)
    ax4.scatter([u_east[0]], [v_north[0]], color="#10B981", marker="*", s=80, label="Surface (0m AGL)", zorder=5)
    ax4.scatter([u_east[-1]], [v_north[-1]], color="#DC2626", marker="^", s=60, label=f"Apogee ({z_agl[-1]:.0f}m)", zorder=5)
    ax4.axhline(0, color="#64748B", linestyle=":", linewidth=0.8)
    ax4.axvline(0, color="#64748B", linestyle=":", linewidth=0.8)
    ax4.set_xlabel("East Component U (m/s)")
    ax4.set_ylabel("North Component V (m/s)")
    ax4.set_title("Wind Hodograph (Vertical Shear)", fontsize=9)
    ax4.axis("equal")
    ax4.legend(loc="upper right", fontsize=7)

    fig.suptitle("MAGI High-Fidelity Atmospheric Environmental Profile", fontsize=10.5, y=0.99)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    return output_path


def generate_recovery_descent_chart(flight: Any, output_path: Path) -> Path:
    """Generates Recovery Profile: Altitude vs Time from Apogee to Touchdown, and sink rate."""
    setup_matplotlib_theme()
    events = _get_flight_events(flight)
    t_apogee = float(flight.apogee_time)
    t_final = float(flight.t_final)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7.5, 4.4), sharex=True)

    t_z = flight.z[:, 0]
    elev = float(flight.env.elevation)
    z_agl = flight.z[:, 1] - elev
    descent_mask = (t_z >= t_apogee * 0.95) & (t_z <= t_final)

    # 1. Descent Altitude
    ax1.plot(t_z[descent_mask], z_agl[descent_mask], color="#047857", linewidth=1.6, label="Altitude AGL (m)")
    ax1.set_ylabel("Altitude AGL (m)")
    ax1.set_xlim(t_apogee * 0.95, t_final * 1.02)
    ax1.set_title("Recovery & Descent Phase Profile", fontsize=9.5)
    ax1.legend(loc="upper right", fontsize=7.5)
    _add_event_lines(ax1, events)

    # 2. Sink rate (|Vz|)
    t_vz = flight.vz[:, 0]
    vz_vals = np.abs(flight.vz[:, 1])
    mask_vz = (t_vz >= t_apogee * 0.95) & (t_vz <= t_final)
    ax2.plot(t_vz[mask_vz], vz_vals[mask_vz], color="#B45309", linewidth=1.5, label="Descent Sink Rate |Vz| (m/s)")
    ax2.axhline(8.0, color="#10B981", linestyle="--", linewidth=1.1, label="Safe Touchdown Limit (≤ 8.0 m/s)")
    ax2.set_ylabel("Descent Speed (m/s)")
    ax2.set_xlabel("Time (s)")
    ax2.legend(loc="upper right", fontsize=7.5)
    _add_event_lines(ax2, events)

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    return output_path


def generate_trajectory_views_chart(flight: Any, output_path: Path) -> Path:
    """Generates 2D trajectory overview: Altitude vs Downrange and Top-Down ground track."""
    setup_matplotlib_theme()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.5, 3.5))

    elev = float(flight.env.elevation)
    x = flight.x[:, 1]
    y = flight.y[:, 1]
    z_agl = flight.z[:, 1] - elev
    downrange = np.sqrt(x**2 + y**2)

    # 1. Altitude vs Downrange
    ax1.plot(downrange, z_agl, color="#1E3A8A", linewidth=1.6)
    apogee_idx = int(np.argmax(z_agl))
    ax1.scatter([downrange[apogee_idx]], [z_agl[apogee_idx]], color="#DC2626", marker="^", s=60, label="Apogee", zorder=5)
    ax1.scatter([0], [0], color="#000000", marker="*", s=80, label="Pad", zorder=5)
    ax1.scatter([downrange[-1]], [0], color="#D97706", marker="X", s=60, label="Touchdown", zorder=5)
    ax1.set_xlabel("Horizontal Distance (m)")
    ax1.set_ylabel("Altitude AGL (m)")
    ax1.set_title("Vertical Profile (Distance vs Alt)", fontsize=9)
    ax1.legend(loc="upper right", fontsize=7.5)

    # 2. Top-Down Ground Track (X-Y)
    ax2.plot(x, y, color="#0284C7", linewidth=1.6)
    ax2.scatter([x[apogee_idx]], [y[apogee_idx]], color="#DC2626", marker="^", s=60, label="Apogee", zorder=5)
    ax2.scatter([0], [0], color="#000000", marker="*", s=80, label="Pad", zorder=5)
    ax2.scatter([x[-1]], [y[-1]], color="#D97706", marker="X", s=60, label="Touchdown", zorder=5)
    ax2.set_xlabel("East / X (m)")
    ax2.set_ylabel("North / Y (m)")
    ax2.set_title("Ground Track (X-Y Plane)", fontsize=9)
    ax2.axis("equal")
    ax2.legend(loc="upper right", fontsize=7.5)

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    return output_path


def generate_multi_scenario_chart(scenario_flights: Dict[str, Any], output_path: Path) -> Path:
    """
    Generates high-density comparative multi-scenario flight dynamics charts:
    - Top panel: Altitude AGL vs Time for all scenarios (Nominal, Ballistic, Main at Apogee, Separation, Only Reefing)
    - Bottom panel: Ground Downrange Distance vs Time for all scenarios
    """
    setup_matplotlib_theme()
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7.5, 5.2))

    styles_map = {
        "Nominal Flight": {"color": "#2563EB", "linestyle": "-", "linewidth": 1.8, "marker": "o"},
        "Ballistic Free-Fall": {"color": "#DC2626", "linestyle": "-.", "linewidth": 1.6, "marker": "X"},
        "Main at Apogee": {"color": "#D97706", "linestyle": "--", "linewidth": 1.6, "marker": "s"},
        "Separation at Main": {"color": "#7C3AED", "linestyle": ":", "linewidth": 1.7, "marker": "^"},
        "Only Reefing Descent": {"color": "#059669", "linestyle": "-", "linewidth": 1.5, "marker": "D"},
    }

    max_t = 0.0
    for name, flight in scenario_flights.items():
        elev = float(flight.env.elevation)
        t_z = flight.z[:, 0]
        z_agl = flight.z[:, 1] - elev
        x = flight.x[:, 1]
        y = flight.y[:, 1]
        downrange = np.sqrt(x**2 + y**2)
        t_xy = flight.x[:, 0]
        t_final = float(flight.t_final)
        max_t = max(max_t, t_final)

        cfg = styles_map.get(name, {"color": "#64748B", "linestyle": "-", "linewidth": 1.5, "marker": "o"})

        # 1. Altitude vs Time
        ax1.plot(t_z, z_agl, color=cfg["color"], linestyle=cfg["linestyle"], linewidth=cfg["linewidth"], label=f"{name} ({t_final:.1f}s)")
        ax1.scatter([t_final], [0], color=cfg["color"], marker=cfg["marker"], s=45, zorder=5)

        # 2. Downrange vs Time
        ax2.plot(t_xy, downrange, color=cfg["color"], linestyle=cfg["linestyle"], linewidth=cfg["linewidth"], label=f"{name} ({downrange[-1]:.0f}m)")
        ax2.scatter([t_xy[-1]], [downrange[-1]], color=cfg["color"], marker=cfg["marker"], s=45, zorder=5)

    ax1.set_ylabel("Altitude AGL (m)")
    ax1.set_title("Comparative Altitude Trajectories (AGL vs Flight Time)", fontsize=9.5)
    ax1.set_ylim(bottom=0)
    ax1.set_xlim(0, max_t * 1.02)
    ax1.legend(loc="upper right", fontsize=7.2)

    ax2.set_ylabel("Ground Distance (m)")
    ax2.set_xlabel("Flight Time (s)")
    ax2.set_title("Ground Drift Distance from Pad vs Flight Time", fontsize=9.5)
    ax2.set_ylim(bottom=0)
    ax2.set_xlim(0, max_t * 1.02)
    ax2.legend(loc="upper left", fontsize=7.2)

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    return output_path


def generate_landing_validation_map_chart(validation_data: Dict[str, Any], output_path: Path) -> Optional[Path]:
    """
    Generates high-resolution Cartographic V&V Map:
    Pad ★, Predicted Touchdown ●, Actual Fuselage ×, Actual Nose Cone ×
    Concentric range rings (500m, 1000m, 1500m) and error vectors.
    """
    if not validation_data or not validation_data.get("has_field_data"):
        return None

    setup_matplotlib_theme()
    fig, ax = plt.subplots(figsize=(7.5, 5.0))

    pred = validation_data["predicted"]
    fuse = validation_data["fuselage"]
    nose = validation_data["nose_cone"]

    # Range rings
    rings = [500, 1000, 1500]
    for r in rings:
        circle = plt.Circle((0, 0), r, color="#94A3B8", fill=False, linestyle=":", linewidth=0.8)
        ax.add_patch(circle)
        ax.text(0, r + 20, f"{r} m", color="#94A3B8", fontsize=6.5, ha="center")

    # Plot origin (Pad)
    ax.scatter(0, 0, marker="*", color="#000000", s=140, label="Launch Pad (Origin)", zorder=10)

    # Plot Predicted Landing
    ax.scatter(pred["x"], pred["y"], marker="o", color="#2563EB", s=90, edgecolors="#0B2545", label=f"Predicted Impact ({pred['dist']:.0f}m)", zorder=9)

    # Plot Actual Fuselage & Nose Cone
    ax.scatter(fuse["x"], fuse["y"], marker="P", color="#EA580C", s=110, edgecolors="#000000", label=f"Measured Fuselage GPS ({fuse['dist']:.0f}m)", zorder=9)
    ax.scatter(nose["x"], nose["y"], marker="X", color="#DC2626", s=110, edgecolors="#000000", label=f"Measured Nose Cone GPS ({nose['dist']:.0f}m)", zorder=9)

    # Error vector lines
    ax.plot([pred["x"], fuse["x"]], [pred["y"], fuse["y"]], color="#EA580C", linestyle="--", linewidth=1.2, label=f"Fuselage Residual ({abs(fuse['err_radial_m']):.0f} m)")
    ax.plot([pred["x"], nose["x"]], [pred["y"], nose["y"]], color="#DC2626", linestyle=":", linewidth=1.2, label=f"Nose Cone Residual ({abs(nose['err_radial_m']):.0f} m)")

    ax.set_xlabel("East Displacement X (m)")
    ax.set_ylabel("North Displacement Y (m)")
    ax.set_title("Landing Prediction Verification & Field GPS Validation", fontsize=10)
    ax.axis("equal")
    ax.legend(loc="upper left", fontsize=7.5)

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    return output_path


def generate_mc_dispersion_chart(outputs_file: Path, output_path: Path, run_id: str, validation_data: Optional[Dict[str, Any]] = None) -> Optional[Path]:
    """Generates 2D Ground Dispersion with 50%, 90%, 95%, 99% covariance ellipses and KDE contours."""
    if not outputs_file.exists():
        return None

    x_impact, y_impact = [], []
    with open(outputs_file, "r") as f:
        for line in f:
            if not line.strip(): continue
            try:
                data = json.loads(line)
                if "x_impact" in data and "y_impact" in data:
                    x_impact.append(data["x_impact"])
                    y_impact.append(data["y_impact"])
            except Exception:
                pass

    if len(x_impact) < 5:
        return None

    setup_matplotlib_theme()
    x = np.array(x_impact)
    y = np.array(y_impact)

    fig, ax = plt.subplots(figsize=(7.5, 5.2))

    # Scatter simulated impacts
    ax.scatter(x, y, s=12, color="#3B82F6", alpha=0.6, label="Simulated Impacts", zorder=3)
    ax.scatter(0, 0, marker="*", color="#000000", s=120, label="Launch Pad", zorder=10)

    # Covariance ellipses
    probs = [(0.50, "#10B981", "50% Containment"), (0.90, "#F59E0B", "90% Containment"), (0.95, "#EF4444", "95% Containment"), (0.99, "#8B5CF6", "99% Containment")]
    for p, col, lbl in probs:
        try:
            ellipse_data = calculate_covariance_ellipse(x, y, p)
            ell = Ellipse(
                xy=ellipse_data["center"],
                width=ellipse_data["width"],
                height=ellipse_data["height"],
                angle=ellipse_data["angle"],
                edgecolor=col,
                fc="None",
                lw=1.5,
                label=lbl,
                zorder=5
            )
            ax.add_patch(ell)
        except Exception:
            pass

    # Overlay validation points if available
    if validation_data and validation_data.get("has_field_data"):
        fuse = validation_data["fuselage"]
        nose = validation_data["nose_cone"]
        ax.scatter(fuse["x"], fuse["y"], marker="P", color="#EA580C", s=100, edgecolors="#000000", label="Measured Fuselage", zorder=9)
        ax.scatter(nose["x"], nose["y"], marker="X", color="#DC2626", s=100, edgecolors="#000000", label="Measured Nose Cone", zorder=9)

    ax.set_xlabel("East Displacement X (m)")
    ax.set_ylabel("North Displacement Y (m)")
    ax.set_title(f"Monte Carlo 2D Ground Dispersion & Containment Ellipses ({len(x)} Cases)", fontsize=9.5)
    ax.axis("equal")
    ax.legend(loc="upper left", fontsize=7)

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    return output_path


def generate_mc_distributions_chart(outputs_file: Path, output_path: Path) -> Optional[Path]:
    """Generates 4-panel Monte Carlo statistical distribution histograms."""
    if not outputs_file.exists():
        return None

    records = []
    with open(outputs_file, "r") as f:
        for line in f:
            if not line.strip(): continue
            try:
                records.append(json.loads(line))
            except Exception:
                pass

    if len(records) < 5:
        return None

    df = pd.DataFrame(records)
    required = ["apogee", "out_of_rail_velocity", "max_mach_number", "impact_velocity"]
    if not all(c in df.columns for c in required):
        return None

    setup_matplotlib_theme()
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(7.5, 5.0))

    # 1. Apogee
    ax1.hist(df["apogee"], bins=25, color="#60A5FA", edgecolor="#1E3A8A", alpha=0.8)
    m_ap = df["apogee"].mean()
    s_ap = df["apogee"].std()
    ax1.axvline(m_ap, color="#DC2626", linestyle="--", linewidth=1.4, label=f"Mean: {m_ap:.0f} m")
    ax1.axvline(m_ap + s_ap, color="#D97706", linestyle=":", linewidth=1.0, label=f"±1σ: {s_ap:.0f} m")
    ax1.axvline(m_ap - s_ap, color="#D97706", linestyle=":", linewidth=1.0)
    ax1.set_xlabel("Apogee Altitude (m)")
    ax1.set_ylabel("Frequency")
    ax1.set_title("Apogee Distribution", fontsize=8.5)
    ax1.legend(fontsize=6.5)

    # 2. Rail Exit Velocity
    ax2.hist(df["out_of_rail_velocity"], bins=25, color="#34D399", edgecolor="#065F46", alpha=0.8)
    m_oor = df["out_of_rail_velocity"].mean()
    ax2.axvline(m_oor, color="#DC2626", linestyle="--", linewidth=1.4, label=f"Mean: {m_oor:.1f} m/s")
    ax2.axvline(30.0, color="#7C3AED", linestyle="-", linewidth=1.2, label="Requirement (≥ 30 m/s)")
    ax2.set_xlabel("Rail Exit Velocity (m/s)")
    ax2.set_ylabel("Frequency")
    ax2.set_title("Rail Exit Velocity Distribution", fontsize=8.5)
    ax2.legend(fontsize=6.5)

    # 3. Max Mach Number
    ax3.hist(df["max_mach_number"], bins=25, color="#F87171", edgecolor="#991B1B", alpha=0.8)
    m_mach = df["max_mach_number"].mean()
    ax3.axvline(m_mach, color="#1D4ED8", linestyle="--", linewidth=1.4, label=f"Mean: {m_mach:.2f} M")
    ax3.axvline(0.80, color="#D97706", linestyle="-", linewidth=1.2, label="Subsonic Boundary (0.80 M)")
    ax3.set_xlabel("Maximum Mach Number (-)")
    ax3.set_ylabel("Frequency")
    ax3.set_title("Max Mach Distribution", fontsize=8.5)
    ax3.legend(fontsize=6.5)

    # 4. Touchdown Velocity
    imp_vel = np.abs(df["impact_velocity"])
    ax4.hist(imp_vel, bins=25, color="#A78BFA", edgecolor="#5B21B6", alpha=0.8)
    m_imp = imp_vel.mean()
    ax4.axvline(m_imp, color="#DC2626", linestyle="--", linewidth=1.4, label=f"Mean: {m_imp:.1f} m/s")
    ax4.axvline(8.0, color="#10B981", linestyle="-", linewidth=1.2, label="Safety Limit (≤ 8.0 m/s)")
    ax4.set_xlabel("Touchdown Velocity (m/s)")
    ax4.set_ylabel("Frequency")
    ax4.set_title("Touchdown Velocity Distribution", fontsize=8.5)
    ax4.legend(fontsize=6.5)

    fig.suptitle("Monte Carlo Output Distributions & Requirement Compliance", fontsize=10, y=0.99)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    return output_path


def generate_mc_convergence_chart(outputs_file: Path, output_path: Path) -> Optional[Path]:
    """Generates Running Mean and Standard Deviation stabilization curves."""
    if not outputs_file.exists():
        return None

    records = []
    with open(outputs_file, "r") as f:
        for line in f:
            if not line.strip(): continue
            try:
                records.append(json.loads(line))
            except Exception:
                pass

    if len(records) < 10:
        return None

    df = pd.DataFrame(records)
    if "apogee" not in df.columns:
        return None

    setup_matplotlib_theme()
    df["run_mean_apogee"] = df["apogee"].expanding().mean()
    df["run_std_apogee"] = df["apogee"].expanding().std()
    x_axis = np.arange(1, len(df) + 1)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7.5, 4.4), sharex=True)

    # 1. Running Mean & Standard Deviation Envelope
    ax1.plot(x_axis, df["run_mean_apogee"], color="#2563EB", linewidth=1.6, label="Running Mean Apogee (m)")
    ax1.fill_between(
        x_axis,
        df["run_mean_apogee"] - df["run_std_apogee"],
        df["run_mean_apogee"] + df["run_std_apogee"],
        color="#2563EB", alpha=0.15, label="±1σ Running Envelope"
    )
    ax1.set_ylabel("Apogee (m)")
    ax1.set_title("Monte Carlo Statistical Convergence & Sample Sufficiency", fontsize=9.5)
    ax1.legend(loc="upper right", fontsize=7.5)

    # 2. Standard Deviation Stabilization (% of Final)
    final_std = df["run_std_apogee"].iloc[-1]
    if final_std > 0:
        pct_dev = (df["run_std_apogee"] / final_std - 1.0) * 100
        ax2.plot(x_axis, pct_dev, color="#DC2626", linewidth=1.5, label="Std Dev Deviation from Final (%)")
        ax2.axhline(5.0, color="#64748B", linestyle="--", linewidth=0.9, label="±5% Stabilization Corridor")
        ax2.axhline(-5.0, color="#64748B", linestyle="--", linewidth=0.9)
        ax2.set_ylim(-20, 20)
        ax2.set_ylabel("Std Dev Drift (%)")
        ax2.set_xlabel("Number of Iterations (N)")
        ax2.legend(loc="lower right", fontsize=7.5)

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    return output_path


def generate_sensitivity_tornado_chart(sensitivity_data: Dict[str, Any], output_path: Path) -> Optional[Path]:
    """Generates a horizontal Tornado Bar Chart of parameter sensitivities."""
    ranking = sensitivity_data.get("sensitivity_ranking", [])
    if not ranking:
        return None

    setup_matplotlib_theme()
    top_items = ranking[:10]
    top_items.reverse()  # Top item at top of chart

    params = [item["parameter"].replace("_", " ").title() for item in top_items]
    corrs = [item["pearson_r"] for item in top_items]
    colors = ["#10B981" if c >= 0 else "#EF4444" for c in corrs]

    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    y_pos = np.arange(len(params))

    bars = ax.barh(y_pos, corrs, color=colors, alpha=0.85, edgecolor="#1E293B", height=0.6)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(params, fontsize=8)
    ax.axvline(0, color="#64748B", linewidth=1.0)
    ax.set_xlim(-1.0, 1.0)
    ax.set_xlabel(f"Pearson Correlation Coefficient (r) with {sensitivity_data.get('sensitivity_target', 'Metric').replace('_', ' ').title()}")
    ax.set_title(f"Global Sensitivity Tornado Ranking ({sensitivity_data.get('num_cases', 0)} Cases)", fontsize=9.5)

    # Annotate values
    for bar, c in zip(bars, corrs):
        width = bar.get_width()
        ha = "left" if width >= 0 else "right"
        offset = 0.03 if width >= 0 else -0.03
        ax.text(width + offset, bar.get_y() + bar.get_height() / 2, f"{c:+.2f}", va="center", ha=ha, fontsize=7.5, weight="bold")

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    return output_path
