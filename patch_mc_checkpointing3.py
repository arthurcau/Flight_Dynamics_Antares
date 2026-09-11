import sys

for filename in ["source/antares_fd/simulation/monte_carlo.py", "source/antares_fd/simulation/monte_carlo_failure.py"]:
    with open(filename, "r") as f:
        content = f.read()

    checkpoint_logic = """
    # Checkpointing Logic
    outputs_file_path = results_dir / "mc_sim.outputs.txt"
    already_done = 0
    if outputs_file_path.exists():
        with open(outputs_file_path, "r") as f:
            already_done = sum(1 for line in f if line.strip())
            
    remaining_sims = num_sims - already_done
    
    if remaining_sims <= 0:
        print(f"[Monte Carlo] All {num_sims} simulations already completed in previous run. Skipping simulation.")
    else:
        print(f"[Monte Carlo] Starting {remaining_sims} simulations (Resuming {already_done}/{num_sims}). Seed={seed}")
        total_sims.value = remaining_sims
        start_time_val.value = time.time()
        
        mc.simulate(number_of_simulations=remaining_sims, append=(already_done > 0), parallel=True)
"""
    
    # Replace the single line mc.simulate
    content = content.replace("    mc.simulate(number_of_simulations=num_sims, append=False, parallel=True)", checkpoint_logic)
    
    # Remove the old print statement
    content = content.replace("    print(f\"[Monte Carlo] Starting {num_sims} simulations. Seed={seed}\")", "")
    
    with open(filename, "w") as f:
        f.write(content)
