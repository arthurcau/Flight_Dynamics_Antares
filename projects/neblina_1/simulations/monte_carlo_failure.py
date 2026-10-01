"""Launch the failure-aware Monte Carlo engine for Neblina 1.

The scenario and sample policy come from shared Antares code and project YAML;
this file only resolves the project directory and starts that runner. Review
notes by Cau.
"""

import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = PROJECT_DIR.parents[1]

sys.path.insert(0, str(PROJECT_ROOT / "source"))
sys.path.insert(0, str(PROJECT_ROOT))

from antares_fd.config.loader import load_project_config
from antares_fd.simulation.monte_carlo_failure import execute_monte_carlo

def main():
    """Load the project configuration and execute its stochastic campaign."""
    print(f"Loading configuration for {PROJECT_DIR.name}...")
    config = load_project_config(PROJECT_DIR)
    
    # Run monte carlo
    execute_monte_carlo(config, PROJECT_DIR)

if __name__ == "__main__":
    main()
