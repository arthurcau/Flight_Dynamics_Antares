"""
ANTARES FLIGHT DYNAMICS
Nominal Flight Simulation
"""
import sys
from pathlib import Path

# Resolve o pacote compartilhado no diretório source, inclusive no Linux.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SOURCE_DIR = PROJECT_ROOT / "source"
if str(SOURCE_DIR) not in sys.path:
    sys.path.insert(0, str(SOURCE_DIR))

from antares_fd.config import load_project_config
from antares_fd.simulation import execute_scenario

def main():
    """Execute o cenário nominal com a configuração do projeto.

    Localiza o projeto por __file__, carrega YAMLs e chama o orquestrador
    compartilhado. Retorna Flight e grava os artefatos previstos pelo executor;
    não define constantes físicas adicionais neste ponto de entrada.
    """
    PROJECT_DIR = Path(__file__).resolve().parents[1]

    # 1. Load nominal configuration (unmodified)
    config = load_project_config(PROJECT_DIR)

    # 2. Execute scenario
    flight = execute_scenario(config, PROJECT_DIR)

    return flight

if __name__ == "__main__":
    main()
