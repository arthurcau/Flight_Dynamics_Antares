import sys
import yaml

with open("projects/neblina_1/config/environment.yaml", "r") as f:
    config = yaml.safe_load(f)

config['environment']['time_window_minutes'] = 120
config['environment']['time_step_minutes'] = 10

with open("projects/neblina_1/config/environment.yaml", "w") as f:
    yaml.dump(config, f, default_flow_style=False)
