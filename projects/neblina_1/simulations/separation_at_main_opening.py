"""
ANTARES FLIGHT DYNAMICS
Separation at Main Opening Simulation
"""
import sys
from pathlib import Path

# Ensures the core 'Source' package can be imported
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SOURCE_DIR = PROJECT_ROOT / "source"
if str(SOURCE_DIR) not in sys.path:
    sys.path.insert(0, str(SOURCE_DIR))
    sys.path.insert(0, str(PROJECT_ROOT))

from antares_fd.config import load_project_config
from antares_fd.simulation import execute_scenario

def main():
    PROJECT_DIR = Path(__file__).resolve().parents[1]
    
    # 1. Load configuration
    config = load_project_config(PROJECT_DIR)
    
    # 2. SCENARIO OVERRIDES: 
    # For this simplified scenario, we simulate the booster section's descent 
    # by subtracting the mass of the separated forward section (e.g., nosecone).
    
    # Assume 2.0 kg is separated at main parachute deployment
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
