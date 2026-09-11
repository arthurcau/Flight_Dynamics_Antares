from rocketpy import Flight
from rocketpy import Environment
from rocketpy import SolidMotor
from rocketpy import Rocket
env = Environment(latitude=0, longitude=0, elevation=0)
env.set_date((2023, 1, 1, 15, 0, 0))
env.set_atmospheric_model(type="standard_atmosphere")
mot = SolidMotor(thrust_source=1000, burn_time=1, dry_mass=1, dry_inertia=(1,1,1), center_of_dry_mass_position=0, grains_center_of_mass_position=0, grain_number=1, grain_separation=0, grain_density=1000, grain_outer_radius=0.1, grain_initial_inner_radius=0.05, grain_initial_height=0.1, nozzle_radius=0.05, throat_radius=0.02)
roc = Rocket(radius=0.1, mass=10, inertia=(1,1,1), power_off_drag=0.5, power_on_drag=0.5, center_of_mass_without_motor=0)
roc.add_motor(mot, position=0)
flt = Flight(roc, env, rail_length=5, terminate_on_apogee=True)
print("Original Apogee:", flt.apogee)
flt.apogee = 9999
print("Overridden Apogee:", flt.apogee)
