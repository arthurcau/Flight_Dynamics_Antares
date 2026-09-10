import sys
from pathlib import Path
sys.path.insert(0, str(Path("source").resolve()))
from antares_fd.config import load_project_config
from antares_fd.builders import build_environment, build_motor, build_vehicle
from rocketpy import StochasticSolidMotor
import numpy as np

PROJECT_DIR = Path("projects/neblina_1")
config = load_project_config(PROJECT_DIR)
motor = build_motor(config.motor, PROJECT_DIR)

stoch_motor = StochasticSolidMotor(
    motor,
    total_impulse=(motor.total_impulse, motor.total_impulse * 0.1)
)

gen_motor = stoch_motor.create_object()
print(f"Generated motor thrust at t=1.8s: {gen_motor.thrust(1.8)}")
print(f"Generated motor max thrust: {gen_motor.max_thrust}")

