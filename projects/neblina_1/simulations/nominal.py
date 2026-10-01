"""
ANTARES FLIGHT DYNAMICS
Run Neblina 1's nominal flight configuration.

The shared orchestrator applies the nominal scenario to a copy of the loaded
configuration, builds the RocketPy objects, runs the flight, and writes the
standard results. Review notes by Cau.
"""
import sys
from pathlib import Path

# Ensures core packages ('source' and 'MAGI' root) can be imported
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SOURCE_DIR = PROJECT_ROOT / "source"
if str(SOURCE_DIR) not in sys.path:
    sys.path.insert(0, str(SOURCE_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from antares_fd.config import load_project_config
from antares_fd.simulation import execute_scenario

def main():
    """Build and run the nominal Neblina 1 flight, returning the RocketPy flight."""
    PROJECT_DIR = Path(__file__).resolve().parents[1]
    
    # 1. Load nominal configuration (unmodified)
    config = load_project_config(PROJECT_DIR)
    
    # 2. Execute scenario
    flight = execute_scenario(config, PROJECT_DIR)
    
    return flight

if __name__ == "__main__":
    main()
