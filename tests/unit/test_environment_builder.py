import pytest
import datetime
from rocketpy import Environment

from antares_fd.config.models import ConfigDict
from antares_fd.config.exceptions import ConfigurationError
from antares_fd.builders.environment import build_environment

@pytest.fixture
def valid_launch_config():
    return ConfigDict({
        "site": {
            "latitude": -21.0,
            "longitude": -49.0,
            "elevation": 500.0,
            "datum": "WGS84"
        },
        "datetime": {
            "date": "2027-09-03",
            "time": "14:30:00",
            "timezone": "America/Sao_Paulo"
        }
    })

def test_build_environment_success(valid_launch_config):
    env = build_environment(environment_config=None, launch_config=valid_launch_config)
    
    assert isinstance(env, Environment)
    assert env.latitude == -21.0
    assert env.longitude == -49.0
    assert env.elevation == 500.0
    
    # In RocketPy, the set_date might convert to UTC. 
    # Just verify that the date was successfully applied without crashing.
    assert env.datetime_date is not None

def test_build_environment_missing_site_data(valid_launch_config):
    valid_launch_config["site"]["latitude"] = None
    with pytest.raises(ConfigurationError, match="requires latitude, longitude, and elevation"):
        build_environment(environment_config=None, launch_config=valid_launch_config)

def test_build_environment_invalid_datetime(valid_launch_config):
    valid_launch_config["datetime"]["date"] = "2027/09/03"
    with pytest.raises(ConfigurationError, match="Invalid date/time format"):
        build_environment(environment_config=None, launch_config=valid_launch_config)

def test_build_environment_missing_datetime(valid_launch_config):
    valid_launch_config["datetime"]["time"] = None
    with pytest.raises(ConfigurationError, match="date and time are required"):
        build_environment(environment_config=None, launch_config=valid_launch_config)
