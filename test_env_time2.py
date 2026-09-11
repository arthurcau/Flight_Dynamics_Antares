from rocketpy import Environment
env = Environment(latitude=0, longitude=0, elevation=0)
env.set_date((2023, 1, 1, 15, 0, 0))
env.set_atmospheric_model(type="standard_atmosphere")
print("Wind X:", env.wind_velocity_x(10))
print("Wind Y:", env.wind_velocity_y(10))
