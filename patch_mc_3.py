import re
with open("source/antares_fd/simulation/monte_carlo.py", "r") as f:
    content = f.read()

stoch_env_block = """
    env_kwargs = {}
    if len(env_ensemble) > 1:
        env_kwargs["ensemble_member"] = env_ensemble
    
    stoch_env = StochasticEnvironment(
        environment=nominal_env,
        **env_kwargs
    )
"""

# Replace the block
content = re.sub(r'stoch_env = StochasticEnvironment\([^)]+\)', stoch_env_block.strip(), content, flags=re.MULTILINE|re.DOTALL)

with open("source/antares_fd/simulation/monte_carlo.py", "w") as f:
    f.write(content)
