"""Supervisor local: cada simulação roda em subprocesso com cancelamento de grupo."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading

from antares_fd.application.projects import ProjectStore
from antares_fd.application.runs import TERMINAL, new_run_id, read_run, run_path
from antares_fd.application.validation import validate_project
from antares_fd.application.workspace import contained, workspace_lock
from antares_fd.storage import write_json_atomic


class JobManager:
    """Controle jobs deste servidor sem compartilhar variáveis globais de campanha."""

    def __init__(self, root: Path, max_jobs: int = 2):
        """Configure capacidade limitada e recupere estados interrompidos do servidor anterior."""
        self.root = Path(root).resolve()
        self.max_jobs = max_jobs
        self.processes = {}
        self.lock = threading.RLock()
        self._lease = workspace_lock(self.root, "gui_server")
        self._lease.__enter__()
        try:
            self._recover()
        except Exception:
            self._lease.__exit__(*sys.exc_info())
            raise

    def _recover(self):
        """Marque jobs órfãos como INTERRUPTED sem tentar matar um PID reutilizado."""
        results = contained(self.root, "results")
        if not results.exists():
            return
        for candidate in results.glob("*/*/execution.json"):
            try:
                path = contained(results, candidate.relative_to(results), exists=True)
                state = json.loads(path.read_text(encoding="utf-8"))
                if state.get("status") in {"RUNNING", "QUEUED"} and state.get("managed"):
                    state.update(status="INTERRUPTED", phase="server_restart")
                    write_json_atomic(state, path)
            except (OSError, ValueError):
                continue

    def start(self, project_id: str, request: dict) -> dict:
        """Valide, crie um job e inicie a CLI comum sem shell e sem argumentos arbitrários."""
        allowed = {"scenario", "mode", "profile", "samples", "workers", "report"}
        if not isinstance(request, dict) or set(request) - allowed:
            raise ValueError("Parâmetros de execução desconhecidos.")
        if not validate_project(self.root, project_id)["valid"]:
            raise ValueError("Corrija os erros de validação antes de executar.")
        from antares_fd.simulation.scenarios import SCENARIOS
        from antares_fd.simulation.uq_campaign import PROFILES
        if request.get("scenario", "nominal") not in SCENARIOS or request.get("mode", "deterministic") not in {"deterministic", "monte_carlo"} or request.get("profile", "debug") not in PROFILES:
            raise ValueError("Cenário, modo ou perfil desconhecido.")
        workers, samples = request.get("workers", 1), request.get("samples")
        if isinstance(workers, bool) or not isinstance(workers, int) or not 1 <= workers <= 64:
            raise ValueError("workers deve estar entre 1 e 64.")
        if samples is not None and (isinstance(samples, bool) or not isinstance(samples, int) or not 1 <= samples <= 20000):
            raise ValueError("samples deve estar entre 1 e 20000.")
        with self.lock:
            if sum(process.poll() is None for process in self.processes.values()) >= self.max_jobs:
                raise ValueError("Capacidade local atingida. Aguarde ou cancele uma execução.")
            project_id = ProjectStore(self.root).path(project_id).name
            run_id = new_run_id()
            path = run_path(self.root, project_id, run_id)
            path.mkdir(parents=True, exist_ok=False)
            state = {"schema_version": 1, "project": project_id, "run_id": run_id,
                     "managed": True, "status": "QUEUED", "phase": "queued", "progress": 0,
                     "created_utc": datetime.now(timezone.utc).isoformat(), "request": request}
            write_json_atomic(state, path / "execution.json")
            command = [sys.executable, "-u", "-m", "antares_fd.cli", "--repo-root", str(self.root),
                       "run", project_id, "--run-id", run_id, "--managed"]
            for option in ("scenario", "mode", "profile", "samples", "workers"):
                if request.get(option) is not None:
                    command += ["--" + option, str(request[option])]
            if request.get("report", True) is False:
                command.append("--no-report")
            environment = dict(os.environ, MPLBACKEND="Agg", PYTHONUNBUFFERED="1", PYTHONIOENCODING="utf-8")
            for key in list(environment):
                if key.startswith("ANTARES_"):
                    del environment[key]
            source = str(Path(__file__).resolve().parents[2])
            environment["PYTHONPATH"] = os.pathsep.join([source, str(self.root), environment.get("PYTHONPATH", "")])
            kwargs = {"start_new_session": True} if os.name != "nt" else {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
            try:
                with (path / "job.log").open("wb") as log:
                    process = subprocess.Popen(command, cwd=self.root, env=environment,
                                               stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, **kwargs)
            except OSError as exc:
                state.update(status="FAILED", error={"type": type(exc).__name__, "message": str(exc)})
                write_json_atomic(state, path / "execution.json")
                raise
            self.processes[(project_id, run_id)] = process
            threading.Thread(target=self._watch, args=(project_id, run_id, process), daemon=True).start()
            return state

    def _watch(self, project_id: str, run_id: str, process):
        """Feche o estado de subprocessos que terminam antes de publicar o manifesto final."""
        code = process.wait()
        with self.lock:
            path = run_path(self.root, project_id, run_id) / "execution.json"
            try:
                state = json.loads(path.read_text(encoding="utf-8"))
                if state.get("status") not in TERMINAL:
                    state.update(status="FAILED", phase="worker_exit", exit_code=code,
                                 error={"type": "WorkerExit", "message": "Worker terminou sem resultado terminal; consulte o log."})
                    write_json_atomic(state, path)
            except (OSError, ValueError):
                pass

    def cancel(self, project_id: str, run_id: str) -> dict:
        """Encerre o grupo do worker local e publique CANCELLED, sem remover resultados parciais."""
        with self.lock:
            process = self.processes.get((project_id, run_id))
            if process is None or process.poll() is not None:
                raise ValueError("Esta execução não está ativa neste servidor.")
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], check=False, capture_output=True)
            else:
                os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                if os.name != "nt":
                    os.killpg(process.pid, signal.SIGKILL)
                else:
                    process.kill()
                process.wait(timeout=5)
            path = run_path(self.root, project_id, run_id) / "execution.json"
            state = json.loads(path.read_text(encoding="utf-8"))
            state.update(status="CANCELLED", phase="cancelled", completed_utc=datetime.now(timezone.utc).isoformat())
            write_json_atomic(state, path)
        return read_run(self.root, project_id, run_id)

    def close(self):
        """Cancele os workers ativos ao encerrar a aplicação local."""
        for (project, run), process in list(self.processes.items()):
            if process.poll() is None:
                try:
                    self.cancel(project, run)
                except (OSError, ValueError):
                    continue
        if self._lease is not None:
            self._lease.__exit__(None, None, None)
            self._lease = None
