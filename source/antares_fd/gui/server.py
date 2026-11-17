"""GUI local com API comum, arquivos contidos e proteção contra requisições externas."""
from __future__ import annotations

import base64
from functools import partial
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import logging
import mimetypes
from pathlib import Path
import secrets
from urllib.parse import unquote, urlsplit
import webbrowser

from antares_fd.application.projects import ConflictError, ProjectStore
from antares_fd.application.jobs import JobManager
from antares_fd.application.runs import list_runs, plain, read_run, run_path, verify_run
from antares_fd.application.validation import doctor, validate_project
from antares_fd.application.workspace import contained
from antares_fd.config.exceptions import ConfigurationError

LOGGER = logging.getLogger(__name__)
MAX_BODY = 24 * 1024 * 1024
STATIC = Path(__file__).with_name("static")


class LocalApplication:
    """Roteador da estação local; nenhuma rota aceita comandos de shell."""

    def __init__(self, root: Path):
        """Associe os serviços à raiz e crie um token efêmero por inicialização."""
        self.root = Path(root).resolve()
        self.projects = ProjectStore(self.root)
        self.jobs = JobManager(self.root)
        self.token = secrets.token_hex(32)

    def get(self, path: list[str]):
        """Retorne documentos de consulta, sempre pelo contrato de aplicação."""
        if path == ["health"]:
            return doctor(self.root)
        if path == ["projects"]:
            return self.projects.list()
        if path == ["datasets"]:
            from antares_fd.application.datasets import verify_catalog
            return verify_catalog(self.root)
        if len(path) >= 2 and path[0] == "projects":
            project = path[1]
            if len(path) == 2:
                return self.projects.read(project)
            if path[2:] == ["validation"]:
                return validate_project(self.root, project)
            if path[2:] == ["history"]:
                return self.projects.history(project)
            if path[2:] == ["runs"]:
                return list_runs(self.root, project)
            if len(path) == 4 and path[2] == "runs":
                return read_run(self.root, project, path[3])
        raise FileNotFoundError("Rota não encontrada.")

    def post(self, path: list[str], body: dict):
        """Execute mutações locais por serviços de projeto, jobs ou catálogo."""
        if path == ["projects"]:
            return self.projects.create(body.get("id"), body.get("source", "00_Copy_This"))
        if path == ["datasets"]:
            from antares_fd.application.datasets import register_dataset
            return register_dataset(self.root, body.get("id"), body.get("path"), kind=body.get("kind"),
                                    owner=body.get("owner"), source=body.get("source"), project=body.get("project"))
        if len(path) >= 3 and path[0] == "projects":
            project, action = path[1:3]
            if action == "save" and len(path) == 3:
                return self.projects.save(project, body.get("config"), body.get("revision"), body.get("note", "Edição pela GUI"))
            if action == "restore" and len(path) == 3:
                return self.projects.restore(project, body.get("target"), body.get("revision"))
            if action == "mass-properties" and len(path) == 3:
                from antares_fd.design.components import mass_properties
                return mass_properties(body)
            if action == "transform-components" and len(path) == 3:
                from antares_fd.design.variants import transform_components
                return transform_components(body.get("components"), swap=body.get("swap"), structural_factor=body.get("structural_factor", 1.0))
            if action == "import-openrocket" and len(path) == 3:
                from antares_fd.design.openrocket import import_design
                try:
                    content = base64.b64decode(body.get("content", ""), validate=True)
                except (ValueError, TypeError) as exc:
                    raise ValueError("Arquivo codificado inválido.") from exc
                return import_design(self.root, project, content, body.get("revision"))
            if action == "asset" and len(path) == 3:
                content = base64.b64decode(body.get("content", ""), validate=True)
                return self.projects.save(project, {}, body.get("revision"), "Inclusão de arquivo de entrada",
                                          assets={body.get("path", ""): content})
            if action == "runs":
                if len(path) == 3:
                    return self.jobs.start(project, body)
                if len(path) == 5 and path[4] == "cancel":
                    return self.jobs.cancel(project, path[3])
                if len(path) == 5 and path[4] == "verify":
                    return verify_run(self.root, project, path[3])
        raise FileNotFoundError("Rota não encontrada.")


class Handler(BaseHTTPRequestHandler):
    """HTTP de loopback: token, mesma origem, limite de corpo e escapes no frontend."""

    def __init__(self, *args, app: LocalApplication, **kwargs):
        """Injete o estado do servidor sem variáveis de aplicação globais."""
        self.app = app
        super().__init__(*args, **kwargs)

    def log_message(self, format, *args):
        """Registre somente a mensagem HTTP padrão, nunca os corpos ou o token."""
        LOGGER.info(format, *args)

    def _trusted(self, *, mutation=False):
        """Exija Host de loopback e, para mutações, token explícito e origem local."""
        port = self.server.server_port
        hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
        host = self.headers.get("Host", "")
        if host not in hosts:
            raise PermissionError("Este serviço atende apenas sua origem local.")
        origin = self.headers.get("Origin")
        if origin and origin not in {"http://" + name for name in hosts}:
            raise PermissionError("Origem não autorizada.")
        if mutation:
            provided = self.headers.get("X-Antares-Token", "")
        else:
            jar = cookies.SimpleCookie()
            try:
                jar.load(self.headers.get("Cookie", ""))
            except cookies.CookieError:
                raise PermissionError("Sessão inválida.") from None
            provided = self.headers.get("X-Antares-Token") or (jar["antares_session"].value if "antares_session" in jar else "")
        if not secrets.compare_digest(provided, self.app.token):
            raise PermissionError("Sessão expirada; recarregue a estação local.")

    def _send(self, data: bytes, content_type: str, status=200, *, session=False):
        """Envie resposta sem cache, com CSP restrita e cookie de sessão local."""
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        if session:
            self.send_header("Set-Cookie", f"antares_session={self.app.token}; HttpOnly; SameSite=Strict; Path=/")
        self.end_headers()
        self.wfile.write(data)

    def _json(self, value, status=200):
        """Serialize JSON com NaN proibido e mensagem de erro estruturada."""
        self._send(json.dumps(plain(value), ensure_ascii=False, default=str, allow_nan=False).encode(), "application/json; charset=utf-8", status)

    def do_GET(self):
        """Sirva assets próprios ou uma consulta autenticada de projeto/resultado."""
        try:
            url = urlsplit(self.path)
            if url.path in {"/", "/app.js", "/style.css"}:
                host = self.headers.get("Host", "")
                if host not in {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}:
                    raise PermissionError("Host não autorizado.")
                name = {"/": "index.html", "/app.js": "app.js", "/style.css": "style.css"}[url.path]
                content = (STATIC / name).read_bytes().replace(b"__ANTARES_TOKEN__", self.app.token.encode())
                self._send(content, mimetypes.guess_type(name)[0] + "; charset=utf-8", session=name == "index.html")
                return
            self._trusted()
            path = [unquote(part) for part in url.path.split("/") if part]
            if path[:2] == ["api", "documents"] and len(path) == 3 and path[2] in {"GUI.md", "ONBOARDING.md"}:
                document = contained(self.app.root, "docs/" + path[2], exists=True)
                self._send(document.read_bytes(), "text/plain; charset=utf-8")
                return
            if path[:2] == ["api", "artifacts"] and len(path) >= 5:
                project, run = path[2:4]
                project = self.app.projects.path(project).name
                root = run_path(self.app.root, project, run)
                artifact = contained(root, "/".join(path[4:]), exists=True)
                if (not artifact.is_file() or artifact.stat().st_size > 64 * 1024 * 1024
                        or artifact.suffix.lower() not in {".pdf", ".png", ".json", ".yaml", ".csv", ".parquet", ".kml", ".txt", ".log", ".nc", ".eng", ".rse", ".ork"}):
                    raise ValueError("Arquivo indisponível para visualização local.")
                self._send(artifact.read_bytes(), mimetypes.guess_type(artifact.name)[0] or "application/octet-stream")
                return
            if not path or path[0] != "api":
                raise FileNotFoundError("Rota não encontrada.")
            self._json(self.app.get(path[1:]))
        except Exception as exc:
            self._error(exc)

    def do_POST(self):
        """Valide autenticação e corpo limitado antes de despachar uma mutação."""
        try:
            self._trusted(mutation=True)
            if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                raise ValueError("Use Content-Type application/json.")
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= MAX_BODY:
                raise ValueError("Corpo vazio ou maior que 24 MiB.")
            body = json.loads(self.rfile.read(length))
            if not isinstance(body, dict):
                raise ValueError("O corpo deve ser um objeto JSON.")
            path = [unquote(part) for part in urlsplit(self.path).path.split("/") if part]
            if not path or path[0] != "api":
                raise FileNotFoundError("Rota não encontrada.")
            self._json(self.app.post(path[1:], body))
        except Exception as exc:
            self._error(exc)

    def _error(self, exc):
        """Converta erros conhecidos em HTTP sem expor traceback ao navegador."""
        if isinstance(exc, PermissionError):
            status = 403
        elif isinstance(exc, ConflictError):
            status = 409
        elif isinstance(exc, FileNotFoundError):
            status = 404
        elif isinstance(exc, (ValueError, TypeError, KeyError, ConfigurationError)):
            status = 400
        else:
            LOGGER.exception("Erro interno da GUI")
            status = 500
        self._json({"error": str(exc) if status != 500 else "Falha interna; consulte o terminal do servidor.", "type": type(exc).__name__}, status)


def make_server(root: Path, port: int = 0) -> ThreadingHTTPServer:
    """Crie o servidor exclusivamente em 127.0.0.1, aceitando porta efêmera para testes."""
    if isinstance(port, bool) or not isinstance(port, int) or not 0 <= port <= 65535:
        raise ValueError("Porta inválida.")
    app = LocalApplication(root)
    try:
        server = ThreadingHTTPServer(("127.0.0.1", port), partial(Handler, app=app))
    except OSError:
        app.jobs.close()
        raise
    server.app = app
    server.daemon_threads = True
    return server


def serve(root: Path, *, port: int = 8765, open_browser: bool = True):
    """Sirva a estação local até Ctrl+C e encerre workers ativos ao sair."""
    server = make_server(root, port)
    url = f"http://127.0.0.1:{server.server_port}"
    print("Antares — Estação de dinâmica de voo: " + url, flush=True)
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        pass
    finally:
        server.app.jobs.close()
        server.server_close()
