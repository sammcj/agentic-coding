"""git and jj queries. Every function degrades to an empty result when the tool or repo is absent."""

from __future__ import annotations

import hashlib
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

_TIMEOUT = 10
_ARCHIVE_DIR_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-(.+)$")
# Hex only, so a rev can never be read as an option or a revision expression.
_REV_RE = re.compile(r"[0-9a-f]{7,40}")
_JJ_TEMPLATE = 'name ++ "\\t" ++ root ++ "\\t" ++ target.change_id().short() ++ "\\n"'


@dataclass(frozen=True)
class Worktree:
    path: str
    label: str  # branch, jj workspace name, or "detached"
    head: str | None
    is_main: bool
    vcs: str  # "git" | "jj" | "none"

    @property
    def key(self) -> str:
        return worktree_key(self.path)


def worktree_key(path: str) -> str:
    return hashlib.sha1(path.encode()).hexdigest()[:8]


def run_result(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str] | None:
    """The finished process whatever its exit code; None only when it could not run or timed out."""
    try:
        return subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=_TIMEOUT, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None


def run(args: list[str], cwd: Path) -> str | None:
    proc = run_result(args, cwd)
    return proc.stdout if proc and proc.returncode == 0 else None


def head(repo: Path) -> str | None:
    out = run(["git", "rev-parse", "HEAD"], repo)
    return out.strip() if out else None


def git_worktrees(repo: Path) -> list[Worktree]:
    """Each worktree's copy of `repo`. `repo` may sit below the top level (a monorepo package), so
    the same subdirectory is taken in every worktree, and a worktree without it is skipped."""
    out = run(["git", "worktree", "list", "--porcelain"], repo)
    if not out:
        return []
    prefix = (run(["git", "rev-parse", "--show-prefix"], repo) or "").strip()
    result: list[Worktree] = []
    for chunk in out.strip().split("\n\n"):
        fields: dict[str, str] = {}
        for line in chunk.splitlines():
            key, _, value = line.partition(" ")
            fields[key] = value
        top = fields.get("worktree")
        if not top or "bare" in fields or "prunable" in fields:
            continue
        path = Path(top) / prefix
        if not path.is_dir():
            continue
        branch = fields.get("branch", "").removeprefix("refs/heads/") or "detached"
        result.append(
            Worktree(
                path=str(path.resolve()),
                label=branch,
                head=fields.get("HEAD"),
                is_main=not result,
                vcs="git",
            )
        )
    return result


def jj_workspaces(repo: Path) -> list[Worktree]:
    out = run(["jj", "workspace", "list", "--ignore-working-copy", "-T", _JJ_TEMPLATE], repo)
    root = run(["jj", "root", "--ignore-working-copy"], repo)
    if not out or not root:
        return []
    # Same subdirectory in every workspace, as for git worktrees.
    try:
        prefix = repo.resolve().relative_to(Path(root.strip()).resolve())
    except ValueError:
        prefix = Path()
    result: list[Worktree] = []
    for line in out.splitlines():
        parts = line.rstrip().split("\t")
        if len(parts) < 2 or not (Path(parts[1]) / prefix).is_dir():
            continue
        result.append(
            Worktree(
                path=str((Path(parts[1]) / prefix).resolve()),
                label=parts[0],
                head=parts[2] if len(parts) > 2 and parts[2] else None,
                is_main=parts[0] == "default",
                vcs="jj",
            )
        )
    result.sort(key=lambda w: not w.is_main)
    return result


def list_worktrees(repo: Path, include_jj: bool) -> list[Worktree]:
    """The repo's working copies, main first. A non-VCS directory is its own single entry."""
    repo = repo.resolve()
    found = git_worktrees(repo)
    if include_jj:
        seen = {w.path for w in found}
        # A colocated jj repo lists the git main copy too; the git entry keeps its branch name.
        found += [w for w in jj_workspaces(repo) if w.path not in seen]
    if not any(w.path == str(repo) for w in found):
        found.insert(0, Worktree(path=str(repo), label="local", head=None, is_main=True, vcs="none"))
    main = next((w for w in found if w.path == str(repo)), found[0])
    others = [w for w in found if w is not main]
    if not main.is_main:
        main = Worktree(main.path, main.label, main.head, True, main.vcs)
    return [main, *[Worktree(w.path, w.label, w.head, False, w.vcs) for w in others]]


def change_first_commits(repo: Path) -> dict[str, str]:
    """slug -> ISO timestamp of the earliest commit touching that change, active or archived.

    An archived change's slug is its directory name minus the date prefix, so the time it spent
    active and its archive directory both count towards the same entry.
    """
    # --relative: paths relative to `repo`, which may be below the top level.
    args = ["git", "log", "--relative", "--format=COMMIT %aI", "--name-only", "--", "openspec/changes/"]
    out = run(args, repo)
    if not out:
        return {}
    earliest: dict[str, str] = {}
    stamp = ""
    for line in out.splitlines():
        if line.startswith("COMMIT "):
            stamp = line[7:].strip()
            continue
        parts = line.split("/")
        if len(parts) < 4 or parts[:2] != ["openspec", "changes"]:
            continue
        if parts[2] == "archive":
            if len(parts) < 5:
                continue
            m = _ARCHIVE_DIR_RE.match(parts[3])
            slug = m.group(2) if m else parts[3]
        else:
            slug = parts[2]
        # git log is newest first, so the last write wins as the earliest.
        earliest[slug] = stamp
    return earliest


@dataclass(frozen=True)
class FileVersion:
    rev: str
    date: str
    subject: str


def file_versions(repo: Path, relpath: str, limit: int = 100) -> list[FileVersion]:
    out = run(["git", "log", f"-n{limit}", "--follow", "--format=%H%x09%aI%x09%s", "--", relpath], repo)
    if not out:
        return []
    versions: list[FileVersion] = []
    for line in out.splitlines():
        parts = line.split("\t", 2)
        if len(parts) == 3:
            versions.append(FileVersion(rev=parts[0], date=parts[1], subject=parts[2]))
    return versions


def show_file(repo: Path, rev: str, relpath: str) -> str | None:
    """File content at a revision. `--follow` history may cross renames, so callers pass the
    path the file had at that revision when they know it; otherwise the current path is tried."""
    if not _REV_RE.fullmatch(rev):
        return None
    # `./` makes the path relative to `repo` rather than the top level.
    return run(["git", "show", f"{rev}:./{relpath}"], repo)


def path_at_rev(repo: Path, rev: str, relpath: str) -> str:
    """The name `relpath` had at `rev`, following renames; `relpath` itself if unknown."""
    if not _REV_RE.fullmatch(rev):
        return relpath
    full = (run(["git", "rev-parse", "--verify", "--quiet", f"{rev}^{{commit}}"], repo) or "").strip()
    out = run(["git", "log", "--relative", "--follow", "--name-only", "--format=%H", "--", relpath], repo)
    if not out or not full:
        return relpath
    current: str | None = None
    for line in out.splitlines():
        if not line:
            continue
        if re.fullmatch(r"[0-9a-f]{40}", line):
            current = line
        elif current == full:
            return line
    return relpath
