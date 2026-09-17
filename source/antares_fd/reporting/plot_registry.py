"""
Chart Generation for Antares Engineering Reports.
Consumes ONLY FlightMetrics. No RocketPy dependencies allowed.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
import numpy as np
import json
import pandas as pd

from antares_fd.analysis.flight_metrics import FlightMetrics
from .theme import setup_matplotlib_theme
from antares_fd.simulation.statistics import calculate_covariance_ellipse


def _get_flight_events(metrics: FlightMetrics) -> List[tuple[float, str]]:
    """Extracts key event timestamps from FlightMetrics."""
    events = [(0.0, "Launch"), (metrics.rail_exit_time, "Rail Exit"), 
              (metrics.burnout_time, "Burnout"), (metrics.apogee_time, "Apogee")]
    
    if metrics.drogue_event:
        events.append((metrics.drogue_event.time, f"{metrics.drogue_event.name} Trigger"))
        if metrics.drogue_event.lag > 0.05:
            events.append((metrics.drogue_event.deploy_time, f"{metrics.drogue_event.name} Open"))
            
    if metrics.main_event:
        events.append((metrics.main_event.time, f"{metrics.main_event.name} Trigger"))
        if metrics.main_event.lag > 0.05:
            events.append((metrics.main_event.deploy_time, f"{metrics.main_event.name} Open"))
            
    events.append((metrics.flight_duration_time, "Touchdown"))
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


def generate_mass_and_propulsion_chart(metrics: FlightMetrics, output_path: Path) -> Path:
    setup_matplotlib_theme()
    g0 = 9.80665
    t_bo = metrics.burn_time
    ts = metrics.timeseries

    mask = ts.time <= t_bo * 1.15
    t_eval = ts.time[mask]
    thrust_vals = ts.thrust[mask]
    mass_vals = ts.mass[mask]
    
    prop_vals = np.maximum(0.0, mass_vals - metrics.dry_mass)
    tw_vals = thrust_vals / (mass_vals * g0)
    
    dt = np.diff(t_eval, prepend=0)
    cum_impulse = np.cumsum(thrust_vals * dt)

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
    ax2.axhline(metrics.dry_mass, color="#64748B", linestyle=":", linewidth=1.0, label=f"Dry Mass ({metrics.dry_mass:.2f} kg)")
    ax2.set_ylabel("Mass (kg)")
    ax2.legend(loc="upper right", fontsize=7.5)
    ax2.set_ylim(bottom=0)

    # 3. Cumulative Impulse
    ax3.plot(t_eval, cum_impulse, color="#059669", linewidth=1.6, label="Cumulative Impulse (N·s)")
    total_imp = metrics.total_impulse
    if total_imp > 0:
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


def generate_kinematics_chart(metrics: FlightMetrics, output_path: Path) -> Path:
    setup_matplotlib_theme()
    events = _get_flight_events(metrics)
    t_cutoff = metrics.apogee_time * 1.15
    ts = metrics.timeseries

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(7.5, 6.0), sharex=True)

    mask = ts.time <= t_cutoff
    t_eval = ts.time[mask]

    # 1. Altitude AGL
    ax1.plot(t_eval, ts.altitude_agl[mask], color="#0B2545", linewidth=1.6, label="Altitude AGL (m)")
    ax1.set_ylabel("Altitude AGL (m)")
    ax1.set_title("Trajectory & Ascent Flight Kinematics (Boost & Coast Phase)", fontsize=9.5)
    ax1.legend(loc="upper left", fontsize=7.5)
    _add_event_lines(ax1, events, t_cutoff)

    # 2. Speed & Mach Number
    ax2.plot(t_eval, ts.speed[mask], color="#007ACC", linewidth=1.5, label="Velocity (m/s)")
    ax2.set_ylabel("Velocity (m/s)", color="#007ACC")
    ax2.tick_params(axis="y", labelcolor="#007ACC")

    ax2_mach = ax2.twinx()
    ax2_mach.plot(t_eval, ts.mach[mask], color="#D97706", linestyle="--", linewidth=1.3, label="Mach")
    ax2_mach.set_ylabel("Mach Number (-)", color="#D97706")
    ax2_mach.tick_params(axis="y", labelcolor="#D97706")
    _add_event_lines(ax2, events, t_cutoff)

    # 3. Acceleration
    a_tot_g = ts.acceleration[mask] / 9.80665
    az_g = ts.acceleration_z[mask] / 9.80665

    ax3.plot(t_eval, a_tot_g, color="#DC2626", linewidth=1.5, label="Total Accel (g)")
    ax3.plot(t_eval, az_g, color="#9333EA", linestyle=":", linewidth=1.2, label="Vertical Accel Z (g)")

    # Explicit peak ascent acceleration callout
    max_ascent_g = metrics.max_ascent_acceleration_g
    t_max_a = metrics.max_ascent_acceleration_time
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


def generate_propulsion_and_loads_chart(metrics: FlightMetrics, output_path: Path) -> Path:
    setup_matplotlib_theme()
    events = _get_flight_events(metrics)
    ts = metrics.timeseries

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7.5, 4.8), sharex=True)

    mask_q = ts.time <= metrics.apogee_time * 1.1
    t_q = ts.time[mask_q]
    q_vals_kpa = ts.dynamic_pressure[mask_q] / 1000.0

    ax1.plot(t_q, q_vals_kpa, color="#0284C7", linewidth=1.6, label="Dynamic Pressure Q (kPa)")
    ax1.set_ylabel("Dynamic Pressure (kPa)")
    ax1.set_ylim(bottom=0)

    # Callout Max Q
    max_q_time = metrics.max_dynamic_pressure_time
    max_q_val = metrics.max_dynamic_pressure / 1000.0
    ax1.plot(max_q_time, max_q_val, marker="o", color="#DC2626", markersize=6)
    ax1.annotate(
        f"Max Q: {max_q_val:.1f} kPa\nat {max_q_time:.2f} s",
        xy=(max_q_time, max_q_val),
        xytext=(max_q_time + 1.2, max_q_val * 0.88),
        arrowprops=dict(facecolor="#DC2626", shrink=0.08, width=1, headwidth=4),
        fontsize=7.5, weight="bold", color="#DC2626"
    )
    ax1.set_title("Aerodynamic Loading & Post-Rail Bending Moment Proxy", fontsize=9.5)
    _add_event_lines(ax1, events, metrics.apogee_time * 1.1)

    # 2. Aerodynamic Bending Moment (Q * alpha)
    post_rail_mask = (ts.time >= metrics.rail_exit_time) & (ts.time <= metrics.apogee_time * 1.1)
    t_post = ts.time[post_rail_mask]
    qa_post = (ts.q_alpha[post_rail_mask]) / 1000.0  # kPa*deg

    ax2.plot(t_post, qa_post, color="#7C3AED", linewidth=1.6, label=r"$Q \cdot \alpha$ (Post-Rail Flight)")
    ax2.fill_between(t_post, qa_post, color="#7C3AED", alpha=0.15)
    ax2.set_ylabel(r"$Q \cdot \alpha$ (kPa·deg)", color="#7C3AED")
    ax2.set_xlabel("Time (s)")
    ax2.set_ylim(bottom=0)

    max_qa_time = metrics.peak_q_alpha_time
    max_qa_val = metrics.peak_q_alpha / 1000.0
    if max_qa_val > 0.0:
        ax2.plot(max_qa_time, max_qa_val, marker="^", color="#7C3AED", markersize=6)
        ax2.annotate(
            f"Peak QA·α: {max_qa_val:.1f} kPa·deg\nat {max_qa_time:.2f} s",
            xy=(max_qa_time, max_qa_val),
            xytext=(max_qa_time + 1.2, max_qa_val * 0.85),
            arrowprops=dict(facecolor="#7C3AED", shrink=0.08, width=1, headwidth=4),
            fontsize=7, weight="bold", color="#7C3AED"
        )

    _add_event_lines(ax2, events, metrics.apogee_time * 1.1)

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    return output_path


def generate_stability_and_attitude_chart(metrics: FlightMetrics, output_path: Path) -> Path:
    setup_matplotlib_theme()
    events = _get_flight_events(metrics)
    t_cutoff = metrics.apogee_time * 1.15
    ts = metrics.timeseries

    mask = ts.time <= t_cutoff
    t_eval = ts.time[mask]
    cg_vals = ts.cg[mask]
    cp_vals = ts.cp[mask]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7.5, 5.0), sharex=True)

    ax1.plot(t_eval, cp_vals, color="#DC2626", linewidth=1.6, label="Center of Pressure (CP)")
    ax1.plot(t_eval, cg_vals, color="#2563EB", linewidth=1.6, label="Center of Gravity (CG)")
    ax1.fill_between(t_eval, cg_vals, cp_vals, color="#10B981", alpha=0.15, label="Static Margin Span (CG -> CP)")
    ax1.set_ylabel("Position from Nose (m)")
    ax1.set_xlim(0, t_cutoff)
    ax1.legend(loc="upper right", fontsize=7.5)
    ax1.set_title("Static Stability Envelope & Aerodynamic Center Migration", fontsize=9.5)
    _add_event_lines(ax1, events, t_cutoff)

    sm_vals = ts.static_margin[mask]

    ax2.plot(t_eval, sm_vals, color="#059669", linewidth=1.6, label="Static Margin (cal)")
    ax2.axhspan(1.5, 3.5, color="#10B981", alpha=0.15, label="Preferred Range (1.5 - 3.5 cal)")
    ax2.axhline(1.0, color="#DC2626", linestyle="--", linewidth=1.1, label="Min Stability Limit (1.0 cal)")

    sm_mq = metrics.max_dynamic_pressure_static_margin
    t_mq = metrics.max_dynamic_pressure_time
    if sm_mq:
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
    ax2.set_ylim(0, max(5.0, float(np.max(sm_vals)) + 0.5))
    ax2.legend(loc="upper right", fontsize=7.5)
    _add_event_lines(ax2, events, t_cutoff)

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    return output_path


def generate_full_atmosphere_chart(metrics: FlightMetrics, output_path: Path) -> Path:
    setup_matplotlib_theme()
    atm = metrics.atmosphere
    z_agl = atm.altitude_agl

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(7.5, 6.2))

    # 1. Wind Speed vs Altitude
    ax1.plot(atm.wind_speed, z_agl, color="#1D4ED8", linewidth=1.6)
    ax1.set_xlabel("Wind Speed (m/s)")
    ax1.set_ylabel("Altitude AGL (m)")
    ax1.set_title("Wind Velocity Magnitude", fontsize=9)
    ax1.set_xlim(left=0)

    # 2. Wind Direction vs Altitude
    ax2.plot(atm.wind_direction, z_agl, color="#D97706", linewidth=1.6)
    ax2.set_xlabel("Wind Direction (ºAzimuth)")
    ax2.set_ylabel("Altitude AGL (m)")
    ax2.set_title("Wind Direction Heading", fontsize=9)
    ax2.set_xlim(0, 360)

    # 3. Density & Speed of Sound
    ax3.plot(atm.density, z_agl, color="#047857", linewidth=1.6, label=r"Density $\rho$ (kg/m$^3$)")
    ax3.set_xlabel(r"Air Density (kg/m$^3$)", color="#047857")
    ax3.set_ylabel("Altitude AGL (m)")
    ax3.tick_params(axis="x", labelcolor="#047857")

    ax3_c = ax3.twiny()
    ax3_c.plot(atm.speed_of_sound, z_agl, color="#7C3AED", linestyle="--", linewidth=1.3, label="Sound Speed (m/s)")
    ax3_c.set_xlabel("Speed of Sound (m/s)", color="#7C3AED")
    ax3_c.tick_params(axis="x", labelcolor="#7C3AED")
    ax3.set_title("Atmospheric Thermodynamics & Acoustics", fontsize=9)

    # 4. Wind Hodograph (U vs V)
    ax4.plot(atm.wind_u, atm.wind_v, color="#0B2545", linewidth=1.4, marker="o", markersize=2)
    if len(atm.wind_u) > 0:
        ax4.scatter([atm.wind_u[0]], [atm.wind_v[0]], color="#10B981", marker="*", s=80, label="Surface (0m AGL)", zorder=5)
        ax4.scatter([atm.wind_u[-1]], [atm.wind_v[-1]], color="#DC2626", marker="^", s=60, label=f"Apogee ({z_agl[-1]:.0f}m)", zorder=5)
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


def generate_recovery_descent_chart(metrics: FlightMetrics, output_path: Path) -> Path:
    setup_matplotlib_theme()
    events = _get_flight_events(metrics)
    t_apogee = metrics.apogee_time
    t_final = metrics.flight_duration_time
    ts = metrics.timeseries

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7.5, 4.4), sharex=True)

    descent_mask = (ts.time >= t_apogee * 0.95) & (ts.time <= t_final)
    t_eval = ts.time[descent_mask]

    # 1. Descent Altitude
    ax1.plot(t_eval, ts.altitude_agl[descent_mask], color="#047857", linewidth=1.6, label="Altitude AGL (m)")
    ax1.set_ylabel("Altitude AGL (m)")
    ax1.set_xlim(t_apogee * 0.95, t_final * 1.02)
    ax1.set_title("Recovery & Descent Phase Profile", fontsize=9.5)
    ax1.legend(loc="upper right", fontsize=7.5)
    _add_event_lines(ax1, events)

    # 2. Sink rate (|Vz|)
    vz_vals = np.abs(ts.velocity_z[descent_mask])
    ax2.plot(t_eval, vz_vals, color="#B45309", linewidth=1.5, label="Descent Sink Rate |Vz| (m/s)")
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


def generate_trajectory_views_chart(metrics: FlightMetrics, output_path: Path) -> Path:
    setup_matplotlib_theme()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.5, 3.5))

    ts = metrics.timeseries
    x = ts.x
    y = ts.y
    z_agl = ts.altitude_agl
    downrange = np.hypot(x, y)

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


def generate_multi_scenario_chart(scenario_metrics: Dict[str, FlightMetrics], output_path: Path) -> Path:
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
    for name, metrics in scenario_metrics.items():
        ts = metrics.timeseries
        t = ts.time
        z_agl = ts.altitude_agl
        downrange = np.hypot(ts.x, ts.y)
        t_final = metrics.flight_duration_time
        max_t = max(max_t, t_final)

        cfg = styles_map.get(name, {"color": "#64748B", "linestyle": "-", "linewidth": 1.5, "marker": "o"})

        # 1. Altitude vs Time
        ax1.plot(t, z_agl, color=cfg["color"], linestyle=cfg["linestyle"], linewidth=cfg["linewidth"], label=f"{name} ({t_final:.1f}s)")
        ax1.scatter([t_final], [0], color=cfg["color"], marker=cfg["marker"], s=45, zorder=5)

        # 2. Downrange vs Time
        ax2.plot(t, downrange, color=cfg["color"], linestyle=cfg["linestyle"], linewidth=cfg["linewidth"], label=f"{name} ({downrange[-1]:.0f}m)")
        ax2.scatter([t[-1]], [downrange[-1]], color=cfg["color"], marker=cfg["marker"], s=45, zorder=5)

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