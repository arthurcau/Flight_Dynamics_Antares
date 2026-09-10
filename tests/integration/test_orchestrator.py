import pytest
from pathlib import Path
from antares_fd.simulation.orchestrator import execute_scenario
from antares_fd.config.models import ProjectConfig, ConfigDict

def test_nominal_orchestration_mocked(tmp_path):
    """
    Integration test asserting that the orchestrator can assemble
    the environment, motor, and vehicle without blowing up, given
    a valid (but minimal) mocked configuration.
    """
    
    # Create minimal mock config mimicking what the loader outputs
    config = ProjectConfig(
        vehicle=ConfigDict({
            "name": "MockRocket",
            "geometry": {
                "reference_diameter": 0.2
            },
            "mass_properties": {
                "mass_without_motor": 15.0,
                "center_of_mass_without_motor": 1.0,
                "inertia": {
                    "I11": 1.0,
                    "I22": 1.0,
                    "I33": 1.0
                }
            },
            "aerodynamics": {
                "power_off_drag": 0.5,
                "power_on_drag": 0.5
            },
            "components": []
        }),
        motor=ConfigDict({
            "thrust_source": 1000.0,
            "dry_mass": 2.0,
            "dry_inertia": [0.1, 0.1, 0.1],
            "center_of_dry_mass_position": 0.0,
            "nozzle_position": 0.0,
            "burn_time": 2.0,
            "nozzle_radius": 0.05,
            "throat_radius": 0.02,
            "grain_number": 1,
            "grain_density": 1000,
            "grain_outer_radius": 0.1,
            "grain_initial_inner_radius": 0.05,
            "grain_initial_height": 0.2,
            "grains_center_of_mass_position": 0.0,
            "grain_separation": 0.0
        }),
        environment=ConfigDict({
            "type": "standard_atmosphere"
        }),
        launch=ConfigDict({
            "site": {
                "latitude": 0.0,
                "longitude": 0.0,
                "elevation": 0.0
            },
            "datetime": {
                "date": "2027-01-01",
                "time": "12:00:00"
            },
            "rail": {
                "length": 5.0,
            }
        }),
        recovery=ConfigDict({
            "enabled": False
        }),
        simulation=ConfigDict({}),
        monte_carlo=ConfigDict({})
    )
    
    # We pass tmp_path as the project_dir. The orchestrator will attempt
    # to export trajectory maps here.
    flight = execute_scenario(config, project_dir=tmp_path, print_summary=False, export_kml=False)
    
    assert flight is not None
