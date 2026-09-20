import datetime
import json
from pathlib import Path
import yaml
import subprocess
import numpy as np
import random
import os
import copy
import traceback
import types
import pandas as pd

from antares_fd.builders import build_environment, build_motor, build_vehicle, add_recovery_system
from antares_fd.config.exceptions import ConfigurationError
from antares_fd.simulation.monte_carlo_storage import CampaignManager
from antares_fd.simulation.monte_carlo_parameters import launch_angle_distribution
from antares_fd.simulation.uncertainty import UncertaintyRegistry, SamplingPlan
from antares_fd.simulation.uq_campaign import MonteCarloCampaign
from antares_fd.simulation.uq_pipeline import finalize_campaign_analysis
from antares_fd.simulation.scenarios import apply_scenario, SCENARIOS, NOMINAL

from rocketpy import Flight, StochasticEnvironment, StochasticSolidMotor, StochasticRocket, StochasticFlight, MonteCarlo

from antares_fd.simulation.monte_carlo_patch import _transfer_rocket_components, ProfileStochasticEnvironment, ConfiguredMonteCarlo
from antares_fd.simulation.runner import run_flight, flight_options



def _deterministic_sim_producer(self, _worker_seed, sim_monitor, mutex, error_event):
    """RocketPy producer variant that assigns the frozen seed by case ID.

    RocketPy's stock producer seeds once per worker. That makes a case's
    random stream depend on scheduling. This drop-in producer keeps RocketPy's
    simulation and serialization code, while reseeding all stochastic models
    immediately after the monitor assigns a deterministic case index.
    """
    inputs_json = ""
    sim_idx = -1
    try:
        while sim_monitor.keep_simulating():
            sim_idx = sim_monitor.increment() - 1
            case_seed = int(self._antares_case_seeds[sim_idx])
            members = getattr(self, "_antares_environment_members", None)
            member_indices = getattr(self, "_antares_environment_indices", None)
            if members and member_indices:
                self.environment.set_profile(members[int(member_indices[sim_idx]) % len(members)])
            self.environment._set_stochastic(case_seed)
            self.rocket._set_stochastic(case_seed)
            self.flight._set_stochastic(case_seed)
            self._antares_active_case_seed = case_seed
            flight = self._MonteCarlo__run_single_simulation()
            inputs_json = self._MonteCarlo__evaluate_flight_inputs(sim_idx)
            outputs_json = self._MonteCarlo__evaluate_flight_outputs(flight, sim_idx)
            mutex.acquire()
            try:
                if error_event.is_set():
                    break
                with open(self.input_file, "a", encoding="utf-8") as stream:
                    stream.write(inputs_json)
                with open(self.output_file, "a", encoding="utf-8") as stream:
                    stream.write(outputs_json)
                sim_monitor.print_update_status()
            finally:
                mutex.release()
    except Exception:
        mutex.acquire()
        try:
            with open(self.error_file, "a", encoding="utf-8") as stream:
                stream.write(inputs_json)
            print(f"Error on deterministic case {sim_idx}:\n{traceback.format_exc()}")
            error_event.set()
        finally:
            mutex.release()


def _failure_records(mc, samples, requested):
    """Represent every missing case explicitly in the canonical failure table."""
    successful = {
        (int(record.get("index", record.get("case_id"))) - 1
         if int(record.get("index", record.get("case_id"))) >= 1
         and int(record.get("index", record.get("case_id"))) <= int(requested)
         else int(record.get("index", record.get("case_id"))))
        for record in getattr(mc, "outputs_log", [])
        if isinstance(record, dict) and record.get("index", record.get("case_id")) is not None
    }
    seed_by_case = {}
    if samples is not None and {"case_id", "seed"}.issubset(samples.columns):
        seed_by_case = samples.set_index("case_id")["seed"].to_dict()
    if successful:
        requested = max(int(requested), max(successful) + 1)
    return [
        {
            "case_id": case_id,
            "seed": seed_by_case.get(case_id),
            "exception_class": "RocketPySimulationError",
            "short_error": "no scalar output was exported for this case",
            "stage": "trajectory",
            "worker": None,
            "status": "FAILED",
        }
        for case_id in range(int(requested))
        if case_id not in successful
    ]

def execute_monte_carlo(config, project_dir):
    """
    Central orchestrator for Monte Carlo campaigns.
    Reads config.monte_carlo and the standard nominal configs to construct
    the Stochastic inputs, then runs a full Monte Carlo campaign using RocketPy.
    """
    mc_cfg = config.monte_carlo if config.monte_carlo else {}
    if not mc_cfg:
        raise ConfigurationError("Monte Carlo configuration (monte_carlo.yaml) is missing or empty.")
        
    scenario_id = str(os.environ.get("ANTARES_MC_SCENARIO", NOMINAL)).lower()
    if scenario_id not in SCENARIOS:
        raise ConfigurationError(f"Unsupported stochastic scenario: {scenario_id}")
    # Scenario overrides are applied before any builder runs.  This keeps the
    # physical vehicle, motor and atmosphere builders shared across scenarios.
    config = apply_scenario(config, scenario_id)
    num_sims = int(os.environ.get("ANTARES_MC_TARGET", mc_cfg.get("num_simulations", 10)))
    seed = mc_cfg.get("random_seed", 42)
    parallel = bool(mc_cfg.get("parallel", True))
    configured_workers = os.environ.get("ANTARES_MC_WORKERS", mc_cfg.get("workers"))
    if configured_workers is not None:
        try:
            configured_workers = int(configured_workers)
        except (TypeError, ValueError) as exc:
            raise ConfigurationError("monte_carlo.workers must be an integer") from exc
        if configured_workers < 1:
            raise ConfigurationError("monte_carlo.workers must be greater than zero")
    effective_workers = configured_workers
    if parallel and effective_workers is None:
        # RocketPy otherwise starts one process per logical CPU. Six workers is
        # the conservative default measured for this project and can be
        # overridden explicitly in the campaign YAML or CLI.
        effective_workers = min(os.cpu_count() or 2, 6)
    if parallel and effective_workers == 1:
        # A single worker is a useful explicit serial benchmark and is not a
        # valid value for RocketPy's parallel backend.
        parallel = False
    
    # Force seed reproducibility
    np.random.seed(seed)
    random.seed(seed)
    
    # 5. Output directory structure (supports campaign mode)
    campaign_dir_env = os.environ.get("ANTARES_CAMPAIGN_DIR")
    is_campaign_active = os.environ.get("ANTARES_CAMPAIGN_ACTIVE") == "1"
    compact_outputs = (
        is_campaign_active
        and os.environ.get("ANTARES_COMPACT_OUTPUTS", "1") != "0"
    )

    if campaign_dir_env:
        results_dir = Path(campaign_dir_env)
        run_id = os.environ.get("ANTARES_CAMPAIGN_RUN_ID", results_dir.name)
    else:
        run_timestamp = datetime.datetime.now(datetime.UTC).strftime('%Y-%m-%dT%H%M%SZ')
        run_id = f"{run_timestamp}_{project_dir.name}_montecarlo_failure"
        results_dir = project_dir.parents[0].parent / "results" / project_dir.name / run_id
        results_dir.mkdir(parents=True, exist_ok=True)

    canonical_campaign = None
    if is_campaign_active:
        profile = str(os.environ.get("ANTARES_MC_PROFILE", mc_cfg.get("profile", "development")))
        if profile == "official":
            campaign_settings = {
                "target_samples": num_sims,
                "min_samples": int(mc_cfg.get("min_samples", 10000)),
                "max_samples": int(os.environ.get("ANTARES_MC_MAX", mc_cfg.get("max_samples", 20000))),
            }
        else:
            campaign_settings = {"target_samples": num_sims, "min_samples": num_sims, "max_samples": num_sims}
        if mc_cfg.get("failure_policy"):
            campaign_settings["failure_policy"] = mc_cfg.get("failure_policy")
        canonical_campaign = MonteCarloCampaign(
            project=project_dir.name,
            root=project_dir.parents[1],
            master_seed=int(seed),
            profile=profile,
            campaign_id=run_id,
            config=campaign_settings,
            scenario_id=scenario_id,
        )
        config_hashes = canonical_campaign.snapshot_config(project_dir)
        canonical_campaign.write_manifest("SAMPLING", extra={"configuration_hashes": config_hashes})
        # The environment variable points at the campaign root so scenario
        # paths are selected by the canonical campaign object.
        results_dir = canonical_campaign.path

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
    
    if canonical_campaign is not None:
        samples_df = canonical_campaign.make_samples(registry_path, canonical_campaign.max_samples, len(env_ensemble))
    elif registry_path.exists():
        registry = UncertaintyRegistry(registry_path)
        plan = SamplingPlan(registry, num_sims, seed, len(env_ensemble))
        samples_df = plan.samples
        plan.export(results_dir / "scenarios.csv")
    else:
        samples_df = None
        if canonical_campaign is not None:
            samples_df = canonical_campaign.make_samples(None, canonical_campaign.max_samples)
        
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
        magi_sampling_method = "MAGI_COMPLETE_PROFILE_PER_CASE"
    else:
        magi_sampling_method = "DETERMINISTIC_PROFILE"

    env_cfg = mc_cfg.get("environment") or {}
    user_wx_std = (env_cfg.get("wind_velocity_x") or {}).get("factor_std", 0.0)
    user_wy_std = (env_cfg.get("wind_velocity_y") or {}).get("factor_std", 0.0)
    
    # Each case receives one complete MAGI profile.  The environment object is
    # swapped immediately before RocketPy creates the case Flight; the shared
    # stochastic wrapper still supplies the launch-site randomization.
    wind_factor_x = user_wx_std if len(env_ensemble) <= 1 else 0.0
    wind_factor_y = user_wy_std if len(env_ensemble) <= 1 else 0.0
    stoch_env = ProfileStochasticEnvironment(
        environment=nominal_env, profiles=env_ensemble,
        wind_velocity_x_factor=(1.0, wind_factor_x),
        wind_velocity_y_factor=(1.0, wind_factor_y),
        elevation=(env_cfg.get("elevation") or {}).get("std", None)
    )
    if canonical_campaign is not None:
        canonical_campaign.settings["magi_sampling_method"] = magi_sampling_method

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
    
    filename = str(results_dir / "mc_sim")
    
    mc = ConfiguredMonteCarlo(
        filename=filename,
        environment=stoch_env,
        rocket=stoch_rocket,
        flight=stoch_flight,
        export_list=[
            'apogee', 'apogee_time', 'x_impact', 'y_impact', 'impact_velocity',
            'max_mach_number', 'max_mach_number_time', 't_final',
            'out_of_rail_velocity', 'out_of_rail_time', 'max_dynamic_pressure',
            'max_dynamic_pressure_time', 'max_speed', 'max_speed_time',
            'max_acceleration', 'max_acceleration_time',
        ],
    )
    if canonical_campaign is not None and samples_df is not None and "atmosphere_ensemble" in samples_df:
        ordered_samples = samples_df.sort_values("case_id")
        member_indices = pd.to_numeric(ordered_samples["atmosphere_ensemble"], errors="coerce").fillna(0).astype(int).tolist()
        mc._antares_environment_members = env_ensemble
        mc._antares_environment_indices = member_indices
    
    manager = None
    all_flights = None
    if not compact_outputs:
        manager = CampaignManager()
        manager.start()
        all_flights = manager.TrajectoryStore(seed)
    
    _orig_run_single = mc._MonteCarlo__run_single_simulation
    deterministic_seeds = None
    if canonical_campaign is not None and samples_df is not None and "seed" in samples_df:
        deterministic_seeds = samples_df.sort_values("case_id")["seed"].astype("uint64").tolist()
        mc._antares_case_seeds = deterministic_seeds
        mc._antares_serial_case = 0

    already_done = 0

    def _patched_run_single(*args, **kwargs):
        # Serial RocketPy execution does not expose a case seed hook. Set it
        # immediately before the original RocketPy simulation. The parallel
        # producer above sets _antares_active_case_seed itself.
        if deterministic_seeds is not None and not hasattr(mc, "_antares_active_case_seed"):
            serial_index = min(mc._antares_serial_case, len(deterministic_seeds) - 1)
            case_seed = int(deterministic_seeds[serial_index])
            mc._antares_serial_case += 1
            members = getattr(mc, "_antares_environment_members", None)
            member_indices = getattr(mc, "_antares_environment_indices", None)
            if members and member_indices:
                mc.environment.obj = members[int(member_indices[serial_index]) % len(members)]
            mc.environment._set_stochastic(case_seed)
            mc.rocket._set_stochastic(case_seed)
            mc.flight._set_stochastic(case_seed)
        # 1. Run the scenario flight.  Only the explicitly ballistic scenario
        # uses a parachute-free continuation; required recovery scenarios use
        # the same RocketPy integration path as nominal.
        flt_nom = _orig_run_single(*args, **kwargs)
        if scenario_id != "ballistic":
            try:
                flt_data = {'x': flt_nom.x[:, 1], 'y': flt_nom.y[:, 1], 'z': flt_nom.z[:, 1]}
                if all_flights is not None:
                    all_flights.append(flt_data)
            except Exception:
                pass
            return flt_nom
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
                if all_flights is not None:
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
                if all_flights is not None:
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
                if all_flights is not None:
                    all_flights.append(flt_data)
            except Exception: pass
            return flt_nom
            
    mc._MonteCarlo__run_single_simulation = _patched_run_single
    if deterministic_seeds is not None and parallel:
        mc._MonteCarlo__sim_producer = types.MethodType(_deterministic_sim_producer, mc)

    outputs_file_path = results_dir / "mc_sim.outputs.txt"
    canonical_outputs_path = (
        canonical_campaign.path / "outputs.parquet"
        if canonical_campaign is not None
        else None
    )
    if canonical_outputs_path is not None and canonical_outputs_path.exists():
        # The canonical Parquet table is authoritative. An interrupted
        # RocketPy run may leave a shorter JSONL compatibility file behind;
        # using it would duplicate valid cases or rerun cases already saved.
        cached_outputs = pd.read_parquet(canonical_outputs_path)
        if not cached_outputs.empty:
            mc.outputs_log = cached_outputs.to_dict("records")
            already_done = len(mc.outputs_log)
            mc.num_of_loaded_sims = already_done
    if already_done == 0 and outputs_file_path.exists():
        with open(outputs_file_path, "r") as f:
            already_done = sum(1 for line in f if line.strip())
    if (
        already_done == 0
        and canonical_campaign is not None
        and canonical_outputs_path is not None
        and canonical_outputs_path.exists()
    ):
        # Finished compact campaigns intentionally remove RocketPy's JSONL
        # compatibility files, while an interrupted run may have left empty
        # placeholders. Rehydrate only scalar records for resume; no
        # trajectory is reconstructed and no stochastic input is regenerated.
        cached_outputs = pd.read_parquet(canonical_outputs_path)
        mc.outputs_log = cached_outputs.to_dict("records")
        already_done = len(mc.outputs_log)
        mc.num_of_loaded_sims = already_done

    if deterministic_seeds is not None:
        mc._antares_serial_case = already_done
            
    batch_size = int(mc_cfg.get("batch_size", num_sims))
    if batch_size < 1:
        raise ConfigurationError("monte_carlo.batch_size must be greater than zero")
    simulation_goal = num_sims
    if canonical_campaign is not None and canonical_campaign.profile == "official":
        simulation_goal = canonical_campaign.min_samples
        existing_summary = canonical_campaign.path / "summary.json"
        if already_done >= canonical_campaign.min_samples and existing_summary.exists():
            try:
                previous_summary = json.loads(existing_summary.read_text(encoding="utf-8"))
                if not previous_summary.get("convergence", {}).get("required_metrics_converged", False):
                    simulation_goal = canonical_campaign.next_target(already_done, converged=False)
            except (OSError, json.JSONDecodeError):
                pass
    if deterministic_seeds is not None:
        mc._antares_serial_case = already_done
    
    try:
        if already_done >= simulation_goal:
            print(f"[Monte Carlo] All {simulation_goal} simulations already completed in previous run. Skipping simulation.")
        else:
            batch_number = len(list(results_dir.glob("batch_*.parquet")))
            while already_done < simulation_goal:
                target = min(simulation_goal, already_done + batch_size)
                before = len(getattr(mc, "outputs_log", []))
                print(f"[Monte Carlo] Starting batch {batch_number:05d}: target {target}/{simulation_goal} (completed {already_done}). Seed={seed}")
                simulate_kwargs = {
                    "number_of_simulations": target,
                    "append": already_done > 0,
                    "parallel": parallel,
                    "include_function_data": False,
                }
                if effective_workers is not None and parallel:
                    simulate_kwargs["n_workers"] = effective_workers
                mc.simulate(**simulate_kwargs)
                after = len(getattr(mc, "outputs_log", []))
                if after <= before:
                    break
                if canonical_campaign is not None:
                    batch_frame = pd.DataFrame(mc.outputs_log[before:after])
                    if "case_id" not in batch_frame and "index" in batch_frame:
                        batch_frame["case_id"] = batch_frame["index"]
                    canonical_campaign.write_batch(batch_number, batch_frame)
                already_done = after
                batch_number += 1
                if canonical_campaign is not None and canonical_campaign.profile == "official" and already_done >= canonical_campaign.min_samples:
                    interim = finalize_campaign_analysis(
                        canonical_campaign,
                        project_dir,
                        output_records=list(getattr(mc, "outputs_log", [])),
                        input_records=list(getattr(mc, "inputs_log", [])),
                        failure_records=[],
                    )
                    if interim["convergence"].get("required_metrics_converged"):
                        break
                    simulation_goal = canonical_campaign.next_target(already_done, converged=False)

        if all_flights is None:
            trajectory_snapshot = {"trajectories": [], "samples": [], "seen": 0}
            all_flights = []
        else:
            trajectory_snapshot = all_flights.snapshot()
            all_flights = trajectory_snapshot["trajectories"]
    finally:
        mc._MonteCarlo__run_single_simulation = _orig_run_single
        if manager is not None:
            manager.shutdown()

    
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(project_dir)).decode().strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=str(project_dir)).decode().strip())
    except:
        commit = "unknown"
        dirty = False

    completed_cases = len(mc.outputs_log) if hasattr(mc, "outputs_log") else 0
    failed_cases = len(mc.errors_log) if hasattr(mc, "errors_log") else 0
    campaign_status = "completed" if completed_cases >= num_sims else "failed"

    summary = {
        "campaign_id": run_id,
        "scenario_id": scenario_id,
        "status": campaign_status.upper(),
        "requested": num_sims,
        "completed": completed_cases,
        "failed": failed_cases,
        "seed": seed,
        "parallel": parallel,
        "workers": effective_workers,
    }
    with open(results_dir / "monte_carlo_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    manifest = {
        "run": {
            "id": run_id,
            "timestamp_utc": datetime.datetime.now(datetime.UTC).isoformat(),
            "status": campaign_status,
            "requested_cases": num_sims,
            "completed_cases": completed_cases,
            "failed_cases": failed_cases,
        },
        "git": {
            "commit": commit,
            "dirty_worktree": dirty,
        },
        "monte_carlo": {
            "enabled": True,
            "scenario_id": scenario_id,
            "seed": seed,
            "simulations": num_sims,
            "parallel": parallel,
            "workers": effective_workers,
            "uncertainty_registry": str(registry_path.name) if registry_path.exists() else "none",
            "magi_sampling_method": magi_sampling_method,
            "paired_realizations": bool(canonical_campaign is not None),
        },
        "storage": {
            "include_function_data": False,
            "trajectories_seen": trajectory_snapshot["seen"],
            "retained_trajectories": len(all_flights),
            "trajectory_policy": "none_for_compact_campaign" if compact_outputs else "four_endpoint_extrema_plus_five_reservoir_samples",
        },
    }
    
    with open(results_dir / "manifest.yaml", "w") as f:
        yaml.dump(manifest, f, default_flow_style=False)

    if len(mc.outputs_log) < num_sims:
        if canonical_campaign is not None:
            finalize_campaign_analysis(
                canonical_campaign,
                project_dir,
                output_records=list(getattr(mc, "outputs_log", [])),
                input_records=list(getattr(mc, "inputs_log", [])),
                failure_records=_failure_records(mc, samples_df, num_sims),
            )
        raise RuntimeError(
            f"Monte Carlo campaign incomplete: {len(mc.outputs_log)}/{num_sims} "
            f"simulations exported. Check worker errors and results in {results_dir}."
        )
        
    print(f"[Monte Carlo] Campaign finished. Results saved to: {results_dir}")

    if canonical_campaign is not None:
        finalize_campaign_analysis(
            canonical_campaign,
            project_dir,
            output_records=list(getattr(mc, "outputs_log", [])),
            input_records=list(getattr(mc, "inputs_log", [])),
            failure_records=_failure_records(mc, samples_df, num_sims),
        )
    
    outputs_file = results_dir / "mc_sim.outputs.txt"
    if outputs_file.exists() and not compact_outputs:
        from antares_fd.simulation.plotters import plot_monte_carlo_dispersion, plot_monte_carlo_distributions, plot_monte_carlo_convergence
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
    elif outputs_file.exists():
        print("[Monte Carlo] Standalone plots and KML skipped in compact campaign mode; the master report will contain consolidated charts.")

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
