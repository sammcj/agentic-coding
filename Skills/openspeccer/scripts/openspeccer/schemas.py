"""Workflow schemas: enumeration, definitions, and the dependency graph drawn on the Schemas page.

Which schemas exist and where a schema resolves from are the OpenSpec CLI's answers (it applies
project > user > package precedence). The repo's own `openspec/schemas/` is read directly only
when the CLI is unavailable, so the page still shows something without it.
"""

from __future__ import annotations

import fnmatch
import json
import os
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import vcs
from .yamlish import YamlError, loads

_TTL = (
    300.0  # the watcher invalidates on any openspec/ change, so this only bounds staleness of package schemas
)


@dataclass
class ArtifactDef:
    id: str
    generates: str | None
    description: str
    requires: list[str]


@dataclass
class SchemaDef:
    name: str
    description: str
    version: Any
    source: str
    path: str | None
    artifacts: list[ArtifactDef]
    apply_requires: list[str]
    apply_tracks: str | None

    @property
    def tracks(self) -> str:
        return self.apply_tracks or "tasks.md"


@dataclass
class Node:
    key: str
    label: str
    kind: str  # "artifact" | "apply"
    level: int
    row: int
    generates: str | None = None
    description: str = ""
    requires: list[str] = field(default_factory=list)
    derived: bool = False  # placed after apply by inference, not by a declared dependency


@dataclass
class Edge:
    source: str
    target: str
    derived: bool


class SchemaCatalog:
    """Caches CLI answers per repo for a short TTL. Failures are not cached, so fixing PATH
    takes effect on the next read."""

    def __init__(self, repo: Path) -> None:
        self.repo = repo
        self._lock = threading.Lock()
        self._list: tuple[float, list[dict[str, Any]]] | None = None
        self._defs: dict[str, tuple[float, SchemaDef | None]] = {}

    def invalidate(self) -> None:
        with self._lock:
            self._list = None
            self._defs.clear()

    def summaries(self) -> tuple[list[dict[str, Any]], str | None]:
        """(schemas, degraded_reason). Each entry: name, description, artifacts, source."""
        with self._lock:
            if self._list and time.monotonic() - self._list[0] < _TTL:
                return self._list[1], None
        out = vcs.run([cli(), "schemas", "--json"], self.repo)
        parsed = _json_list(out)
        if parsed is not None:
            with self._lock:
                self._list = (time.monotonic(), parsed)
            return parsed, None
        local = []
        for name in self._project_schema_names():
            d = self.get(name)
            if d:
                local.append(
                    {
                        "name": d.name,
                        "description": d.description,
                        "artifacts": [a.id for a in d.artifacts],
                        "source": "project",
                    }
                )
        return local, "OpenSpec CLI unavailable - showing project schemas only"

    def get(self, name: str) -> SchemaDef | None:
        if not is_safe_name(name):
            return None
        with self._lock:
            hit = self._defs.get(name)
            if hit and time.monotonic() - hit[0] < _TTL:
                return hit[1]
        path, source, answered = self._resolve(name)
        result = _read_schema(path, source) if path else None
        # A miss is remembered only when the CLI itself said so. A CLI that could not run is
        # retried, since it may be on PATH next time; that failure costs milliseconds, while a
        # CLI answer costs about a second and is called for every change naming the schema.
        if result is not None or answered:
            with self._lock:
                self._defs[name] = (time.monotonic(), result)
        return result

    def _resolve(self, name: str) -> tuple[Path | None, str, bool]:
        """(schema.yaml path, source, whether the CLI answered)."""
        proc = vcs.run_result([cli(), "schema", "which", name, "--json"], self.repo)
        out = proc.stdout if proc else ""
        if out:
            try:
                data = json.loads(out[out.index("{") :])
                if isinstance(data, dict) and data.get("path"):
                    return Path(data["path"]) / "schema.yaml", str(data.get("source", "unknown")), True
            except ValueError:
                pass
        local = self.repo / "openspec" / "schemas" / name / "schema.yaml"
        if local.is_file():
            return local, "project", proc is not None
        return None, "", proc is not None

    def _project_schema_names(self) -> list[str]:
        root = self.repo / "openspec" / "schemas"
        if not root.is_dir():
            return []
        return sorted(p.parent.name for p in root.glob("*/schema.yaml"))


def cli() -> str:
    """The OpenSpec CLI to run; override for installs outside PATH (and in tests)."""
    return os.environ.get("OPENSPECCER_OPENSPEC_BIN", "openspec")


def is_safe_name(name: str) -> bool:
    return bool(name) and name.replace("-", "").replace("_", "").isalnum() and not name.startswith("-")


def _json_list(out: str | None) -> list[dict[str, Any]] | None:
    if not out:
        return None
    try:
        data = json.loads(out[out.index("[") :])
    except ValueError:
        return None
    return [d for d in data if isinstance(d, dict) and "name" in d] if isinstance(data, list) else None


def _read_schema(path: Path, source: str) -> SchemaDef | None:
    try:
        data = loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, YamlError):
        return None
    if not isinstance(data, dict):
        return None
    artifacts = []
    for raw in data.get("artifacts") or []:
        if isinstance(raw, dict) and raw.get("id"):
            artifacts.append(
                ArtifactDef(
                    id=str(raw["id"]),
                    generates=str(raw["generates"]) if raw.get("generates") else None,
                    description=str(raw.get("description") or ""),
                    requires=[str(r) for r in raw.get("requires") or []],
                )
            )
    apply_raw = data.get("apply")
    apply: dict[str, Any] = apply_raw if isinstance(apply_raw, dict) else {}
    return SchemaDef(
        name=str(data.get("name") or path.parent.name),
        description=str(data.get("description") or ""),
        version=data.get("version"),
        source=source,
        path=str(path.parent),
        artifacts=artifacts,
        apply_requires=[str(r) for r in apply.get("requires") or []],
        apply_tracks=str(apply["tracks"]) if apply.get("tracks") else None,
    )


def build_graph(schema: SchemaDef) -> tuple[list[Node], list[Edge]]:
    """Nodes placed in dependency levels plus the edges worth drawing.

    Levels come from the full `requires` graph. Drawn edges are its transitive reduction: an
    edge a longer path already implies adds nothing and detours around the step implying it.
    An artifact that depends on everything apply needs, while apply does not need it, can only
    run after implementation; OpenSpec cannot declare that, so it is inferred and marked derived.
    """
    ids = {a.id for a in schema.artifacts}
    preds: dict[str, list[tuple[str, bool]]] = {
        a.id: [(r, False) for r in a.requires if r in ids] for a in schema.artifacts
    }
    apply_reqs = [r for r in schema.apply_requires if r in ids]
    apply_key = "apply" if "apply" not in ids else "apply (phase)"
    preds[apply_key] = [(r, False) for r in apply_reqs]

    def closure(start: list[str]) -> set[str]:
        seen: set[str] = set()
        stack = list(start)
        while stack:
            n = stack.pop()
            if n in seen:
                continue
            seen.add(n)
            stack.extend(p for p, _ in preds.get(n, []))
        return seen

    derived: set[str] = set()
    if apply_reqs and not _has_cycle(preds):
        before_apply = closure(apply_reqs)
        for a in schema.artifacts:
            if a.id not in before_apply and set(apply_reqs) <= closure(a.requires):
                derived.add(a.id)
                preds[a.id] = [*preds[a.id], (apply_key, True)]

    levels = _levels(preds, [a.id for a in schema.artifacts] + [apply_key])
    edges = _reduce(preds)
    rows: dict[int, int] = {}
    nodes: list[Node] = []
    for a in schema.artifacts:
        lvl = levels[a.id]
        nodes.append(
            Node(
                key=a.id,
                label=a.id,
                kind="artifact",
                level=lvl,
                row=rows.setdefault(lvl, 0),
                generates=a.generates,
                description=a.description,
                requires=a.requires,
                derived=a.id in derived,
            )
        )
        rows[lvl] += 1
    lvl = levels[apply_key]
    nodes.append(
        Node(
            key=apply_key,
            label="apply",
            kind="apply",
            level=lvl,
            row=rows.setdefault(lvl, 0),
            generates=schema.apply_tracks,
            description="Implementation: work through the tracked tasks",
            requires=schema.apply_requires,
        )
    )
    return nodes, edges


def _has_cycle(preds: dict[str, list[tuple[str, bool]]]) -> bool:
    state: dict[str, int] = {}

    def visit(n: str) -> bool:
        state[n] = 1
        for p, _ in preds.get(n, []):
            s = state.get(p, 0)
            if s == 1 or (s == 0 and visit(p)):
                return True
        state[n] = 2
        return False

    return any(state.get(n, 0) == 0 and visit(n) for n in preds)


def _levels(preds: dict[str, list[tuple[str, bool]]], order: list[str]) -> dict[str, int]:
    """Longest path from a root. Under a cycle, a back edge is ignored rather than looping."""
    levels: dict[str, int] = {}
    visiting: set[str] = set()

    def level(n: str) -> int:
        if n in levels:
            return levels[n]
        if n in visiting:
            return 0
        visiting.add(n)
        ps = [level(p) for p, _ in preds.get(n, []) if p not in visiting]
        visiting.discard(n)
        levels[n] = 1 + max(ps) if ps else 0
        return levels[n]

    for n in order:
        level(n)
    return levels


def _reduce(preds: dict[str, list[tuple[str, bool]]]) -> list[Edge]:
    def reachable(src: str, dst: str, skip: tuple[str, str]) -> bool:
        # Is `src` reachable backwards from `dst` without using the edge `skip`?
        stack = [p for p, _ in preds.get(dst, []) if (p, dst) != skip]
        seen: set[str] = set()
        while stack:
            n = stack.pop()
            if n == src:
                return True
            if n in seen:
                continue
            seen.add(n)
            stack.extend(p for p, _ in preds.get(n, []))
        return False

    edges = []
    for target, ps in preds.items():
        for source, derived in ps:
            if not reachable(source, target, (source, target)):
                edges.append(Edge(source=source, target=target, derived=derived))
    return edges


def schema_order(schema: SchemaDef) -> list[str]:
    """Artifact ids in dependency order (level, then declaration)."""
    nodes, _ = build_graph(schema)
    arts = [n for n in nodes if n.kind == "artifact"]
    return [n.key for n in sorted(arts, key=lambda n: (n.level, n.row))]


def artifact_for_file(schema: SchemaDef, relpath: str) -> str | None:
    """The schema artifact whose `generates` pattern covers a change file, if any."""
    for a in schema.artifacts:
        g = a.generates
        if not g:
            continue
        if g == relpath or fnmatch.fnmatch(relpath, g):
            return a.id
        if "**/" in g and fnmatch.fnmatch(relpath, g.replace("**/", "")):
            return a.id
    return None
