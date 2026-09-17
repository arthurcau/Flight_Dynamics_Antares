"""
Flight Metrics Extraction & Engineering Analysis.

Extracts comprehensive performance, kinematic, aerodynamic, stability,
propulsion, and recovery metrics from a RocketPy Flight instance.
Centralized, single-source-of-truth calculation for tables, charts, and compliance.
"""

from typing import Any, Dict, Optional, Tuple
import numpy as np
from antares_fd.analysis.flight_metrics import (
    FlightMetrics,
    FlightTimeSeries,
    AtmosphereProfile,
    EventRecord,
    ParachuteEvent
)


def extract_flight_metrics(flight: Any, config: Optional[Any] = None, project_dir: Optional[Any] = None) -> FlightMetrics:
    """
    Extracts complete quantitative engineering metrics from a simulated Flight.
    Every metric is computed exactly once to guarantee consistency across all reports.

    Args:
        flight: RocketPy Flight instance.
        config: Optional ProjectConfig or loaded dictionary.
        project_dir: Optional Path to project directory.

    Returns:
        Structured FlightMetrics containing single-source-of-truth values and timeseries vectors.
    """
    rocket = flight.rocket
    motor = rocket.motor
    env = flight.env
    g0 = 9.80665

    # 1. Temporal landmarks
    t_liftoff = float(flight.out_of_rail_time)
    t_burnout = float(motor.burn_out_time)
    t_apogee = float(flight.apogee_time)
    t_final = float(flight.t_final)
    coast_duration = float(t_apogee - t_burnout) if t_apogee > t_burnout else 0.0

    # Timeseries interpolation (Unified Time Vector)
    # 0 to rail exit, rail exit to apogee, apogee to end
    t_ascent1 = np.linspace(0, t_liftoff, 50, endpoint=False)
    t_ascent2 = np.linspace(t_liftoff, t_apogee, 200, endpoint=False)
    t_descent = np.linspace(t_apogee, t_final, 300)
    t_eval = np.concatenate([t_ascent1, t_ascent2, t_descent])

    # Basic attributes
    elev = float(env.elevation)
    
    # 2. Extract Base Timeseries
    ts_z = np.array([flight.z(t) for t in t_eval])
    ts_alt_agl = ts_z - elev
    ts_x = np.array([flight.x(t) for t in t_eval])
    ts_y = np.array([flight.y(t) for t in t_eval])
    
    ts_vz = np.array([flight.vz(t) for t in t_eval])
    ts_speed = np.array([flight.speed(t) for t in t_eval])
    ts_mach = np.array([flight.mach_number(t) for t in t_eval])
    
    ts_ax = np.array([flight.ax(t) for t in t_eval])
    ts_ay = np.array([flight.ay(t) for t in t_eval])
    ts_az = np.array([flight.az(t) for t in t_eval])
    ts_a_tot = np.sqrt(ts_ax**2 + ts_ay**2 + ts_az**2)

    ts_q = np.array([flight.dynamic_pressure(t) for t in t_eval])
    ts_alpha = np.array([flight.angle_of_attack(t) for t in t_eval])
    ts_sm = np.array([flight.static_margin(t) for t in t_eval])

    # Fix initial singularity for Q*alpha inside rail
    rail_mask = (t_eval < t_liftoff)
    ts_q_alpha = ts_q * np.abs(ts_alpha)
    ts_q_alpha[rail_mask] = 0.0

    # Propulsion and Mass Timeseries
    ts_thrust = np.array([motor.thrust(t) if t <= t_burnout else 0.0 for t in t_eval])
    ts_mass = np.array([rocket.total_mass(t) for t in t_eval])
    ts_cg = np.array([rocket.center_of_mass(t) for t in t_eval])
    ts_cp = np.array([rocket.cp_position(t) for t in t_eval])
    
    # Angular properties
    ts_w1 = np.array([flight.w1(t) if hasattr(flight, 'w1') else 0.0 for t in t_eval])
    ts_w2 = np.array([flight.w2(t) if hasattr(flight, 'w2') else 0.0 for t in t_eval])
    ts_w3 = np.array([flight.w3(t) if hasattr(flight, 'w3') else 0.0 for t in t_eval])
    ts_omega_mag = np.sqrt(ts_w1**2 + ts_w2**2 + ts_w3**2)

    timeseries = FlightTimeSeries(
        time=t_eval,
        altitude_agl=ts_alt_agl,
        altitude_asl=ts_z,
        x=ts_x,
        y=ts_y,
        z=ts_z,
        speed=ts_speed,
        velocity_z=ts_vz,
        mach=ts_mach,
        acceleration=ts_a_tot,
        acceleration_z=ts_az,
        dynamic_pressure=ts_q,
        angle_of_attack=ts_alpha,
        static_margin=ts_sm,
        thrust=ts_thrust,
        mass=ts_mass,
        cg=ts_cg,
        cp=ts_cp,
        omega_mag=ts_omega_mag,
        q_alpha=ts_q_alpha
    )

    # Calculate Scalar Metrics
    apogee_agl = float(np.max(ts_alt_agl))
    apogee_asl = float(np.max(ts_z))

    drift_apogee = float(np.hypot(flight.x(t_apogee), flight.y(t_apogee)))
    drift_final = float(np.hypot(ts_x[-1], ts_y[-1]))
    landing_azimuth = float(np.degrees(np.arctan2(ts_x[-1], ts_y[-1])) % 360)

    # 4. Accelerations (Ascent vs Recovery)
    ascent_mask = (t_eval <= t_apogee)
    max_ascent_accel_ms2 = float(np.max(ts_a_tot[ascent_mask])) if np.any(ascent_mask) else 0.0
    t_max_ascent_accel = float(t_eval[ascent_mask][np.argmax(ts_a_tot[ascent_mask])]) if np.any(ascent_mask) else 0.0

    max_tot_accel_ms2 = float(np.max(ts_a_tot))
    t_max_tot_accel = float(t_eval[np.argmax(ts_a_tot)])
    
    # 5. Peak Aero
    max_q_idx = int(np.argmax(ts_q[ascent_mask])) if np.any(ascent_mask) else int(np.argmax(ts_q))
    t_max_q = float(t_eval[ascent_mask][max_q_idx]) if np.any(ascent_mask) else float(t_eval[max_q_idx])
    
    post_rail_ascent = (t_eval >= t_liftoff) & (t_eval <= t_apogee)
    peak_qa = float(np.max(ts_q_alpha[post_rail_ascent])) if np.any(post_rail_ascent) else 0.0
    t_peak_qa = float(t_eval[post_rail_ascent][np.argmax(ts_q_alpha[post_rail_ascent])]) if np.any(post_rail_ascent) else 0.0
    
    # T/W Mechanics
    m_liftoff = float(rocket.total_mass(0))
    initial_tw = float(motor.thrust(0) / (m_liftoff * g0)) if m_liftoff > 0 else 0.0
    rail_exit_tw = float(motor.thrust(t_liftoff) / (rocket.total_mass(t_liftoff) * g0)) if rocket.total_mass(t_liftoff) > 0 else 0.0
    
    burn_tw = ts_thrust[(t_eval <= t_burnout)] / (ts_mass[(t_eval <= t_burnout)] * g0)
    peak_tw = float(np.max(burn_tw)) if len(burn_tw) > 0 else initial_tw
    
    # Parachute events
    drogue_evt = None
    main_evt = None
    if hasattr(flight, "parachute_events"):
        for p_time, p_obj in flight.parachute_events:
            p_time = float(p_time)
            deploy_t = float(p_time + getattr(p_obj, "lag", 0.0))
            is_drogue = "drogue" in p_obj.name.lower() or drogue_evt is None
            
            # Shock: max accel in [deploy_t - 0.5, deploy_t + 2.5]
            shock_mask = (t_eval >= deploy_t - 0.5) & (t_eval <= deploy_t + 2.5)
            shock_g = float(np.max(ts_a_tot[shock_mask]) / g0) if np.any(shock_mask) else 0.0
            
            evt = ParachuteEvent(
                name=p_obj.name,
                time=p_time,
                altitude_agl=float(flight.z(p_time) - elev),
                dynamic_pressure=float(flight.dynamic_pressure(p_time)),
                speed=float(flight.speed(p_time)),
                deploy_time=deploy_t,
                lag=float(getattr(p_obj, "lag", 0.0)),
                cd_s=float(p_obj.cd_s),
                opening_shock_g=shock_g,
                steady_sink_rate=None  # Estimated below
            )
            if is_drogue:
                drogue_evt = evt
            else:
                main_evt = evt

    # Estimate steady state sink rate
    if drogue_evt:
        t_drogue_end = main_evt.trigger_time if main_evt else t_final
        t_mid = 0.5 * (drogue_evt.deploy_time + t_drogue_end)
        if t_mid < t_final and (t_mid - drogue_evt.deploy_time > 1.0):
            drogue_evt = ParachuteEvent(**{**drogue_evt.__dict__, "steady_sink_rate": float(abs(flight.vz(t_mid)))})
    if main_evt:
        t_eval_main = min(main_evt.deploy_time + 8.0, t_final - 0.5)
        if t_eval_main > main_evt.deploy_time:
            main_evt = ParachuteEvent(**{**main_evt.__dict__, "steady_sink_rate": float(abs(flight.vz(t_eval_main)))})

    v_impact = float(abs(flight.vz(t_final)))
    e_kin = float(0.5 * ts_mass[-1] * (v_impact**2))

    # Static Margin bounds
    burn_mask = (t_eval >= 0) & (t_eval <= t_burnout)
    sm_min_burn = float(np.min(ts_sm[burn_mask])) if np.any(burn_mask) else ts_sm[0]
    sm_max_burn = float(np.max(ts_sm[burn_mask])) if np.any(burn_mask) else ts_sm[0]

    # Coordinate field verification logic
    validation = None
    if project_dir and "neblina_1" in str(project_dir):
        lat_nose = -21.9438267
        lon_nose = -48.9602672
        lat_fuse = -21.943290
        lon_fuse = -48.960191
        lat_pad = float(env.latitude)
        lon_pad = float(env.longitude)
        r_earth = 6378137.0
        
        x_nose = float(np.radians(lon_nose - lon_pad) * r_earth * np.cos(np.radians(lat_pad)))
        y_nose = float(np.radians(lat_nose - lat_pad) * r_earth)
        x_fuse = float(np.radians(lon_fuse - lon_pad) * r_earth * np.cos(np.radians(lat_pad)))
        y_fuse = float(np.radians(lat_fuse - lat_pad) * r_earth)
        
        impact_x = float(ts_x[-1])
        impact_y = float(ts_y[-1])
        
        validation = {
            "has_field_data": True,
            "pad": {"lat": lat_pad, "lon": lon_pad},
            "predicted": {
                "x": impact_x,
                "y": impact_y,
                "dist": drift_final,
                "azimuth_deg": landing_azimuth,
            },
            "nose_cone": {
                "lat": lat_nose,
                "lon": lon_nose,
                "x": x_nose,
                "y": y_nose,
                "dist": float(np.hypot(x_nose, y_nose)),
                "azimuth_deg": float(np.degrees(np.arctan2(x_nose, y_nose)) % 360),
                "err_radial_m": float(np.hypot(x_nose, y_nose) - drift_final),
                "err_x_m": float(x_nose - impact_x),
                "err_y_m": float(y_nose - impact_y),
            },
            "fuselage": {
                "lat": lat_fuse,
                "lon": lon_fuse,
                "x": x_fuse,
                "y": y_fuse,
                "dist": float(np.hypot(x_fuse, y_fuse)),
                "azimuth_deg": float(np.degrees(np.arctan2(x_fuse, y_fuse)) % 360),
                "err_radial_m": float(np.hypot(x_fuse, y_fuse) - drift_final),
                "err_x_m": float(x_fuse - impact_x),
                "err_y_m": float(y_fuse - impact_y),
            }
        }

    
    # Atmosphere Extraction
    z_max = apogee_asl if apogee_asl > elev else 4000.0
    z_eval_env = np.linspace(elev, z_max * 1.1, 250)
    z_agl_env = z_eval_env - elev
    
    env_u, env_v = [], []
    env_spd, env_dir = [], []
    env_rho, env_sos = [], []
    for tz in z_eval_env:
        try:
            wx = float(env.wind_velocity_x(tz))
            wy = float(env.wind_velocity_y(tz))
            env_u.append(wx)
            env_v.append(wy)
            env_spd.append(np.hypot(wx, wy))
            env_dir.append(np.degrees(np.arctan2(wx, wy)) % 360)
            env_rho.append(float(env.density(tz)))
            env_sos.append(float(env.speed_of_sound(tz)))
        except:
            env_u.append(0.0)
            env_v.append(0.0)
            env_spd.append(0.0)
            env_dir.append(0.0)
            env_rho.append(1.2)
            env_sos.append(340.0)

    atm_prof = AtmosphereProfile(
        altitude_agl=z_agl_env,
        wind_u=np.array(env_u),
        wind_v=np.array(env_v),
        wind_speed=np.array(env_spd),
        wind_direction=np.array(env_dir),
        density=np.array(env_rho),
        speed_of_sound=np.array(env_sos)
    )

    return FlightMetrics(
        project_name=project_dir.name if project_dir else "Antares",
        vehicle_name=getattr(rocket, "name", "Rocket"),
        flight_name=getattr(flight, "name", "Flight"),
        environment_type=getattr(env, "atmospheric_model_type", "Atmosphere"),
        latitude=float(env.latitude),
        longitude=float(env.longitude),
        elevation_m=elev,
        liftoff_time=0.0,
        rail_exit_time=t_liftoff,
        burnout_time=t_burnout,
        apogee_time=t_apogee,
        flight_duration_time=t_final,
        coast_duration=coast_duration,
        apogee_agl=apogee_agl,
        apogee_asl=apogee_asl,
        drift_at_apogee=drift_apogee,
        drift_at_impact=drift_final,
        impact_x=float(ts_x[-1]),
        impact_y=float(ts_y[-1]),
        landing_azimuth=landing_azimuth,
        max_speed=float(np.max(ts_speed)),
        max_speed_time=float(t_eval[np.argmax(ts_speed)]),
        max_mach=float(np.max(ts_mach)),
        max_mach_time=float(t_eval[np.argmax(ts_mach)]),
        burnout_speed=float(flight.speed(t_burnout)),
        burnout_altitude_agl=float(flight.z(t_burnout) - elev),
        max_ascent_acceleration_g=max_ascent_accel_ms2 / g0,
        max_ascent_acceleration_time=t_max_ascent_accel,
        max_ascent_vertical_acceleration_g=float(np.max(ts_az[ascent_mask]) / g0) if np.any(ascent_mask) else 0.0,
        max_total_acceleration_g=max_tot_accel_ms2 / g0,
        max_total_acceleration_time=t_max_tot_accel,
        rail_length=getattr(flight, "rail_length", 5.2),
        rail_exit_velocity=float(flight.out_of_rail_velocity),
        rail_exit_static_margin=float(flight.static_margin(t_liftoff)),
        crosswind_speed=np.hypot(env.wind_velocity_x(elev+5.2), env.wind_velocity_y(elev+5.2)) if hasattr(env, 'wind_velocity_x') else 0.0,
        crosswind_ratio=float(flight.out_of_rail_velocity / max(0.1, np.hypot(env.wind_velocity_x(elev+5.2), env.wind_velocity_y(elev+5.2)))) if hasattr(env, 'wind_velocity_x') else 0.0,
        max_dynamic_pressure=float(np.max(ts_q)),
        max_dynamic_pressure_time=t_max_q,
        max_dynamic_pressure_altitude=float(flight.z(t_max_q) - elev),
        max_dynamic_pressure_mach=float(flight.mach_number(t_max_q)),
        max_dynamic_pressure_aoa=float(flight.angle_of_attack(t_max_q)),
        max_dynamic_pressure_static_margin=float(flight.static_margin(t_max_q)),
        peak_q_alpha=peak_qa,
        peak_q_alpha_time=t_peak_qa,
        max_ascent_aoa=float(np.max(ts_alpha[post_rail_ascent])) if np.any(post_rail_ascent) else 0.0,
        motor_name=getattr(motor, "name", "SolidMotor"),
        total_impulse=float(getattr(motor, "total_impulse", 0.0)),
        average_thrust=float(getattr(motor, "average_thrust", 0.0)),
        max_thrust=float(getattr(motor, "max_thrust", 0.0)),
        burn_time=t_burnout,
        propellant_mass=float(getattr(motor, "propellant_initial_mass", m_liftoff - ts_mass[burn_mask][-1])),
        specific_impulse=0.0, # Computed if valid
        initial_tw=initial_tw,
        rail_exit_tw=rail_exit_tw,
        peak_tw=peak_tw,
        average_burn_tw=0.0,
        liftoff_mass=m_liftoff,
        rail_exit_mass=float(rocket.total_mass(t_liftoff)),
        burnout_mass=float(rocket.total_mass(t_burnout)),
        landing_mass=float(rocket.total_mass(t_final)),
        dry_mass=float(rocket.mass),
        cg_liftoff=float(rocket.center_of_mass(0)),
        cg_burnout=float(rocket.center_of_mass(t_burnout)),
        cp_liftoff=float(rocket.cp_position(0)),
        cp_burnout=float(rocket.cp_position(t_burnout)),
        static_margin_liftoff=float(flight.static_margin(0)),
        static_margin_rail_exit=float(flight.static_margin(t_liftoff)),
        static_margin_burnout=float(flight.static_margin(t_burnout)),
        static_margin_min_burn=sm_min_burn,
        static_margin_max_burn=sm_max_burn,
        max_angular_velocity=float(np.degrees(np.max(ts_omega_mag[ascent_mask]))) if np.any(ascent_mask) else 0.0,
        max_roll_rate=float(np.degrees(np.max(np.abs(ts_w3[ascent_mask])))) if np.any(ascent_mask) else 0.0,
        drogue_event=drogue_evt,
        main_event=main_evt,
        touchdown_velocity=v_impact,
        touchdown_kinetic_energy=e_kin,
        validation=validation,
        timeseries=timeseries,
        atmosphere=atm_prof
    )
