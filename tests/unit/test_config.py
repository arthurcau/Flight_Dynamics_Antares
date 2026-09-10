import pytest
from pathlib import Path
from antares_fd.config.loader import load_project_config
from antares_fd.config.exceptions import ConfigurationError

def test_missing_config_dir(tmp_path):
    project_dir = tmp_path / "my_rocket"
    project_dir.mkdir()
    
    with pytest.raises(ConfigurationError, match="Config directory not found"):
        load_project_config(project_dir)

def test_missing_required_files(tmp_path):
    project_dir = tmp_path / "my_rocket"
    config_dir = project_dir / "config"
    config_dir.mkdir(parents=True)
    
    # Missing vehicle.yaml, etc.
    with pytest.raises(ConfigurationError, match="Configuration file not found"):
        load_project_config(project_dir)

def test_missing_vehicle_name(tmp_path):
    project_dir = tmp_path / "my_rocket"
    config_dir = project_dir / "config"
    config_dir.mkdir(parents=True)
    
    (config_dir / "vehicle.yaml").write_text("vehicle:\n  mass: 10\n")
    (config_dir / "recovery.yaml").write_text("recovery:\n  enabled: true\n")
    (config_dir / "launch.yaml").write_text("launch:\n  site: apu\n")
    
    with pytest.raises(ConfigurationError, match="vehicle.yaml is missing required field: name"):
        load_project_config(project_dir)

def test_successful_load(tmp_path):
    project_dir = tmp_path / "my_rocket"
    config_dir = project_dir / "config"
    config_dir.mkdir(parents=True)
    
    (config_dir / "vehicle.yaml").write_text("vehicle:\n  name: TestRocket\n  mass: 10\n")
    (config_dir / "recovery.yaml").write_text("recovery:\n  enabled: true\n")
    (config_dir / "launch.yaml").write_text("launch:\n  site: apu\n")
    (config_dir / "monte_carlo.yaml").write_text("monte_carlo:\n  num_simulations: 50\n")
    
    config = load_project_config(project_dir)
    
    assert config.vehicle.name == "TestRocket"
    assert config.vehicle.mass == 10
    assert config.recovery.enabled is True
    assert config.launch.site == "apu"
    assert config.monte_carlo.num_simulations == 50
    assert config.motor is None

def test_malformed_yaml(tmp_path):
    project_dir = tmp_path / "my_rocket"
    config_dir = project_dir / "config"
    config_dir.mkdir(parents=True)
    
    (config_dir / "vehicle.yaml").write_text("vehicle: \n - [\n malformed")
    
    with pytest.raises(ConfigurationError, match="Malformed YAML"):
        load_project_config(project_dir)
