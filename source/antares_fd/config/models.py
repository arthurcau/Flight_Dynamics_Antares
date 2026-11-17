from dataclasses import dataclass
from typing import Any, Optional

class ConfigDict(dict):
    """
    A dictionary subclass that allows dot notation for accessing keys.
    Useful for transparently accessing YAML configuration trees like `config.vehicle.mass`.
    """
    def __getattr__(self, name: str) -> Any:
        """Leia uma chave pelo acesso de atributo.

        Retorna self[name]; chave ausente gera AttributeError para manter o contrato
        de getattr e hasattr, sem fabricar um valor padrão.
        """
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'ConfigDict' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        """Grave um atributo como chave do dicionário de configuração.

        Atribui value em self[name] e retorna None. A operação modifica a instância
        e mantém acesso por chave e por atributo sobre o mesmo armazenamento.
        """
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
    environment: Optional[ConfigDict] = None
    simulation: Optional[ConfigDict] = None
    monte_carlo: Optional[ConfigDict] = None
