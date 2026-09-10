import sys
from pathlib import Path
sys.path.insert(0, str(Path("source").resolve()))
from antares_fd.config import load_project_config
from antares_fd.simulation import execute_scenario
PROJECT_DIR = Path("projects/neblina_1")
config = load_project_config(PROJECT_DIR)
flight = execute_scenario(config, PROJECT_DIR)
print(flight.parachute_events)
