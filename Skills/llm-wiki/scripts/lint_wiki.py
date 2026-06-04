#!/usr/bin/env python3
"""Deterministic structural lint for an llm-wiki.

Reports the deterministic checks from references/lint.md that are pure
file/link/frontmatter logic: frontmatter completeness and supersession
consistency, index <-> article agreement, internal link resolution, raw
reference resolution, and the local/ leak guard. It is read-only and prints
only findings - the agent applies the fixes and handles the judgement-tier
(heuristic) checks itself.

Why a script: these checks tempt an agent to improvise a one-off program and
pipe it through the shell as a heredoc, where `!` gets escaped and corrupts
the code. A committed helper removes that failure mode. Concept-map mermaid
syntax has its own validator, scripts/lint_mermaid.py.

stdlib only; writes nothing. Run with uv when available:

    uv run scripts/lint_wiki.py [ROOT] [--checks frontmatter,index,links,raw,local] [--json]

ROOT is the project root holding raw/ and wiki/ (default: current directory).
Exit status: 0 if clean, 1 if any finding, 2 on usage error.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

SPECIAL = {"README.md", "index.md", "log.md", "gaps.md"}
REQUIRED = ["title", "type", "topic", "created", "updated", "status"]
CALLOUT = "[!warning] Superseded by"
ALL_CHECKS = ["frontmatter", "index", "links", "raw", "local"]

# Markdown links [text](target), excluding image links (leading !) and any
# optional "title" after the target. Captures the raw target.
LINK_RE = re.compile(r'(?<!!)\[[^\]]*\]\(\s*<?([^)>\s]+)>?(?:\s+"[^"]*")?\s*\)')
# Fenced code blocks and inline code, stripped before link scanning so a
# mermaid concept-map block or a markdown example never yields a false link.
CODE_RE = re.compile(r'```.*?```|`[^`]*`', re.DOTALL)


class Finding:
    __slots__ = ("check", "path", "msg")

    def __init__(self, check: str, path, msg: str):
        self.check = check
        self.path = str(path)
        self.msg = msg


def parse_frontmatter(text: str):
    """Return (frontmatter dict, body). Minimal scalar YAML; stdlib only."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return {}, text
    fm = {}
    for line in lines[1:end]:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in line:
            continue
        key, _, val = line.partition(":")
        fm[key.strip()] = val.strip()
    return fm, "\n".join(lines[end + 1:])


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def is_external(target: str) -> bool:
    return target.startswith(("http://", "https://", "mailto:", "#")) or "://" in target


def link_targets(text: str):
    text = CODE_RE.sub("", text)
    for match in LINK_RE.finditer(text):
        target = match.group(1).strip()
        if target and not is_external(target):
            yield target


def article_files(wiki: Path):
    for path in sorted(wiki.rglob("*.md")):
        if path.name not in SPECIAL:
            yield path


def under(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False


def unique_match(base: Path, name: str):
    matches = list(base.rglob(name))
    return matches[0] if len(matches) == 1 else None


def suggest(missing_from: Path, base: Path, name: str) -> str:
    match = unique_match(base, name)
    if not match:
        return ""
    rel = os.path.relpath(match, missing_from.parent)
    return f" (did you mean {rel}?)"


def check_frontmatter(wiki: Path):
    for art in article_files(wiki):
        fm, body = parse_frontmatter(read(art))
        if not fm:
            yield Finding("frontmatter", art, "missing or malformed YAML frontmatter")
            continue
        for field in REQUIRED:
            if not fm.get(field):
                yield Finding("frontmatter", art, f"missing required field: {field}")
        if fm.get("status") == "stale":
            sb = fm.get("superseded_by", "")
            if not sb:
                yield Finding("frontmatter", art, "status: stale but no superseded_by set")
            else:
                dest = (art.parent / sb.split("#")[0]).resolve()
                if not dest.exists():
                    yield Finding("frontmatter", art,
                                  f"superseded_by points to a missing file: {sb}")
            if CALLOUT not in body:
                yield Finding("frontmatter", art,
                              "status: stale but no supersession callout in body")


def check_index(wiki: Path):
    index = wiki / "index.md"
    if not index.exists():
        yield Finding("index", index, "wiki/index.md is missing")
        return
    listed = set()
    for target in link_targets(read(index)):
        base = target.split("#")[0]
        if not base or Path(base).name in SPECIAL or not base.endswith(".md"):
            continue
        dest = (index.parent / base).resolve()
        listed.add(dest)
        if not dest.exists():
            yield Finding("index", index, f"index entry points to a missing file: {target}")
    for art in article_files(wiki):
        if art.resolve() not in listed:
            yield Finding("index", art, "article is missing from wiki/index.md")


def check_links(wiki: Path, raw: Path, local: Path):
    """Internal (wiki) and raw link resolution, scanning article bodies only."""
    for art in article_files(wiki):
        for target in link_targets(read(art)):
            base = target.split("#")[0]
            if not base:
                continue
            name = Path(base).name
            if name in SPECIAL:  # links to special files are exempt (per lint.md)
                continue
            dest = (art.parent / base).resolve()
            if under(dest, local):
                continue  # handled by the local-leak guard
            if under(dest, raw):
                if not dest.exists():
                    yield Finding("raw", art,
                                  f"broken raw link: {target}{suggest(art, raw, name)}")
            elif not dest.exists():
                yield Finding("links", art,
                              f"broken link: {target}{suggest(art, wiki, name)}")


def check_local(root: Path, wiki: Path, raw: Path, local: Path):
    """No committed file may link into local/. Scans wiki/, raw/, and the root
    SKILL.md and CLAUDE.md (index/log/gaps/README live under wiki/)."""
    files = list(wiki.rglob("*.md"))
    if raw.exists():
        files += list(raw.rglob("*.md"))
    for name in ("SKILL.md", "CLAUDE.md"):
        if (root / name).exists():
            files.append(root / name)
    for path in sorted(set(files)):
        for target in link_targets(read(path)):
            base = target.split("#")[0]
            if not base:
                continue
            dest = (path.parent / base).resolve()
            if under(dest, local):
                yield Finding("local", path, f"committed file links into local/: {target}")


def run_checks(root: Path, checks) -> list:
    wiki, raw, local = root / "wiki", root / "raw", root / "local"
    findings = []
    if "frontmatter" in checks:
        findings += check_frontmatter(wiki)
    if "index" in checks:
        findings += check_index(wiki)
    if "links" in checks or "raw" in checks:
        for finding in check_links(wiki, raw, local):
            if finding.check in checks:
                findings.append(finding)
    if "local" in checks:
        findings += check_local(root, wiki, raw, local)
    seen, unique = set(), []
    for finding in findings:
        key = (finding.check, finding.path, finding.msg)
        if key not in seen:
            seen.add(key)
            unique.append(finding)
    return unique


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Deterministic structural lint for an llm-wiki.")
    parser.add_argument("root", nargs="?", default=".",
                        help="project root holding raw/ and wiki/ (default: .)")
    parser.add_argument("--checks", default="all",
                        help=f"comma-separated subset of: {','.join(ALL_CHECKS)} (default: all)")
    parser.add_argument("--json", action="store_true", help="emit findings as JSON")
    return parser.parse_args(argv)


def main(argv) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    if not (root / "wiki").is_dir():
        print(f"error: no wiki/ under {root}. Run an ingest first to initialise the wiki.",
              file=sys.stderr)
        return 2
    if args.checks == "all":
        checks = set(ALL_CHECKS)
    else:
        checks = {c.strip() for c in args.checks.split(",") if c.strip()}
        unknown = checks - set(ALL_CHECKS)
        if unknown:
            print(f"error: unknown check(s): {', '.join(sorted(unknown))}. "
                  f"Choose from: {', '.join(ALL_CHECKS)}", file=sys.stderr)
            return 2

    findings = run_checks(root, checks)

    if args.json:
        print(json.dumps([{"check": f.check,
                           "path": os.path.relpath(f.path, root),
                           "message": f.msg} for f in findings], indent=2))
    else:
        for check in ALL_CHECKS:
            group = [f for f in findings if f.check == check]
            if not group:
                continue
            print(f"[{check}]")
            for finding in group:
                print(f"  {os.path.relpath(finding.path, root)}: {finding.msg}")
        if not findings:
            print("No deterministic issues found.")

    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
