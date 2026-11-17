"""Caminhos contidos no workspace, hashes e exclusão mútua entre processos."""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import re
import time


class ConflictError(ValueError):
    """Uma revisão foi alterada desde a leitura ou um identificador já existe."""


def identifier(value: str) -> str:
    """Valide identificadores de projeto, execução e dataset sem separadores.

    Aceita até 80 letras ASCII, números, hífen ou underscore; retorna o texto.
    A restrição impede que um identificador seja interpretado como caminho.
    """
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", value):
        raise ValueError("Identificador: use 1–80 letras, números, hífen ou underscore.")
    return value


def contained(root: Path, relative: str | Path, *, exists: bool = False) -> Path:
    """Resolva um caminho relativo dentro de root e rejeite links simbólicos.

    Verifica contenção antes e depois da resolução e cada componente existente.
    Não cria arquivos; exists=True exige que o destino já exista.
    """
    root = Path(root).absolute()
    relative = Path(relative)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("O caminho deve ser relativo e permanecer no workspace.")
    if root.is_symlink():
        raise ValueError("A raiz não pode ser um link simbólico.")
    candidate = root
    for part in relative.parts:
        candidate /= part
        if candidate.is_symlink():
            raise ValueError("Links simbólicos não são aceitos neste caminho.")
    resolved = candidate.resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError("Caminho fora do workspace.")
    if exists and not resolved.exists():
        raise FileNotFoundError(str(relative))
    return resolved


def sha256(path: Path) -> str:
    """Calcule SHA-256 em blocos de 1 MiB sem alterar o arquivo de origem."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


@contextmanager
def workspace_lock(root: Path, key: str):
    """Serialize mutações locais usando lock do sistema operacional.

    O lock tem espera limitada a cinco segundos, é liberado em finally e não
    depende de apagar arquivos após crash. Funciona com fcntl e msvcrt.
    """
    directory = contained(root, ".antares/locks")
    directory.mkdir(parents=True, exist_ok=True)
    path = contained(directory, identifier(key) + ".lock")
    with path.open("a+b") as stream:
        if path.stat().st_size == 0:
            stream.write(b"0")
            stream.flush()
        acquired = False
        for _ in range(100):
            try:
                stream.seek(0)
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
                break
            except (BlockingIOError, OSError):
                time.sleep(0.05)
        if not acquired:
            raise ConflictError("Outra operação está alterando estes dados. Tente novamente.")
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
