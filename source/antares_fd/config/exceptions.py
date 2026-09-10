class ConfigurationError(Exception):
    """Base class for configuration errors."""
    pass

class AtmosphereUnavailableError(ConfigurationError):
    """Raised when the requested atmospheric source is unavailable."""
    pass
