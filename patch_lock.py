import sys

for filename in ["source/antares_fd/simulation/monte_carlo.py", "source/antares_fd/simulation/monte_carlo_failure.py"]:
    with open(filename, "r") as f:
        content = f.read()

    # Replace the manager setup
    old_setup = """    manager = Manager()
    shared_counter = manager.Value('i', 0)
    start_time_val = manager.Value('d', time.time())
    total_sims = manager.Value('i', 0)"""
    
    new_setup = """    manager = Manager()
    shared_counter = manager.Value('i', 0)
    start_time_val = manager.Value('d', time.time())
    total_sims = manager.Value('i', 0)
    counter_lock = manager.Lock()"""
    
    content = content.replace(old_setup, new_setup)
    
    # Replace the lock
    content = content.replace("with shared_counter.get_lock():", "with counter_lock:")
    
    with open(filename, "w") as f:
        f.write(content)
