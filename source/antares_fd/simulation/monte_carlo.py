import datetime
from pathlib import Path
import yaml
import subprocess
import numpy as np
import random
import os

from antares_fd.builders import build_environment, build_motor, build_vehicle, add_recovery_system
from antares_fd.config.exceptions import ConfigurationError
from antares_fd.simulation.monte_carlo_parameters import launch_angle_distribution
from antares_fd.simulation.monte_carlo_storage import CampaignManager

from rocketpy import Flight, StochasticEnvironment, StochasticSolidMotor, StochasticRocket, StochasticFlight, MonteCarlo

from antares_fd.simulation.monte_carlo_patch import _transfer_rocket_components, ProfileStochasticEnvironment, ConfiguredMonteCarlo
from antares_fd.simulation.runner import run_flight, flight_options


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
    scenario_id = os.environ.get("ANTARES_MC_SCENARIO", "nominal")
    from antares_fd.simulation.scenarios import apply_scenario
    config = apply_scenario(config, scenario_id)

    # Force seed reproducibility
    np.random.seed(seed)
    random.seed(seed)
    
    from antares_fd.builders.environment import build_environment, build_environment_ensemble
    
    print("[Monte Carlo] Building Nominal Models and Stochastics...")
    # Get nominal env for vehicle builder, and the ensemble list for Monte Carlo
    nominal_env = build_environment(config.environment, config.launch)
    env_ensemble = build_environment_ensemble(config.environment, config.launch)
    
    env_cfg = mc_cfg.get("environment") or {}
    user_wx_std = (env_cfg.get("wind_velocity_x") or {}).get("factor_std", 0.0)
    user_wy_std = (env_cfg.get("wind_velocity_y") or {}).get("factor_std", 0.0)
    
    stoch_env = ProfileStochasticEnvironment(
        environment=nominal_env, profiles=env_ensemble,
        wind_velocity_x_factor=(1.0, user_wx_std),
        wind_velocity_y_factor=(1.0, user_wy_std),
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
    _transfer_rocket_components(rocket, stoch_rocket)

    rail_len = (config.launch.get("rail") or {}).get("length", 5.2)
    inc = (config.launch.get("rail") or {}).get("inclination_deg", 85.0)
    hdg = (config.launch.get("rail") or {}).get("heading_deg", 0.0)

    flight = run_flight(rocket, nominal_env, config.launch, config.simulation)
    flt_cfg = mc_cfg.get("flight") or {}

    stoch_flight = StochasticFlight(
        flight,
        inclination=launch_angle_distribution(inc, flt_cfg.get("inclination"), "inclination"),
        heading=launch_angle_distribution(hdg, flt_cfg.get("heading"), "heading"),
    )

    # 5. Output directory structure (supports campaign mode)
    campaign_dir_env = os.environ.get("ANTARES_CAMPAIGN_DIR")
    is_campaign_active = os.environ.get("ANTARES_CAMPAIGN_ACTIVE") == "1"

    if campaign_dir_env:
        results_dir = Path(campaign_dir_env)
        run_id = os.environ.get("ANTARES_CAMPAIGN_RUN_ID", results_dir.name)
        if scenario_id != "nominal":
            results_dir = results_dir / "scenarios" / scenario_id
            results_dir.mkdir(parents=True, exist_ok=True)
    else:
        run_timestamp = datetime.datetime.now(datetime.UTC).strftime('%Y-%m-%dT%H%M%SZ')
        run_id = f"{run_timestamp}_{project_dir.name}_montecarlo"
        results_dir = project_dir.parents[0].parent / "results" / project_dir.name / run_id
        results_dir.mkdir(parents=True, exist_ok=True)
    
    filename = str(results_dir / "mc_sim")
    
    # 6. Run Monte Carlo

    mc = ConfiguredMonteCarlo(
        filename=filename,
        environment=stoch_env,
        rocket=stoch_rocket,
        flight=stoch_flight,
        export_list=['apogee', 'apogee_time', 'x_impact', 'y_impact', 'impact_velocity', 'max_mach_number', 't_final', 'out_of_rail_velocity', 'max_dynamic_pressure', 'max_speed'],
    )
    # Use RocketPy's process backend for every shared object.
    manager = CampaignManager()
    manager.start()
    all_flights = manager.TrajectoryStore(seed)
    
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
    

    # Checkpointing Logic
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

    
    # 7. Write Manifest and Traceability
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(project_dir)).decode().strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=str(project_dir)).decode().strip())
    except Exception:
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
            "simulations": num_sims
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
    
    # 8. Generate Dispersion Plots
    from antares_fd.simulation.plotters import plot_monte_carlo_dispersion, plot_monte_carlo_distributions, plot_monte_carlo_convergence
    outputs_file = results_dir / "mc_sim.outputs.txt"
    if outputs_file.exists():
        plot_monte_carlo_dispersion(outputs_file, results_dir, run_id, nominal_flight=flight, all_flights=all_flights,
                                   sample_flights=trajectory_snapshot["samples"])
        plot_monte_carlo_distributions(outputs_file, results_dir, run_id)
        plot_monte_carlo_convergence(outputs_file, results_dir, run_id)

    # 9. Generate Canonical Engineering PDF Report (standalone only)
    if is_campaign_active:
        print(f"[Campaign Mode] Monte Carlo outputs registered in campaign directory: {results_dir}")
    else:
        try:
            from antares_fd.reporting import FlightDynamicsReport
            report = FlightDynamicsReport(flight=flight, config=config, project_dir=project_dir, mc_results_dir=results_dir, run_id=run_id)
            pdf_path = results_dir / "flight_dynamics_report.pdf"
            report.generate(pdf_path)
            print(f"[Report] Engineering PDF report generated: {pdf_path}")
        except Exception as e:
            print(f"[Report] Failed to generate engineering PDF report: {e}")

    return mc
