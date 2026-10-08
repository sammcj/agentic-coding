"""The installed OpenSpec CLI's command tree, read from its own `--help` output.

Asking the CLI keeps the reference in step with whichever version is installed. Each help call
costs ~0.1s, so a tree of ~40 commands is fetched in parallel and kept for the process lifetime.
"""

from __future__ import annotations

import re
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from . import vcs
from .schemas import cli

_SECTION_RE = re.compile(r"^([A-Z][\w ]*):\s*$")
_ITEM_RE = re.compile(r"^  (\S.*?)(?:\s{2,}(\S.*))?$")
_WORKERS = 8  # enough to fetch the whole tree in well under a second
_MAX_DEPTH = 3  # OpenSpec nests two levels (`openspec new change`); one spare
_SKIP_COMMANDS = {"help"}
_SKIP_OPTIONS = {"-h, --help"}


def parse_help(text: str) -> dict[str, Any]:
    """Split commander-style help into usage, description and its titled sections."""
    usage, description, sections = "", [], {}
    current: list[dict[str, str]] | None = None
    for line in text.splitlines():
        if not line.strip():
            continue
        if line.startswith("Usage:"):
            usage = line[len("Usage:") :].strip()
        elif m := _SECTION_RE.match(line):
            current = sections.setdefault(m.group(1).lower(), [])
        elif current is None:
            description.append(line.strip())
        elif item := _ITEM_RE.match(line):
            current.append({"term": item.group(1).strip(), "desc": (item.group(2) or "").strip()})
        elif current:
            # commander wraps long descriptions onto lines indented past the term column
            last = current[-1]
            last["desc"] = f"{last['desc']} {line.strip()}".strip()
    return {"usage": usage, "description": " ".join(description), "sections": sections}


def _names(term: str) -> list[str]:
    """`list|ls [options]` -> ["list", "ls"]: the command name, then its aliases."""
    return term.split()[0].split("|")


def _usage_path(usage: str, depth: int) -> list[str]:
    """`openspec store list|ls [options]` at depth 2 -> ["store", "list"]."""
    return [_names(t)[0] for t in usage.split()[1 : depth + 1]]


def _command_entry(path: list[str], help_text: str) -> dict[str, Any]:
    parsed = parse_help(help_text)
    sections = parsed["sections"]
    subs = [c for c in sections.get("commands", []) if _names(c["term"])[0] not in _SKIP_COMMANDS]
    return {
        "path": path,
        "aliases": [],
        "usage": parsed["usage"],
        "description": parsed["description"],
        "arguments": sections.get("arguments", []),
        "options": [o for o in sections.get("options", []) if o["term"] not in _SKIP_OPTIONS],
        "children": [_names(c["term"])[0] for c in subs],
        "child_aliases": {_names(c["term"])[0]: _names(c["term"])[1:] for c in subs},
    }


class CommandCatalog:
    def __init__(self, cwd: Path) -> None:
        self.cwd = cwd
        self._lock = threading.Lock()
        self._cached: dict[str, Any] | None = None

    def get(self) -> dict[str, Any]:
        with self._lock:
            if self._cached is None:
                result = self._fetch()
                # Only a whole answer is kept: a missing CLI may be installed while the server
                # runs, and a help call that timed out under load may succeed next time.
                if result["error"] is None and not result["partial"]:
                    self._cached = result
                return result
            return self._cached

    def _help(self, path: list[str]) -> str | None:
        proc = vcs.run_result([cli(), *path, "--help"], self.cwd)
        return proc.stdout if proc and proc.returncode == 0 and proc.stdout.strip() else None

    def _fetch(self) -> dict[str, Any]:
        version = vcs.run([cli(), "--version"], self.cwd)
        root_help = self._help([])
        if root_help is None:
            error = f"could not run `{cli()} --help`"
            return {"version": None, "commands": [], "global_options": [], "error": error, "partial": False}
        root = _command_entry([], root_help)
        commands: list[dict[str, Any]] = []
        partial = False
        with ThreadPoolExecutor(_WORKERS) as pool:
            level = [[name] for name in root["children"]]
            while level:
                helps = list(pool.map(self._help, level))
                next_level = []
                for path, text in zip(level, helps, strict=True):
                    if text is None:
                        partial = True
                        continue
                    entry = _command_entry(path, text)
                    # An unknown name gets its parent's help back; following it would never end.
                    if _usage_path(entry["usage"], len(path)) != path:
                        continue
                    commands.append(entry)
                    if len(path) < _MAX_DEPTH:
                        next_level.extend([*path, child] for child in entry["children"])
                level = next_level
        by_path = {tuple(c["path"]): c for c in commands}
        ordered: list[dict[str, Any]] = []

        # Parents first, in the CLI's own order.
        def walk(prefix: tuple[str, ...], parent: dict[str, Any]) -> None:
            for name in parent["children"]:
                if entry := by_path.get((*prefix, name)):
                    entry["aliases"] = parent["child_aliases"].get(name, [])
                    ordered.append(entry)
                    walk((*prefix, name), entry)

        walk((), root)
        return {
            "version": (version or "").strip() or None,
            "description": root["description"],
            "global_options": root["options"],
            "commands": ordered,
            "error": None,
            "partial": partial,
        }
