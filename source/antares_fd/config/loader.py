import yaml
from pathlib import Path
from typing import Any

from .exceptions import ConfigurationError
from .models import ProjectConfig, ConfigDict

def _load_yaml_file(file_path: Path) -> dict:
    if not file_path.exists():
        raise ConfigurationError(f"Configuration file not found: {file_path}")
    
    with file_path.open("r", encoding="utf-8") as f:
        try:
            data = yaml.safe_load(f)
            if data is None:
                return {}
            return data
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Malformed YAML in {file_path}: {e}")

def _dict_to_config_dict(d: Any) -> Any:
    if isinstance(d, dict):
        return ConfigDict({k: _dict_to_config_dict(v) for k, v in d.items()})
    elif isinstance(d, list):
        return [_dict_to_config_dict(v) for v in d]
    return d

def load_project_config(project_dir: Path) -> ProjectConfig:
    """
    Loads all relevant YAML configuration files from a project directory
    and returns a unified ProjectConfig object.
    
    Raises:
        ConfigurationError: If required files are missing or malformed.
    """
    config_dir = project_dir / "config"
    
    if not config_dir.exists():
        raise ConfigurationError(f"Config directory not found at {config_dir}")
        
    # Load required configurations
    vehicle_raw = _load_yaml_file(config_dir / "vehicle.yaml")
    recovery_raw = _load_yaml_file(config_dir / "recovery.yaml")
    launch_raw = _load_yaml_file(config_dir / "launch.yaml")
    
    # Isolate root sections if they exist, or take the whole file
    vehicle_data = vehicle_raw.get("vehicle", vehicle_raw)
    recovery_data = recovery_raw.get("recovery", recovery_raw)
    launch_data = launch_raw.get("launch", launch_raw)
    
    # Wrap dicts for dot-notation access
    vehicle_config = _dict_to_config_dict(vehicle_data)
    recovery_config = _dict_to_config_dict(recovery_data)
    launch_config = _dict_to_config_dict(launch_data)
    
    # Validate required fields (fail-fast philosophy)
    # Example validation: checking if name is present
    if getattr(vehicle_config, "name", None) is None:
        raise ConfigurationError("vehicle.yaml is missing required field: name")
        
    # Attempt to load future configurations (optional for now)
    motor_config = None
    if (config_dir / "motor.yaml").exists():
        motor_raw = _load_yaml_file(config_dir / "motor.yaml")
        motor_config = _dict_to_config_dict(motor_raw.get("motor", motor_raw))
        
    environment_config = None
    if (config_dir / "environment.yaml").exists():
        env_raw = _load_yaml_file(config_dir / "environment.yaml")
        environment_config = _dict_to_config_dict(env_raw.get("environment", env_raw))
        
    simulation_config = None
    if (config_dir / "simulation.yaml").exists():
        sim_raw = _load_yaml_file(config_dir / "simulation.yaml")
        simulation_config = _dict_to_config_dict(sim_raw.get("simulation", sim_raw))
        
    monte_carlo_config = None
    if (config_dir / "monte_carlo.yaml").exists():
        mc_raw = _load_yaml_file(config_dir / "monte_carlo.yaml")
        monte_carlo_config = _dict_to_config_dict(mc_raw.get("monte_carlo", mc_raw))
        
    return ProjectConfig(
        vehicle=vehicle_config,
        recovery=recovery_config,
        launch=launch_config,
        motor=motor_config,
        environment=environment_config,
        simulation=simulation_config,
        monte_carlo=monte_carlo_config
    )
