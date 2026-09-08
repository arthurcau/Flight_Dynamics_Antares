from rocketpy import Flight
from antares_fd.config.exceptions import ConfigurationError

def run_flight(rocket, environment, launch_config, simulation_config):
    """Executes the RocketPy Flight simulation."""
    print("Running Flight...")
    
    if not launch_config:
        raise ConfigurationError("launch_config is required for Flight")
        
    rail = launch_config.get("rail", {})
    length = rail.get("length")
    if length is None:
        raise ConfigurationError("launch.rail.length is required")
        
    inclination = rail.get("inclination_deg", 90.0)
    heading = rail.get("heading_deg", 0.0)
    if heading is None:
        # Default to 0 if not provided, but RocketPy requires an angle.
        # Strict fail-fast:
        raise ConfigurationError("launch.rail.heading_deg is required")
        
    # We can use simulation_config for numerical solver settings later
    # e.g., terminate_on_apogee, time_overshoot, max_time_step
    
    flight = Flight(
        rocket=rocket,
        environment=environment,
        rail_length=length,
        inclination=inclination,
        heading=heading
    )
    
    return flight
