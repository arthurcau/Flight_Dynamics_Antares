import pytest
from rocketpy import Rocket
from antares_fd.config.models import ConfigDict
from antares_fd.config.exceptions import ConfigurationError
from antares_fd.builders.recovery import add_recovery_system

@pytest.fixture
def mock_rocket():
    return Rocket(
        radius=0.1,
        mass=10.0,
        inertia=(1,1,1),
        power_off_drag=1.0,
        power_on_drag=1.0,
        center_of_mass_without_motor=0.0
    )

@pytest.fixture
def valid_recovery_config():
    return ConfigDict({
        "enabled": True,
        "settings": {
            "default_sampling_rate": 100.0
        },
        "devices": [
            {
                "id": "drogue",
                "name": "Drogue Parachute",
                "enabled": True,
                "type": "parachute",
                "aerodynamics": {
                    "method": "cd_s",
                    "cd_s": 1.5
                },
                "trigger": {
                    "type": "apogee"
                },
                "deployment": {
                    "lag": 1.0
                }
            },
            {
                "id": "main",
                "name": "Main Parachute",
                "enabled": True,
                "type": "parachute",
                "aerodynamics": {
                    "method": "cd_s",
                    "cd_s": 5.0
                },
                "trigger": {
                    "type": "altitude",
                    "altitude": {
                        "value": 400.0
                    }
                },
                "deployment": {
                    "lag": 1.5
                }
            }
        ]
    })

def test_add_recovery_system_success(mock_rocket, valid_recovery_config):
    add_recovery_system(mock_rocket, valid_recovery_config)
    
    assert len(mock_rocket.parachutes) == 2
    
    drogue = mock_rocket.parachutes[0]
    assert drogue.name == "Drogue Parachute"
    assert drogue.cd_s == 1.5
    assert drogue.trigger == "apogee"
    assert drogue.lag == 1.0
    
    main_para = mock_rocket.parachutes[1]
    assert main_para.name == "Main Parachute"
    assert main_para.cd_s == 5.0
    assert main_para.trigger == 400.0
    assert main_para.lag == 1.5

def test_add_recovery_system_missing_cd_s(mock_rocket, valid_recovery_config):
    valid_recovery_config["devices"][0]["aerodynamics"]["cd_s"] = None
    with pytest.raises(ConfigurationError, match="requires cd_s"):
        add_recovery_system(mock_rocket, valid_recovery_config)

def test_add_recovery_system_missing_lag(mock_rocket, valid_recovery_config):
    valid_recovery_config["devices"][1]["deployment"]["lag"] = None
    with pytest.raises(ConfigurationError, match="requires deployment lag"):
        add_recovery_system(mock_rocket, valid_recovery_config)

def test_add_recovery_system_disabled(mock_rocket, valid_recovery_config):
    valid_recovery_config["enabled"] = False
    add_recovery_system(mock_rocket, valid_recovery_config)
    assert len(mock_rocket.parachutes) == 0
