import sys
from pathlib import Path
sys.path.insert(0, str(Path("source").resolve()))
from antares_fd.config import load_project_config
from antares_fd.builders import build_motor
from rocketpy import StochasticSolidMotor

PROJECT_DIR = Path("projects/neblina_1")
config = load_project_config(PROJECT_DIR)
motor = build_motor(config.motor, PROJECT_DIR)

stoch_motor = StochasticSolidMotor(
    motor,
    total_impulse=(motor.total_impulse, motor.total_impulse * 0.1)
)

gen = stoch_motor.create_object()
print(gen.thrust.x_array[:5])
print(gen.thrust.y_array[:5])
