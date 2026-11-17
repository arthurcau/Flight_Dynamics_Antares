"""
Flight Metrics Extraction & Engineering Analysis.

Extracts comprehensive performance, kinematic, aerodynamic, stability,
propulsion, and recovery metrics from a RocketPy Flight instance.
Centralized, single-source-of-truth calculation for tables, charts, and compliance.
"""

from typing import Any, Optional
import numpy as np
from antares_fd.analysis.flight_metrics import (
    FlightMetrics,
    FlightTimeSeries,
    AtmosphereProfile,
    EventRecord,
    ParachuteEvent,
    EventRegistry,
)


def extract_flight_metrics(flight: Any, config: Optional[Any] = None, project_dir: Optional[Any] = None) -> FlightMetrics:
    """
    Extracts complete quantitative engineering metrics from a simulated Flight.
    Every metric is computed exactly once to guarantee consistency across all reports.
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

    # Q*alpha is an aerodynamic bending-load indicator, not a structural
    # bending moment.  Its physically useful window is configurable and is
    # intentionally restricted to powered ascent/coast before apogee.
    ts_q_alpha = ts_q * np.abs(ts_alpha)
    rail_mask = (t_eval < t_liftoff)
    ts_q_alpha[rail_mask] = 0.0
    model_limits = {}
    if config is not None:
        try:
            model_limits = dict(config.vehicle.get("model_limits", {}))
        except (AttributeError, TypeError):
            model_limits = {}
    window_cfg = dict(model_limits.get("aero_analysis_window", {}))
    min_q = float(window_cfg.get("minimum_dynamic_pressure_pa", 100.0))
    min_speed = float(window_cfg.get("minimum_speed_mps", 20.0))
    aero_mask = (
        (t_eval >= t_liftoff)
        & (t_eval <= t_apogee)
        & (ts_q >= min_q)
        & (ts_speed >= min_speed)
    )

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
    landing_east = float(ts_x[-1])
    landing_north = float(ts_y[-1])
    drift_final = float(np.hypot(landing_east, landing_north))
    landing_azimuth = float(np.degrees(np.arctan2(landing_east, landing_north)) % 360)

    # 4. Accelerations (Ascent strictly, since deployment shocks are unphysical numerical artifacts)
    ascent_mask = (t_eval <= t_apogee)
    max_tot_accel = float(np.max(ts_a_tot[ascent_mask])) if np.any(ascent_mask) else 0.0
    t_max_tot_accel = float(t_eval[ascent_mask][np.argmax(ts_a_tot[ascent_mask])]) if np.any(ascent_mask) else 0.0

    rail_accel_x = float(flight.ax(t_liftoff))
    rail_accel_y = float(flight.ay(t_liftoff))
    rail_accel_z = float(flight.az(t_liftoff))
    rail_exit_accel = float(np.sqrt(rail_accel_x**2 + rail_accel_y**2 + rail_accel_z**2))

    # 5. Peak Aero
    max_q_idx = int(np.argmax(ts_q[ascent_mask])) if np.any(ascent_mask) else int(np.argmax(ts_q))
    t_max_q = float(t_eval[ascent_mask][max_q_idx]) if np.any(ascent_mask) else float(t_eval[max_q_idx])

    peak_qa = float(np.max(ts_q_alpha[aero_mask])) if np.any(aero_mask) else 0.0
    t_peak_qa = float(t_eval[aero_mask][np.argmax(ts_q_alpha[aero_mask])]) if np.any(aero_mask) else 0.0
    max_mach_idx = int(np.argmax(ts_mach))
    t_max_mach = float(t_eval[max_mach_idx])

    # T/W Mechanics
    m_liftoff = float(rocket.total_mass(0))
    initial_tw = float(motor.thrust(0) / (m_liftoff * g0)) if m_liftoff > 0 else 0.0
    t_ignition = float(getattr(motor, "burn_start_time", 0.0))
    ignition_tw = float(motor.thrust(t_ignition) / (rocket.total_mass(t_ignition) * g0)) if rocket.total_mass(t_ignition) > 0 else 0.0
    rail_exit_tw = float(motor.thrust(t_liftoff) / (rocket.total_mass(t_liftoff) * g0)) if rocket.total_mass(t_liftoff) > 0 else 0.0

    burn_tw = ts_thrust[(t_eval <= t_burnout)] / (ts_mass[(t_eval <= t_burnout)] * g0)
    peak_tw = float(np.max(burn_tw)) if len(burn_tw) > 0 else initial_tw
    avg_burn_tw = float(np.mean(burn_tw)) if len(burn_tw) > 0 else initial_tw

    # Parachute events
    drogue_evt = None
    main_evt = None
    if hasattr(flight, "parachute_events"):
        for p_time, p_obj in flight.parachute_events:
            p_time = float(p_time)
            deploy_t = float(p_time + getattr(p_obj, "lag", 0.0))
            is_drogue = "drogue" in p_obj.name.lower() or drogue_evt is None

            # The recovery shock is an unphysical numerical discontinuity due to CdS step change.
            shock_mask = (t_eval >= deploy_t - 0.5) & (t_eval <= deploy_t + 2.5)
            numerical_shock_g = float(np.max(ts_a_tot[shock_mask]) / g0) if np.any(shock_mask) else 0.0

            evt = ParachuteEvent(
                name=p_obj.name,
                time=p_time,
                altitude_agl=float(flight.z(p_time) - elev),
                dynamic_pressure=float(flight.dynamic_pressure(p_time)),
                speed=float(flight.speed(p_time)),
                deploy_time=deploy_t,
                lag=float(getattr(p_obj, "lag", 0.0)),
                cd_s=float(p_obj.cd_s),
                numerical_transient_shock_g=numerical_shock_g,
                steady_sink_rate=None
            )
            if is_drogue:
                drogue_evt = evt
            else:
                main_evt = evt

    # Estimate steady state sink rate
    if drogue_evt:
        t_drogue_end = main_evt.time if main_evt else t_final
        t_mid = 0.5 * (drogue_evt.deploy_time + t_drogue_end)
        if t_mid < t_final and (t_mid - drogue_evt.deploy_time > 1.0):
            drogue_evt = ParachuteEvent(**{**drogue_evt.__dict__, "steady_sink_rate": float(abs(flight.vz(t_mid)))})
    if main_evt:
        t_eval_main = min(main_evt.deploy_time + 8.0, t_final - 0.5)
        if t_eval_main > main_evt.deploy_time:
            main_evt = ParachuteEvent(**{**main_evt.__dict__, "steady_sink_rate": float(abs(flight.vz(t_eval_main)))})

    # RocketPy's vertical velocity is signed (downward is negative).  The
    # engineering touchdown speed and energy use positive magnitude.
    v_impact = float(abs(flight.vz(t_final)))
    e_kin = float(0.5 * ts_mass[-1] * (v_impact**2))

    # Static Margin bounds
    burn_mask = (t_eval >= 0) & (t_eval <= t_burnout)
    sm_min_burn = float(np.min(ts_sm[burn_mask])) if np.any(burn_mask) else ts_sm[0]
    max_sm = float(np.max(ts_sm))

    # Field validation requires source, date, datum and uncertainty for a
    # measured landing location. The former project-specific constants had no
    # traceable evidence, so no simulated landing is labeled validated here.
    validation = None

    # Atmosphere Extraction
    z_max = apogee_asl if apogee_asl > elev else 4000.0
    requested_upper_asl = z_max * 1.1
    atmosphere_meta = getattr(env, "antares_atmosphere", {})
    bounds = atmosphere_meta.get("altitude_bounds_asl_m") if isinstance(atmosphere_meta, dict) else None
    if bounds is None:
        source_altitude = getattr(getattr(getattr(env, "pressure", None), "source", None), "altitude", None)
        if source_altitude is not None:
            source_altitude = np.asarray(source_altitude, dtype=float)
            if source_altitude.ndim == 1 and len(source_altitude) >= 2:
                bounds = [float(source_altitude[0]), float(source_altitude[-1])]
    lower_asl = max(elev, float(bounds[0])) if bounds is not None else elev
    upper_asl = min(requested_upper_asl, float(bounds[1])) if bounds is not None else requested_upper_asl
    if not np.isfinite([lower_asl, upper_asl]).all() or upper_asl <= lower_asl:
        raise ValueError("Atmospheric profile does not cover a usable altitude range for reporting")
    coverage_status = (
        "PROFILE_LIMITED_TO_DECLARED_COVERAGE"
        if bounds is not None and (lower_asl > elev or upper_asl < requested_upper_asl)
        else "COMPLETE_WITHIN_REQUESTED_RANGE"
    )
    z_eval_env = np.linspace(lower_asl, upper_asl, 250)
    z_agl_env = z_eval_env - elev

    env_u, env_v = [], []
    env_spd, env_dir = [], []
    env_rho, env_sos = [], []
    for tz in z_eval_env:
        wx = float(env.wind_velocity_x(tz))
        wy = float(env.wind_velocity_y(tz))
        env_u.append(wx)
        env_v.append(wy)
        env_spd.append(np.hypot(wx, wy))
        env_dir.append(np.degrees(np.arctan2(wx, wy)) % 360)
        env_rho.append(float(env.density(tz)))
        env_sos.append(float(env.speed_of_sound(tz)))

    atm_prof = AtmosphereProfile(
        altitude_agl=z_agl_env,
        wind_u=np.array(env_u),
        wind_v=np.array(env_v),
        wind_speed=np.array(env_spd),
        wind_direction=np.array(env_dir),
        density=np.array(env_rho),
        speed_of_sound=np.array(env_sos),
        coverage_status=coverage_status,
        coverage_bounds_asl_m=tuple(map(float, bounds)) if bounds is not None else None,
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
        flight_duration=t_final,
        coast_duration=coast_duration,
        apogee_agl=apogee_agl,
        apogee_asl=apogee_asl,
        drift_at_apogee=drift_apogee,
        landing_east=landing_east,
        landing_north=landing_north,
        landing_distance=drift_final,
        landing_azimuth=landing_azimuth,
        max_velocity=float(np.max(ts_speed)),
        max_velocity_time=float(t_eval[np.argmax(ts_speed)]),
        max_mach=float(np.max(ts_mach)),
        max_mach_time=t_max_mach,
        burnout_velocity=float(flight.speed(t_burnout)),
        rail_exit_velocity=float(flight.out_of_rail_velocity),
        rail_exit_acceleration=rail_exit_accel,
        max_total_acceleration=max_tot_accel / g0,
        max_total_acceleration_time=t_max_tot_accel,
        max_dynamic_pressure=float(np.max(ts_q)),
        max_q_time=t_max_q,
        max_q_altitude=float(flight.z(t_max_q) - elev),
        max_q_mach=float(flight.mach_number(t_max_q)),
        peak_valid_q_alpha=peak_qa,
        peak_valid_q_alpha_time=t_peak_qa,
        max_angle_of_attack=float(np.max(ts_alpha[aero_mask])) if np.any(aero_mask) else 0.0,
        angle_of_attack_at_max_q=float(flight.angle_of_attack(t_max_q)),
        static_margin_liftoff=float(flight.static_margin(0)),
        static_margin_rail_exit=float(flight.static_margin(t_liftoff)),
        static_margin_max_q=float(flight.static_margin(t_max_q)),
        static_margin_burnout=float(flight.static_margin(t_burnout)),
        minimum_burn_static_margin=sm_min_burn,
        maximum_static_margin=max_sm,
        maximum_angular_velocity=float(np.degrees(np.max(ts_omega_mag[ascent_mask]))) if np.any(ascent_mask) else 0.0,
        motor_name=getattr(motor, "name", "SolidMotor"),
        burnout_mass=float(rocket.total_mass(t_burnout)),
        total_impulse=float(getattr(motor, "total_impulse", 0.0)),
        average_thrust=float(getattr(motor, "average_thrust", 0.0)),
        max_thrust=float(getattr(motor, "max_thrust", 0.0)),
        propellant_mass=float(getattr(motor, "propellant_initial_mass", m_liftoff - ts_mass[burn_mask][-1])),
        initial_tw=initial_tw,
        rail_exit_tw=rail_exit_tw,
        peak_tw=peak_tw,
        average_burn_tw=avg_burn_tw,
        drogue_deployment_time=drogue_evt.time if drogue_evt else None,
        main_deployment_time=main_evt.time if main_evt else None,
        drogue_descent_rate=drogue_evt.steady_sink_rate if drogue_evt else None,
        main_descent_rate=main_evt.steady_sink_rate if main_evt else None,
        drogue_event=drogue_evt,
        main_event=main_evt,
        touchdown_velocity=v_impact,
        touchdown_energy=e_kin,
        validation=validation,
        timeseries=timeseries,
        atmosphere=atm_prof,
        ignition_tw=ignition_tw,
        aero_analysis_window={
            "start": "rail_exit",
            "end": "apogee",
            "minimum_dynamic_pressure_pa": min_q,
            "minimum_speed_mps": min_speed,
        },
        events=EventRegistry(
            ignition=EventRecord("Ignition", t_ignition, float(flight.z(t_ignition) - elev), float(flight.dynamic_pressure(t_ignition)), float(flight.speed(t_ignition))),
            first_motion=EventRecord("First motion", 0.0, float(flight.z(0.0) - elev), float(flight.dynamic_pressure(0.0)), float(flight.speed(0.0))),
            rail_exit=EventRecord("Rail exit", t_liftoff, float(flight.z(t_liftoff) - elev), float(flight.dynamic_pressure(t_liftoff)), float(flight.speed(t_liftoff))),
            max_acceleration=EventRecord("Max acceleration", t_max_tot_accel, float(flight.z(t_max_tot_accel) - elev), float(flight.dynamic_pressure(t_max_tot_accel)), float(flight.speed(t_max_tot_accel))),
            max_q=EventRecord("Max-Q", t_max_q, float(flight.z(t_max_q) - elev), float(flight.dynamic_pressure(t_max_q)), float(flight.speed(t_max_q))),
            max_mach=EventRecord("Max Mach", t_max_mach, float(flight.z(t_max_mach) - elev), float(flight.dynamic_pressure(t_max_mach)), float(ts_speed[max_mach_idx])),
            burnout=EventRecord("Burnout", t_burnout, float(flight.z(t_burnout) - elev), float(flight.dynamic_pressure(t_burnout)), float(flight.speed(t_burnout))),
            apogee=EventRecord("Apogee", t_apogee, apogee_agl, float(flight.dynamic_pressure(t_apogee)), float(flight.speed(t_apogee))),
            drogue_trigger=drogue_evt,
            drogue_inflation=EventRecord("Drogue inflation", drogue_evt.deploy_time, drogue_evt.altitude_agl, drogue_evt.dynamic_pressure, drogue_evt.speed) if drogue_evt else None,
            main_trigger=main_evt,
            main_inflation=EventRecord("Main inflation", main_evt.deploy_time, main_evt.altitude_agl, main_evt.dynamic_pressure, main_evt.speed) if main_evt else None,
            touchdown=EventRecord("Touchdown", t_final, 0.0, float(flight.dynamic_pressure(t_final)), v_impact),
        )
    )
