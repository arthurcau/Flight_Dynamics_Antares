from rocketpy import Environment, SolidMotor, Rocket, Flight, StochasticEnvironment, StochasticSolidMotor, StochasticRocket, StochasticFlight, MonteCarlo

# Just test if StochasticEnvironment takes wind_velocity_x_factor=(1, 0.2)
try:
    env = Environment(latitude=0, longitude=0, elevation=0)
    env.set_date((2025, 1, 1, 12, 0, 0))
    env.set_atmospheric_model(type="standard_atmosphere")
    stoch_env = StochasticEnvironment(env, wind_velocity_x_factor=(1, 0.2), wind_velocity_y_factor=(1, 0.2))
    print("Stoch Env success")
except Exception as e:
    print("Stoch Env error", e)
