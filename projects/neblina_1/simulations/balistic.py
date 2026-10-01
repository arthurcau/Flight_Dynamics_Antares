"""Run the canonical ballistic scenario using this project's YAML data.

The filename keeps a historical misspelling; the campaign runner maps it to
the canonical ``ballistic`` scenario ID. Review notes by Cau.
"""
from pathlib import Path
import sys

PROJECT_DIR = Path(__file__).resolve().parents[1]
ROOT = PROJECT_DIR.parents[1]
sys.path.insert(0, str(ROOT / "source"))
from antares_fd.config import load_project_config
from antares_fd.simulation import execute_scenario


def main():
    """Load Neblina 1 inputs and run the ballistic scenario."""
    return execute_scenario(load_project_config(PROJECT_DIR), PROJECT_DIR, scenario_id="ballistic")


if __name__ == "__main__":
    main()
