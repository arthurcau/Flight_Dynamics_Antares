import sys
import re

for filename in ["source/antares_fd/simulation/monte_carlo.py", "source/antares_fd/simulation/monte_carlo_failure.py"]:
    with open(filename, "r") as f:
        content = f.read()

    # 1. Modify the monkey patch to include a progress bar
    patch_setup = """    # Setup Progress Tracking
    import time
    from multiprocessing import Manager
    manager = Manager()
    shared_counter = manager.Value('i', 0)
    start_time_val = manager.Value('d', time.time())
    total_sims = manager.Value('i', 0)
    
    def _patched_run_single(*args, **kwargs):
        with shared_counter.get_lock():
            shared_counter.value += 1
            completed = shared_counter.value
            tot = total_sims.value
        if tot > 0 and (completed % max(1, tot // 10) == 0 or completed == tot):
            elapsed = time.time() - start_time_val.value
            eta = (elapsed / completed) * (tot - completed)
            progress = (completed / tot) * 100
            print(f"[Monte Carlo Progress] {completed}/{tot} ({progress:.1f}%) | Elapsed: {elapsed:.1f}s | ETA: {eta:.1f}s")
"""
    
    content = content.replace("    def _patched_run_single(*args, **kwargs):", patch_setup)

    # 2. Add checkpointing logic before mc.simulate
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
    
    # We replace from `print("[Monte Carlo] Starting` to `mc.simulate(...)`
    # Use regex
    pattern = r'print\("\[Monte Carlo\] Starting \d+ simulations.*?"\).*?mc\.simulate\(number_of_simulations=num_sims, append=False, parallel=True\)'
    content = re.sub(pattern, checkpoint_logic.strip(), content, flags=re.DOTALL)
    
    with open(filename, "w") as f:
        f.write(content)
