import sys
from pathlib import Path
from antares_fd.config.loader import load_project_config
from antares_fd.simulation.orchestrator import execute_scenario

config = load_project_config(Path("projects/00_Copy_This"))
flight = execute_scenario(config, Path("projects/00_Copy_This"), print_summary=False, export_kml=False)

print([d for d in dir(flight) if "pitch" in d or "roll" in d or "yaw" in d or "euler" in d or "attitude" in d])
