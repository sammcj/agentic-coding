"""Markdown structure parsers: `tasks.md` checklists and spec documents.

Both only need line-level structure (headings, checkboxes, fences), so neither is a full
Markdown parser. Rendering happens in the browser.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_FENCE_RE = re.compile(r"^\s{0,3}(```|~~~)")
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
# Only column-0 checkboxes count; an indented one is part of its parent task's text.
_CHECKBOX_RE = re.compile(r"^[-*+] \[([ xX])\]\s+(.*)$")
# Lines that end a lazy continuation: a new list item, heading, quote, fence or rule.
_BLOCK_OPENER_RE = re.compile(r"^(?:[-*+]\s|\d+[.)]\s|#{1,6}\s|>|```|~~~|(?:[-*_]\s*){3,}$)")
_DELTA_OP_RE = re.compile(r"^(ADDED|MODIFIED|REMOVED|RENAMED)\b")


@dataclass
class TaskItem:
    text: str
    done: bool
    line: int


@dataclass
class TaskSection:
    title: str | None
    items: list[TaskItem] = field(default_factory=list)


@dataclass
class Tasks:
    sections: list[TaskSection]
    total: int
    done: int


def parse_tasks(text: str) -> Tasks:
    sections: list[TaskSection] = [TaskSection(title=None)]
    last: TaskItem | None = None
    pending_blanks = 0
    in_fence = False
    for lineno, line in enumerate(_lines(text), start=1):
        fence = bool(_FENCE_RE.match(line))
        if in_fence or (fence and line.startswith((" ", "\t"))):
            if fence:
                in_fence = not in_fence
            if last is not None:
                last.text += "\n" * (pending_blanks + 1) + _dedent2(line)
                pending_blanks = 0
            continue
        if fence:
            in_fence = True
            last = None
            continue
        if m := _CHECKBOX_RE.match(line):
            last = TaskItem(text=m.group(2), done=m.group(1) != " ", line=lineno)
            sections[-1].items.append(last)
            pending_blanks = 0
            continue
        if (h := _HEADING_RE.match(line)) and not line.startswith((" ", "\t")):
            sections.append(TaskSection(title=h.group(2)))
            last = None
            continue
        if last is None:
            continue
        if line.strip() == "":
            pending_blanks += 1
            continue
        indented = line.startswith(("  ", "\t"))
        if indented or (pending_blanks == 0 and not _BLOCK_OPENER_RE.match(line)):
            last.text += "\n" * (pending_blanks + 1) + _dedent2(line)
            pending_blanks = 0
        else:
            last = None
    kept = [s for s in sections if s.items or s.title is not None]
    total = sum(len(s.items) for s in kept)
    done = sum(1 for s in kept for i in s.items if i.done)
    return Tasks(sections=kept, total=total, done=done)


def count_tasks(text: str) -> tuple[int, int]:
    """(done, total) without building the item texts - the scan hot path only needs counts."""
    done = total = 0
    in_fence = False
    for line in _lines(text):
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if not in_fence and (m := _CHECKBOX_RE.match(line)):
            total += 1
            done += m.group(1) != " "
    return done, total


@dataclass
class Block:
    """A `###` requirement or a `####` scenario (or any other heading at those levels)."""

    name: str
    kind: str  # "requirement" | "scenario" | "section"
    anchor: str
    body: str
    children: list[Block] = field(default_factory=list)


@dataclass
class Group:
    """A `##` section: `Purpose`, `Requirements`, `ADDED Requirements`, ..."""

    heading: str | None
    op: str | None
    anchor: str | None
    body: str
    blocks: list[Block] = field(default_factory=list)


@dataclass
class SpecDoc:
    title: str | None
    intro: str
    groups: list[Group]
    requirement_count: int


def parse_spec(text: str) -> SpecDoc:
    slugger = _Slugger()
    title: str | None = None
    intro = ""
    groups: list[Group] = []
    group: Group | None = None
    block: Block | None = None
    child: Block | None = None
    buf: list[str] = []

    def flush() -> None:
        nonlocal intro
        body = "\n".join(buf).strip("\n")
        target = child or block or group
        if target is None:
            intro = body
        else:
            target.body = body

    in_fence = False
    for line in _lines(text):
        if _FENCE_RE.match(line):
            in_fence = not in_fence
        h = None if in_fence else _HEADING_RE.match(line)
        level = len(h.group(1)) if h else 0
        if h and level == 1 and title is None and group is None:
            title = h.group(2)
            continue
        if h and level in (2, 3, 4):
            text_ = h.group(2)
            if level == 2:
                flush()
                op = m.group(1) if (m := _DELTA_OP_RE.match(text_)) else None
                group = Group(heading=text_, op=op, anchor=slugger.slug(text_), body="")
                groups.append(group)
                block = child = None
            elif level == 3:
                flush()
                if group is None:
                    group = Group(heading=None, op=None, anchor=None, body="")
                    groups.append(group)
                block = _block(text_, slugger)
                group.blocks.append(block)
                child = None
            elif block is not None:
                flush()
                child = _block(text_, slugger)
                block.children.append(child)
            else:
                buf.append(line)
                continue
            buf = []
            continue
        buf.append(line)
    flush()
    count = sum(1 for g in groups for b in g.blocks if b.kind == "requirement")
    return SpecDoc(title=title, intro=intro, groups=groups, requirement_count=count)


def _block(heading: str, slugger: _Slugger) -> Block:
    kind = "section"
    name = heading
    for prefix, k in (("Requirement:", "requirement"), ("Scenario:", "scenario")):
        if heading.startswith(prefix):
            kind, name = k, heading[len(prefix) :].strip()
    return Block(name=name, kind=kind, anchor=slugger.slug(heading), body="")


class _Slugger:
    """GitHub-style heading slugs, de-duplicated with a numeric suffix."""

    def __init__(self) -> None:
        self.seen: dict[str, int] = {}

    def slug(self, text: str) -> str:
        base = re.sub(r"[^\w\- ]", "", text.lower()).strip().replace(" ", "-") or "section"
        n = self.seen.get(base, 0)
        self.seen[base] = n + 1
        return base if n == 0 else f"{base}-{n}"


def _lines(text: str) -> list[str]:
    return text.replace("\r\n", "\n").replace("\r", "\n").split("\n")


def _dedent2(line: str) -> str:
    """Strip up to two leading spaces: the content offset of a `- ` list marker."""
    if line.startswith("\t"):
        return line[1:]
    n = len(line) - len(line.lstrip(" "))
    return line[min(n, 2) :]
