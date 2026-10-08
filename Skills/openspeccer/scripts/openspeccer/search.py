"""Full-text search: case-insensitive substring over spec files and change artifacts."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .scan import ARTIFACT_EXTS, Change, Spec, walk_files

_SNIPPET = 80
_LIMIT = 100


@dataclass
class Hit:
    kind: str  # "spec" | "change"
    title: str
    topic: str | None
    slug: str | None
    source_key: str | None
    status: str | None
    file: str | None  # artifact path within the change, or None for a spec
    snippet: str
    offset: int  # where the match starts within `snippet`, or -1 for a name-only match


def _display(name: str) -> str:
    return re.sub(r"[-_/]+", " ", name)


def _snippet(text: str, idx: int, qlen: int) -> tuple[str, int]:
    start = max(0, idx - _SNIPPET)
    end = min(len(text), idx + qlen + _SNIPPET)
    raw = text[start:end]
    # Collapse whitespace while tracking where the match moved to.
    before = re.sub(r"\s+", " ", raw[: idx - start])
    match = raw[idx - start : idx - start + qlen]
    after = re.sub(r"\s+", " ", raw[idx - start + qlen :])
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(text) else ""
    return prefix + before.lstrip() + match + after.rstrip() + suffix, len(prefix + before.lstrip())


def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def search(openspec_dir: Path, specs: list[Spec], changes: list[Change], query: str) -> list[Hit]:
    q = query.strip().lower()
    if not q:
        return []
    hits: list[Hit] = []
    for spec in specs:
        text = _read(openspec_dir / "specs" / spec.topic / "spec.md")
        idx = text.lower().find(q)
        name_hit = q in spec.topic.lower() or q in _display(spec.topic).lower()
        if idx >= 0 or name_hit:
            snippet, offset = _snippet(text, idx, len(q)) if idx >= 0 else (text[:160], -1)
            hits.append(Hit("spec", spec.topic, spec.topic, None, None, None, None, snippet, offset))

    ordered = [c for c in changes if c.status == "active"] + sorted(
        (c for c in changes if c.status == "archived"), key=lambda c: c.slug, reverse=True
    )
    for change in ordered:
        name_hit = q in change.slug.lower() or q in _display(change.name).lower()
        root = Path(change.dir)
        best: Hit | None = None
        for f in walk_files(root):
            if not f.name.endswith(ARTIFACT_EXTS):
                continue
            text = _read(f)
            idx = text.lower().find(q)
            if idx >= 0:
                snippet, offset = _snippet(text, idx, len(q))
                best = Hit(
                    "change",
                    change.name,
                    None,
                    change.slug,
                    change.source.key,
                    change.status,
                    f.relative_to(root).as_posix(),
                    snippet,
                    offset,
                )
                break
        if best is None and name_hit:
            best = Hit(
                "change",
                change.name,
                None,
                change.slug,
                change.source.key,
                change.status,
                None,
                "",
                -1,
            )
        if best:
            hits.append(best)
        if len(hits) >= _LIMIT:
            break
    return hits[:_LIMIT]
