"""Filesystem scan of an `openspec/` tree into specs and changes. Pure reads, no CLI calls except
through the schema catalog, which caches."""

from __future__ import annotations

import contextlib
import hashlib
import os
import re
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path

from .docs import count_tasks, parse_spec
from .schemas import SchemaDef, artifact_for_file
from .vcs import Worktree
from .yamlish import YamlError, loads

ARTIFACT_EXTS = (".md", ".yaml", ".yml", ".json")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_ARCHIVE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-(.+)$")
_SAFE_SEGMENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_MAX_DEPTH = 4


@dataclass
class Source:
    key: str
    label: str
    is_main: bool
    vcs: str

    @classmethod
    def of(cls, wt: Worktree) -> Source:
        return cls(key=wt.key, label=wt.label, is_main=wt.is_main, vcs=wt.vcs)


@dataclass
class Artifact:
    id: str  # path without `.md` ("proposal", "loop/intake"); data files keep their extension
    path: str  # relative to the change directory; "specs" for the delta tree
    title: str
    kind: str  # "markdown" | "tasks" | "data" | "specs"
    mtime: float
    schema_artifact: str | None = None


@dataclass
class TaskCount:
    done: int
    total: int


@dataclass
class Change:
    slug: str  # directory name
    name: str  # slug without an archive date prefix
    status: str  # "active" | "archived"
    dir: str
    source: Source
    schema: str | None
    created: str | None
    archived: str | None
    updated: str
    tasks: TaskCount | None
    lane: str
    artifacts: list[Artifact]
    spec_topics: list[str]
    variants: int = 1  # distinct copies across worktrees; >1 means they disagree


@dataclass
class Spec:
    topic: str
    title: str | None
    requirement_count: int
    updated: str
    history: list[str] = field(default_factory=list)  # change slugs with a delta for this topic
    in_flight: list[str] = field(default_factory=list)  # active subset of history


def is_safe_slug(slug: str) -> bool:
    return bool(_SAFE_SEGMENT.match(slug))


def is_safe_topic(topic: str) -> bool:
    return bool(topic) and all(_SAFE_SEGMENT.match(s) for s in topic.split("/"))


def discover_specs(specs_root: Path) -> dict[str, Path]:
    """topic -> spec.md path. OpenSpec's rule: skip dot entries, never follow a symlinked
    directory, ignore a spec.md directly in the root, and accept a symlinked spec.md only if it
    resolves inside the root. An unreadable entry is skipped rather than failing the scan."""
    found: dict[str, Path] = {}
    if not specs_root.is_dir():
        return found
    root_real = specs_root.resolve()

    def walk(d: Path, parts: list[str]) -> None:
        try:
            entries = sorted(os.scandir(d), key=lambda e: e.name)
        except OSError:
            return
        for e in entries:
            if e.name.startswith("."):
                continue
            try:
                if e.is_dir(follow_symlinks=False):
                    if len(parts) < 8:
                        walk(Path(e.path), [*parts, e.name])
                elif e.name == "spec.md" and parts and e.is_file():
                    if e.is_symlink() and not Path(e.path).resolve().is_relative_to(root_real):
                        continue
                    found["/".join(parts)] = Path(e.path)
            except OSError:
                continue

    walk(specs_root, [])
    return dict(sorted(found.items()))


def read_yaml(path: Path) -> dict:
    try:
        data = loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, YamlError):
        return {}
    return data if isinstance(data, dict) else {}


def default_schema(openspec_dir: Path) -> str | None:
    value = read_yaml(openspec_dir / "config.yaml").get("schema")
    return str(value) if value else None


def iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, UTC).isoformat(timespec="seconds")


def walk_files(root: Path, skip_top: tuple[str, ...] = ()) -> Iterator[Path]:
    """Files under root, skipping dot entries and symlinked directories, to a bounded depth. A
    symlinked file is kept only if it resolves inside root, so a link cannot expose files beyond it."""
    root_real = root.resolve()

    def walk(d: Path, depth: int) -> Iterator[Path]:
        try:
            entries = sorted(os.scandir(d), key=lambda e: e.name)
        except OSError:
            return
        for e in entries:
            if e.name.startswith(".") or (depth == 0 and e.name in skip_top):
                continue
            try:
                if e.is_dir(follow_symlinks=False):
                    if depth < _MAX_DEPTH:
                        yield from walk(Path(e.path), depth + 1)
                elif e.is_file():
                    if e.is_symlink() and not Path(e.path).resolve().is_relative_to(root_real):
                        continue
                    yield Path(e.path)
            except OSError:
                continue

    yield from walk(root, 0)


def _mtime(p: Path) -> float:
    try:
        return p.stat().st_mtime
    except OSError:
        return 0.0


def humanise(stem: str) -> str:
    words = re.sub(r"[-_]+", " ", stem).strip()
    return words[:1].upper() + words[1:] if words else stem


def list_artifacts(change_dir: Path, schema: SchemaDef | None) -> list[Artifact]:
    tracks = schema.tracks if schema else "tasks.md"
    out: list[Artifact] = []
    for f in walk_files(change_dir, skip_top=("specs",)):
        rel = f.relative_to(change_dir).as_posix()
        if not rel.endswith(ARTIFACT_EXTS):
            continue
        is_md = rel.endswith(".md")
        kind = "tasks" if rel == tracks else "markdown" if is_md else "data"
        art_id = rel[:-3] if is_md else rel
        out.append(
            Artifact(
                id=art_id,
                path=rel,
                title=humanise(Path(art_id).name) if is_md else Path(rel).name,
                kind=kind,
                mtime=_mtime(f),
                schema_artifact=artifact_for_file(schema, rel) if schema else None,
            )
        )
    specs = discover_specs(change_dir / "specs")
    if specs:
        out.append(
            Artifact(
                id="specs",
                path="specs",
                title="Specs",
                kind="specs",
                mtime=max(_mtime(p) for p in specs.values()),
                schema_artifact=artifact_for_file(schema, "specs/x/spec.md") if schema else None,
            )
        )
    out.sort(key=lambda a: -a.mtime)
    return out


def lane_for(status: str, tasks: TaskCount | None) -> str:
    if status == "archived":
        return "archived"
    if tasks is None or tasks.total == 0:
        return "proposed"
    if tasks.done == 0:
        return "planned"
    if tasks.done < tasks.total:
        return "in_progress"
    return "ready"


@dataclass
class ScanCache:
    """Results that depend only on a change directory's files, reused across scans while those
    files are unchanged. Values are never mutated after insertion, so concurrent scans may share it."""

    prints: dict[str, tuple[tuple, str]] = field(default_factory=dict)
    archived: dict[str, tuple[tuple, Change]] = field(default_factory=dict)


@dataclass
class ScanContext:
    default_schema: str | None
    schema_of: Callable[[str], SchemaDef | None]
    first_commits: dict[str, str]
    cache: ScanCache = field(default_factory=ScanCache)


def valid_date(value: object) -> str | None:
    """`value` as YYYY-MM-DD if it is a real calendar date, else None."""
    text = str(value) if value else ""
    if not _DATE_RE.match(text):
        return None
    try:
        date.fromisoformat(text)
    except ValueError:
        return None
    return text


def scan_change(change_dir: Path, status: str, source: Source, ctx: ScanContext) -> Change:
    slug = change_dir.name
    m = _ARCHIVE_RE.match(slug) if status == "archived" else None
    name = m.group(2) if m else slug
    meta = read_yaml(change_dir / ".openspec.yaml")
    schema_name = str(meta.get("schema") or ctx.default_schema or "") or None
    schema = ctx.schema_of(schema_name) if schema_name else None
    artifacts = list_artifacts(change_dir, schema)

    tasks = None
    tracked_rel = schema.tracks if schema else "tasks.md"
    tracked = change_dir / tracked_rel
    # Only a file the listing accepted, so a symlink out of the change is never read.
    if any(a.path == tracked_rel for a in artifacts):
        try:
            done, total = count_tasks(tracked.read_text(encoding="utf-8"))
            tasks = TaskCount(done=done, total=total)
        except (OSError, UnicodeDecodeError):
            pass

    created = valid_date(meta.get("created"))
    if created is None and name in ctx.first_commits:
        created = ctx.first_commits[name][:10]
    updated = max([_mtime(change_dir), *(a.mtime for a in artifacts)])
    return Change(
        slug=slug,
        name=name,
        status=status,
        dir=str(change_dir),
        source=source,
        schema=schema_name,
        created=created,
        archived=valid_date(m.group(1)) if m else None,
        updated=iso(updated),
        tasks=tasks,
        lane=lane_for(status, tasks),
        artifacts=artifacts,
        spec_topics=list(discover_specs(change_dir / "specs")),
    )


def change_dirs(changes_root: Path) -> list[Path]:
    try:
        return sorted(
            p
            for p in changes_root.iterdir()
            if p.is_dir() and not p.is_symlink() and not p.name.startswith(".") and p.name != "archive"
        )
    except OSError:
        return []


def tree_signature(change_dir: Path) -> tuple:
    """(relpath, mtime_ns, size) per file plus the directory's own mtime: moves when any file does."""
    entries: list[tuple] = []
    for f in walk_files(change_dir):
        try:
            st = f.stat()
        except OSError:
            continue
        entries.append((f.relative_to(change_dir).as_posix(), st.st_mtime_ns, st.st_size))
    with contextlib.suppress(OSError):
        entries.append(("", change_dir.stat().st_mtime_ns, 0))
    return tuple(entries)


def newest_mtime(signature: tuple) -> int:
    return max((e[1] for e in signature), default=0)


def fingerprint(change_dir: Path, signature: tuple, cache: ScanCache) -> str:
    """Content hash of a change directory, recomputed only when its signature moves."""
    hit = cache.prints.get(str(change_dir))
    if hit and hit[0] == signature:
        return hit[1]
    h = hashlib.sha1()
    for rel, *_ in signature:
        if not rel:
            continue
        h.update(rel.encode())
        try:
            h.update(hashlib.sha1((change_dir / rel).read_bytes()).digest())
        except OSError:
            h.update(b"?")
    digest = h.hexdigest()
    cache.prints[str(change_dir)] = (signature, digest)
    return digest


def scan_active(worktrees: list[Worktree], archived_names: set[str], ctx: ScanContext) -> list[Change]:
    """Active changes across working copies, one per slug.

    Identical copies collapse to the main one. When copies disagree, the most recently modified
    copy wins, main included: that is where the work is happening. A worktree copy of a
    change main has already archived is a stale branch and is dropped.
    """
    copies: dict[str, list[tuple[Worktree, Path]]] = {}
    for wt in worktrees:
        for d in change_dirs(Path(wt.path) / "openspec" / "changes"):
            copies.setdefault(d.name, []).append((wt, d))

    result: list[Change] = []
    for slug, found in copies.items():
        main_copy = next((d for wt, d in found if wt.is_main), None)
        if main_copy is None and slug in archived_names:
            continue
        if len(found) == 1:
            wt, d = found[0]
            result.append(scan_change(d, "active", Source.of(wt), ctx))
            continue
        sigs = {d: tree_signature(d) for _, d in found}
        prints = {d: fingerprint(d, sigs[d], ctx.cache) for _, d in found}
        if len(set(prints.values())) > 1:
            wt, d = max(found, key=lambda c: newest_mtime(sigs[c[1]]))
        else:
            wt, d = next((c for c in found if c[0].is_main), found[0])
        change = scan_change(d, "active", Source.of(wt), ctx)
        change.variants = len(set(prints.values()))
        result.append(change)
    result.sort(key=lambda c: c.updated, reverse=True)
    return result


def scan_archived(openspec_dir: Path, source: Source, ctx: ScanContext) -> list[Change]:
    out = []
    for d in change_dirs(openspec_dir / "changes" / "archive"):
        # There can be hundreds and they rarely move: reuse each until its files or the inputs it
        # takes from the context change.
        m = _ARCHIVE_RE.match(d.name)
        name = m.group(2) if m else d.name
        sig = (tree_signature(d), ctx.default_schema, ctx.first_commits.get(name), source.key)
        hit = ctx.cache.archived.get(str(d))
        if hit and hit[0] == sig:
            out.append(hit[1])
            continue
        change = scan_change(d, "archived", source, ctx)
        ctx.cache.archived[str(d)] = (sig, change)
        out.append(change)
    out.sort(key=lambda c: c.slug, reverse=True)
    return out


def scan_specs(openspec_dir: Path, changes: list[Change]) -> list[Spec]:
    specs: list[Spec] = []
    for topic, path in discover_specs(openspec_dir / "specs").items():
        try:
            doc = parse_spec(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            continue
        history = [c.slug for c in changes if topic in c.spec_topics]
        in_flight = [c.slug for c in changes if c.status == "active" and topic in c.spec_topics]
        specs.append(
            Spec(
                topic=topic,
                title=doc.title,
                requirement_count=doc.requirement_count,
                updated=iso(_mtime(path)),
                history=history,
                in_flight=in_flight,
            )
        )
    return specs


def stats(specs: list[Spec], changes: list[Change], today: datetime | None = None) -> dict:
    now = today or datetime.now(UTC)
    active = [c for c in changes if c.status == "active"]
    archived = [c for c in changes if c.status == "archived"]
    lifecycles = [
        (datetime.fromisoformat(c.archived) - datetime.fromisoformat(c.created)).days
        for c in archived
        if c.created and c.archived
    ]
    stale = [c for c in active if (now - datetime.fromisoformat(c.updated)).days > 30]
    lanes: dict[str, int] = {}
    for c in changes:
        lanes[c.lane] = lanes.get(c.lane, 0) + 1
    return {
        "specs": len(specs),
        "requirements": sum(s.requirement_count for s in specs),
        "active": len(active),
        "archived": len(archived),
        "tasks_done": sum(c.tasks.done for c in active if c.tasks),
        "tasks_total": sum(c.tasks.total for c in active if c.tasks),
        "avg_lifecycle_days": round(sum(lifecycles) / len(lifecycles), 1) if lifecycles else None,
        "stale": len(stale),
        "lanes": lanes,
    }
