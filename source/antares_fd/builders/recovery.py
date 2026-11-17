from antares_fd.config.exceptions import ConfigurationError
import math


def _finite_number(value, field, *, minimum=None, positive=False):
    """Valide um parâmetro escalar da recuperação antes de alterar o foguete.

    Converte value em float, rejeita booleanos e valores não finitos e exige
    o limite mínimo informado. positive=True exige valor maior que zero.
    Retorna float ou lança ConfigurationError com identificação de field.
    """
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ConfigurationError(f"{field} must be a finite number") from exc
    if isinstance(value, bool) or not math.isfinite(number):
        raise ConfigurationError(f"{field} must be a finite number")
    if positive and number <= 0:
        raise ConfigurationError(f"{field} must be positive")
    if minimum is not None and number < minimum:
        raise ConfigurationError(f"{field} must be at least {minimum}")
    return number

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
        if alt_config.get("direction", "descending") not in {"descending", "descent"}:
            raise ConfigurationError("Altitude recovery triggers currently support descent only")
        # RocketPy uses the float value directly for descending altitude triggers
        return _finite_number(value, "recovery trigger altitude", minimum=0)
    elif ttype == "time":
        time_config = trigger_config.get("time", {})
        value = time_config.get("value")
        if value is None:
            raise ConfigurationError("recovery trigger time value is required")
        # O schema atual não define um callable temporal verificável.
        raise ConfigurationError("Time-based recovery triggers are not natively supported as a simple value in this builder yet. Use a custom trigger.")
    elif ttype == "custom":
        raise ConfigurationError("Custom recovery triggers are not yet implemented in the generic builder.")
    else:
        raise ConfigurationError(f"Unsupported recovery trigger type: {ttype}")

def add_recovery_system(rocket, config, *, verbose=True):
    """
    Adds Parachute objects to the RocketPy Rocket based on the recovery configuration.
    """
    if verbose:
        print("Adding Recovery System...")

    if not config or not config.get("enabled", False):
        return

    settings = config.get("settings", {})
    if settings.get("altitude_reference", "AGL") != "AGL":
        raise ConfigurationError("Recovery altitude_reference must be AGL")
    default_sampling = settings.get("default_sampling_rate", 100.0)

    devices = config.get("devices", [])
    validated_devices = []

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
            cd_s = (_finite_number(cd, f"{name}.drag_coefficient", positive=True)
                    * _finite_number(area, f"{name}.reference_area", positive=True))

        if cd_s is None:
            raise ConfigurationError(f"recovery device '{name}' requires cd_s")
        cd_s = _finite_number(cd_s, f"{name}.cd_s", positive=True)

        # Trigger
        trigger = _build_trigger(device.get("trigger", {}))

        # Sampling
        sampling_rate = device.get("sampling", {}).get("rate", default_sampling)
        sampling_rate = _finite_number(sampling_rate, f"{name}.sampling_rate", positive=True)

        # Deployment Lag
        lag = device.get("deployment", {}).get("lag")
        if lag is None:
            raise ConfigurationError(f"recovery device '{name}' requires deployment lag")
        lag = _finite_number(lag, f"{name}.lag", minimum=0)

        # Sensor Noise
        noise = None
        sensor_model = device.get("sensor_model", {})
        if sensor_model.get("pressure", {}).get("noise_enabled", False):
            bias = sensor_model["pressure"].get("bias", 0.0)
            std_dev = sensor_model["pressure"].get("standard_deviation", 0.0)
            corr = sensor_model["pressure"].get("time_correlation", 0.0)
            bias = _finite_number(bias, f"{name}.noise.bias")
            std_dev = _finite_number(std_dev, f"{name}.noise.standard_deviation", minimum=0)
            corr = _finite_number(corr, f"{name}.noise.time_correlation", minimum=-1)
            if corr > 1:
                raise ConfigurationError(f"{name}.noise.time_correlation must be in [-1, 1]")
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

        validated_devices.append(kwargs)

    # Uma configuração inválida não deve deixar dispositivos parcialmente adicionados.
    for kwargs in validated_devices:
        rocket.add_parachute(**kwargs)
