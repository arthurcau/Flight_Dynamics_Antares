with open("source/antares_fd/simulation/monte_carlo.py", "r") as f:
    content = f.read()

content = content.replace("wind_velocity_x=(nominal_env.wind_velocity_x, wind_x_std if wind_x_std > 0 else (user_wx_std or 0.0)),", "wind_velocity_x_factor=(1.0, (wind_x_std/3.0) if wind_x_std > 0 else (user_wx_std or 0.0)),")
content = content.replace("wind_velocity_y=(nominal_env.wind_velocity_y, wind_y_std if wind_y_std > 0 else (user_wx_std or 0.0)),", "wind_velocity_y_factor=(1.0, (wind_y_std/3.0) if wind_y_std > 0 else (user_wx_std or 0.0)),")

with open("source/antares_fd/simulation/monte_carlo.py", "w") as f:
    f.write(content)
