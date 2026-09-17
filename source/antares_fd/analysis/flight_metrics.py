from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union
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
    numerical_transient_shock_g: float
    steady_sink_rate: Optional[float]


@dataclass(frozen=True)
class EventRegistry:
    """Canonical event timestamps shared by tables, plots and interpretation."""

    ignition: Optional[EventRecord] = None
    first_motion: Optional[EventRecord] = None
    rail_exit: Optional[EventRecord] = None
    peak_thrust: Optional[EventRecord] = None
    max_acceleration: Optional[EventRecord] = None
    max_q: Optional[EventRecord] = None
    max_mach: Optional[EventRecord] = None
    burnout: Optional[EventRecord] = None
    apogee: Optional[EventRecord] = None
    drogue_trigger: Optional[ParachuteEvent] = None
    drogue_inflation: Optional[EventRecord] = None
    main_trigger: Optional[ParachuteEvent] = None
    main_inflation: Optional[EventRecord] = None
    touchdown: Optional[EventRecord] = None


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
    
    # 2. Temporal Landmarks
    liftoff_time: float
    rail_exit_time: float
    burnout_time: float
    apogee_time: float
    flight_duration: float
    coast_duration: float

    # 3. Trajectory & Landing
    apogee_agl: float
    apogee_asl: float
    drift_at_apogee: float
    landing_east: float
    landing_north: float
    landing_distance: float
    landing_azimuth: float

    # 4. Kinematics (Speed & Mach)
    max_velocity: float
    max_velocity_time: float
    max_mach: float
    max_mach_time: float
    burnout_velocity: float
    rail_exit_velocity: float
    rail_exit_acceleration: float
    
    # 5. Accelerations
    max_total_acceleration: float
    max_total_acceleration_time: float

    # 6. Aerodynamic Loads (Max Q and Bending Proxy)
    max_dynamic_pressure: float
    max_q_time: float
    max_q_altitude: float
    max_q_mach: float
    peak_valid_q_alpha: float
    peak_valid_q_alpha_time: float
    
    # 7. Stability & Attitude
    max_angle_of_attack: float
    angle_of_attack_at_max_q: float
    static_margin_liftoff: float
    static_margin_rail_exit: float
    static_margin_max_q: float
    static_margin_burnout: float
    minimum_burn_static_margin: float
    maximum_static_margin: float
    maximum_angular_velocity: float

    # 8. Propulsion & Mass
    motor_name: str
    burnout_mass: float
    total_impulse: float
    average_thrust: float
    max_thrust: float
    propellant_mass: float
    initial_tw: float
    rail_exit_tw: float
    peak_tw: float
    average_burn_tw: float
    
    # 9. Recovery
    drogue_deployment_time: Optional[float]
    main_deployment_time: Optional[float]
    drogue_descent_rate: Optional[float]
    main_descent_rate: Optional[float]
    drogue_event: Optional[ParachuteEvent]
    main_event: Optional[ParachuteEvent]
    touchdown_velocity: float
    touchdown_energy: float

    # 10. Field Validation Data (If available)
    validation: Optional[Dict[str, Any]]

    # Timeseries arrays & Environment
    timeseries: FlightTimeSeries
    atmosphere: AtmosphereProfile
    # Added at the end to preserve compatibility with archived constructors.
    ignition_tw: float = 0.0
    aero_analysis_window: Dict[str, Any] = field(default_factory=dict)
    events: EventRegistry = field(default_factory=EventRegistry)
