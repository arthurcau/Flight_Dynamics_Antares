import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = PROJECT_DIR.parents[1]

sys.path.insert(0, str(PROJECT_ROOT / "source"))
sys.path.insert(0, str(PROJECT_ROOT))

from antares_fd.config.loader import load_project_config
from antares_fd.simulation.monte_carlo_failure import execute_monte_carlo

def main():
    print(f"Loading configuration for {PROJECT_DIR.name}...")
    config = load_project_config(PROJECT_DIR)
    
    # Run monte carlo
    execute_monte_carlo(config, PROJECT_DIR)

if __name__ == "__main__":
    main()
