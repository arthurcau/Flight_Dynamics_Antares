"""Command line entry point for Antares Flight Dynamics campaigns."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path

from antares_fd.config import load_project_config
from antares_fd.simulation.uq_campaign import MonteCarloCampaign, PROFILES


def _project(root: Path, name: str) -> Path:
    candidates = [path for path in (root / "projects").iterdir() if path.is_dir() and path.name.lower() == name.lower()]
    if not candidates:
        raise SystemExit(f"Project not found below {root / 'projects'}: {name}")
    return candidates[0]


def _run_script(project_dir: Path) -> None:
    script = project_dir / "simulations" / "monte_carlo_failure.py"
    if not script.exists():
        script = project_dir / "simulations" / "monte_carlo.py"
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
    archive = subparsers.add_parser("archive", help="archive a completed campaign")
    archive.add_argument("campaign_id")
    archive.add_argument("--project", default="neblina_1")
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    if args.command == "archive":
        campaign = MonteCarloCampaign(args.project, root, campaign_id=args.campaign_id)
        print(campaign.archive())
        return 0
    if args.command != "mc":
        return 2
    project_dir = _project(root, args.project)
    config = load_project_config(project_dir)
    mc_cfg = config.monte_carlo or {}
    seed = int(mc_cfg.get("random_seed", 42))
    if args.resume:
        campaign = MonteCarloCampaign(project_dir.name, root, seed, args.profile, args.resume)
        manifest_path = campaign.path / "manifest.json"
        if not manifest_path.exists():
            raise SystemExit(f"Campaign manifest not found: {manifest_path}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        seed = int(manifest.get("master_seed", seed))
        profile = manifest.get("profile", args.profile)
        # Rehydrate the campaign limits from the immutable manifest. The
        # sample table can intentionally be larger than the initial target
        # (official campaigns reserve up to 20k rows), so sample_table_rows
        # must never be used as the resume target.
        requested = int(manifest.get("requested_samples", manifest.get("sample_table_rows", 0)))
        if requested < 1:
            raise SystemExit(f"Campaign manifest has no valid requested sample count: {manifest_path}")
        campaign = MonteCarloCampaign(
            project_dir.name,
            root,
            seed,
            profile,
            args.resume,
            config={
                "target_samples": requested,
                "min_samples": int(manifest.get("min_samples", requested)),
                "max_samples": int(manifest.get("max_samples", requested)),
            },
        )
        target = requested
    else:
        target = int(PROFILES[args.profile].get("target_samples", mc_cfg.get("num_simulations", 10)))
        campaign = MonteCarloCampaign(project_dir.name, root, seed, args.profile, config={"target_samples": target, "min_samples": target, "max_samples": target})

    previous = {key: os.environ.get(key) for key in ("ANTARES_CAMPAIGN_DIR", "ANTARES_CAMPAIGN_ACTIVE", "ANTARES_CAMPAIGN_RUN_ID", "ANTARES_MC_TARGET", "ANTARES_MC_PROFILE", "ANTARES_MC_WORKERS", "ANTARES_MC_MAX")}
    os.environ.update({"ANTARES_CAMPAIGN_DIR": str(campaign.path), "ANTARES_CAMPAIGN_ACTIVE": "1", "ANTARES_CAMPAIGN_RUN_ID": campaign.campaign_id, "ANTARES_MC_TARGET": str(target), "ANTARES_MC_PROFILE": campaign.profile})
    if args.workers is not None:
        os.environ["ANTARES_MC_WORKERS"] = str(args.workers)
    os.environ["ANTARES_MC_MAX"] = str(campaign.max_samples if campaign.profile == "official" else target)
    try:
        _run_script(project_dir)
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
