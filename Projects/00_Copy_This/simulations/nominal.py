"""
ANTARES FLIGHT DYNAMICS
Nominal Flight Simulation

This script runs the nominal configuration of the current project.

Physical parameters shall NOT be defined in this file.
All vehicle, motor, recovery, environment and launch parameters
must come from the project's configuration files.
"""

import sys
from pathlib import Path

# Ensures the core 'Source' package can be imported even if run via IDE play button
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SOURCE_DIR = PROJECT_ROOT / "Source"
if str(SOURCE_DIR) not in sys.path:
    sys.path.insert(0, str(SOURCE_DIR))

from antares_fd.config import load_project_config
from antares_fd.builders import build_environment, build_motor, build_vehicle, add_recovery_system
from antares_fd.simulation import run_flight, print_flight_summary


# =============================================================================
# PROJECT PATH
# =============================================================================

PROJECT_DIR = Path(__file__).resolve().parents[1]


# =============================================================================
# NOMINAL SIMULATION
# =============================================================================

def main():

    print("=" * 70)
    print("ANTARES FLIGHT DYNAMICS")
    print("Nominal Flight Simulation")
    print("=" * 70)

    # -------------------------------------------------------------------------
    # Load project configuration
    # -------------------------------------------------------------------------

    config = load_project_config(PROJECT_DIR)

    print(f"\nProject: {config.vehicle.name}")
    print(f"Revision: {config.vehicle.revision}")


    # -------------------------------------------------------------------------
    # Build Environment
    # -------------------------------------------------------------------------

    environment = build_environment(
        environment_config=config.environment,
        launch_config=config.launch,
    )


    # -------------------------------------------------------------------------
    # Build Motor
    # -------------------------------------------------------------------------

    motor = build_motor(
        config=config.motor,
        project_dir=PROJECT_DIR,
    )


    # -------------------------------------------------------------------------
    # Build Vehicle
    # -------------------------------------------------------------------------

    rocket = build_vehicle(
        vehicle_config=config.vehicle,
        motor=motor,
        project_dir=PROJECT_DIR,
    )


    # -------------------------------------------------------------------------
    # Add Recovery System
    # -------------------------------------------------------------------------

    add_recovery_system(
        rocket=rocket,
        config=config.recovery,
    )


    # -------------------------------------------------------------------------
    # Run Flight
    # -------------------------------------------------------------------------

    flight = run_flight(
        rocket=rocket,
        environment=environment,
        launch_config=config.launch,
        simulation_config=config.simulation,
    )


    # -------------------------------------------------------------------------
    # Results
    # -------------------------------------------------------------------------
    # 5. Output Summary
    print_flight_summary(flight, project_dir=PROJECT_DIR)


    return flight


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    flight = main()