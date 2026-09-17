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
import datetime
import importlib.util
from pathlib import Path
from typing import Dict, Any, Optional

import yaml

from antares_fd.config import load_project_config
from antares_fd.reporting import FlightDynamicsReport


SCENARIO_NAME_MAP = {
    "nominal": "Nominal Flight",
    "balistic": "Ballistic Free-Fall",
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

    # 5. Execute Monte Carlo Simulation (Single Run)
    mc_executed = False
    mc_error = None
    if mc_scripts:
        primary_mc = mc_scripts[0]
        print(f"\n[Monte Carlo] Executing stochastic campaign: {primary_mc.stem}...")
        os.environ["ANTARES_CURRENT_SCENARIO"] = primary_mc.stem
        try:
            spec = importlib.util.spec_from_file_location(f"sim_{primary_mc.stem}", str(primary_mc))
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                sys.modules[f"sim_{primary_mc.stem}"] = mod
                spec.loader.exec_module(mod)
                if hasattr(mod, "main"):
                    mod.main()
                    mc_executed = True
                    print(f"      -> Monte Carlo simulation finished successfully.")
        except Exception as e:
            mc_error = e
            print(f"      -> [ERROR] Monte Carlo execution error: {e}")
        finally:
            os.environ.pop("ANTARES_CURRENT_SCENARIO", None)

    # 6. Generate the SINGLE UNIFIED MASTER PDF REPORT
    print("\n[Report] Synthesizing Single Unified Master PDF Report...")
    cfg_nominal = load_project_config(project_dir)
    flight_nominal = scenario_flights.get("Nominal Flight") or (next(iter(scenario_flights.values())) if scenario_flights else None)

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
