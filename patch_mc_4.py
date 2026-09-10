import re
with open("source/antares_fd/simulation/monte_carlo.py", "r") as f:
    content = f.read()

stoch_env_block = """
    # Compute std dev from MAGI ensemble
    wind_x_std = 0.0
    wind_y_std = 0.0
    if len(env_ensemble) > 1:
        # get max wind speed to scale
        wx_list = []
        wy_list = []
        for e in env_ensemble:
            wx_list.append(e.wind_velocity_x(1000))
            wy_list.append(e.wind_velocity_y(1000))
        wind_x_std = float(np.std(wx_list)) if wx_list else 1.0
        wind_y_std = float(np.std(wy_list)) if wy_list else 1.0
        print(f"[MAGI-Stochastic] Computed Ensemble variance: std_x={wind_x_std:.2f}, std_y={wind_y_std:.2f}")

    # Fallback to config if ensemble is disabled
    user_wx_std = config.environment.get("wind_velocity_x_factor_std", None)
    
    stoch_env = StochasticEnvironment(
        environment=nominal_env,
        wind_velocity_x=(nominal_env.wind_velocity_x, wind_x_std if wind_x_std > 0 else (user_wx_std or 0.0)),
        wind_velocity_y=(nominal_env.wind_velocity_y, wind_y_std if wind_y_std > 0 else (user_wx_std or 0.0)),
        elevation=config.environment.get("elevation_std", None)
    )
"""

content = re.sub(r'env_kwargs = \{\}.*?stoch_env = StochasticEnvironment\([\s\S]*?\n    \)', stoch_env_block.strip(), content, flags=re.MULTILINE|re.DOTALL)

with open("source/antares_fd/simulation/monte_carlo.py", "w") as f:
    f.write(content)
