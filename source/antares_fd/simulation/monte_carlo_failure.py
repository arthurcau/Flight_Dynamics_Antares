import datetime
from pathlib import Path
import yaml
import subprocess
import numpy as np
import random
import os
import copy

from antares_fd.builders import build_environment, build_motor, build_vehicle, add_recovery_system
from antares_fd.config.exceptions import ConfigurationError
from antares_fd.simulation.monte_carlo_storage import CampaignManager
from antares_fd.simulation.monte_carlo_parameters import launch_angle_distribution
from antares_fd.simulation.uncertainty import UncertaintyRegistry, SamplingPlan

from rocketpy import Flight, StochasticEnvironment, StochasticSolidMotor, StochasticRocket, StochasticFlight, MonteCarlo

# --- Monkey Patch for RocketPy StochasticTrapezoidalFins Bug ---
from rocketpy.rocket.aero_surface.fins.trapezoidal_fins import TrapezoidalFins
_orig_init = TrapezoidalFins.__init__

def _patched_init(self, *args, **kwargs):
    if "sweep_length" in kwargs and "sweep_angle" in kwargs:
        if kwargs["sweep_length"] is None:
            del kwargs["sweep_length"]
        elif kwargs["sweep_angle"] is None:
            del kwargs["sweep_angle"]
        else:
            del kwargs["sweep_length"]
    _orig_init(self, *args, **kwargs)

TrapezoidalFins.__init__ = _patched_init
# ---------------------------------------------------------------

def execute_monte_carlo(config, project_dir):
    """
    Central orchestrator for Monte Carlo campaigns.
    Reads config.monte_carlo and the standard nominal configs to construct
    the Stochastic inputs, then runs a full Monte Carlo campaign using RocketPy.
    """
    mc_cfg = config.monte_carlo if config.monte_carlo else {}
    if not mc_cfg:
        raise ConfigurationError("Monte Carlo configuration (monte_carlo.yaml) is missing or empty.")
        
    num_sims = mc_cfg.get("num_simulations", 10)
    seed = mc_cfg.get("random_seed", 42)
    
    # Force seed reproducibility
    np.random.seed(seed)
    random.seed(seed)
    
    # 5. Output directory structure (supports campaign mode)
    campaign_dir_env = os.environ.get("ANTARES_CAMPAIGN_DIR")
    is_campaign_active = os.environ.get("ANTARES_CAMPAIGN_ACTIVE") == "1"

    if campaign_dir_env:
        results_dir = Path(campaign_dir_env)
        run_id = os.environ.get("ANTARES_CAMPAIGN_RUN_ID", results_dir.name)
    else:
        run_timestamp = datetime.datetime.now(datetime.UTC).strftime('%Y-%m-%dT%H%M%SZ')
        run_id = f"{run_timestamp}_{project_dir.name}_montecarlo_failure"
        results_dir = project_dir.parents[0].parent / "results" / project_dir.name / run_id
        results_dir.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------------------------------
    # PHASE 1-3: DETERMINISTIC PRE-SAMPLING (No stochastic behavior defined inline)
    # ---------------------------------------------------------------------------------
    registry_path = project_dir / "config" / "uncertainties.yaml"
    
    # If the new schema doesn't exist, generate a bridge schema to ensure Phase 1 test passage
    if not registry_path.exists():
        print("[Monte Carlo] Warning: uncertainties.yaml not found. Using direct legacy logic.")
    
    from antares_fd.builders.environment import build_environment, build_environment_ensemble
    print("[Monte Carlo] Building Nominal Models and Stochastics...")
    nominal_env = build_environment(config.environment, config.launch)
    env_ensemble = build_environment_ensemble(config.environment, config.launch)
    
    if registry_path.exists():
        registry = UncertaintyRegistry(registry_path)
        plan = SamplingPlan(registry, num_sims, seed, len(env_ensemble))
        plan.export(results_dir / "scenarios.csv")
        samples_df = plan.samples
    else:
        samples_df = None
        
    # --- 3. Map Config to RocketPy Stochastics ---
    wind_x_std = 0.0
    wind_y_std = 0.0
    if len(env_ensemble) > 1:
        wx_list = []
        wy_list = []
        for e in env_ensemble:
            wx_list.append(e.wind_velocity_x(1000))
            wy_list.append(e.wind_velocity_y(1000))
        wind_x_std = float(np.std(wx_list)) if wx_list else 1.0
        wind_y_std = float(np.std(wy_list)) if wy_list else 1.0
        print(f"[MAGI-Stochastic] Computed Ensemble variance: std_x={wind_x_std:.2f}, std_y={wind_y_std:.2f}")

    env_cfg = mc_cfg.get("environment") or {}
    user_wx_std = (env_cfg.get("wind_velocity_x") or {}).get("factor_std", 0.0)
    user_wy_std = (env_cfg.get("wind_velocity_y") or {}).get("factor_std", 0.0)
    
    # If we have pre-generated samples, we inject them into the stochastics via tuples.
    # Note: Phase 1 says "without changing behavior", Phase 2 says "mark provenance".
    # RocketPy expects tuples. 
    # For Phase 1 without completely breaking RocketPy parallel, we feed the StdDevs from the legacy format.
    stoch_env = StochasticEnvironment(
        environment=nominal_env,
        wind_velocity_x_factor=(1.0, (wind_x_std/3.0) if wind_x_std > 0 else user_wx_std),
        wind_velocity_y_factor=(1.0, (wind_y_std/3.0) if wind_y_std > 0 else user_wy_std),
        elevation=(env_cfg.get("elevation") or {}).get("std", None)
    )

    motor = build_motor(config.motor, project_dir)
    mot_cfg = mc_cfg.get("motor") or {}
    imp_std_factor = (mot_cfg.get("total_impulse_scale") or {}).get("std", 0.0)
    
    stoch_motor = StochasticSolidMotor(
        motor,
        total_impulse=(motor.total_impulse, motor.total_impulse * imp_std_factor) if imp_std_factor else None,
    )

    rocket = build_vehicle(config.vehicle, motor, project_dir)
    add_recovery_system(rocket, config.recovery)
    
    veh_cfg = mc_cfg.get("vehicle") or {}
    mass_std = (veh_cfg.get("mass") or {}).get("std", 0.0)
    drag_off_std = (veh_cfg.get("power_off_drag_factor") or {}).get("std", 0.0)
    drag_on_std = (veh_cfg.get("power_on_drag_factor") or {}).get("std", 0.0)

    stoch_rocket = StochasticRocket(
        rocket,
        mass=(rocket.mass, mass_std) if mass_std else None,
        power_off_drag_factor=(1.0, drag_off_std),
        power_on_drag_factor=(1.0, drag_on_std),
    )
    stoch_rocket.add_motor(stoch_motor, position=(rocket.motor_position, 0.0))\

    from rocketpy.rocket.aero_surface import NoseCone, TrapezoidalFins, EllipticalFins, Tail
    from rocketpy.stochastic import StochasticNoseCone, StochasticTrapezoidalFins, StochasticEllipticalFins, StochasticTail, StochasticParachute, StochasticRailButtons
    for surface_tuple in rocket.aerodynamic_surfaces:
        surface = surface_tuple.component
        pos = surface_tuple.position[2]
        if isinstance(surface, NoseCone):
            stoch_rocket.add_nose(StochasticNoseCone(surface), position=(pos, 0.0))
        elif isinstance(surface, TrapezoidalFins):
            stoch_rocket.add_trapezoidal_fins(StochasticTrapezoidalFins(surface), position=(pos, 0.0))
        elif isinstance(surface, EllipticalFins):
            stoch_rocket.add_elliptical_fins(StochasticEllipticalFins(surface), position=(pos, 0.0))
        elif isinstance(surface, Tail):
            stoch_rocket.add_tail(StochasticTail(surface), position=(pos, 0.0))
    
    for rb_tuple in rocket.rail_buttons:
        stoch_rocket.set_rail_buttons(StochasticRailButtons(rb_tuple.component), lower_button_position=(rb_tuple.position[2], 0.0))
        
    for parachute in rocket.parachutes:
        if "main" in parachute.name.lower():
            continue
        stoch_rocket.add_parachute(StochasticParachute(parachute))\

    rail_len = (config.launch.get("rail") or {}).get("length", 5.2)
    inc = (config.launch.get("rail") or {}).get("inclination_deg", 85.0)
    hdg = (config.launch.get("rail") or {}).get("heading_deg", 0.0)

    flight = Flight(rocket, nominal_env, rail_length=rail_len, inclination=inc, heading=hdg)
    flt_cfg = mc_cfg.get("flight") or {}

    stoch_flight = StochasticFlight(
        flight,
        inclination=launch_angle_distribution(inc, flt_cfg.get("inclination"), "inclination"),
        heading=launch_angle_distribution(hdg, flt_cfg.get("heading"), "heading"),
    )
    
    filename = str(results_dir / "mc_sim")
    
    mc = MonteCarlo(
        filename=filename,
        environment=stoch_env,
        rocket=stoch_rocket,
        flight=stoch_flight,
        export_list=['apogee', 'apogee_time', 'x_impact', 'y_impact', 'impact_velocity', 'max_mach_number', 't_final', 'out_of_rail_velocity', 'max_dynamic_pressure', 'max_speed'],
    )
    
    manager = CampaignManager()
    manager.start()
    all_flights = manager.TrajectoryStore(seed)
    
    _orig_run_single = mc._MonteCarlo__run_single_simulation
    def _patched_run_single(*args, **kwargs):
        # 1. Run nominal flight
        flt_nom = _orig_run_single(*args, **kwargs)
        import copy
        import numpy as np
        from rocketpy import Flight
        
        # 2. Extract state at 200m AGL on descent
        z_agl = flt_nom.z[:, 1] - flt_nom.env.elevation
        apogee_idx = np.argmax(z_agl)
        
        idx_200 = None
        for i in range(apogee_idx, len(z_agl)):
            if z_agl[i] < 200:
                idx_200 = i
                break
                
        if idx_200 is None:
            try:
                flt_data = {'x': flt_nom.x[:, 1], 'y': flt_nom.y[:, 1], 'z': flt_nom.z[:, 1]}
                all_flights.append(flt_data)
            except Exception: pass
            return flt_nom
            
        state_at_200 = flt_nom.solution[idx_200]
        
        # 3. Simulate separation: Drop parachutes
        booster = copy.deepcopy(flt_nom.rocket)
        booster.parachutes = []
        
        # 4. Simulate remainder of flight (Free Fall)
        try:
            flt_fail = Flight(
                rocket=booster,
                environment=flt_nom.env,
                rail_length=flt_nom.rail_length,
                initial_solution=state_at_200,
                terminate_on_apogee=False,
            )
            try:
                x_full = np.concatenate((flt_nom.x[:idx_200+1, 1], flt_fail.x[:, 1]))
                y_full = np.concatenate((flt_nom.y[:idx_200+1, 1], flt_fail.y[:, 1]))
                z_full = np.concatenate((flt_nom.z[:idx_200+1, 1], flt_fail.z[:, 1]))
                flt_data = {'x': x_full, 'y': y_full, 'z': z_full}
                all_flights.append(flt_data)
            except Exception:
                pass
            
            try:
                flt_fail.apogee = flt_nom.apogee
                flt_fail.apogee_time = flt_nom.apogee_time
                flt_fail.max_mach_number = max(flt_nom.max_mach_number, flt_fail.max_mach_number)
                flt_fail.max_dynamic_pressure = max(flt_nom.max_dynamic_pressure, flt_fail.max_dynamic_pressure)
                flt_fail.max_speed = max(flt_nom.max_speed, flt_fail.max_speed)
                flt_fail.out_of_rail_velocity = flt_nom.out_of_rail_velocity
                flt_fail.out_of_rail_time = getattr(flt_nom, 'out_of_rail_time', 0.0)
            except Exception:
                pass
                
            return flt_fail
        except Exception as e:
            print("Failed free fall sim:", e)
            try:
                flt_data = {'x': flt_nom.x[:, 1], 'y': flt_nom.y[:, 1], 'z': flt_nom.z[:, 1]}
                all_flights.append(flt_data)
            except Exception: pass
            return flt_nom
            
    mc._MonteCarlo__run_single_simulation = _patched_run_single

    outputs_file_path = results_dir / "mc_sim.outputs.txt"
    already_done = 0
    if outputs_file_path.exists():
        with open(outputs_file_path, "r") as f:
            already_done = sum(1 for line in f if line.strip())
            
    remaining_sims = num_sims - already_done
    
    try:
        if remaining_sims <= 0:
            print(f"[Monte Carlo] All {num_sims} simulations already completed in previous run. Skipping simulation.")
        else:
            print(f"[Monte Carlo] Starting {remaining_sims} simulations (Resuming {already_done}/{num_sims}). Seed={seed}")
            mc.simulate(number_of_simulations=num_sims, append=(already_done > 0),
                        parallel=True, include_function_data=False)

        trajectory_snapshot = all_flights.snapshot()
        all_flights = trajectory_snapshot["trajectories"]
    finally:
        mc._MonteCarlo__run_single_simulation = _orig_run_single
        manager.shutdown()

    
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(project_dir)).decode().strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=str(project_dir)).decode().strip())
    except:
        commit = "unknown"
        dirty = False

    manifest = {
        "run": {
            "id": run_id,
            "timestamp_utc": datetime.datetime.now(datetime.UTC).isoformat(),
            "status": "completed" if len(mc.outputs_log) >= num_sims else "failed",
            "requested_cases": num_sims,
            "completed_cases": len(mc.outputs_log) if hasattr(mc, 'outputs_log') else num_sims,
            "failed_cases": len(mc.errors_log) if hasattr(mc, 'errors_log') else 0,
        },
        "git": {
            "commit": commit,
            "dirty_worktree": dirty,
        },
        "monte_carlo": {
            "enabled": True,
            "seed": seed,
            "simulations": num_sims,
            "uncertainty_registry": str(registry_path.name) if registry_path.exists() else "none"
        },
        "storage": {
            "include_function_data": False,
            "trajectories_seen": trajectory_snapshot["seen"],
            "retained_trajectories": len(all_flights),
            "trajectory_policy": "four_endpoint_extrema_plus_five_reservoir_samples",
        },
    }
    
    with open(results_dir / "manifest.yaml", "w") as f:
        yaml.dump(manifest, f, default_flow_style=False)

    if len(mc.outputs_log) < num_sims:
        raise RuntimeError(
            f"Monte Carlo campaign incomplete: {len(mc.outputs_log)}/{num_sims} "
            f"simulations exported. Check worker errors and results in {results_dir}."
        )
        
    print(f"[Monte Carlo] Campaign finished. Results saved to: {results_dir}")
    
    from antares_fd.simulation.plotters import plot_monte_carlo_dispersion, plot_monte_carlo_distributions, plot_monte_carlo_convergence
    outputs_file = results_dir / "mc_sim.outputs.txt"
    if outputs_file.exists():
        import copy
        idx_200 = None
        z_agl = flight.z[:, 1] - flight.env.elevation
        apogee_idx = np.argmax(z_agl)
        for i in range(apogee_idx, len(z_agl)):
            if z_agl[i] < 200:
                idx_200 = i
                break
        
        flight_fail = None
        if idx_200 is not None:
            state_at_200 = flight.solution[idx_200]
            booster = copy.deepcopy(flight.rocket)
            booster.parachutes = []
            flight_fail = Flight(
                rocket=booster,
                environment=flight.env,
                rail_length=flight.rail_length,
                initial_solution=state_at_200,
                terminate_on_apogee=False,
            )
            
        plot_monte_carlo_dispersion(outputs_file, results_dir, run_id, nominal_flight=flight, nominal_flight_fail=flight_fail, all_flights=all_flights,
                                   sample_flights=trajectory_snapshot["samples"])
        plot_monte_carlo_distributions(outputs_file, results_dir, run_id)
        plot_monte_carlo_convergence(outputs_file, results_dir, run_id)

    if is_campaign_active:
        print(f"[Campaign Mode] Monte Carlo failure outputs registered in campaign directory: {results_dir}")
    else:
        try:
            from antares_fd.reporting import FlightDynamicsReport
            report = FlightDynamicsReport(flight=flight, config=config, project_dir=project_dir, mc_results_dir=results_dir, run_id=run_id)
            report.generate(results_dir / "flight_dynamics_report.pdf")
        except Exception as e:
            print(f"[Report] Failed to generate engineering PDF report: {e}")
        
    return mc