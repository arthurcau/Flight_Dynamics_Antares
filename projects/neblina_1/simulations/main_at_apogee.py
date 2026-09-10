"""
ANTARES FLIGHT DYNAMICS
Main at Apogee Flight Simulation
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
    
    # 2. SCENARIO OVERRIDES: Disable drogue and set main trigger to apogee
    for device in config.recovery.get("devices", []):
        if device.get("id") == "drogue":
            device["enabled"] = False
        elif device.get("id") == "main":
            device["trigger"] = {"type": "apogee"}
            device["name"] = "Main Parachute (At Apogee)"
            
    # 3. Execute scenario
    flight = execute_scenario(config, PROJECT_DIR)
    
    return flight

if __name__ == "__main__":
    main()
