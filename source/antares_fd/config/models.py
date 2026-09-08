from dataclasses import dataclass
from typing import Any, Dict

class ConfigDict(dict):
    """
    A dictionary subclass that allows dot notation for accessing keys.
    Useful for transparently accessing YAML configuration trees like `config.vehicle.mass`.
    """
    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'ConfigDict' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value

@dataclass
class ProjectConfig:
    """
    Top-level configuration object returned by the loader.
    """
    vehicle: ConfigDict
    recovery: ConfigDict
    launch: ConfigDict
    motor: ConfigDict | None = None
    environment: ConfigDict | None = None
    simulation: ConfigDict | None = None
