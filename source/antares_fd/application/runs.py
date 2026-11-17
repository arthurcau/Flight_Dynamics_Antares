"""Execução isolada, snapshots verificáveis e consulta de artefatos de campanha."""
from __future__ import annotations

import dataclasses
from datetime import datetime, timezone
import json
import importlib.metadata
import platform
from pathlib import Path
import shutil
from types import SimpleNamespace
import uuid

import numpy as np
import pandas as pd

from antares_fd.application.projects import ProjectStore, input_files, project_revision
from antares_fd.application.validation import validate_project
from antares_fd.application.workspace import contained, identifier, sha256, workspace_lock
from antares_fd.storage import write_json_atomic, write_parquet_atomic
from antares_fd import __version__

TERMINAL = {"COMPLETE", "COMPLETE_NOT_CONVERGED", "PARTIAL", "FAILED", "CANCELLED", "INTERRUPTED"}
SCALAR_METRICS = ("apogee_agl", "max_mach", "rail_exit_velocity", "touchdown_velocity", "total_impulse", "flight_duration")


def new_run_id() -> str:
    """Crie um ID UTC com sufixo aleatório, independente de nomes de arquivos externos."""
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]


def run_path(root: Path, project: str, run_id: str) -> Path:
    """Resolva um diretório de execução com identificadores contidos em results/."""
    return contained(root, f"results/{identifier(project)}/{identifier(run_id)}")


def plain(value):
    """Converta dataclasses/NumPy em JSON, preservando ausências como null.

    Valores NaN de métricas não avaliadas viram null apenas na apresentação;
    os artefatos tabulares mantêm seus indicadores de indisponibilidade.
    """
    if dataclasses.is_dataclass(value):
        return {field.name: plain(getattr(value, field.name)) for field in dataclasses.fields(value)}
    if isinstance(value, dict):
        return {key: plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, np.ndarray)):
        return [plain(item) for item in value]
    if isinstance(value, np.generic):
        return plain(value.item())
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def snapshot_project(root: Path, project_id: str, destination: Path) -> dict:
    """Congele entradas em uma cópia autocontida e verifique hashes após copiar.

    O lock é liberado antes da integração. Edições posteriores não alteram o
    modelo congelado usado pelo worker; fontes originais não são reescritas.
    """
    store = ProjectStore(root)
    with workspace_lock(root, project_id):
        project = store.path(project_id)
        before = project_revision(project)
        hashes = {}
        destination.mkdir(parents=True, exist_ok=False)
        for source in input_files(project):
            relative = source.relative_to(project)
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            digest = sha256(source)
            shutil.copy2(source, target)
            if sha256(target) != digest or sha256(source) != digest:
                raise ValueError("Entrada alterada durante o snapshot: " + str(relative))
            hashes[relative.as_posix()] = digest
        if project_revision(project) != before:
            raise ValueError("Projeto mudou durante o snapshot.")
    return {"revision": before, "files": hashes}


def _deterministic(snapshot: Path, output: Path, scenario: str, report: bool):
    """Integre um cenário com os construtores comuns e grave métricas e séries.

    A exportação usa apenas dados desse Flight; não consulta mapas externos.
    O PDF é opcional e seu erro não transforma uma integração em sucesso total.
    """
    from antares_fd.config import load_project_config
    from antares_fd.design.components import resolve_vehicle_mass
    from antares_fd.analysis.metrics import extract_flight_metrics
    from antares_fd.simulation.orchestrator import execute_scenario
    from antares_fd.simulation.scenarios import apply_scenario
    config = load_project_config(snapshot)
    config.vehicle = resolve_vehicle_mass(config.vehicle)
    flight = execute_scenario(config, snapshot, scenario_id=scenario, print_summary=False)
    from antares_fd.environment.archive import archive_environment
    archive_environment(flight.env, output)
    metrics = extract_flight_metrics(flight, config=apply_scenario(config, scenario), project_dir=snapshot)
    serialized = plain(metrics)
    series = serialized.pop("timeseries")
    atmosphere = serialized.pop("atmosphere")
    write_json_atomic(serialized, output / "master_metrics.json")
    write_parquet_atomic(pd.DataFrame(series), output / "timeseries.parquet")
    arrays = {key: value for key, value in atmosphere.items() if isinstance(value, list)}
    lengths = {len(value) for value in arrays.values()}
    if len(lengths) == 1:
        write_parquet_atomic(pd.DataFrame(arrays), output / "atmosphere.parquet")
    write_json_atomic({key: value for key, value in atmosphere.items() if not isinstance(value, list)}, output / "atmosphere_metadata.json")
    from rocketpy.simulation.flight_data_exporter import FlightDataExporter
    FlightDataExporter(flight).export_kml(file_name=str(output / "trajectory.kml"), altitude_mode="absolute")
    if report:
        from antares_fd.reporting.pdf_report import FlightDynamicsReport
        FlightDynamicsReport(flight=flight, config=config, project_dir=snapshot, run_id=output.name).generate(output / "flight_dynamics_report.pdf")
    return metrics



def software_provenance(root: Path) -> dict:
    """Registre intérprete, bibliotecas e lock utilizado, sem alegar identidade entre CPUs."""
    from antares_fd.analysis.provenance import get_git_provenance
    packages = {}
    for name in ("rocketpy", "numpy", "scipy", "pandas", "pyarrow", "PyYAML", "matplotlib", "multiprocess", "netCDF4"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    lock = Path(root) / ("requirements-py" + platform.python_version_tuple()[0] + platform.python_version_tuple()[1] + ".lock")
    return {"version": __version__, "python": platform.python_version(), "platform": platform.platform(),
            "packages": packages, "git": get_git_provenance(root),
            "lockfile": {"path": lock.name, "sha256": sha256(lock)} if lock.exists() else None}


def execute_run(root: Path, project_id: str, *, scenario: str = "nominal", mode: str = "deterministic",
                profile: str = "debug", samples: int | None = None, workers: int = 1,
                report: bool = True, run_id: str | None = None, managed: bool = False) -> dict:
    """Execute CLI/GUI por um contrato comum, com estados persistidos e entradas congeladas.

    A GUI chama este serviço em subprocesso separado. Validação acontece antes
    da aquisição meteorológica; exceções registram FAILED e são propagadas.
    """
    from antares_fd.simulation.scenarios import SCENARIOS
    from antares_fd.simulation.uq_campaign import PROFILES
    if scenario not in SCENARIOS or mode not in {"deterministic", "monte_carlo"} or profile not in PROFILES:
        raise ValueError("Cenário, modo ou perfil desconhecido.")
    if isinstance(workers, bool) or not isinstance(workers, int) or not 1 <= workers <= 64:
        raise ValueError("workers deve estar entre 1 e 64.")
    if samples is not None and (isinstance(samples, bool) or not isinstance(samples, int) or not 1 <= samples <= 20000):
        raise ValueError("samples deve estar entre 1 e 20000.")
    validation = validate_project(root, project_id)
    if not validation["valid"]:
        raise ValueError("Projeto inválido: " + "; ".join(row["path"] + ": " + row["message"] for row in validation["issues"] if row["severity"] == "error"))
    store = ProjectStore(root)
    project_id = store.path(project_id).name
    run_id = run_id or new_run_id()
    output = run_path(root, project_id, run_id)
    if output.exists() and not managed:
        raise FileExistsError("A execução já existe.")
    if managed and output.exists():
        previous = json.loads((output / "execution.json").read_text(encoding="utf-8"))
        if previous.get("status") != "QUEUED":
            raise ValueError("A execução gerenciada não está na fila.")
    output.mkdir(parents=True, exist_ok=managed)
    state = {"schema_version": 1, "run_id": run_id, "project": project_id, "status": "RUNNING",
             "mode": mode, "scenario": scenario, "profile": profile, "samples": samples,
             "workers": workers, "managed": managed, "created_utc": datetime.now(timezone.utc).isoformat(), "progress": 0,
             "validation": validation, "software_version": __version__}
    def phase(name, progress):
        """Persista progresso por fase e emita um registro legível pelo supervisor."""
        state.update(phase=name, progress=progress)
        write_json_atomic(state, output / "execution.json")
        print("ANTARES_PROGRESS " + json.dumps({"phase": name, "progress": progress}), flush=True)
    try:
        phase("snapshot", 5)
        snapshot = output / "inputs" / "projects" / project_id
        state["inputs"] = snapshot_project(root, project_id, snapshot)
        frozen_validation = validate_project(snapshot.parents[1], project_id)
        if not frozen_validation["valid"]:
            raise ValueError("As entradas congeladas não passaram na validação; revise o projeto.")
        state["validation"] = frozen_validation
        write_json_atomic(software_provenance(root), output / "software_provenance.json")
        phase("simulation", 15)
        if mode == "deterministic":
            _deterministic(snapshot, output, scenario, report)
            status = "COMPLETE"
        else:
            import argparse
            from antares_fd.application.monte_carlo import run_campaign
            from antares_fd.simulation.monte_carlo_failure import execute_monte_carlo
            from antares_fd.config import load_project_config
            args = SimpleNamespace(project=project_id, profile=profile, samples=samples, workers=workers,
                                   scenario=scenario, all_scenarios=False, resume=None, campaign_id=run_id)
            def runner(_project):
                """Execute o único motor estocástico com a entrada congelada e raiz explícita."""
                return execute_monte_carlo(load_project_config(snapshot), snapshot, workspace_root=root, archive_atmospheres=True)
            run_campaign(root, store.path(project_id), args, runner, argparse.ArgumentParser(), model_project_dir=snapshot)
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            status = manifest["status"]
        phase("artifacts", 95)
        artifacts = {path.relative_to(output).as_posix(): sha256(path)
                     for path in output.rglob("*") if path.is_file() and path.name not in {"job.log", "execution.json", "artifact_manifest.json"}}
        write_json_atomic({"schema_version": 1, "files": artifacts}, output / "artifact_manifest.json")
        state.update(status=status, completed_utc=datetime.now(timezone.utc).isoformat())
        phase("finished", 100)
    except BaseException as exc:
        state.update(status="CANCELLED" if isinstance(exc, KeyboardInterrupt) else "FAILED",
                     error={"type": type(exc).__name__, "message": str(exc)}, completed_utc=datetime.now(timezone.utc).isoformat())
        write_json_atomic(state, output / "execution.json")
        raise
    return state


def list_runs(root: Path, project_id: str) -> list[dict]:
    """Liste execuções novas e legadas, mantendo status e ausência de métricas explícitos."""
    project = ProjectStore(root).path(project_id)
    directory = contained(root, "results/" + project.name)
    rows = []
    if not directory.exists():
        return rows
    for path in sorted(directory.iterdir(), reverse=True):
        if path.is_symlink() or not path.is_dir():
            continue
        try:
            metadata_path = contained(path, "execution.json")
            metadata = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.exists() else {}
            metrics_path = contained(path, "master_metrics.json")
            if not metrics_path.exists():
                metrics_path = contained(path, "reports/master_metrics.json")
            metrics = json.loads(metrics_path.read_text(encoding="utf-8")) if metrics_path.exists() else {}
            if metadata.get("mode") == "monte_carlo":
                metrics = _mc_summary(path, metadata).get("medians", {})
            rows.append({"run_id": path.name, "status": metadata.get("status", "LEGACY"),
                         "mode": metadata.get("mode"), "scenario": metadata.get("scenario"),
                         "revision": metadata.get("inputs", {}).get("revision"),
                         "metrics": {key: metrics.get(key) for key in SCALAR_METRICS}})
        except (OSError, ValueError) as exc:
            rows.append({"run_id": path.name, "status": "INVALID", "error": str(exc), "metrics": {}})
    return rows


def _mc_summary(path: Path, state: dict) -> dict:
    """Leia distribuições canônicas sem confundir mediana, voo único e apogeu ASL.

    A visualização reduz nuvens/ECDF a até 1000 pontos; tabelas completas
    permanecem nos artefatos. Distribuições representam apenas casos válidos.
    """
    scenario = identifier(state.get("scenario", "nominal"))
    base = contained(path, "scenarios/" + scenario)
    result = {"scenario": scenario, "case_count": 0, "medians": {}}
    for name in ("statistics", "ecdf", "convergence", "sensitivity", "outputs"):
        target = contained(base, name + ".parquet")
        if not target.exists():
            result[name] = []
            continue
        frame = pd.read_parquet(target)
        if name == "outputs":
            result["case_count"] = len(frame)
            keys = [key for key in ("case_id", "landing_east", "landing_north") if key in frame]
            result["landing"] = plain(frame[keys].iloc[::max(1, (len(frame) + 999) // 1000)].to_dict("records"))
            result["medians"] = {key: float(frame[key].median()) for key in SCALAR_METRICS if key in frame and frame[key].notna().any()}
        elif name == "ecdf" and not frame.empty:
            reduced = pd.concat([group.iloc[::max(1, (len(group) + 999) // 1000)] for _, group in frame.groupby("metric")])
            result[name] = plain(reduced.to_dict("records"))
        else:
            result[name] = plain(frame.head(2000).to_dict("records"))
    return result


def read_run(root: Path, project_id: str, run_id: str) -> dict:
    """Leia estado, métricas e série reduzida para visualização, sem reexecutar física."""
    project_id = ProjectStore(root).path(project_id).name
    path = run_path(root, project_id, run_id)
    if not path.is_dir():
        raise FileNotFoundError("Execução não encontrada.")
    state_path = contained(path, "execution.json")
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {"status": "LEGACY"}
    metrics_path = contained(path, "master_metrics.json")
    if not metrics_path.exists():
        metrics_path = contained(path, "reports/master_metrics.json")
    metrics = json.loads(metrics_path.read_text(encoding="utf-8")) if metrics_path.exists() else {}
    series = {}
    series_path = contained(path, "timeseries.parquet")
    if series_path.exists():
        frame = pd.read_parquet(series_path)
        frame = frame.iloc[::max(1, len(frame) // 1000)]
        series = plain(frame.to_dict("list"))
    artifacts = [item.relative_to(path).as_posix() for item in sorted(path.rglob("*"))
                 if item.is_file() and not item.is_symlink() and "inputs" not in item.relative_to(path).parts]
    log_path = contained(path, "job.log")
    log = ""
    if log_path.exists():
        with log_path.open("rb") as stream:
            stream.seek(max(0, log_path.stat().st_size - 32000))
            log = stream.read().decode("utf-8", errors="replace")
    campaign = _mc_summary(path, state) if state.get("mode") == "monte_carlo" else None
    if campaign is not None:
        metrics = campaign["medians"]
    return {"run_id": run_id, "state": state, "metrics": metrics, "series": series, "campaign": campaign,
            "artifacts": artifacts, "log": log}


def verify_run(root: Path, project_id: str, run_id: str) -> dict:
    """Verifique cada hash registrado e identifique arquivos ausentes ou alterados."""
    path = run_path(root, ProjectStore(root).path(project_id).name, run_id)
    manifest = json.loads(contained(path, "artifact_manifest.json", exists=True).read_text(encoding="utf-8"))
    errors = []
    for relative, expected in manifest["files"].items():
        try:
            if sha256(contained(path, relative, exists=True)) != expected:
                errors.append(relative)
        except (OSError, ValueError):
            errors.append(relative)
    return {"valid": not errors, "checked": len(manifest["files"]), "invalid": errors}
