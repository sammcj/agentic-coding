# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Lint mermaid code blocks embedded in markdown.

Standard library only. Extracts ```mermaid fenced blocks and checks the
breakages that stop a diagram rendering on GitHub or in Obsidian: empty
blocks, a missing diagram type, unbalanced brackets or quotes, and style
classes that are used but never defined. Two opt-in policy checks back the
llm-wiki concept-map rules - --require-edge-labels and --max-nodes.

Usage:
    uv run scripts/lint_mermaid.py wiki/
    uv run scripts/lint_mermaid.py --require-edge-labels --max-nodes 12 wiki/topic/article.md

Exit status is 1 when any error is found (and when any warning is found
under --strict), 0 otherwise.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# Diagram-type keywords mermaid accepts on the first content line.
_DIAGRAM_TYPES = frozenset({
    "flowchart", "graph", "sequenceDiagram", "classDiagram", "stateDiagram",
    "stateDiagram-v2", "erDiagram", "journey", "gantt", "pie", "gitGraph",
    "mindmap", "timeline", "quadrantChart", "requirementDiagram", "sankey",
    "sankey-beta", "xychart-beta", "block-beta", "packet-beta", "C4Context",
})

_ARROW_RE = re.compile(r"-{2,3}>|-\.-+>|={2,3}>|--[xo]\b|-\.-+|---+")
_NODE_DEF_RE = re.compile(r"\b([A-Za-z0-9_]+)\s*[\[\(\{]")
_CLASSDEF_RE = re.compile(r"\bclassDef\s+([A-Za-z0-9_]+)")
_CLASS_TRIPLE_RE = re.compile(r":::([A-Za-z0-9_]+)")
_CLASS_STMT_RE = re.compile(r"\bclass\s+([A-Za-z0-9_,\s]+?)\s+([A-Za-z0-9_]+)\s*;?$")
_QUOTED_RE = re.compile(r'"[^"]*"')


@dataclass
class Finding:
    file: str
    line: int
    level: str  # "error" | "warn"
    message: str


@dataclass
class Block:
    fence_line: int          # 1-based line of the opening ```mermaid fence
    lines: list[str]         # body lines, excluding the fences


def find_blocks(text: str) -> list[Block]:
    """Return every fenced ```mermaid block in a markdown document."""
    blocks: list[Block] = []
    in_block = False
    fence_line = 0
    body: list[str] = []
    for i, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if not in_block and stripped.startswith("```") and stripped[3:].strip().lower() == "mermaid":
            in_block, fence_line, body = True, i, []
        elif in_block and stripped.startswith("```"):
            blocks.append(Block(fence_line, body))
            in_block = False
        elif in_block:
            body.append(raw)
    if in_block:  # unterminated fence; lint what we captured
        blocks.append(Block(fence_line, body))
    return blocks


def _content_lines(lines: list[str]) -> list[tuple[int, str]]:
    """Body lines paired with their offset from the fence, skipping comments."""
    out: list[tuple[int, str]] = []
    for offset, raw in enumerate(lines, start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("%%"):
            continue
        out.append((offset, raw))
    return out


def check_type(block: Block, content: list[tuple[int, str]]) -> list[Finding]:
    if not content:
        return [Finding("", block.fence_line, "error", "empty mermaid block")]
    first = content[0][1].strip()
    token = first.split()[0].split(":")[0] if first else ""
    if token not in _DIAGRAM_TYPES:
        return [Finding("", block.fence_line, "warn",
                        f"first line is not a known diagram type: {token!r}")]
    return []


def check_balance(block: Block, content: list[tuple[int, str]]) -> list[Finding]:
    """Bracket and quote balance, ignoring text inside double quotes."""
    findings: list[Finding] = []
    pairs = {"[": "]", "(": ")", "{": "}"}
    counts = dict.fromkeys("[](){}", 0)
    quotes = 0
    for _, raw in content:
        quotes += raw.count('"')
        bare = _QUOTED_RE.sub("", raw)
        for ch in bare:
            if ch in counts:
                counts[ch] += 1
    for opener, closer in pairs.items():
        if counts[opener] != counts[closer]:
            findings.append(Finding("", block.fence_line, "error",
                                    f"unbalanced '{opener}{closer}': "
                                    f"{counts[opener]} open, {counts[closer]} close"))
    if quotes % 2:
        findings.append(Finding("", block.fence_line, "error",
                                "odd number of double quotes (an unclosed label)"))
    return findings


def check_classes(block: Block, content: list[tuple[int, str]]) -> list[Finding]:
    defined: set[str] = set()
    used: set[tuple[int, str]] = set()
    for offset, raw in content:
        defined.update(_CLASSDEF_RE.findall(raw))
        for name in _CLASS_TRIPLE_RE.findall(raw):
            used.add((block.fence_line + offset - 1, name))
        stmt = _CLASS_STMT_RE.search(raw.strip())
        if stmt and not raw.strip().startswith("classDef"):
            used.add((block.fence_line + offset - 1, stmt.group(2)))
    return [
        Finding("", line, "warn", f"style class {name!r} used but never defined")
        for line, name in sorted(used)
        if name not in defined
    ]


def check_edge_labels(block: Block, content: list[tuple[int, str]]) -> list[Finding]:
    findings: list[Finding] = []
    for offset, raw in content:
        if not _ARROW_RE.search(raw):
            continue
        bare = _QUOTED_RE.sub("", raw)
        # A labelled edge carries a pipe label (-->|x|) or an inline -- x --> label.
        if "|" in raw or re.search(r"--\s*[^->|]+\s*--", bare):
            continue
        findings.append(Finding("", block.fence_line + offset - 1, "warn",
                                "edge has no relationship label"))
    return findings


def check_node_count(block: Block, content: list[tuple[int, str]], limit: int) -> list[Finding]:
    nodes: set[str] = set()
    for _, raw in content:
        nodes.update(_NODE_DEF_RE.findall(_QUOTED_RE.sub("", raw)))
    if len(nodes) > limit:
        return [Finding("", block.fence_line, "warn",
                        f"{len(nodes)} nodes exceeds the {limit}-node guideline; "
                        "the theme may be too broad")]
    return []


def lint_text(text: str, opts: argparse.Namespace) -> list[Finding]:
    findings: list[Finding] = []
    for block in find_blocks(text):
        content = _content_lines(block.lines)
        findings += check_type(block, content)
        findings += check_balance(block, content)
        findings += check_classes(block, content)
        if opts.require_edge_labels:
            findings += check_edge_labels(block, content)
        if opts.max_nodes:
            findings += check_node_count(block, content, opts.max_nodes)
    return findings


def iter_markdown(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for arg in paths:
        p = Path(arg)
        if p.is_dir():
            files.extend(sorted(p.rglob("*.md")))
        elif p.is_file():
            files.append(p)
        else:
            print(f"Warning: no such path: {arg}", file=sys.stderr)
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint mermaid blocks in markdown.")
    parser.add_argument("paths", nargs="*", default=["."],
                        help="markdown files or directories (default: .)")
    parser.add_argument("--require-edge-labels", action="store_true",
                        help="warn on flowchart edges with no relationship label")
    parser.add_argument("--max-nodes", type=int, default=0,
                        help="warn when a block exceeds this node count (0 disables)")
    parser.add_argument("--strict", action="store_true",
                        help="treat warnings as failures")
    parser.add_argument("--json", action="store_true", help="emit findings as JSON")
    opts = parser.parse_args()

    all_findings: list[Finding] = []
    for path in iter_markdown(opts.paths):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"Warning: could not read {path}: {exc}", file=sys.stderr)
            continue
        for f in lint_text(text, opts):
            f.file = str(path)
            all_findings.append(f)

    errors = sum(1 for f in all_findings if f.level == "error")
    warnings = sum(1 for f in all_findings if f.level == "warn")

    if opts.json:
        print(json.dumps({
            "findings": [vars(f) for f in all_findings],
            "errors": errors, "warnings": warnings,
        }, indent=2))
    else:
        for f in all_findings:
            print(f"{f.file}:{f.line}: {f.level}: {f.message}")
        if all_findings:
            print(f"\n{errors} error(s), {warnings} warning(s)")
        else:
            print("No mermaid issues found.")

    if errors or (opts.strict and warnings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
