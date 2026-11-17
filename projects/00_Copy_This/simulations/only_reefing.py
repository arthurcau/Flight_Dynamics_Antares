"""Run the canonical only_reefing scenario using this project's YAML data."""
from pathlib import Path
import sys

PROJECT_DIR = Path(__file__).resolve().parents[1]
ROOT = PROJECT_DIR.parents[1]
sys.path.insert(0, str(ROOT / "source"))
from antares_fd.config import load_project_config
from antares_fd.simulation import execute_scenario


def main():
    """Execute o cenário only_reefing com a configuração do projeto.

    Localiza o projeto por __file__, carrega YAMLs e chama o orquestrador
    compartilhado. Retorna Flight e grava os artefatos previstos pelo executor;
    não define constantes físicas adicionais neste ponto de entrada.
    """
    return execute_scenario(load_project_config(PROJECT_DIR), PROJECT_DIR, scenario_id="only_reefing")


if __name__ == "__main__":
    main()
