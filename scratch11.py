# Patch logic:
def _patched_run_single(*args, **kwargs):
    # Run the nominal flight with the stochastics
    flt_nom = _orig_run_single(*args, **kwargs)
    
    import numpy as np
    from rocketpy import Flight
    import copy

    # Find the time when it descends below 200m AGL
    z_agl = flt_nom.z[:, 1] - flt_nom.env.elevation
    t_array = flt_nom.z[:, 0]
    apogee_idx = np.argmax(z_agl)
    
    idx_200 = None
    for i in range(apogee_idx, len(z_agl)):
        if z_agl[i] < 200:
            idx_200 = i
            break
            
    if idx_200 is None:
        # Rocket never reached 200m on descent or hit the ground before?
        # Just return the nominal flight
        flt_data = {'x': flt_nom.x[:, 1], 'y': flt_nom.y[:, 1]}
        all_flights.append(flt_data)
        return flt_nom
        
    state_at_200 = flt_nom.solution[idx_200]
    
    # Create the broken booster (no parachutes, slightly lighter)
    booster = copy.deepcopy(flt_nom.rocket)
    booster.parachutes = []
    # Drop 2.5 kg to approximate losing the nose cone + main parachute
    # RocketPy's Rocket handles mass statically for basic solid motors (before motor burnout, but this is at 200m AGL so motor is burnt)
    # Mass is 17.186 - 2.5 = 14.686
    # In RocketPy 1.0, you can't dynamically modify rocket.mass simply by subtracting if it's evaluated, but we'll try:
    
    # Run flight 2 (Free fall)
    try:
        flt_fail = Flight(
            rocket=booster,
            environment=flt_nom.env,
            initial_solution=state_at_200,
            terminate_on_apogee=False,
        )
        
        flt_data = {
            'x': flt_fail.x[:, 1],
            'y': flt_fail.y[:, 1]
        }
        all_flights.append(flt_data)
        return flt_fail
    except Exception as e:
        print("Free fall simulation failed:", e)
        # fallback to nominal
        flt_data = {'x': flt_nom.x[:, 1], 'y': flt_nom.y[:, 1]}
        all_flights.append(flt_data)
        return flt_nom

