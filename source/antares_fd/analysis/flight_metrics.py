from dataclasses import dataclass, field
from typing import Dict, List, Optional
import numpy as np


@dataclass(frozen=True)
class EventRecord:
    name: str
    time: float
    altitude_agl: float
    dynamic_pressure: float
    speed: float


@dataclass(frozen=True)
class ParachuteEvent(EventRecord):
    deploy_time: float
    lag: float
    cd_s: float
    opening_shock_g: float
    steady_sink_rate: Optional[float]


@dataclass(frozen=True)
class FlightTimeSeries:
    time: np.ndarray
    altitude_agl: np.ndarray
    altitude_asl: np.ndarray
    x: np.ndarray
    y: np.ndarray
    z: np.ndarray
    speed: np.ndarray
    velocity_z: np.ndarray
    mach: np.ndarray
    acceleration: np.ndarray
    acceleration_z: np.ndarray
    dynamic_pressure: np.ndarray
    angle_of_attack: np.ndarray
    static_margin: np.ndarray
    thrust: np.ndarray
    mass: np.ndarray
    cg: np.ndarray
    cp: np.ndarray
    omega_mag: np.ndarray
    q_alpha: np.ndarray


@dataclass(frozen=True)
class AtmosphereProfile:
    altitude_agl: np.ndarray
    wind_u: np.ndarray
    wind_v: np.ndarray
    wind_speed: np.ndarray
    wind_direction: np.ndarray
    density: np.ndarray
    speed_of_sound: np.ndarray


@dataclass(frozen=True)
class FlightMetrics:
    # 1. Mission Info
    project_name: str
    vehicle_name: str
    flight_name: str
    environment_type: str
    latitude: float
    longitude: float
    elevation_m: float
    
    # 2. Temporal Timelines
    liftoff_time: float
    rail_exit_time: float
    burnout_time: float
    apogee_time: float
    flight_duration_time: float
    coast_duration: float

    # 3. Trajectory & Landing
    apogee_agl: float
    apogee_asl: float
    drift_at_apogee: float
    drift_at_impact: float
    impact_x: float
    impact_y: float
    landing_azimuth: float

    # 4. Kinematics (Speed & Mach)
    max_speed: float
    max_speed_time: float
    max_mach: float
    max_mach_time: float
    burnout_speed: float
    burnout_altitude_agl: float
    
    # 5. Ascending Acceleration (Airframe loads prior to deployment)
    max_ascent_acceleration_g: float
    max_ascent_acceleration_time: float
    max_ascent_vertical_acceleration_g: float

    # 6. Peak Acceleration (Including Deployment Shocks)
    max_total_acceleration_g: float
    max_total_acceleration_time: float

    # 7. Rail Exit Dynamics
    rail_length: float
    rail_exit_velocity: float
    rail_exit_static_margin: float
    crosswind_speed: float
    crosswind_ratio: float

    # 8. Aerodynamic Loads (Max Q and Bending)
    max_dynamic_pressure: float
    max_dynamic_pressure_time: float
    max_dynamic_pressure_altitude: float
    max_dynamic_pressure_mach: float
    max_dynamic_pressure_aoa: float
    max_dynamic_pressure_static_margin: float
    peak_q_alpha: float
    peak_q_alpha_time: float
    max_ascent_aoa: float

    # 9. Propulsion & Mass
    motor_name: str
    total_impulse: float
    average_thrust: float
    max_thrust: float
    burn_time: float
    propellant_mass: float
    specific_impulse: float
    initial_tw: float
    rail_exit_tw: float
    peak_tw: float
    average_burn_tw: float
    
    liftoff_mass: float
    rail_exit_mass: float
    burnout_mass: float
    landing_mass: float
    dry_mass: float
    
    cg_liftoff: float
    cg_burnout: float
    cp_liftoff: float
    cp_burnout: float
    
    # 10. Stability Tracking
    static_margin_liftoff: float
    static_margin_rail_exit: float
    static_margin_burnout: float
    static_margin_min_burn: float
    static_margin_max_burn: float

    # 11. Angular Rates
    max_angular_velocity: float
    max_roll_rate: float
    
    # 12. Recovery
    drogue_event: Optional[ParachuteEvent]
    main_event: Optional[ParachuteEvent]
    touchdown_velocity: float
    touchdown_kinetic_energy: float

    # 13. Field Validation Data (If available)
    validation: Optional[Dict[str, Any]]

    # Timeseries arrays & Environment
    timeseries: FlightTimeSeries
    atmosphere: AtmosphereProfile
