"""Command line entry point for Antares Flight Dynamics campaigns."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path

from antares_fd.config import load_project_config
from antares_fd.simulation.uq_campaign import MonteCarloCampaign, StochasticScenarioCampaign, PROFILES
from antares_fd.simulation.scenarios import REQUIRED_SCENARIOS, scenario_ids as configured_scenario_ids


def _project(root: Path, name: str) -> Path:
    candidates = [path for path in (root / "projects").iterdir() if path.is_dir() and path.name.lower() == name.lower()]
    if not candidates:
        raise SystemExit(f"Project not found below {root / 'projects'}: {name}")
    return candidates[0]


def _run_script(project_dir: Path) -> None:
    script = project_dir / "simulations" / "monte_carlo.py"
    if not script.exists():
        script = project_dir / "simulations" / "monte_carlo_failure.py"
    spec = importlib.util.spec_from_file_location("antares_cli_monte_carlo", script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load Monte Carlo script: {script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.main()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="antares-fd")
    subparsers = parser.add_subparsers(dest="command", required=True)
    mc = subparsers.add_parser("mc", help="run a resumable Monte Carlo campaign")
    mc.add_argument("project")
    mc.add_argument("--profile", choices=sorted(PROFILES), default="development")
    mc.add_argument("--resume", metavar="CAMPAIGN_ID")
    mc.add_argument("--workers", type=int)
    mc.add_argument("--all-scenarios", action="store_true", help="run configured stochastic scenario campaigns")
    report = subparsers.add_parser("report", help="render a report from an existing campaign artifact")
    report.add_argument("run_id")
    report.add_argument("--project", default="neblina_1")
    archive = subparsers.add_parser("archive", help="archive a completed campaign")
    archive.add_argument("campaign_id")
    archive.add_argument("--project", default="neblina_1")
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    if args.command == "archive":
        campaign = MonteCarloCampaign(args.project, root, campaign_id=args.campaign_id)
        print(campaign.archive())
        return 0
    if args.command == "report":
        from antares_fd.reporting.pdf_report import FlightDynamicsReport
        campaign_path = root / "results" / args.project / args.run_id
        if not campaign_path.exists():
            raise SystemExit(f"Campaign not found: {campaign_path}")
        output = campaign_path / "evidence_report.pdf"
        FlightDynamicsReport.from_artifacts(campaign_path, project_dir=_project(root, args.project)).generate(output)
        print(output)
        return 0
    if args.command != "mc":
        return 2
    project_dir = _project(root, args.project)
    config = load_project_config(project_dir)
    mc_cfg = config.monte_carlo or {}
    seed = int(mc_cfg.get("random_seed", 42))
    scenarios = tuple(configured_scenario_ids(config)) if args.all_scenarios else ("nominal",)
    if args.resume:
        manifest_path = root / "results" / project_dir.name / args.resume / "manifest.json"
        if not manifest_path.exists():
            raise SystemExit(f"Campaign manifest not found: {manifest_path}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        seed = int(manifest.get("master_seed", seed))
        profile = manifest.get("profile", args.profile)
        scenarios = tuple(manifest.get("scenario_ids", scenarios)) if args.all_scenarios else ("nominal",)
        # Rehydrate the campaign limits from the immutable manifest. The
        # sample table can intentionally be larger than the initial target
        # (official campaigns reserve up to 20k rows), so sample_table_rows
        # must never be used as the resume target.
        requested = int(manifest.get("requested_samples", manifest.get("sample_table_rows", 0)))
        if requested < 1:
            raise SystemExit(f"Campaign manifest has no valid requested sample count: {manifest_path}")
        campaign = StochasticScenarioCampaign(
            project_dir.name, root, seed, profile, args.resume,
            config={
                "target_samples": requested,
                "min_samples": int(manifest.get("min_samples", requested)),
                "max_samples": int(manifest.get("max_samples", requested)),
            },
            scenario_ids=scenarios,
        )
        target = requested
    else:
        target = int(PROFILES[args.profile].get("target_samples", mc_cfg.get("num_simulations", 10)))
        campaign = StochasticScenarioCampaign(
            project_dir.name, root, seed, args.profile,
            config={"target_samples": target, "min_samples": target, "max_samples": int(PROFILES[args.profile].get("max_samples", target))},
            scenario_ids=scenarios,
        )

    # Sampling is a campaign operation.  It runs once and is reused by every
    # scenario, so paired deltas compare the same physical realization.
    registry_path = project_dir / "config" / "uncertainties.yaml"
    configuration_hashes = campaign.snapshot_config(project_dir)
    samples = campaign.ensure_samples(registry_path if registry_path.exists() else None)
    campaign.write_manifest(
        "SAMPLING",
        profile=campaign.profile,
        requested_samples=campaign.target_samples,
        min_samples=campaign.min_samples,
        max_samples=campaign.max_samples,
        sample_table_rows=int(len(samples)),
        configuration_hashes=configuration_hashes,
    )

    previous = {key: os.environ.get(key) for key in ("ANTARES_CAMPAIGN_DIR", "ANTARES_CAMPAIGN_ACTIVE", "ANTARES_CAMPAIGN_RUN_ID", "ANTARES_MC_TARGET", "ANTARES_MC_PROFILE", "ANTARES_MC_WORKERS", "ANTARES_MC_MAX")}
    os.environ.update({"ANTARES_CAMPAIGN_DIR": str(campaign.path), "ANTARES_CAMPAIGN_ACTIVE": "1", "ANTARES_CAMPAIGN_RUN_ID": campaign.campaign_id, "ANTARES_MC_TARGET": str(target), "ANTARES_MC_PROFILE": campaign.profile})
    if args.workers is not None:
        os.environ["ANTARES_MC_WORKERS"] = str(args.workers)
    os.environ["ANTARES_MC_MAX"] = str(campaign.max_samples if campaign.profile == "official" else target)
    try:
        for scenario_id in scenarios:
            os.environ["ANTARES_MC_SCENARIO"] = scenario_id
            _run_script(project_dir)
        if args.all_scenarios:
            pairing = campaign.finalize_paired_comparison()
            campaign.write_manifest(
                "COMPLETE",
                profile=campaign.profile,
                requested_samples=campaign.target_samples,
                min_samples=campaign.min_samples,
                max_samples=campaign.max_samples,
                sample_table_rows=int(len(samples)),
                configuration_hashes=configuration_hashes,
                paired_comparison=pairing,
                scenario_summaries=campaign.scenario_manifests(),
            )
    finally:
        os.environ.pop("ANTARES_MC_SCENARIO", None)
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
