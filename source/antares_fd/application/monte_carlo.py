"""Controlador Monte Carlo compartilhado; mantém o contrato legado da CLI."""
from __future__ import annotations

import json
import os
from pathlib import Path

MC_CAMPAIGN_ENVIRONMENT_KEYS = (
    "ANTARES_CAMPAIGN_DIR", "ANTARES_CAMPAIGN_ACTIVE", "ANTARES_CAMPAIGN_RUN_ID",
    "ANTARES_COMPACT_OUTPUTS", "ANTARES_CURRENT_SCENARIO", "ANTARES_MC_SCENARIO",
    "ANTARES_MC_TARGET", "ANTARES_MC_PROFILE", "ANTARES_MC_WORKERS", "ANTARES_MC_MAX",
)


def run_campaign(root, project_dir, args, runner, parser, *, model_project_dir=None):
    """Execute uma campanha canônica e restaure controles em todos os caminhos.

    runner seleciona o mesmo motor compartilhado para CLI/GUI; o callback legado
    continua instrumentável. model_project_dir permite entradas congeladas sem
    alterar a raiz de armazenamento. Falhas preservam manifestos terminais.
    """
    from antares_fd.config import load_project_config
    from antares_fd.simulation.scenarios import scenario_ids as configured_scenario_ids
    from antares_fd.simulation.uq_campaign import PROFILES, StochasticScenarioCampaign, campaign_path_for

    if args.profile not in PROFILES:
        parser.error(f"Unknown Monte Carlo profile {args.profile!r}; choose from {sorted(PROFILES)}")
    model_project_dir = Path(model_project_dir or project_dir)
    config = load_project_config(model_project_dir)
    mc_cfg = config.monte_carlo or {}
    seed = int(mc_cfg.get("random_seed", 42))
    scenarios = tuple(configured_scenario_ids(config)) if args.all_scenarios else (getattr(args, "scenario", "nominal"),)
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
        requested = getattr(args, "samples", None)
        target = int(requested if requested is not None else PROFILES[args.profile].get("target_samples", mc_cfg.get("num_simulations", 10)))
        if target < 1 or target > 20000:
            parser.error("A quantidade deve estar entre 1 e 20000 casos.")
        campaign = StochasticScenarioCampaign(
            project_dir.name, root, seed, args.profile,
            campaign_id=getattr(args, "campaign_id", None),
            config={"target_samples": target, "min_samples": target, "max_samples": max(target, int(PROFILES[args.profile].get("max_samples", target)))},
            scenario_ids=scenarios,
        )

    previous = {key: os.environ.get(key) for key in MC_CAMPAIGN_ENVIRONMENT_KEYS}
    failed_scenario_id = None
    completed_scenario_ids: list[str] = []
    phase = "configuration_snapshot"
    try:
        # Sampling is a campaign operation. It runs once and is reused by all
        # scenarios, so paired deltas compare the same physical realization.
        registry_path = model_project_dir / "config" / "uncertainties.yaml"
        configuration_hashes = campaign.snapshot_config(model_project_dir)
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
            runner(project_dir)
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

