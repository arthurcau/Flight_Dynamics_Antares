from rocketpy import Rocket, SolidMotor, StochasticRocket, StochasticSolidMotor
import traceback

try:
    m = SolidMotor(
        thrust_source=1000, burn_time=1, grain_number=1, grain_separation=0, grain_density=1,
        grain_outer_radius=0.1, grain_initial_inner_radius=0.05, grain_initial_height=0.1,
        nozzle_radius=0.05, throat_radius=0.02, interpolation_method='linear',
        coordinate_system_orientation='tail_to_nose', dry_mass=1, dry_inertia=(1,1,1),
        grains_center_of_mass_position=0, center_of_dry_mass_position=0
    )
    r = Rocket(
        radius=0.1, mass=10, inertia=(1,1,1), power_off_drag=1,
        center_of_mass_without_motor=0, coordinate_system_orientation='tail_to_nose'
    )
    r.add_motor(m, position=-1)
    
    print("Rocket motors:", len(r.motors))
    sr = StochasticRocket(r)
    sm = StochasticSolidMotor(m)
    
    # Try removing motors first?
    r.motors.clear() 
    # Can we just clear sr.motors?
    # sr is a StochasticRocket. Let's see what it has
except Exception as e:
    traceback.print_exc()

