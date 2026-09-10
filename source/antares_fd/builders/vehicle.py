from pathlib import Path
from rocketpy import Rocket
from antares_fd.config.exceptions import ConfigurationError

def _resolve_drag_source(drag_config, project_dir: Path):
    if not drag_config:
        return 0.0
    
    source_type = drag_config.get("source_type")
    if source_type == "file":
        filepath = drag_config.get("file")
        if not filepath:
            raise ConfigurationError("drag source_type is 'file' but no 'file' path provided")
        full_path = project_dir / filepath
        if not full_path.exists():
            # For the template, we might want to return 0.0 or a dummy, 
            # but strict validation says we must fail fast.
            # However, if this is 00_Copy_This, it might not exist.
            # We'll fail fast as requested by architecture principles.
            raise ConfigurationError(f"Drag file not found: {full_path}")
        return str(full_path)
    elif source_type == "constant":
        const_val = drag_config.get("constant")
        if const_val is None:
            raise ConfigurationError("drag source_type is 'constant' but no 'constant' provided")
        return float(const_val)
    return 0.0

def build_vehicle(vehicle_config, motor, project_dir: Path) -> Rocket:
    """Builds the RocketPy Rocket object from the vehicle configuration."""
    print("Building Vehicle...")
    
    # --- 1. Basic Geometry and Mass Properties ---
    geometry = vehicle_config.get("geometry", {})
    mass_props = vehicle_config.get("mass_properties", {})
    
    ref_dia = geometry.get("reference_diameter")
    if ref_dia is None:
        raise ConfigurationError("vehicle.geometry.reference_diameter is required")
        
    mass = mass_props.get("mass_without_motor")
    if mass is None:
        raise ConfigurationError("vehicle.mass_properties.mass_without_motor is required")
        
    cm = mass_props.get("center_of_mass_without_motor")
    if cm is None:
        raise ConfigurationError("vehicle.mass_properties.center_of_mass_without_motor is required")
        
    inertia_config = mass_props.get("inertia", {})
    inertia = [
        inertia_config.get("I11"),
        inertia_config.get("I22"),
        inertia_config.get("I33"),
        inertia_config.get("I12", 0.0),
        inertia_config.get("I13", 0.0),
        inertia_config.get("I23", 0.0)
    ]
    if None in inertia[:3]:
        raise ConfigurationError("vehicle.mass_properties.inertia I11, I22, I33 are required")

    # --- 2. Aerodynamics ---
    drag = vehicle_config.get("drag", {})
    power_on_drag = _resolve_drag_source(drag.get("power_on", {}), project_dir)
    power_off_drag = _resolve_drag_source(drag.get("power_off", {}), project_dir)

    rocket = Rocket(
        radius=ref_dia / 2.0,
        mass=mass,
        inertia=inertia,
        power_off_drag=power_off_drag,
        power_on_drag=power_on_drag,
        center_of_mass_without_motor=cm,
        coordinate_system_orientation=vehicle_config.get("coordinate_system", {}).get("rocketpy_orientation", "nose_to_tail")
    )

    # --- 3. Motor Installation ---
    motor_mount = vehicle_config.get("motor_mount", {})
    if motor_mount.get("enabled", False):
        pos = motor_mount.get("position")
        if pos is None:
            raise ConfigurationError("vehicle.motor_mount.position is required")
        if motor:
            rocket.add_motor(motor=motor, position=pos)

    # --- 4. Aerodynamic Surfaces ---
    nose = vehicle_config.get("nose", {})
    if nose.get("enabled", False):
        kind = nose.get("type", "").replace("_", "")
        length = nose.get("length")
        pos = nose.get("position", 0.0)
        base_radius = nose.get("base_radius")
        if base_radius is None:
            base_radius = ref_dia / 2.0
            
        if length is None:
            raise ConfigurationError("vehicle.nose.length is required")
            
        rocket.add_nose(
            length=length,
            kind=kind,
            position=pos,
            base_radius=base_radius
        )

    tails = vehicle_config.get("tails", [])
    for t in tails:
        if t.get("enabled", True):
            for field in ["top_radius", "bottom_radius", "length", "position"]:
                if t.get(field) is None:
                    raise ConfigurationError(f"vehicle.tails requires {field}")
            rocket.add_tail(
                top_radius=t.get("top_radius"),
                bottom_radius=t.get("bottom_radius"),
                length=t.get("length"),
                position=t.get("position")
            )

    fin_sets = vehicle_config.get("fin_sets", [])
    for f in fin_sets:
        if f.get("enabled", True):
            ftype = f.get("type")
            pos = f.get("position")
            if pos is None:
                raise ConfigurationError(f"vehicle.fin_sets position is required for fin set '{f.get('name')}'")
            
            radius = f.get("body_radius")
            if radius is None:
                radius = ref_dia / 2.0
                
            n = f.get("number")
            if n is None:
                raise ConfigurationError(f"vehicle.fin_sets number is required for fin set '{f.get('name')}'")
                
            if ftype == "trapezoidal":
                for field in ["root_chord", "tip_chord", "span"]:
                    if f.get(field) is None:
                        raise ConfigurationError(f"vehicle.fin_sets (trapezoidal) requires {field}")
                fin_kwargs = {
                    "n": n,
                    "root_chord": f.get("root_chord"),
                    "tip_chord": f.get("tip_chord"),
                    "span": f.get("span"),
                    "position": pos,
                    "cant_angle": f.get("cant_angle_deg", 0.0),
                    "radius": radius
                }
                if f.get("sweep_length") is not None:
                    fin_kwargs["sweep_length"] = f.get("sweep_length")
                if f.get("sweep_angle_deg") is not None:
                    fin_kwargs["sweep_angle"] = f.get("sweep_angle_deg")
                    
                rocket.add_trapezoidal_fins(**fin_kwargs)
            elif ftype == "elliptical":
                for field in ["root_chord", "span"]:
                    if f.get(field) is None:
                        raise ConfigurationError(f"vehicle.fin_sets (elliptical) requires {field}")
                rocket.add_elliptical_fins(
                    n=n,
                    root_chord=f.get("root_chord"),
                    span=f.get("span"),
                    position=pos,
                    cant_angle=f.get("cant_angle_deg", 0.0),
                    radius=radius
                )

    # --- 5. Rail Guides ---
    rails = vehicle_config.get("rail_guides", {})
    if rails.get("enabled", False):
        u_pos = rails.get("upper_position")
        l_pos = rails.get("lower_position")
        if u_pos is None or l_pos is None:
            raise ConfigurationError("vehicle.rail_guides upper and lower positions are required")
        rocket.set_rail_buttons(
            upper_button_position=u_pos,
            lower_button_position=l_pos,
            angular_position=rails.get("angular_position_deg", 45.0)
        )

    return rocket
