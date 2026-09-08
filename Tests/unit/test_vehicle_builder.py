import pytest
from pathlib import Path
from rocketpy import Rocket

from antares_fd.config.models import ConfigDict
from antares_fd.config.exceptions import ConfigurationError
from antares_fd.builders.vehicle import build_vehicle

@pytest.fixture
def valid_vehicle_config():
    return ConfigDict({
        "geometry": {
            "reference_diameter": 0.15
        },
        "mass_properties": {
            "mass_without_motor": 15.0,
            "center_of_mass_without_motor": 1.0,
            "inertia": {
                "I11": 0.5,
                "I22": 4.0,
                "I33": 4.0
            }
        },
        "drag": {
            "power_on": {"source_type": "constant", "constant": 0.4},
            "power_off": {"source_type": "constant", "constant": 0.45}
        },
        "nose": {
            "enabled": True,
            "type": "von_karman",
            "length": 0.5,
            "position": 0.0
        },
        "fin_sets": [
            {
                "enabled": True,
                "type": "trapezoidal",
                "name": "Main Fins",
                "number": 4,
                "position": 2.0,
                "root_chord": 0.2,
                "tip_chord": 0.1,
                "span": 0.15,
                "sweep_length": 0.05
            }
        ],
        "motor_mount": {
            "enabled": True,
            "position": 2.5
        },
        "rail_guides": {
            "enabled": True,
            "upper_position": 1.0,
            "lower_position": 2.2
        }
    })

def test_build_vehicle_success(valid_vehicle_config, tmp_path):
    rocket = build_vehicle(valid_vehicle_config, motor=None, project_dir=tmp_path)
    assert isinstance(rocket, Rocket)
    assert rocket.mass == 15.0
    assert rocket.radius == 0.075  # 0.15 / 2
    
def test_build_vehicle_missing_mass(valid_vehicle_config, tmp_path):
    valid_vehicle_config["mass_properties"]["mass_without_motor"] = None
    with pytest.raises(ConfigurationError, match="mass_without_motor is required"):
        build_vehicle(valid_vehicle_config, motor=None, project_dir=tmp_path)

def test_build_vehicle_missing_drag_file(valid_vehicle_config, tmp_path):
    valid_vehicle_config["drag"]["power_off"] = {
        "source_type": "file",
        "file": "missing.csv"
    }
    with pytest.raises(ConfigurationError, match="Drag file not found"):
        build_vehicle(valid_vehicle_config, motor=None, project_dir=tmp_path)
