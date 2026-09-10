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
flight = Flight(rocket=rocket, environment=env, rail_length=6.0, inclination=80, heading=90)
print(f"Total mass at t=0: {rocket.total_mass(0)}")
print(f"Total weight: {rocket.total_mass(0)*9.81}")
print(f"Thrust at t=1.8: {motor.thrust(1.8)}")
print(f"Max Thrust: {motor.max_thrust}")
print(f"Liftoff time: {flight.out_of_rail_time}")
