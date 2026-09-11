import datetime
from pathlib import Path
import yaml
import subprocess
import numpy as np
import random

from antares_fd.builders import build_environment, build_motor, build_vehicle, add_recovery_system
from antares_fd.config.exceptions import ConfigurationError

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
    
    from antares_fd.builders.environment import build_environment, build_environment_ensemble
    
    print("[Monte Carlo] Building Nominal Models and Stochastics...")
    # Get nominal env for vehicle builder, and the ensemble list for Monte Carlo
    nominal_env = build_environment(config.environment, config.launch)
    env_ensemble = build_environment_ensemble(config.environment, config.launch)
    
    # Motor & Vehicle built exactly like a nominal run
    nominal_motor = build_motor(config.motor, project_dir)
    nominal_rocket = build_vehicle(config.vehicle, nominal_motor, project_dir)
    add_recovery_system(nominal_rocket, config.recovery)
    
    # --- 3. Map Config to RocketPy Stochastics ---
    # We use the list of environments in `ensemble_member` if there are multiple.
    # Otherwise we just use the nominal_env and random noise.
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
    env_cfg = mc_cfg.get("environment") or {}
    user_wx_std = (env_cfg.get("wind_velocity_x") or {}).get("factor_std", 0.0)
    user_wy_std = (env_cfg.get("wind_velocity_y") or {}).get("factor_std", 0.0)
    
    stoch_env = StochasticEnvironment(
        environment=nominal_env,
        wind_velocity_x_factor=(1.0, (wind_x_std/3.0) if wind_x_std > 0 else user_wx_std),
        wind_velocity_y_factor=(1.0, (wind_y_std/3.0) if wind_y_std > 0 else user_wy_std),
        elevation=(env_cfg.get("elevation") or {}).get("std", None)
    )
    # 2. Motor
    motor = build_motor(config.motor, project_dir)
    mot_cfg = mc_cfg.get("motor") or {}
    imp_std_factor = (mot_cfg.get("total_impulse_scale") or {}).get("std", 0.0)
    
    stoch_motor = StochasticSolidMotor(
        motor,
        total_impulse=(motor.total_impulse, motor.total_impulse * imp_std_factor) if imp_std_factor else None,
    )

    # 3. Vehicle
    rocket = build_vehicle(config.vehicle, motor, project_dir)
    add_recovery_system(rocket, config.recovery)
    
    veh_cfg = mc_cfg.get("vehicle") or {}
    mass_std = (veh_cfg.get("mass") or {}).get("std", 0.0)
    drag_off_std = (veh_cfg.get("power_off_drag_factor") or {}).get("std", 0.0)
    drag_on_std = (veh_cfg.get("power_on_drag_factor") or {}).get("std", 0.0)

    stoch_rocket = StochasticRocket(
        rocket,
        mass=(rocket.mass, mass_std) if mass_std else None,
        power_off_drag_factor=(1.0, drag_off_std) if drag_off_std else None,
        power_on_drag_factor=(1.0, drag_on_std) if drag_on_std else None,
    )
    stoch_rocket.add_motor(stoch_motor, position=(rocket.motor_position, 0.0))

    # Transfer aero surfaces and parachutes to stochastic rocket
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
        stoch_rocket.add_parachute(StochasticParachute(parachute))


    rail_len = (config.launch.get("rail") or {}).get("length", 5.2)
    inc = (config.launch.get("rail") or {}).get("inclination_deg", 85.0)
    hdg = (config.launch.get("rail") or {}).get("heading_deg", 0.0)

    flight = Flight(rocket, nominal_env, rail_length=rail_len, inclination=inc, heading=hdg)
    flt_cfg = mc_cfg.get("flight") or {}
    inc_std = (flt_cfg.get("inclination") or {}).get("std", 0.0)
    hdg_std = (flt_cfg.get("heading") or {}).get("std", 0.0)

    stoch_flight = StochasticFlight(
        flight,
        inclination=(inc, inc_std) if inc_std else None,
        heading=(hdg, hdg_std) if hdg_std else None,
    )

    # 5. Output directory structure
    run_timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H%M%SZ')
    run_id = f"{run_timestamp}_{project_dir.name}_montecarlo"
    results_dir = project_dir.parents[0].parent / "results" / project_dir.name / run_id
    results_dir.mkdir(parents=True, exist_ok=True)
    
    filename = str(results_dir / "mc_sim")
    
    # 6. Run Monte Carlo
    print(f"[Monte Carlo] Starting {num_sims} simulations. Seed={seed}")
    mc = MonteCarlo(
        filename=filename,
        environment=stoch_env,
        rocket=stoch_rocket,
        flight=stoch_flight,
        export_list=['apogee', 'apogee_time', 'x_impact', 'y_impact', 'impact_velocity', 'max_mach_number', 't_final', 'out_of_rail_velocity', 'max_dynamic_pressure', 'max_speed'],
    )
    # --- Capture all flights via Multiprocess Manager ---
    import multiprocess
    manager = multiprocess.Manager()
    all_flights = manager.list()
    
    _orig_run_single = mc._MonteCarlo__run_single_simulation
    def _patched_run_single(*args, **kwargs):
        flt = _orig_run_single(*args, **kwargs)
        try:
            # We only extract what's needed for plotting to avoid pickle issues over IPC
            flt_data = {
                'x': flt.x[:, 1],
                'y': flt.y[:, 1], 'z': flt.z[:, 1]
            }
            all_flights.append(flt_data)
        except Exception:
            pass
        return flt
    mc._MonteCarlo__run_single_simulation = _patched_run_single
    # -------------------------------------------------------
    
    mc.simulate(number_of_simulations=num_sims, append=False, parallel=True)
    
    # 7. Write Manifest and Traceability
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(project_dir)).decode().strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=str(project_dir)).decode().strip())
    except:
        commit = "unknown"
        dirty = False

    manifest = {
        "run": {
            "id": run_id,
            "timestamp_utc": datetime.datetime.utcnow().isoformat(),
            "status": "completed",
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
            "simulations": num_sims
        }
    }
    
    with open(results_dir / "manifest.yaml", "w") as f:
        yaml.dump(manifest, f, default_flow_style=False)
        
    print(f"[Monte Carlo] Campaign finished. Results saved to: {results_dir}")
    
    # 8. Generate Dispersion Plots
    from antares_fd.simulation.plotters import plot_monte_carlo_dispersion
    outputs_file = results_dir / "mc_sim.outputs.txt"
    if outputs_file.exists():
        plot_monte_carlo_dispersion(outputs_file, results_dir, run_id, nominal_flight=flight, all_flights=all_flights)

    # 9. Generate LaTeX PDF Report
    try:
        from antares_fd.simulation.report import generate_latex_report
        generate_latex_report(config, results_dir, run_id)
    except Exception as e:
        print(f"[Report] Failed to generate LaTeX report: {e}")

    return mc
