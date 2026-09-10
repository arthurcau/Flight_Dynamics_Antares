import sys
from pathlib import Path
sys.path.insert(0, str(Path("source").resolve()))
from rocketpy import Environment, SolidMotor, Rocket, Flight
from antares_fd.config import load_project_config
from antares_fd.builders.environment import build_environment
from antares_fd.builders.motor import build_motor
from antares_fd.builders.vehicle import build_vehicle
PROJECT_DIR = Path("projects/neblina_1")
config = load_project_config(PROJECT_DIR)
env = build_environment(config.environment, config.launch)
motor = build_motor(config.motor, PROJECT_DIR)
rocket = build_vehicle(config.vehicle, motor, PROJECT_DIR)
flight = Flight(rocket=rocket, environment=env, rail_length=6.0, inclination=80, heading=90, terminate_on_apogee=False)
print("State history:", flight.solution)
