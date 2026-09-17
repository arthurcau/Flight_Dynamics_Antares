from antares_fd.builders import build_environment, build_motor, build_vehicle, add_recovery_system
from antares_fd.simulation.runner import run_flight
from antares_fd.simulation.results import print_flight_summary
from antares_fd.simulation.scenarios import apply_scenario, NOMINAL

def execute_scenario(config, project_dir, print_summary=True, export_kml=True, scenario_id=NOMINAL):
    """
    Central orchestrator that builds the environment, motor, and vehicle
    from a given config, runs the simulation, and optionally exports the results.
    """
    # Apply the canonical override to a copy.  Builders and the report receive
    # the same scenario-specific configuration, while the caller's nominal
    # ProjectConfig remains immutable for subsequent paired runs.
    scenario_config = apply_scenario(config, scenario_id)

    # 1. Build Environment
    environment = build_environment(scenario_config.environment, scenario_config.launch)
    
    # 2. Build Motor
    motor = build_motor(scenario_config.motor, project_dir)
    
    # 3. Build Vehicle
    rocket = build_vehicle(scenario_config.vehicle, motor, project_dir)
    
    # 4. Add Recovery System
    add_recovery_system(rocket, scenario_config.recovery)
    
    # 5. Run Flight
    flight = run_flight(rocket, environment, scenario_config.launch, scenario_config.simulation)
    
    # 6. Export Results
    if print_summary:
        print_flight_summary(flight, project_dir=project_dir)
        
    return flight
