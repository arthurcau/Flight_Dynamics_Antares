import sys
from pathlib import Path
sys.path.insert(0, str(Path("source").resolve()))
from antares_fd.config import load_project_config
from antares_fd.builders.environment import build_environment
PROJECT_DIR = Path("projects/neblina_1")
config = load_project_config(PROJECT_DIR)
env = build_environment(config.environment, config.launch)
print(env)
