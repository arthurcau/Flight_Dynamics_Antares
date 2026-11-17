"""
ANTARES FLIGHT DYNAMICS
Unified Campaign Orchestrator.

Executes declared simulation scenarios (deterministic + Monte Carlo)
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
from typing import Dict, Any

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
    "ballistic": "Ballistic Free-Fall",
    "main_at_apogee": "Main at Apogee",
    "only_reefing": "Only Reefing Descent",
}


DETERMINISTIC_ENTRYPOINTS = (
    "nominal",
    "main_at_apogee",
    "only_reefing",
    "drogue_only",
)
# Não executar auxiliares fora desta lista. Os antigos exemplos de separação
# foram removidos: subtraíam massa presumida antes da ignição, sem evento físico.
MONTE_CARLO_ENTRYPOINTS = ("monte_carlo", "montecarlo")
CAMPAIGN_ENVIRONMENT_KEYS = (
    "ANTARES_CAMPAIGN_DIR", "ANTARES_CAMPAIGN_ACTIVE", "ANTARES_CAMPAIGN_RUN_ID",
    "ANTARES_COMPACT_OUTPUTS", "ANTARES_CURRENT_SCENARIO", "ANTARES_MC_SCENARIO",
    "ANTARES_MC_TARGET", "ANTARES_MC_PROFILE", "ANTARES_MC_WORKERS", "ANTARES_MC_MAX",
)


def select_campaign_scripts(simulations_dir: Path) -> tuple[list[Path], list[Path]]:
    """Select only declared flight entry points; unrelated helpers never run."""

    simulations_dir = Path(simulations_dir)
    nominal = simulations_dir / "nominal.py"
    if not nominal.is_file():
        raise FileNotFoundError(f"Campaign requires a nominal.py flight entry point: {nominal}")
    deterministic = [
        path for stem in DETERMINISTIC_ENTRYPOINTS
        if (path := simulations_dir / f"{stem}.py").is_file()
    ]
    ballistic = simulations_dir / "ballistic.py"
    legacy_ballistic = simulations_dir / "balistic.py"
    selected_ballistic = ballistic if ballistic.is_file() else legacy_ballistic
    if selected_ballistic.is_file():
        insertion = next(
            (index for index, path in enumerate(deterministic) if path.stem == "drogue_only"),
            len(deterministic),
        )
        deterministic.insert(insertion, selected_ballistic)
    stochastic = [
        path for stem in MONTE_CARLO_ENTRYPOINTS
        if (path := simulations_dir / f"{stem}.py").is_file()
    ]
    return deterministic, stochastic[:1]


def run_project_campaign(simulations_dir: Path) -> Path:
    """Run a campaign and restore every campaign control variable on all exits."""
    previous = {key: os.environ.get(key) for key in CAMPAIGN_ENVIRONMENT_KEYS}
    try:
        return _run_project_campaign_impl(simulations_dir)
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _run_project_campaign_impl(simulations_dir: Path) -> Path:
    """
    Executes declared simulation files in `simulations_dir`, aggregates results,
    and produces a single master engineering PDF report in a single output directory.
    """
    simulations_dir = Path(simulations_dir).resolve()
    project_dir = simulations_dir.parent
    project_root = project_dir.parents[1]
    deterministic_scripts, mc_scripts = select_campaign_scripts(simulations_dir)

    # Ensure python paths
    source_dir = project_root / "source"
    if str(source_dir) not in sys.path:
        sys.path.insert(0, str(source_dir))
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    # 1. Create the SINGLE Campaign Results Directory
    timestamp = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H%M%S.%fZ")
    run_id = f"{timestamp}_{project_dir.name}_campaign"
    campaign_dir = project_root / "results" / project_dir.name / run_id
    campaign_dir.mkdir(parents=True, exist_ok=False)
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

    # 3. Execute Deterministic Simulations
    scenario_flights: Dict[str, Any] = {}
    deterministic_failures: list[dict[str, str]] = []
    print(f"\nDiscovered {len(deterministic_scripts)} deterministic scenarios and {len(mc_scripts)} Monte Carlo campaigns.")

    for i, script_path in enumerate(deterministic_scripts, 1):
        stem = script_path.stem
        scenario_id = "ballistic" if stem == "balistic" else stem
        label = SCENARIO_NAME_MAP.get(scenario_id, scenario_id.replace("_", " ").title())
        print(f"\n[{i}/{len(deterministic_scripts)}] Executing: {stem} ({label})...")
        os.environ["ANTARES_CURRENT_SCENARIO"] = scenario_id

        try:
            spec = importlib.util.spec_from_file_location(f"sim_{stem}", str(script_path))
            if spec is None or spec.loader is None:
                raise RuntimeError(f"Could not load deterministic entry point: {script_path}")
            mod = importlib.util.module_from_spec(spec)
            sys.modules[f"sim_{stem}"] = mod
            spec.loader.exec_module(mod)
            if not hasattr(mod, "main"):
                raise RuntimeError(f"Deterministic entry point has no main(): {script_path}")
            flt = mod.main()
            if flt:
                scenario_flights[label] = flt
                print(f"      -> Apogee: {flt.apogee:.1f} m | Duration: {flt.t_final:.1f} s | Status: OK")
            else:
                raise RuntimeError(f"Deterministic entry point returned no flight: {script_path}")
        except Exception as e:
            deterministic_failures.append({"scenario": scenario_id, "error_type": type(e).__name__, "message": str(e)})
            print(f"      -> [ERROR] Failed running {stem}: {e}")
        finally:
            os.environ.pop("ANTARES_CURRENT_SCENARIO", None)

    if "Nominal Flight" not in scenario_flights:
        failed_manifest = {
            "campaign": {
                "run_id": run_id,
                "project": project_dir.name,
                "timestamp_utc": datetime.datetime.now(datetime.UTC).isoformat(),
                "status": "FAILED_NOMINAL_SCENARIO",
                "deterministic_scenarios": list(scenario_flights.keys()),
                "deterministic_failures": deterministic_failures,
                "monte_carlo_executed": False,
            }
        }
        with (campaign_dir / "manifest.yaml").open("w", encoding="utf-8") as stream:
            yaml.safe_dump(failed_manifest, stream, sort_keys=False)
        raise RuntimeError("Nominal flight failed; campaign report cannot use another scenario as nominal")

    # 4. Execute one shared stochastic campaign for every configured scenario.
    # All scenarios point at the same immutable sample table and receive the
    # same case-local seeds, which makes the eventual paired comparison valid.
    mc_executed = False
    mc_error = None
    mc_failed_scenario_id = None
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
                if spec is None or spec.loader is None:
                    raise RuntimeError(f"Could not load Monte Carlo entry point: {primary_mc}")
                mod = importlib.util.module_from_spec(spec)
                sys.modules[f"sim_{primary_mc.stem}_{scenario_id}"] = mod
                spec.loader.exec_module(mod)
                if not hasattr(mod, "main"):
                    raise RuntimeError(f"Monte Carlo entry point has no main(): {primary_mc}")
                mod.main()
                mc_executed = True
                print(f"      -> {scenario_id} completed successfully.")
            except Exception as e:
                mc_error = e
                mc_failed_scenario_id = scenario_id
                print(f"      -> [ERROR] {scenario_id} Monte Carlo error: {e}")
                break
            finally:
                os.environ.pop("ANTARES_CURRENT_SCENARIO", None)
                os.environ.pop("ANTARES_MC_SCENARIO", None)
        if scenario_campaign is not None and mc_executed:
            scenario_campaign.finalize_paired_comparison()

    # 5. Generate the SINGLE UNIFIED MASTER PDF REPORT
    print("\n[Report] Synthesizing Single Unified Master PDF Report...")
    cfg_nominal = load_project_config(project_dir)
    flight_nominal = scenario_flights["Nominal Flight"]

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
            "deterministic_failures": deterministic_failures,
            "monte_carlo_executed": mc_executed,
            "monte_carlo_status": "FAILED" if mc_error is not None else ("COMPLETE" if mc_executed else "NOT_RUN"),
            "status": "PARTIAL" if deterministic_failures or mc_error is not None else "COMPLETE",
            "monte_carlo_error": (
                {"scenario_id": mc_failed_scenario_id, "type": type(mc_error).__name__, "message": str(mc_error)}
                if mc_error is not None else None
            ),
            "master_report_pdf": str(generated_pdf.name),
        }
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        yaml.dump(campaign_manifest, f, default_flow_style=False)

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
