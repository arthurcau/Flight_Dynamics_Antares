import sys

for filename in ["source/antares_fd/simulation/monte_carlo.py", "source/antares_fd/simulation/monte_carlo_failure.py"]:
    with open(filename, "r") as f:
        content = f.read()

    # 1. Modify the monkey patch to include a progress bar
    # We need to create a counter before the patch.
    # Look for: "def _patched_run_single(*args, **kwargs):"
    patch_setup = """
    import time
    from multiprocessing import Manager
    manager = Manager()
    shared_counter = manager.Value('i', 0)
    start_time_val = manager.Value('d', time.time())
    total_sims = manager.Value('i', 0) # will set later
"""
    
    # We will inject the counter code inside _patched_run_single
    counter_code = """
        with shared_counter.get_lock():
            shared_counter.value += 1
            completed = shared_counter.value
            tot = total_sims.value
        
        if completed % max(1, tot // 20) == 0 or completed == tot:
            elapsed = time.time() - start_time_val.value
            eta = (elapsed / completed) * (tot - completed) if completed > 0 else 0
            progress = (completed / tot) * 100 if tot > 0 else 0
            print(f"[Monte Carlo Progress] {completed}/{tot} ({progress:.1f}%) | Elapsed: {elapsed:.1f}s | ETA: {eta:.1f}s")
"""
    
    # Find def _patched_run_single
    if "def _patched_run_single" in content:
        content = content.replace("def _patched_run_single(*args, **kwargs):", patch_setup + "\n    def _patched_run_single(*args, **kwargs):\n" + counter_code)

    # 2. Add checkpointing logic before mc.simulate
    checkpoint_logic = """
    # Checkpointing Logic
    outputs_file = results_dir / "mc_sim.outputs.txt"
    already_done = 0
    if outputs_file.exists():
        with open(outputs_file, "r") as f:
            for line in f:
                if line.strip(): already_done += 1
                
    remaining_sims = num_sims - already_done
    
    if remaining_sims <= 0:
        print(f"[Monte Carlo] All {num_sims} simulations already completed in previous run. Skipping simulation.")
    else:
        print(f"[Monte Carlo] Starting {remaining_sims} simulations (Resuming {already_done}/{num_sims}). Seed={seed}")
        total_sims.value = remaining_sims
        start_time_val.value = time.time()
        
        mc.simulate(number_of_simulations=remaining_sims, append=(already_done > 0), parallel=True)
"""
    
    # Replace the old simulate line
    old_sim_line = "    mc.simulate(number_of_simulations=num_sims, append=False, parallel=True)"
    
    # Wait, in the files there's a print("Starting x simulations...") before simulate
    # I should replace that block.
    # Let's just do a string replacement of the block from `print("[Monte Carlo] Starting"` to `mc.simulate`
    
    # I will do this manually by reading the file and doing regex or find.
