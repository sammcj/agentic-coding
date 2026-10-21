"""What a change's MODIFIED requirements will do to the main spec on archive.

A port of OpenSpec's own delta reading (core/parsers/requirement-blocks.js and
utils/requirement-diff.js, as of 1.14.3), so the diff a reviewer sees is the one archive
applies. tests/test_cli_parity.py compares the two whenever the CLI is installed.
"""

from __future__ import annotations

import difflib
import re

# OpenSpec writes these with adjacent overlapping quantifiers (`\s*(.+)\s*$`), which can
# backtrack in polynomial time. These match the same lines; callers do the trimming instead.
_REQUIREMENT_RE = re.compile(r"^###\s*Requirement:(.+)$", re.IGNORECASE)
_SECTION_RE = re.compile(r"^##\s(.+)$")
_TOP_LEVEL_RE = re.compile(r"^##\s+")
_MAIN_SECTION_RE = re.compile(r"^##\s+Requirements\s*$", re.IGNORECASE)
_RENAME_RE = re.compile(r"^\s*(?:[-*+]\s*)?(FROM|TO):\s*`?###\s*Requirement:(.+)$")
_FENCE_OPEN_RE = re.compile(r"^\s*(`{3,}|~{3,})")
_FENCE_CLOSE_RE = re.compile(r"^\s*(`{3,}|~{3,})\s*$")

# Lines and their fence mask: True for a fence line or anything inside one.
Lines = tuple[list[str], list[bool]]


def requirement_changes(delta: str, main: str | None) -> list[dict]:
    """Each MODIFIED requirement in a delta, line-diffed against the main-spec block it replaces.

    Matches by exact name first, then ignoring case and spacing (flagged inexact, since archive
    will not merge it), and under its original name when the same delta renames it.
    """
    lines = _split(delta)
    renames = _rename_map(lines)
    base = _blocks(_main_section(_split(main or "")))
    out = []
    for body in _sections(lines, "modified requirements"):
        for name, raw in _blocks(body):
            lookup = renames.get(_fold(name), name)
            match = next((b for b in base if b[0] == lookup), None) or next(
                (b for b in base if _fold(b[0]) == _fold(lookup)), None
            )
            diff = line_diff(match[1], raw, context=4) if match else {"lines": [], "added": 0, "removed": 0}
            out.append(
                {
                    "name": name,
                    "base_name": match[0] if match else lookup,
                    "found": match is not None,
                    "exact": match is not None and match[0] == lookup,
                    **diff,
                }
            )
    return out


def line_diff(a: str, b: str, context: int = 3) -> dict:
    lines = []
    added = removed = 0
    # The first two lines are the ---/+++ file header, present whenever there is any diff.
    for line in list(difflib.unified_diff(a.splitlines(), b.splitlines(), lineterm="", n=context))[2:]:
        tag = line[:1] if line[:1] in "+-@" else " "
        added += tag == "+"
        removed += tag == "-"
        lines.append({"t": tag, "text": line[1:] if tag != "@" else line})
    return {"lines": lines, "added": added, "removed": removed}


def _split(text: str) -> Lines:
    lines = text.removeprefix("﻿").replace("\r\n", "\n").replace("\r", "\n").split("\n")
    mask = [False] * len(lines)
    fence: str | None = None
    for i, line in enumerate(lines):
        if fence is None:
            if m := _FENCE_OPEN_RE.match(line):
                fence = m.group(1)
                mask[i] = True
            continue
        mask[i] = True
        # Closes only on a bare run of the same character, at least as long as the opener.
        if (m := _FENCE_CLOSE_RE.match(line)) and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence):
            fence = None
    return lines, mask


def _sections(src: Lines, title: str) -> list[Lines]:
    """Bodies of every `##` section whose whole title matches, ignoring case."""
    lines, mask = src
    heads = [
        (i, m.group(1).strip())
        for i, line in enumerate(lines)
        if not mask[i] and (m := _SECTION_RE.match(line))
    ]
    out = []
    for n, (i, t) in enumerate(heads):
        end = heads[n + 1][0] if n + 1 < len(heads) else len(lines)
        if t.lower() == title:
            out.append((lines[i + 1 : end], mask[i + 1 : end]))
    return out


def _main_section(src: Lines) -> Lines:
    """The first `## Requirements` section of a main spec: the only place archive looks."""
    lines, mask = src
    start = next((i for i, line in enumerate(lines) if not mask[i] and _MAIN_SECTION_RE.match(line)), None)
    if start is None:
        return [], []
    after = range(start + 1, len(lines))
    end = next((i for i in after if not mask[i] and _TOP_LEVEL_RE.match(lines[i])), len(lines))
    return lines[start + 1 : end], mask[start + 1 : end]


def _blocks(src: Lines) -> list[tuple[str, str]]:
    """(name, raw) per requirement; a block runs to the next requirement or `##` heading."""
    lines, mask = src
    out: list[tuple[str, str]] = []
    current: list[str] | None = None
    name = ""
    for i, line in enumerate(lines):
        header = None if mask[i] else _REQUIREMENT_RE.match(line)
        if header or (not mask[i] and _TOP_LEVEL_RE.match(line)):
            if current is not None:
                out.append((name, "\n".join(current).rstrip()))
            current = [line] if header else None
            name = _requirement_name(header.group(1).lstrip()) if header else ""
        elif current is not None:
            current.append(line)
    if current is not None:
        out.append((name, "\n".join(current).rstrip()))
    return out


def _rename_map(delta: Lines) -> dict[str, str]:
    """Folded final name -> original name, following chains such as A -> B, B -> C."""
    renames: dict[str, str] = {}
    for lines, mask in _sections(delta, "renamed requirements"):
        pending: str | None = None
        for i, line in enumerate(lines):
            if mask[i] or not (m := _RENAME_RE.match(line)):
                continue
            raw = m.group(2).strip()
            name = _requirement_name(raw[:-1] if len(raw) > 1 and raw.endswith("`") else raw)
            if m.group(1) == "FROM":
                pending = name
            elif pending is not None:
                renames[_fold(name)] = renames.pop(_fold(pending), pending)
                pending = None
    return renames


def _requirement_name(raw: str) -> str:
    # A closing `#` run ends the heading only after a space or tab, so `C#` keeps its `#`.
    text = raw.rstrip(" \t")
    bare = text.rstrip("#")
    if bare != text and bare.endswith((" ", "\t")):
        text = bare
    return text.strip()


def _fold(name: str) -> str:
    return re.sub(r"\s+", " ", _requirement_name(name).lower())
