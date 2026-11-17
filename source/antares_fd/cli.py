"""Command line entry point for Antares Flight Dynamics campaigns."""

from __future__ import annotations

import argparse
import os
from pathlib import Path


MC_CAMPAIGN_ENVIRONMENT_KEYS = (
    "ANTARES_CAMPAIGN_DIR", "ANTARES_CAMPAIGN_ACTIVE", "ANTARES_CAMPAIGN_RUN_ID",
    "ANTARES_COMPACT_OUTPUTS", "ANTARES_CURRENT_SCENARIO", "ANTARES_MC_SCENARIO",
    "ANTARES_MC_TARGET", "ANTARES_MC_PROFILE", "ANTARES_MC_WORKERS", "ANTARES_MC_MAX",
)


def _project(root: Path, name: str) -> Path:
    """Localize um projeto pelo nome na raiz informada.

    Resolve os candidatos aceitos e exige um diretório existente; retorna Path
    ou lança erro de seleção antes de iniciar qualquer simulação.
    """
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
    """Execute o motor Monte Carlo comum para a entrada de compatibilidade mc.

    O nome privado é mantido para extensões existentes. Carrega apenas YAML,
    sem executar scripts do projeto; novos comandos run congelam as entradas.
    """
    from antares_fd.config import load_project_config
    from antares_fd.simulation.monte_carlo_failure import execute_monte_carlo
    execute_monte_carlo(load_project_config(project_dir), project_dir)


def main(argv: list[str] | None = None) -> int:
    """Execute a interface de linha de comando do Antares Flight Dynamics.

    Interpreta argv com argparse e despacha campanhas, relatórios, telemetria
    e reconstrução. Valida caminhos e opções antes de executar o fluxo escolhido;
    restaura variáveis de ambiente temporárias e retorna o código de saída.
    Comandos de análise leem artefatos; comandos de simulação geram novos resultados.
    """
    parser = argparse.ArgumentParser(prog="antares-fd")
    parser.add_argument("--repo-root", type=Path, help="repository containing projects/ and results/ (or set ANTARES_FD_ROOT)")
    subparsers = parser.add_subparsers(dest="command", required=True)
    mc = subparsers.add_parser("mc", help="run a resumable Monte Carlo campaign")
    mc.add_argument("project")
    mc.add_argument("--profile", default="development")
    mc.add_argument("--resume", metavar="CAMPAIGN_ID")
    mc.add_argument("--workers", type=int)
    mc.add_argument("--all-scenarios", action="store_true", help="run configured stochastic scenario campaigns")
    mc.add_argument("--samples", type=int, help="explicit target (1–20000)")
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
    from antares_fd.application.cli import register_commands, handle_command
    register_commands(subparsers)
    args = parser.parse_args(argv)
    root = Path(args.repo_root or os.environ.get("ANTARES_FD_ROOT") or Path(__file__).resolve().parents[2]).resolve()
    handled = handle_command(args, root)
    if handled is not None:
        return handled
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
    from antares_fd.application.monte_carlo import run_campaign
    return run_campaign(root, _project(root, args.project), args, _run_script, parser)


if __name__ == "__main__":
    raise SystemExit(main())
