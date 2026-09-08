import pytest
from pathlib import Path

from antares_fd.config import load_project_config, ConfigurationError

def test_load_project_config_success(tmp_path):
    # Setup mock project directory with valid configuration
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    
    vehicle_yaml = """
    vehicle:
      name: "Test Rocket"
      revision: "1.0"
      mass_properties:
        mass_without_motor: 10.0
    """
    recovery_yaml = """
    recovery:
      enabled: true
    """
    launch_yaml = """
    launch:
      site:
        latitude: -21.0
        longitude: -49.0
    """
    
    (config_dir / "vehicle.yaml").write_text(vehicle_yaml)
    (config_dir / "recovery.yaml").write_text(recovery_yaml)
    (config_dir / "launch.yaml").write_text(launch_yaml)
    
    # Load the config
    config = load_project_config(tmp_path)
    
    # Assert dot notation works and values are correct
    assert config.vehicle.name == "Test Rocket"
    assert config.vehicle.revision == "1.0"
    assert config.vehicle.mass_properties.mass_without_motor == 10.0
    assert config.recovery.enabled is True
    assert config.launch.site.latitude == -21.0
    
    # Ensure missing future files default to None
    assert config.motor is None
    assert config.environment is None
    assert config.simulation is None

def test_load_project_config_missing_dir(tmp_path):
    with pytest.raises(ConfigurationError, match="Config directory not found"):
        load_project_config(tmp_path)

def test_load_project_config_missing_file(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    
    (config_dir / "vehicle.yaml").write_text("vehicle: {name: 'Test'}")
    (config_dir / "recovery.yaml").write_text("recovery: {}")
    # Missing launch.yaml
    
    with pytest.raises(ConfigurationError, match="Configuration file not found"):
        load_project_config(tmp_path)

def test_load_project_config_malformed_yaml(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    
    (config_dir / "vehicle.yaml").write_text("vehicle: [unclosed list")
    (config_dir / "recovery.yaml").write_text("recovery: {}")
    (config_dir / "launch.yaml").write_text("launch: {}")
    
    with pytest.raises(ConfigurationError, match="Malformed YAML"):
        load_project_config(tmp_path)
