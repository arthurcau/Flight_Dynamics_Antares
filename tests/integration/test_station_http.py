"""Contrato HTTP, isolamento de arquivos e ciclo real de workers locais."""
import json
import threading
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from antares_fd.application.jobs import JobManager
from antares_fd.application.projects import ProjectStore
from antares_fd.application.runs import read_run
from antares_fd.gui.server import make_server


@pytest.fixture
def station(engineering_workspace):
    """Abra servidor efêmero e encerre todos os workers no fim de cada teste."""
    server = make_server(engineering_workspace)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server
    server.shutdown()
    server.app.jobs.close()
    server.server_close()
    thread.join(timeout=5)


def request(server, path, body=None, *, token=True, extra=None):
    """Retorne status e corpo de uma requisição real, inclusive respostas de erro."""
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-Antares-Token"] = server.app.token
    headers.update(extra or {})
    data = json.dumps(body).encode() if body is not None else None
    req = Request(f"http://127.0.0.1:{server.server_port}" + path, data=data, headers=headers)
    try:
        with urlopen(req, timeout=15) as response:
            return response.status, response.read()
    except HTTPError as exc:
        return exc.code, exc.read()


def test_session_origin_conflict_and_invalid_science(station):
    assert request(station, "/")[0] == 200
    assert request(station, "/api/projects", token=False)[0] == 403
    assert request(station, "/api/projects", extra={"Host": "external.example"})[0] == 403
    assert request(station, "/api/projects", {}, extra={"Origin": "https://external.example"})[0] == 403
    code, content = request(station, "/api/projects/reference")
    before = json.loads(content)
    assert code == 200
    data = {"revision": before["revision"], "config": before["config"], "note": "Contrato HTTP"}
    data["config"]["vehicle"]["vehicle"]["mass_properties"]["mass_without_motor"] += 1
    assert request(station, "/api/projects/reference/save", data)[0] == 200
    assert request(station, "/api/projects/reference/save", data)[0] == 409
    invalid = {"schema_version": 1, "coverage": "COMPLETE", "components": [{"id": "bad", "mass_kg": -1}]}
    assert request(station, "/api/projects/reference/mass-properties", invalid)[0] == 400
    assert request(station, "/api/projects/%2e%2e")[0] == 400


def test_assets_and_run_readers_reject_symlinks(station, tmp_path):
    root = station.app.root
    before = ProjectStore(root).read("reference")
    for path in ("", "../private.txt", "sources/../../private.txt"):
        assert request(station, "/api/projects/reference/asset", {"path": path, "content": "", "revision": before["revision"]})[0] == 400
    run = root / "results/reference/safe"
    run.mkdir(parents=True)
    private = tmp_path / "private.json"
    private.write_text('{"secret":true}')
    (run / "master_metrics.json").symlink_to(private)
    assert request(station, "/api/artifacts/reference/safe/master_metrics.json")[0] == 400
    assert request(station, "/api/projects/reference/runs/safe")[0] == 400
    assert request(station, "/api/projects/reference/runs/missing")[0] == 404


def test_real_worker_cancel_and_server_shutdown(station):
    manager = station.app.jobs
    request_data = {"mode": "monte_carlo", "samples": 20000, "workers": 2, "report": False}
    job = manager.start("reference", request_data)
    result = manager.cancel("reference", job["run_id"])
    assert result["state"]["status"] == "CANCELLED"
    assert manager.processes[("reference", job["run_id"])].poll() is not None
    second = manager.start("reference", request_data)
    manager.close()
    assert read_run(manager.root, "reference", second["run_id"])["state"]["status"] == "CANCELLED"
    assert all(process.poll() is not None for process in manager.processes.values())


def test_real_worker_completes_shared_cli(station):
    manager = station.app.jobs
    job = manager.start("reference", {"report": False})
    process = manager.processes[("reference", job["run_id"])]
    process.wait(timeout=90)
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        result = read_run(manager.root, "reference", job["run_id"])
        if result["state"]["status"] == "COMPLETE":
            break
        time.sleep(.05)
    assert result["state"]["status"] == "COMPLETE", result["log"]
    assert result["metrics"]["apogee_agl"] > 100


def test_server_recovers_abandoned_state(engineering_workspace):
    directory = engineering_workspace / "results/reference/orphan"
    directory.mkdir(parents=True)
    path = directory / "execution.json"
    path.write_text(json.dumps({"status": "RUNNING", "managed": True}))
    manager = JobManager(engineering_workspace)
    try:
        assert json.loads(path.read_text())["status"] == "INTERRUPTED"
    finally:
        manager.close()
