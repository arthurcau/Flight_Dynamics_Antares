import sys
from pathlib import Path

sys.path.insert(0, str(Path("source").resolve()))
from antares_fd.config.loader import load_project_config

config = load_project_config(Path("projects/neblina_1"))
print(config.launch.get("heading"))
print(config.launch.get("rail", {}).get("heading_deg"))
