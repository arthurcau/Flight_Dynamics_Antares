"""
ANTARES FLIGHT DYNAMICS
Unified Campaign Orchestrator.

Discovers and executes all simulation scenarios (deterministic + Monte Carlo)
in a project's simulations directory within a SINGLE execution lifecycle.
Guarantees that:
1. ONLY ONE campaign folder is created in results/<project_name>/<run_id>.
2. ALL intermediate data (trajectories, KMLs, Monte Carlo outputs) are centralized.
3. ONLY ONE comprehensive, master engineering PDF report is compiled.
"""

import sys
import os
import json
import datetime
import importlib.util
from pathlib import Path
from typing import Dict, Any, Optional

import yaml

from antares_fd.config import load_project_config
from antares_fd.reporting import FlightDynamicsReport
from antares_fd.simulation.scenarios import scenario_ids as configured_scenario_ids
from antares_fd.simulation.scenarios import apply_scenario
from antares_fd.simulation.uq_campaign import StochasticScenarioCampaign, PROFILES
from antares_fd.analysis.metrics import extract_flight_metrics
from antares_fd.analysis.scenario_uq import deterministic_scenario_consistency


SCENARIO_NAME_MAP = {
    "nominal": "Nominal Flight",
    "balistic": "Ballistic Free-Fall",  # legacy project filename
    "ballistic": "Ballistic Free-Fall",
    "main_at_apogee": "Main at Apogee",
    "separation_at_main_opening": "Separation at Main",
    "only_reefing": "Only Reefing Descent",
}


def run_project_campaign(simulations_dir: Path) -> Path:
    """
    Executes all simulation files in `simulations_dir`, aggregates their results,
    and produces a single master engineering PDF report in a single output directory.
    """
    simulations_dir = Path(simulations_dir).resolve()
    project_dir = simulations_dir.parent
    project_root = project_dir.parents[1]

    # Ensure python paths
    source_dir = project_root / "source"
    if str(source_dir) not in sys.path:
        sys.path.insert(0, str(source_dir))
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    # 1. Create the SINGLE Campaign Results Directory
    timestamp = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H%M%SZ")
    run_id = f"{timestamp}_{project_dir.name}_campaign"
    campaign_dir = project_root / "results" / project_dir.name / run_id
    campaign_dir.mkdir(parents=True, exist_ok=True)
    trajectories_dir = campaign_dir / "trajectories"
    trajectories_dir.mkdir(parents=True, exist_ok=True)

    # 2. Activate Campaign Environment to suppress redundant individual reports
    os.environ["ANTARES_CAMPAIGN_DIR"] = str(campaign_dir)
    os.environ["ANTARES_CAMPAIGN_ACTIVE"] = "1"
    os.environ["ANTARES_CAMPAIGN_RUN_ID"] = run_id
    # Campaign reports already contain the consolidated figures. Keep only the
    # artifacts that are useful for reproducibility and review by default;
    # callers can set ANTARES_COMPACT_OUTPUTS=0 to retain every legacy export.
    previous_compact_outputs = os.environ.get("ANTARES_COMPACT_OUTPUTS")
    compact_outputs = previous_compact_outputs != "0"
    os.environ["ANTARES_COMPACT_OUTPUTS"] = "1" if compact_outputs else "0"

    print("\n" + "=" * 75)
    print("ANTARES FLIGHT DYNAMICS — UNIFIED SIMULATION CAMPAIGN")
    print(f"Vehicle / Project: {project_dir.name}")
    print(f"Campaign Directory: {campaign_dir}")
    print("=" * 75)

    # 3. Discover Simulation Scripts
    all_scripts = sorted([
        f for f in simulations_dir.glob("*.py")
        if not f.name.startswith("run_all")
        and not f.name.startswith("__")
        and not f.name.startswith("test_")
    ])

    deterministic_scripts = []
    mc_scripts = []

    for s in all_scripts:
        stem = s.stem.lower()
        if "monte_carlo" in stem or "montecarlo" in stem:
            mc_scripts.append(s)
        else:
            deterministic_scripts.append(s)

    # ``monte_carlo_failure.py`` is a project-level compatibility wrapper in
    # Neblina 1, while ``monte_carlo.py`` is the canonical entry point that
    # already dispatches all configured scenarios.  Counting both as
    # campaigns is misleading and can make a future runner execute the same
    # campaign twice.  Keep the failure wrapper available when it is the only
    # Monte Carlo entry point in another project.
    canonical_mc = [path for path in mc_scripts if path.stem.lower() in {"monte_carlo", "montecarlo"}]
    if canonical_mc:
        mc_scripts = canonical_mc + [path for path in mc_scripts if path.stem.lower() not in {"monte_carlo_failure", "montecarlo_failure"}]

    # Put nominal first
    deterministic_scripts.sort(key=lambda p: 0 if p.stem.lower() == "nominal" else 1)

    # The ordinary campaign is the nominal stochastic analysis.  A file named
    # ``monte_carlo_failure`` is a failure-mode campaign and must never be
    # silently selected as the nominal population.
    mc_scripts.sort(key=lambda p: 0 if "failure" not in p.stem.lower() else 1)

    # 4. Execute Deterministic Simulations
    scenario_flights: Dict[str, Any] = {}
    print(f"\nDiscovered {len(deterministic_scripts)} deterministic scenarios and {len(mc_scripts)} Monte Carlo campaigns.")

    for i, script_path in enumerate(deterministic_scripts, 1):
        stem = script_path.stem
        label = SCENARIO_NAME_MAP.get(stem, stem.replace("_", " ").title())
        print(f"\n[{i}/{len(deterministic_scripts)}] Executing: {stem} ({label})...")
        os.environ["ANTARES_CURRENT_SCENARIO"] = stem

        try:
            spec = importlib.util.spec_from_file_location(f"sim_{stem}", str(script_path))
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                sys.modules[f"sim_{stem}"] = mod
                spec.loader.exec_module(mod)
                if hasattr(mod, "main"):
                    flt = mod.main()
                    if flt:
                        scenario_flights[label] = flt
                        print(f"      -> Apogee: {flt.apogee:.1f} m | Duration: {flt.t_final:.1f} s | Status: OK")
        except Exception as e:
            print(f"      -> [ERROR] Failed running {stem}: {e}")
        finally:
            os.environ.pop("ANTARES_CURRENT_SCENARIO", None)

    # 5. Execute one shared stochastic campaign for every configured scenario.
    # All scenarios point at the same immutable sample table and receive the
    # same case-local seeds, which makes the eventual paired comparison valid.
    mc_executed = False
    mc_error = None
    scenario_campaign = None
    if mc_scripts:
        primary_mc = mc_scripts[0]
        base_config = load_project_config(project_dir)
        mc_cfg = base_config.monte_carlo or {}
        profile = str(mc_cfg.get("profile", "development"))
        if profile not in PROFILES:
            profile = "development"
        target = int(mc_cfg.get("num_simulations", PROFILES[profile]["target_samples"]))
        scenario_campaign = StochasticScenarioCampaign(
            project_dir.name,
            project_root,
            master_seed=int(mc_cfg.get("random_seed", 42)),
            profile=profile,
            campaign_id=run_id,
            config={"target_samples": target, "min_samples": target, "max_samples": int(PROFILES[profile].get("max_samples", target))},
            scenario_ids=tuple(configured_scenario_ids(base_config)),
        )
        registry = project_dir / "config" / "uncertainties.yaml"
        scenario_campaign.ensure_samples(registry if registry.exists() else None)
        scenario_campaign.write_manifest("SAMPLING", profile=profile)
        for scenario_id in scenario_campaign.scenario_ids:
            print(f"\n[Monte Carlo] Executing {scenario_id}: {primary_mc.stem}...")
            os.environ["ANTARES_CURRENT_SCENARIO"] = primary_mc.stem
            os.environ["ANTARES_MC_SCENARIO"] = scenario_id
            os.environ["ANTARES_MC_TARGET"] = str(target)
            os.environ["ANTARES_MC_PROFILE"] = profile
            try:
                spec = importlib.util.spec_from_file_location(f"sim_{primary_mc.stem}_{scenario_id}", str(primary_mc))
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    sys.modules[f"sim_{primary_mc.stem}_{scenario_id}"] = mod
                    spec.loader.exec_module(mod)
                    if hasattr(mod, "main"):
                        mod.main()
                        mc_executed = True
                        print(f"      -> {scenario_id} completed successfully.")
            except Exception as e:
                mc_error = e
                print(f"      -> [ERROR] {scenario_id} Monte Carlo error: {e}")
                break
            finally:
                os.environ.pop("ANTARES_CURRENT_SCENARIO", None)
                os.environ.pop("ANTARES_MC_SCENARIO", None)
        if scenario_campaign is not None and mc_executed:
            scenario_campaign.finalize_paired_comparison()

    # 6. Generate the SINGLE UNIFIED MASTER PDF REPORT
    print("\n[Report] Synthesizing Single Unified Master PDF Report...")
    cfg_nominal = load_project_config(project_dir)
    flight_nominal = scenario_flights.get("Nominal Flight") or (next(iter(scenario_flights.values())) if scenario_flights else None)

    if scenario_flights:
        reverse_names = {label_id: scenario_id for scenario_id, label_id in SCENARIO_NAME_MAP.items()}
        deterministic_metrics = {}
        for label, flight in scenario_flights.items():
            scenario_id = reverse_names.get(label, label.lower().replace(" ", "_"))
            scenario_config = apply_scenario(cfg_nominal, scenario_id) if scenario_id in {"nominal", "main_at_apogee", "only_reefing", "ballistic", "drogue_only"} else cfg_nominal
            deterministic_metrics[scenario_id] = extract_flight_metrics(flight, scenario_config, project_dir)
        (campaign_dir / "deterministic_scenario_consistency.json").write_text(
            json.dumps(deterministic_scenario_consistency(deterministic_metrics), indent=2), encoding="utf-8"
        )

    master_pdf_path = campaign_dir / "flight_dynamics_report.pdf"

    report = FlightDynamicsReport(
        flight=flight_nominal,
        config=cfg_nominal,
        project_dir=project_dir,
        mc_results_dir=campaign_dir if mc_executed else None,
        run_id=run_id,
        scenario_flights=scenario_flights,
    )
    generated_pdf = report.generate(master_pdf_path)

    # The report has consumed RocketPy's compatibility logs. Canonical Parquet
    # artifacts and the immutable sample table are the archival representation
    # for compact campaigns; remove the redundant line oriented exports.
    if compact_outputs and mc_executed:
        for redundant in campaign_dir.glob("mc_sim.*.txt"):
            redundant.unlink(missing_ok=True)
        (campaign_dir / "scenarios.csv").unlink(missing_ok=True)

    # 7. Write Consolidated Campaign Manifest
    manifest_path = campaign_dir / "manifest.yaml"
    campaign_manifest = {
        "campaign": {
            "run_id": run_id,
            "project": project_dir.name,
            "timestamp_utc": datetime.datetime.now(datetime.UTC).isoformat(),
            "deterministic_scenarios": list(scenario_flights.keys()),
            "monte_carlo_executed": mc_executed,
            "master_report_pdf": str(generated_pdf.name),
        }
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        yaml.dump(campaign_manifest, f, default_flow_style=False)

    # Reset campaign environment
    os.environ.pop("ANTARES_CAMPAIGN_DIR", None)
    os.environ.pop("ANTARES_CAMPAIGN_ACTIVE", None)
    os.environ.pop("ANTARES_CAMPAIGN_RUN_ID", None)
    os.environ.pop("ANTARES_MC_TARGET", None)
    os.environ.pop("ANTARES_MC_PROFILE", None)
    if previous_compact_outputs is None:
        os.environ.pop("ANTARES_COMPACT_OUTPUTS", None)
    else:
        os.environ["ANTARES_COMPACT_OUTPUTS"] = previous_compact_outputs

    print("\n" + "=" * 75)
    print("UNIFIED CAMPAIGN COMPLETE — ALL RESULTS CENTRALIZED IN ONE DIRECTORY")
    print("=" * 75)
    print(f"Campaign Directory : {campaign_dir}")
    print(f"Master PDF Report  : {generated_pdf}")
    print(f"Master Metrics JSON: {campaign_dir / 'master_metrics.json'}")
    print(f"Manifest YAML      : {manifest_path}")
    print("=" * 75 + "\n")

    if mc_error is not None:
        raise RuntimeError(f"Monte Carlo campaign failed; report was written to {generated_pdf}") from mc_error

    return generated_pdf
