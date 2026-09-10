import sys
from pathlib import Path
from antares_fd.config.loader import load_project_config
from antares_fd.simulation.orchestrator import execute_scenario

config = load_project_config(Path("projects/00_Copy_This"))
flight = execute_scenario(config, Path("projects/00_Copy_This"), print_summary=False, export_kml=False)

def check_var(name, attr):
    try:
        val = getattr(flight, attr)
        # Function object in RocketPy?
        print(f"{name}: has .source array? {hasattr(val, 'source')}")
    except Exception as e:
        print(f"{name}: Error - {e}")

check_var("x", "x")
check_var("y", "y")
check_var("z", "z")
check_var("ax", "ax")
check_var("ay", "ay")
check_var("az", "az")
check_var("pitch", "pitch")
check_var("roll", "roll")
check_var("yaw", "yaw")
check_var("alpha", "angle_of_attack")
check_var("mach", "mach_number")
check_var("sm", "static_margin")
