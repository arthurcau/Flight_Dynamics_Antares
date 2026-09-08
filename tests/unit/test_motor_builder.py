import pytest
from pathlib import Path
from rocketpy import SolidMotor

from antares_fd.config.models import ConfigDict
from antares_fd.config.exceptions import ConfigurationError
from antares_fd.builders.motor import build_motor

@pytest.fixture
def valid_motor_config():
    return ConfigDict({
        "type": "solid",
        "thrust_source": "motor.eng",
        "burn_time": 3.0,
        "dry_mass": 1.5,
        "dry_inertia": [0.1, 0.1, 0.05],
        "center_of_dry_mass_position": 0.5,
        "grains_center_of_mass_position": 0.5,
        "grain_number": 4,
        "grain_separation": 0.005,
        "grain_density": 1500,
        "grain_outer_radius": 0.033,
        "grain_initial_inner_radius": 0.015,
        "grain_initial_height": 0.12,
        "nozzle_radius": 0.012,
        "throat_radius": 0.008,
        "interpolation_method": "linear",
        "coordinate_system_orientation": "nozzle_to_combustion_chamber"
    })

def test_build_motor_success(valid_motor_config, tmp_path):
    # We need a dummy .eng file for rocketpy to parse without errors, 
    # but rocketpy SolidMotor constructor parses the file immediately.
    # So we write a simple dummy .eng file.
    eng_file = tmp_path / "motor.eng"
    eng_file.write_text("Dummy Motor\n  0.0  0.0\n  3.0  1000.0\n")
    
    motor = build_motor(valid_motor_config, project_dir=tmp_path)
    
    assert isinstance(motor, SolidMotor)
    assert motor.burn_time[1] == 3.0
    assert motor.dry_mass == 1.5
    assert motor.grain_number == 4

def test_build_motor_missing_config(tmp_path):
    with pytest.raises(ConfigurationError, match="motor configuration is missing"):
        build_motor(None, project_dir=tmp_path)

def test_build_motor_invalid_arguments(valid_motor_config, tmp_path):
    # Remove a required parameter to trigger TypeError from SolidMotor
    eng_file = tmp_path / "motor.eng"
    eng_file.write_text("Dummy Motor\n  0.0  0.0\n  3.0  1000.0\n")
    
    valid_motor_config["grain_number"] = None
    
    with pytest.raises(ConfigurationError, match="Failed to build SolidMotor"):
        build_motor(valid_motor_config, project_dir=tmp_path)
