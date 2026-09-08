import datetime
from rocketpy import Environment
from antares_fd.config.exceptions import ConfigurationError

def build_environment(environment_config, launch_config) -> Environment:
    """Builds the RocketPy Environment object from configurations."""
    print("Building Environment...")
    
    if not launch_config:
        raise ConfigurationError("launch_config is required to build Environment")
        
    site = launch_config.get("site", {})
    lat = site.get("latitude")
    lon = site.get("longitude")
    elev = site.get("elevation")
    datum = site.get("datum", "SIRGAS2000")
    
    if lat is None or lon is None or elev is None:
        raise ConfigurationError("launch.site requires latitude, longitude, and elevation")
        
    env = Environment(
        latitude=lat,
        longitude=lon,
        elevation=elev,
        datum=datum
    )
    
    dt_config = launch_config.get("datetime", {})
    date_str = dt_config.get("date")
    time_str = dt_config.get("time")
    tz = dt_config.get("timezone", "America/Sao_Paulo")
    
    if date_str and time_str:
        try:
            # Parse YYYY-MM-DD and HH:MM:SS
            year, month, day = map(int, date_str.split('-'))
            hour, minute, second = map(int, time_str.split(':'))
            env.set_date(
                (year, month, day, hour, minute, second),
                timezone=tz
            )
        except ValueError:
            raise ConfigurationError(f"Invalid date/time format. Expected YYYY-MM-DD and HH:MM:SS, got '{date_str}' '{time_str}'")
    else:
        # If date or time is not defined, we might raise an error based on rules
        raise ConfigurationError("launch.datetime.date and time are required")
        
    # Later: Apply atmospheric models from environment_config
    if environment_config:
        # Placeholder for atmospheric model setup
        # e.g., env.set_atmospheric_model(...)
        pass
    else:
        # Optional: default atmosphere if nothing is specified?
        # RocketPy uses standard atmosphere by default
        env.set_atmospheric_model(type="standard_atmosphere")

    return env
