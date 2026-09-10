"""
ANTARES FLIGHT DYNAMICS
Only Reefing Simulation
"""
import sys
from pathlib import Path

# Ensures the core 'Source' package can be imported
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SOURCE_DIR = PROJECT_ROOT / "source"
if str(SOURCE_DIR) not in sys.path:
    sys.path.insert(0, str(SOURCE_DIR))

from antares_fd.config import load_project_config
from antares_fd.simulation import execute_scenario

def main():
    PROJECT_DIR = Path(__file__).resolve().parents[1]
    
    # 1. Load configuration
    config = load_project_config(PROJECT_DIR)
    
    # 2. SCENARIO OVERRIDES: 
    # Models a single main parachute that opens reefed at apogee, and disreefs 
    # at the specified main altitude. 
    main_cd_s = None
    for device in config.recovery.get("devices", []):
        if device.get("id") == "main":
            main_cd_s = device.get("aerodynamics", {}).get("cd_s")
            device["name"] = "Main Parachute (Disreefed)"

    for device in config.recovery.get("devices", []):
        if device.get("id") == "drogue":
            # The drogue acts as the reefed state of the main parachute.
            device["name"] = "Main Parachute (Reefed)"
            if main_cd_s is not None:
                # Example: Reefed state has 15% of the fully open Cd*S
                device["aerodynamics"]["cd_s"] = main_cd_s * 0.3

    # 3. Execute scenario
    flight = execute_scenario(config, PROJECT_DIR)
    
    return flight

if __name__ == "__main__":
    main()
