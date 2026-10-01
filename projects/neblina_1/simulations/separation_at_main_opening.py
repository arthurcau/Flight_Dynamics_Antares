"""
ANTARES FLIGHT DYNAMICS
Simplified mass-change example associated with main deployment.

This script subtracts an assumed 2 kg before the entire simulated flight; it
does not model a timed separation at main opening and is excluded from the
campaign runner. Review notes by Cau.
"""
import sys
from pathlib import Path

# Allow direct execution from a source checkout without an editable install.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SOURCE_DIR = PROJECT_ROOT / "source"
if str(SOURCE_DIR) not in sys.path:
    sys.path.insert(0, str(SOURCE_DIR))
    sys.path.insert(0, str(PROJECT_ROOT))

from antares_fd.config import load_project_config
from antares_fd.simulation import execute_scenario

def main():
    """Run the nominal flight after applying the illustrative 2 kg mass reduction."""
    PROJECT_DIR = Path(__file__).resolve().parents[1]
    
    # 1. Load configuration
    config = load_project_config(PROJECT_DIR)
    
    # This changes mass from ignition onward; it is not a deployment-time event.
    # Keep the assumed value visible until a measured separation mass is available.
    separated_mass = 2.0 
    original_mass = config.vehicle["mass_properties"]["mass_without_motor"]
    
    if original_mass and original_mass > separated_mass:
        print(f"Modifying vehicle mass to simulate separation. Original: {original_mass} kg, New: {original_mass - separated_mass} kg")
        config.vehicle["mass_properties"]["mass_without_motor"] = original_mass - separated_mass

    # 3. Execute scenario
    flight = execute_scenario(config, PROJECT_DIR)
    
    return flight

if __name__ == "__main__":
    main()
