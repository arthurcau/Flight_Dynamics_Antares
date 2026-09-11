import sys
from pathlib import Path

# Add the 'source' directory to the Python path
sys.path.insert(0, str(Path("source").resolve()))

from antares_fd.config.loader import load_project_config
from antares_fd.simulation.monte_carlo_failure import execute_monte_carlo

PROJECT_DIR = Path("projects/neblina_1")

def main():
    print(f"Loading configuration for {PROJECT_DIR.name}...")
    config = load_project_config(PROJECT_DIR)
    
    # Run monte carlo
    execute_monte_carlo(config, PROJECT_DIR)

if __name__ == "__main__":
    main()
