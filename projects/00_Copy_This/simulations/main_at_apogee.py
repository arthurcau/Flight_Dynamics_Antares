"""Run the canonical main_at_apogee scenario using this project's YAML data."""
from pathlib import Path
import sys

PROJECT_DIR = Path(__file__).resolve().parents[1]
ROOT = PROJECT_DIR.parents[1]
sys.path.insert(0, str(ROOT / "source"))
from antares_fd.config import load_project_config
from antares_fd.simulation import execute_scenario


def main():
    return execute_scenario(load_project_config(PROJECT_DIR), PROJECT_DIR, scenario_id="main_at_apogee")


if __name__ == "__main__":
    main()
