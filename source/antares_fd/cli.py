"""Command line entry point for Antares Flight Dynamics campaigns."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path


MC_CAMPAIGN_ENVIRONMENT_KEYS = (
    "ANTARES_CAMPAIGN_DIR", "ANTARES_CAMPAIGN_ACTIVE", "ANTARES_CAMPAIGN_RUN_ID",
    "ANTARES_COMPACT_OUTPUTS", "ANTARES_CURRENT_SCENARIO", "ANTARES_MC_SCENARIO",
    "ANTARES_MC_TARGET", "ANTARES_MC_PROFILE", "ANTARES_MC_WORKERS", "ANTARES_MC_MAX",
)


def _project(root: Path, name: str) -> Path:
    projects_root = root / "projects"
    if projects_root.is_symlink():
        raise SystemExit(f"Project directory cannot be a symlink: {projects_root}")
    resolved_projects = projects_root.resolve()
    for path in projects_root.iterdir():
        if path.name.lower() != name.lower() or not path.is_dir():
            continue
        if path.is_symlink():
            raise SystemExit(f"Project directory cannot be a symlink: {path}")
        resolved = path.resolve()
        if not resolved.is_relative_to(resolved_projects):
            raise SystemExit(f"Project path resolves outside projects/: {path}")
        return resolved
    raise SystemExit(f"Project not found below {projects_root}: {name}")


def _run_script(project_dir: Path) -> None:
    script = project_dir / "simulations" / "monte_carlo.py"
    if not script.exists():
        raise FileNotFoundError(f"Canonical Monte Carlo entry point is missing: {script}")
    spec = importlib.util.spec_from_file_location("antares_cli_monte_carlo", script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load Monte Carlo script: {script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.main()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="antares-fd")
    parser.add_argument("--repo-root", type=Path, help="repository containing projects/ and results/ (or set ANTARES_FD_ROOT)")
    subparsers = parser.add_subparsers(dest="command", required=True)
    mc = subparsers.add_parser("mc", help="run a resumable Monte Carlo campaign")
    mc.add_argument("project")
    mc.add_argument("--profile", default="development")
    mc.add_argument("--resume", metavar="CAMPAIGN_ID")
    mc.add_argument("--workers", type=int)
    mc.add_argument("--all-scenarios", action="store_true", help="run configured stochastic scenario campaigns")
    report = subparsers.add_parser("report", help="render a report from an existing campaign artifact")
    report.add_argument("run_id")
    report.add_argument("--project", default="neblina_1")
    archive = subparsers.add_parser("archive", help="archive a completed campaign")
    archive.add_argument("campaign_id")
    archive.add_argument("--project", default="neblina_1")
    telemetry = subparsers.add_parser("telemetry", help="inspect recorded telemetry")
    telemetry_subparsers = telemetry.add_subparsers(dest="telemetry_command", required=True)
    telemetry_audit = telemetry_subparsers.add_parser("audit", help="audit telemetry without modifying its source")
    telemetry_audit.add_argument("project")
    telemetry_audit.add_argument("--metadata", type=Path, help="dataset metadata YAML (defaults to the project's telemetry metadata)")
    telemetry_audit.add_argument("--source", type=Path, help="override the raw source path declared by the metadata")
    telemetry_audit.add_argument("--output", type=Path, help="output directory (must not already exist)")
    telemetry_process = telemetry_subparsers.add_parser("process", help="derive a marked flight section from a verified audit")
    telemetry_process.add_argument("project")
    telemetry_process.add_argument("--audit", type=Path, required=True, help="verified telemetry audit directory")
    telemetry_process.add_argument("--section", help="section marker (default: sole marker in project metadata)")
    telemetry_process.add_argument("--output", type=Path, help="new output directory under results by default")
    args = parser.parse_args(argv)
    root = Path(args.repo_root or os.environ.get("ANTARES_FD_ROOT") or Path(__file__).resolve().parents[2]).resolve()
    if not (root / "projects").is_dir():
        parser.error(f"No projects/ directory below {root}; pass --repo-root or set ANTARES_FD_ROOT")
    if args.command == "archive":
        project_dir = _project(root, args.project)
        from antares_fd.simulation.uq_campaign import MonteCarloCampaign, campaign_path_for

        try:
            campaign_path = campaign_path_for(root, project_dir.name, args.campaign_id)
        except ValueError as exc:
            parser.error(str(exc))
        manifest_path = campaign_path / "manifest.json"
        if manifest_path.is_symlink():
            parser.error(f"Campaign manifest cannot be a symlink: {manifest_path}")
        if not manifest_path.is_file():
            raise SystemExit(f"Campaign manifest not found: {manifest_path}")
        campaign = MonteCarloCampaign(project_dir.name, root, campaign_id=args.campaign_id)
        print(campaign.archive())
        return 0
    if args.command == "report":
        from antares_fd.reporting.pdf_report import FlightDynamicsReport
        from antares_fd.simulation.uq_campaign import campaign_path_for

        project_dir = _project(root, args.project)
        try:
            campaign_path = campaign_path_for(root, project_dir.name, args.run_id)
        except ValueError as exc:
            parser.error(str(exc))
        if not campaign_path.exists():
            raise SystemExit(f"Campaign not found: {campaign_path}")
        output = campaign_path / "evidence_report.pdf"
        FlightDynamicsReport.from_artifacts(campaign_path, project_dir=project_dir).generate(output)
        print(output)
        return 0
    if args.command == "telemetry":
        project_dir = _project(root, args.project)
        if args.telemetry_command == "audit":
            from antares_fd.telemetry.artifacts import audit_project

            output = audit_project(
                project_dir,
                repo_root=root,
                metadata_path=args.metadata,
                source_path=args.source,
                output_dir=args.output,
            )
        else:
            import yaml

            from antares_fd.reconstruction.artifacts import process_audit_section

            metadata_path = project_dir / "telemetry" / "metadata" / "dataset.yaml"
            metadata = yaml.safe_load(metadata_path.read_text(encoding="utf-8"))
            markers = metadata.get("section_markers", [])
            if args.section is None and len(markers) != 1:
                raise SystemExit("Pass --section when project metadata does not declare exactly one marker")
            section = args.section or markers[0]
            output = process_audit_section(
                args.audit,
                repo_root=root,
                section_marker=section,
                output_dir=args.output,
            )
        print(output)
        return 0
    if args.command != "mc":
        return 2
    from antares_fd.config import load_project_config
    from antares_fd.simulation.scenarios import scenario_ids as configured_scenario_ids
    from antares_fd.simulation.uq_campaign import PROFILES, StochasticScenarioCampaign, campaign_path_for

    if args.profile not in PROFILES:
        parser.error(f"Unknown Monte Carlo profile {args.profile!r}; choose from {sorted(PROFILES)}")
    project_dir = _project(root, args.project)
    config = load_project_config(project_dir)
    mc_cfg = config.monte_carlo or {}
    seed = int(mc_cfg.get("random_seed", 42))
    scenarios = tuple(configured_scenario_ids(config)) if args.all_scenarios else ("nominal",)
    if args.resume:
        try:
            manifest_path = campaign_path_for(root, project_dir.name, args.resume) / "manifest.json"
        except ValueError as exc:
            parser.error(str(exc))
        if manifest_path.is_symlink():
            parser.error(f"Campaign manifest cannot be a symlink: {manifest_path}")
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

    previous = {key: os.environ.get(key) for key in MC_CAMPAIGN_ENVIRONMENT_KEYS}
    failed_scenario_id = None
    completed_scenario_ids: list[str] = []
    phase = "configuration_snapshot"
    try:
        # Sampling is a campaign operation. It runs once and is reused by all
        # scenarios, so paired deltas compare the same physical realization.
        registry_path = project_dir / "config" / "uncertainties.yaml"
        configuration_hashes = campaign.snapshot_config(project_dir)
        phase = "sample_preparation"
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

        os.environ.update({"ANTARES_CAMPAIGN_DIR": str(campaign.path), "ANTARES_CAMPAIGN_ACTIVE": "1", "ANTARES_CAMPAIGN_RUN_ID": campaign.campaign_id, "ANTARES_MC_TARGET": str(target), "ANTARES_MC_PROFILE": campaign.profile})
        if args.workers is not None:
            os.environ["ANTARES_MC_WORKERS"] = str(args.workers)
        os.environ["ANTARES_MC_MAX"] = str(campaign.max_samples if campaign.profile == "official" else target)

        phase = "scenario_execution"
        for scenario_id in scenarios:
            failed_scenario_id = scenario_id
            os.environ["ANTARES_MC_SCENARIO"] = scenario_id
            _run_script(project_dir)
            completed_scenario_ids.append(scenario_id)
            failed_scenario_id = None

        phase = "scenario_manifest_validation"
        scenario_summaries = campaign.scenario_manifests()
        scenario_statuses = [
            str(scenario_summaries.get(scenario_id, {}).get("status", "UNKNOWN"))
            for scenario_id in scenarios
        ]
        terminal_statuses = {"COMPLETE", "COMPLETE_NOT_CONVERGED", "PARTIAL"}
        if any(status not in terminal_statuses for status in scenario_statuses):
            raise RuntimeError(
                "Monte Carlo scenario runner returned without terminal manifests: "
                + ", ".join(f"{scenario}={status}" for scenario, status in zip(scenarios, scenario_statuses))
            )

        phase = "paired_comparison"
        pairing = campaign.finalize_paired_comparison() if args.all_scenarios else None
        if "PARTIAL" in scenario_statuses:
            campaign_status = "PARTIAL"
        elif "COMPLETE_NOT_CONVERGED" in scenario_statuses:
            campaign_status = "COMPLETE_NOT_CONVERGED"
        else:
            campaign_status = "COMPLETE"
        phase = "campaign_manifest_finalization"
        campaign.write_manifest(
            campaign_status,
            profile=campaign.profile,
            requested_samples=campaign.target_samples,
            min_samples=campaign.min_samples,
            max_samples=campaign.max_samples,
            sample_table_rows=int(len(samples)),
            configuration_hashes=configuration_hashes,
            paired_comparison=pairing,
            completed_scenario_ids=completed_scenario_ids,
            scenario_summaries=scenario_summaries,
        )
    except Exception as exc:
        failure = {"type": type(exc).__name__, "message": str(exc)}
        if failed_scenario_id is not None:
            child_campaign = campaign.scenario(failed_scenario_id)
            child_manifest_path = child_campaign.path / "manifest.json"
            child_manifest = {}
            if child_manifest_path.exists():
                try:
                    child_manifest = json.loads(child_manifest_path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    child_manifest = {}
            if child_manifest.get("status") not in {"COMPLETE", "COMPLETE_NOT_CONVERGED", "PARTIAL", "FAILED"}:
                child_campaign.write_manifest("FAILED", extra={"failure": failure, "failure_phase": phase})
        scenario_summaries = campaign.scenario_manifests()
        campaign.write_manifest(
            "PARTIAL" if completed_scenario_ids else "FAILED",
            completed_scenario_ids=completed_scenario_ids,
            failed_scenario_id=failed_scenario_id,
            failure_phase=phase,
            failure=failure,
            scenario_summaries=scenario_summaries,
        )
        raise
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
