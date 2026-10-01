import subprocess
from pathlib import Path

from antares_fd.analysis.provenance import get_git_provenance


def test_worktree_snapshot_hash_tracks_dirty_and_untracked_content(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    tracked = tmp_path / "tracked.txt"
    tracked.write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "add", "tracked.txt"], check=True)
    subprocess.run([
        "git", "-C", str(tmp_path), "-c", "user.name=Test",
        "-c", "user.email=test@example.invalid", "commit", "-qm", "initial",
    ], check=True)

    tracked.write_text("modified\n", encoding="utf-8")
    untracked = tmp_path / "new.txt"
    untracked.write_text("first\n", encoding="utf-8")
    first = get_git_provenance(tmp_path)
    untracked.write_text("second\n", encoding="utf-8")
    second = get_git_provenance(tmp_path)

    assert first["dirty"] == "dirty"
    assert first["working_tree_snapshot_sha256"] != second["working_tree_snapshot_sha256"]
