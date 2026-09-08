from antares_fd.config.exceptions import ConfigurationError

def _build_trigger(trigger_config):
    """
    Translates the YAML trigger configuration into a RocketPy trigger.
    RocketPy triggers can be 'apogee', a float (altitude), or a callable.
    """
    ttype = trigger_config.get("type")
    
    if ttype == "apogee":
        return "apogee"
    elif ttype == "altitude":
        alt_config = trigger_config.get("altitude", {})
        value = alt_config.get("value")
        if value is None:
            raise ConfigurationError("recovery trigger altitude value is required")
        # RocketPy uses the float value directly for descending altitude triggers
        return float(value)
    elif ttype == "time":
        time_config = trigger_config.get("time", {})
        value = time_config.get("value")
        if value is None:
            raise ConfigurationError("recovery trigger time value is required")
        # RocketPy expects a callable for time triggers: lambda p, y: y[5] > value etc.
        # But for standard parameters, RocketPy supports time based?
        # Actually RocketPy parachutes trigger on time using a custom function.
        # We will require a custom function for time, or fail fast for now.
        raise ConfigurationError("Time-based recovery triggers are not natively supported as a simple value in this builder yet. Use a custom trigger.")
    elif ttype == "custom":
        raise ConfigurationError("Custom recovery triggers are not yet implemented in the generic builder.")
    else:
        raise ConfigurationError(f"Unsupported recovery trigger type: {ttype}")

def add_recovery_system(rocket, config):
    """
    Adds Parachute objects to the RocketPy Rocket based on the recovery configuration.
    """
    print("Adding Recovery System...")
    
    if not config or not config.get("enabled", False):
        return
        
    settings = config.get("settings", {})
    default_sampling = settings.get("default_sampling_rate", 100.0)
    
    devices = config.get("devices", [])
    
    for device in devices:
        if not device.get("enabled", True):
            continue
            
        if device.get("type") != "parachute":
            raise ConfigurationError(f"Unsupported recovery device type: {device.get('type')}")
            
        name = device.get("name", device.get("id", "Parachute"))
        
        # Aerodynamics
        aero = device.get("aerodynamics", {})
        if aero.get("method") == "cd_s":
            cd_s = aero.get("cd_s")
        else:
            # Calculate from cd and area if provided
            cd = aero.get("drag_coefficient")
            area = aero.get("reference_area")
            if cd is None or area is None:
                raise ConfigurationError(f"recovery device '{name}' requires cd_s or drag_coefficient + reference_area")
            cd_s = cd * area
            
        if cd_s is None:
            raise ConfigurationError(f"recovery device '{name}' requires cd_s")
            
        # Trigger
        trigger = _build_trigger(device.get("trigger", {}))
        
        # Sampling
        sampling_rate = device.get("sampling", {}).get("rate", default_sampling)
        
        # Deployment Lag
        lag = device.get("deployment", {}).get("lag")
        if lag is None:
            raise ConfigurationError(f"recovery device '{name}' requires deployment lag")
            
        # Sensor Noise
        noise = None
        sensor_model = device.get("sensor_model", {})
        if sensor_model.get("pressure", {}).get("noise_enabled", False):
            bias = sensor_model["pressure"].get("bias", 0.0)
            std_dev = sensor_model["pressure"].get("standard_deviation", 0.0)
            corr = sensor_model["pressure"].get("time_correlation", 0.0)
            noise = (bias, std_dev, corr)
            
        kwargs = {
            "name": name,
            "cd_s": cd_s,
            "trigger": trigger,
            "sampling_rate": sampling_rate,
            "lag": lag
        }
        if noise:
            kwargs["noise"] = noise
            
        rocket.add_parachute(**kwargs)
