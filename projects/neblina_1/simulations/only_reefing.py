"""Run the configured two-stage reefing recovery scenario.

The shared scenario registry uses a reduced-area reefed stage near apogee and
the configured main parachute for the later descent. Review notes by Cau.
"""
from pathlib import Path
import sys

PROJECT_DIR = Path(__file__).resolve().parents[1]
ROOT = PROJECT_DIR.parents[1]
sys.path.insert(0, str(ROOT / "source"))
from antares_fd.config import load_project_config
from antares_fd.simulation import execute_scenario


def main():
    """Load Neblina 1 inputs and run the only-reefing scenario."""
    return execute_scenario(load_project_config(PROJECT_DIR), PROJECT_DIR, scenario_id="only_reefing")


if __name__ == "__main__":
    main()
