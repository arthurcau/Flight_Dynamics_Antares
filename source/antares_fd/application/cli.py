"""Comandos estáveis de projeto, validação, execução, datasets e GUI."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from antares_fd.config.exceptions import ConfigurationError


COMMANDS = {"project", "validate", "doctor", "run", "gui", "import-openrocket", "components", "datasets", "results"}


def register_commands(subparsers):
    """Registre a API de aplicação na mesma árvore argparse dos comandos legados."""
    project = subparsers.add_parser("project", help="criar, revisar e consultar projetos")
    project_sub = project.add_subparsers(dest="project_command", required=True)
    project_sub.add_parser("list")
    new = project_sub.add_parser("new")
    new.add_argument("project")
    new.add_argument("--from", dest="source", default="00_Copy_This")
    for name in ("show", "history"):
        project_sub.add_parser(name).add_argument("project")
    restore = project_sub.add_parser("restore")
    restore.add_argument("project")
    restore.add_argument("revision")
    restore.add_argument("--expected-revision", required=True)
    migrate = project_sub.add_parser("migrate")
    migrate.add_argument("project")
    migrate.add_argument("--apply", action="store_true")
    subparsers.add_parser("validate", help="validar sem consultar rede ou integrar").add_argument("project")
    subparsers.add_parser("doctor", help="inspecionar instalação sem alterar o ambiente")
    run = subparsers.add_parser("run", help="executar cenário pela mesma API da GUI")
    run.add_argument("project")
    run.add_argument("--scenario", default="nominal")
    run.add_argument("--mode", choices=("deterministic", "monte_carlo"), default="deterministic")
    run.add_argument("--profile", default="debug")
    run.add_argument("--samples", type=int)
    run.add_argument("--workers", type=int, default=1)
    run.add_argument("--no-report", action="store_true")
    run.add_argument("--run-id", help=argparse.SUPPRESS)
    run.add_argument("--managed", action="store_true", help=argparse.SUPPRESS)
    gui = subparsers.add_parser("gui", help="abrir a estação local no navegador")
    gui.add_argument("--port", type=int, default=8765)
    gui.add_argument("--no-browser", action="store_true")
    importer = subparsers.add_parser("import-openrocket", help="importar .ork com relatório de cobertura")
    importer.add_argument("project")
    importer.add_argument("file", type=Path)
    importer.add_argument("--expected-revision", required=True)
    components = subparsers.add_parser("components", help="calcular massa, CG e inércias do inventário")
    components.add_argument("project")
    datasets = subparsers.add_parser("datasets", help="catalogar e verificar evidências locais")
    dataset_sub = datasets.add_subparsers(dest="dataset_command", required=True)
    dataset_sub.add_parser("list")
    dataset_sub.add_parser("verify")
    add = dataset_sub.add_parser("add")
    add.add_argument("id")
    add.add_argument("path")
    add.add_argument("--kind", required=True)
    add.add_argument("--owner", required=True)
    add.add_argument("--source", required=True)
    add.add_argument("--project")
    results = subparsers.add_parser("results", help="consultar resultados sem reexecutar física")
    result_sub = results.add_subparsers(dest="result_command", required=True)
    result_sub.add_parser("list").add_argument("project")
    for action in ("show", "verify"):
        child = result_sub.add_parser(action)
        child.add_argument("project")
        child.add_argument("run_id")
    compare = result_sub.add_parser("compare")
    compare.add_argument("project")
    compare.add_argument("run_ids", nargs="+", help="IDs de execuções a comparar")


def handle_command(args, root: Path) -> int | None:
    """Despache comandos novos; None deixa o fluxo legado da CLI continuar.

    Erros de entrada geram JSON e código 2; validação e integridade usam código
    1 quando há pendências. Falhas científicas durante execução ficam no manifesto.
    """
    if args.command not in COMMANDS:
        return None
    from antares_fd.application.projects import ProjectStore
    from antares_fd.application.runs import plain
    try:
        result, code = _dispatch(args, root, ProjectStore), 0
        if isinstance(result, dict):
            if result.get("valid") is False or result.get("healthy") is False:
                code = 1
        print(json.dumps(plain(result), indent=2, ensure_ascii=False, default=str, allow_nan=False))
        return code
    except (ValueError, FileNotFoundError, FileExistsError, ConfigurationError) as exc:
        print(json.dumps({"error": str(exc), "type": type(exc).__name__}, ensure_ascii=False), file=sys.stderr)
        return 2


def _dispatch(args, root: Path, store_class):
    """Execute uma operação de aplicação sem duplicar lógica de cálculo ou persistência."""
    from antares_fd.application.validation import doctor, migrate_project, validate_project
    from antares_fd.application.runs import execute_run, list_runs, read_run, verify_run
    from antares_fd.application.datasets import read_catalog, register_dataset, verify_catalog
    if args.command == "doctor":
        return doctor(root)
    if args.command == "gui":
        from antares_fd.gui.server import serve
        serve(root, port=args.port, open_browser=not args.no_browser)
        return {"status": "closed"}
    store = store_class(root)
    if args.command == "project":
        if args.project_command == "list":
            return store.list()
        if args.project_command == "new":
            return store.create(args.project, args.source)
        if args.project_command == "show":
            return store.read(args.project)
        if args.project_command == "history":
            return store.history(args.project)
        if args.project_command == "restore":
            return store.restore(args.project, args.revision, args.expected_revision)
        return migrate_project(root, args.project, apply=args.apply)
    if args.command == "validate":
        return validate_project(root, args.project)
    if args.command == "run":
        return execute_run(root, args.project, scenario=args.scenario, mode=args.mode, profile=args.profile,
                           samples=args.samples, workers=args.workers, report=not args.no_report,
                           run_id=args.run_id, managed=args.managed)
    if args.command == "import-openrocket":
        from antares_fd.design.openrocket import import_design
        return import_design(root, args.project, args.file.read_bytes(), args.expected_revision)
    if args.command == "components":
        from antares_fd.design.components import mass_properties
        return mass_properties(store.read(args.project)["config"].get("components", {}))
    if args.command == "datasets":
        if args.dataset_command == "list":
            return read_catalog(root)
        if args.dataset_command == "verify":
            return verify_catalog(root)
        return register_dataset(root, args.id, args.path, kind=args.kind, owner=args.owner,
                                source=args.source, project=args.project)
    if args.result_command == "list":
        return list_runs(root, args.project)
    if args.result_command == "show":
        return read_run(root, args.project, args.run_id)
    if args.result_command == "verify":
        return verify_run(root, args.project, args.run_id)
    selected = [row for row in list_runs(root, args.project) if row["run_id"] in args.run_ids]
    if len(selected) != len(set(args.run_ids)):
        raise ValueError("Uma das execuções selecionadas não foi encontrada.")
    revisions = {row.get("revision") for row in selected}
    return {"runs": selected, "same_revision": len(revisions) == 1 if None not in revisions and revisions else None,
            "notice": "Comparação descritiva; verificar cenários, unidades e hipóteses antes de atribuir causas."}
