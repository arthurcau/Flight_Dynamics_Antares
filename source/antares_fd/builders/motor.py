from pathlib import Path
from rocketpy import SolidMotor, HybridMotor, LiquidMotor
from antares_fd.config.exceptions import ConfigurationError

def build_motor(config, project_dir: Path):
    """
    Builds a RocketPy Motor object from configuration.
    
    NOTE: The canonical schema for motor.yaml has not yet been fully 
    defined by the engineering team. This builder provides a minimal 
    implementation to allow the simulation pipeline to run, assuming 
    the configuration matches RocketPy's SolidMotor arguments.
    """
    print("Building Motor...")
    if not config:
        raise ConfigurationError("motor configuration is missing. A motor.yaml file is required.")
        
    motor_type = config.get("type", "solid").lower()
    
    if motor_type == "solid":
        # We expect config to provide the basic RocketPy SolidMotor parameters
        thrust_source = config.get("thrust_source")
        if isinstance(thrust_source, str):
            thrust_source = str(project_dir / thrust_source)
            
        try:
            return SolidMotor(
                thrust_source=thrust_source,
                burn_time=config.get("burn_time"),
                dry_mass=config.get("dry_mass"),
                dry_inertia=config.get("dry_inertia", (0,0,0)),
                center_of_dry_mass_position=config.get("center_of_dry_mass_position"),
                grains_center_of_mass_position=config.get("grains_center_of_mass_position"),
                grain_number=config.get("grain_number"),
                grain_separation=config.get("grain_separation"),
                grain_density=config.get("grain_density"),
                grain_outer_radius=config.get("grain_outer_radius"),
                grain_initial_inner_radius=config.get("grain_initial_inner_radius"),
                grain_initial_height=config.get("grain_initial_height"),
                nozzle_radius=config.get("nozzle_radius"),
                throat_radius=config.get("throat_radius"),
                interpolation_method=config.get("interpolation_method", "linear"),
                coordinate_system_orientation=config.get("coordinate_system_orientation", "nozzle_to_combustion_chamber")
            )
        except TypeError as e:
            raise ConfigurationError(f"Failed to build SolidMotor. Verify motor.yaml matches required RocketPy arguments. Error: {e}")
            
    else:
        raise ConfigurationError(f"Motor type '{motor_type}' is not yet supported or defined.")
