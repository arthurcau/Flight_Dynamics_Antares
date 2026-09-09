from antares_fd.builders import build_environment, build_motor, build_vehicle, add_recovery_system
from antares_fd.simulation.runner import run_flight
from antares_fd.simulation.results import print_flight_summary

def execute_scenario(config, project_dir, print_summary=True, export_kml=True):
    """
    Central orchestrator that builds the environment, motor, and vehicle
    from a given config, runs the simulation, and optionally exports the results.
    """
    # 1. Build Environment
    environment = build_environment(config.environment, config.launch)
    
    # 2. Build Motor
    motor = build_motor(config.motor, project_dir)
    
    # 3. Build Vehicle
    rocket = build_vehicle(config.vehicle, motor, project_dir)
    
    # 4. Add Recovery System
    add_recovery_system(rocket, config.recovery)
    
    # 5. Run Flight
    flight = run_flight(rocket, environment, config.launch, config.simulation)
    
    # 6. Export Results
    if print_summary:
        print_flight_summary(flight, project_dir=project_dir)
        
    return flight
