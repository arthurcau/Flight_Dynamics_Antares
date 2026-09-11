import sys
from pathlib import Path

# Add source to path
sys.path.insert(0, str(Path("source").resolve()))
from antares_fd.builders.environment import build_environment
from antares_fd.config.loader import load_project_config

project_dir = Path("projects/neblina_1")
config = load_project_config(project_dir)
env = build_environment(config.environment, config.launch)
print("SUCCESS!")
