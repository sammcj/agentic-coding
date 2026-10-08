"""The repository being viewed: snapshot assembly, detail reads, and the caches behind them."""

from __future__ import annotations

import difflib
import functools
import threading
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from . import vcs
from .agents import detect_agents
from .docs import parse_spec, parse_tasks
from .scan import (
    Change,
    ScanCache,
    ScanContext,
    Source,
    Spec,
    default_schema,
    discover_specs,
    is_safe_slug,
    is_safe_topic,
    read_yaml,
    scan_active,
    scan_archived,
    scan_change,
    scan_specs,
    stats,
)
from .schemas import SchemaCatalog, build_graph, schema_order
from .search import search

_AGENTS_TTL = 30.0  # seconds; see Repo._agents_now


class NotFound(LookupError):
    pass


class Repo:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.openspec = self.root / "openspec"
        self.catalog = SchemaCatalog(self.root)
        self._lock = threading.Lock()
        self._version = 0
        self._snapshots: dict[tuple[bool, bool], tuple[int, dict[str, Any], list[Change], list[Spec]]] = {}
        # One scan per scope at a time: requests arriving together after a bump share its result.
        self._scan_locks: dict[tuple[bool, bool], threading.Lock] = {}
        self._first_commits: tuple[str | None, dict[str, str]] = (None, {})
        self._scan_cache = ScanCache()
        self._agents: tuple[float, list[dict[str, Any]]] = (-_AGENTS_TTL, [])

    # -- versioning: the watcher bumps this, and every cache keyed on it goes stale --

    @property
    def version(self) -> int:
        return self._version

    def bump(self) -> int:
        with self._lock:
            self._version += 1
            self._snapshots.clear()
            return self._version

    def worktrees(self, aggregate: bool, include_jj: bool) -> list[vcs.Worktree]:
        found = vcs.list_worktrees(self.root, include_jj)
        return found if aggregate else found[:1]

    def _context(self) -> ScanContext:
        head = vcs.head(self.root)
        cached_head, commits = self._first_commits
        if head is None:
            commits = {}
        elif head != cached_head:
            commits = vcs.change_first_commits(self.root)
            self._first_commits = (head, commits)
        return ScanContext(
            default_schema=default_schema(self.openspec),
            schema_of=functools.cache(self.catalog.get),  # one lookup per schema per scan
            first_commits=commits,
            cache=self._scan_cache,
        )

    def schemas_changed(self) -> None:
        """Schema definitions moved: drop everything derived from them."""
        self.catalog.invalidate()
        self._scan_cache.archived.clear()

    def _agents_now(self) -> list[dict[str, Any]]:
        # Agent setup sits outside openspec/, so the watcher never sees it change. A short TTL
        # keeps it current without walking those directories on every scan.
        at, agents = self._agents
        if time.monotonic() - at >= _AGENTS_TTL:
            agents = [asdict(a) for a in detect_agents(self.root)]
            self._agents = (time.monotonic(), agents)
        return agents

    def _scan(self, aggregate: bool, include_jj: bool) -> tuple[dict[str, Any], list[Change], list[Spec]]:
        key = (aggregate, include_jj)
        with self._lock:
            scan_lock = self._scan_locks.setdefault(key, threading.Lock())
        with scan_lock:
            hit = self._snapshots.get(key)
            if hit and hit[0] == self._version:
                return hit[1], hit[2], hit[3]
            return self._scan_now(key)

    def _scan_now(self, key: tuple[bool, bool]) -> tuple[dict[str, Any], list[Change], list[Spec]]:
        aggregate, include_jj = key
        version = self._version
        ctx = self._context()
        worktrees = self.worktrees(aggregate, include_jj)
        main = worktrees[0]
        archived = scan_archived(self.openspec, Source.of(main), ctx)
        active = scan_active(worktrees, {c.name for c in archived}, ctx)
        changes = active + archived
        specs = scan_specs(self.openspec, changes)
        snapshot = {
            "repo": {"path": str(self.root), "name": self.root.name},
            "version": version,
            "aggregate": aggregate,
            "include_jj": include_jj,
            "default_schema": ctx.default_schema,
            "worktrees": [{**asdict(w), "key": w.key} for w in worktrees],
            "stats": stats(specs, changes),
            "specs": [asdict(s) for s in specs],
            "changes": [asdict(c) for c in changes],
            "agents": self._agents_now(),
        }
        with self._lock:
            if self._version == version:
                self._snapshots[key] = (version, snapshot, changes, specs)
        return snapshot, changes, specs

    def snapshot(self, aggregate: bool = True, include_jj: bool = False) -> dict[str, Any]:
        return self._scan(aggregate, include_jj)[0]

    # -- detail reads --

    def _find_change(self, slug: str, wt_key: str | None, aggregate: bool, include_jj: bool) -> Change:
        """The change as the given scope shows it, or one worktree's own copy when `wt_key` names it."""
        if not is_safe_slug(slug):
            raise NotFound(slug)
        _, changes, _ = self._scan(aggregate, include_jj)
        matches = [c for c in changes if c.slug == slug and (not wt_key or c.source.key == wt_key)]
        if matches:
            return matches[0]
        if not wt_key:
            raise NotFound(slug)
        # A copy the election did not pick: read that worktree's directory directly.
        for wt in self.worktrees(True, include_jj):
            if wt.key == wt_key:
                d = Path(wt.path) / "openspec" / "changes" / slug
                if d.is_dir() and not d.is_symlink():
                    return scan_change(d, "active", Source.of(wt), self._context())
        raise NotFound(slug)

    def change_detail(
        self, slug: str, wt_key: str | None = None, include_jj: bool = False, aggregate: bool = True
    ) -> dict:
        change = self._find_change(slug, wt_key, aggregate, include_jj)
        root = Path(change.dir)
        artifacts = []
        for a in change.artifacts:
            item: dict[str, Any] = asdict(a)
            if a.kind == "specs":
                item["specs"] = [
                    {"topic": t, "path": f"specs/{t}/spec.md", **_doc(_read(p))}
                    for t, p in discover_specs(root / "specs").items()
                ]
            else:
                content = _read(root / a.path)
                item["content"] = content
                if a.kind == "tasks":
                    item["tasks"] = asdict(parse_tasks(content))
            artifacts.append(item)
        schema = self.catalog.get(change.schema) if change.schema else None
        detail = asdict(change)
        detail["artifacts"] = artifacts
        detail["schema_order"] = schema_order(schema) if schema else None
        detail["meta"] = read_yaml(root / ".openspec.yaml")
        return detail

    def spec_detail(self, topic: str, include_jj: bool = False, aggregate: bool = True) -> dict:
        path = self._spec_path(topic)
        content = _read(path)
        _, changes, _ = self._scan(aggregate, include_jj)
        history = []
        for c in changes:
            if topic not in c.spec_topics:
                continue
            delta = parse_spec(_read(Path(c.dir) / "specs" / topic / "spec.md"))
            ops: dict[str, int] = {}
            for g in delta.groups:
                if g.op:
                    ops[g.op] = ops.get(g.op, 0) + len(g.blocks)
            history.append(
                {
                    "slug": c.slug,
                    "name": c.name,
                    "status": c.status,
                    "date": c.archived or c.created,
                    "source_key": c.source.key,
                    "ops": ops,
                }
            )
        history.sort(key=lambda h: (h["status"] == "active", h["date"] or ""), reverse=True)
        relpath = path.relative_to(self.root).as_posix()
        versions = [asdict(v) for v in vcs.file_versions(self.root, relpath)]
        return {"topic": topic, "content": content, **_doc(content), "history": history, "versions": versions}

    def spec_delta(
        self, topic: str, slug: str, wt_key: str | None, include_jj: bool = False, aggregate: bool = True
    ) -> dict:
        if not is_safe_topic(topic):
            raise NotFound(topic)
        change = self._find_change(slug, wt_key, aggregate, include_jj)
        path = discover_specs(Path(change.dir) / "specs").get(topic)
        if path is None:
            raise NotFound(topic)
        content = _read(path)
        return {"topic": topic, "slug": slug, "content": content, **_doc(content)}

    def spec_diff(self, topic: str, base: str, head: str = "working") -> dict:
        """Line diff of a main spec between two git revisions (`working` = the file on disk)."""
        path = self._spec_path(topic)
        relpath = path.relative_to(self.root).as_posix()

        def content_at(rev: str) -> str:
            if rev == "working":
                return _read(path)
            text = vcs.show_file(self.root, rev, vcs.path_at_rev(self.root, rev, relpath))
            if text is None:
                raise NotFound(rev)
            return text

        a, b = content_at(base), content_at(head)
        lines = []
        added = removed = 0
        for line in difflib.unified_diff(a.splitlines(), b.splitlines(), lineterm="", n=3):
            if line.startswith(("---", "+++")):
                continue
            tag = line[:1] if line[:1] in "+-@" else " "
            added += tag == "+"
            removed += tag == "-"
            lines.append({"t": tag, "text": line[1:] if tag != "@" else line})
        return {
            "topic": topic,
            "base": base,
            "head": head,
            "lines": lines,
            "added": added,
            "removed": removed,
        }

    def _spec_path(self, topic: str) -> Path:
        if not is_safe_topic(topic):
            raise NotFound(topic)
        path = discover_specs(self.openspec / "specs").get(topic)
        if path is None:
            raise NotFound(topic)
        return path

    # -- schemas and search --

    def schemas(self, include_jj: bool = False, aggregate: bool = True) -> dict:
        listed, degraded = self.catalog.summaries()
        snap, changes, _ = self._scan(aggregate, include_jj)
        default = snap["default_schema"]
        usage: dict[str, int] = {}
        for c in changes:
            if c.status == "active":
                usage[c.schema or default or "?"] = usage.get(c.schema or default or "?", 0) + 1
        items = [
            {
                "name": s.get("name"),
                "description": s.get("description", ""),
                "artifact_count": len(s.get("artifacts") or []),
                "source": s.get("source", "unknown"),
                "active_changes": usage.get(str(s.get("name")), 0),
                "is_default": s.get("name") == default,
            }
            for s in listed
        ]
        known = {i["name"] for i in items}
        unresolved = {k: v for k, v in usage.items() if k not in known}
        return {"schemas": items, "degraded": degraded, "unresolved": unresolved, "default": default}

    def schema_detail(self, name: str) -> dict:
        schema = self.catalog.get(name)
        if schema is None:
            raise NotFound(name)
        nodes, edges = build_graph(schema)
        return {
            "name": schema.name,
            "description": schema.description,
            "version": schema.version,
            "source": schema.source,
            "path": schema.path,
            "tracks": schema.tracks,
            "nodes": [asdict(n) for n in nodes],
            "edges": [asdict(e) for e in edges],
        }

    def search(self, query: str, include_jj: bool = False, aggregate: bool = True) -> list[dict]:
        _, changes, specs = self._scan(aggregate, include_jj)
        return [asdict(h) for h in search(self.openspec, specs, changes, query)]


def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def _doc(content: str) -> dict:
    return {"doc": asdict(parse_spec(content))}
