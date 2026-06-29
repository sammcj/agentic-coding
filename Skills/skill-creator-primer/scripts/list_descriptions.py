#!/usr/bin/env python3
"""List every skill's directory, name, and description.

Lists each skill one directory deep under a root - matching ``<root>/*/SKILL.md`` only - and
prints its directory, name, and description, read from the YAML frontmatter. A nested SKILL.md
in a subfolder (for example ``<root>/some-skill/references/SKILL.md``) is deliberately ignored,
so example or reference copies are not mistaken for real skills. Standard library only, so it
runs anywhere python3 is available - no PyYAML, ripgrep, or yq needed.

Descriptions in this ecosystem are single-line, so a line-oriented read is enough; this is a
listing aid for a human/agent review, not a strict parser.

Usage:
    python3 list_descriptions.py [root]
"""

import re
import sys
from pathlib import Path

_FRONTMATTER = re.compile(r"^---\r?\n(.*?)\r?\n---", re.DOTALL)


def _field(block, key):
    """Return the value of a top-level ``key:`` line in a frontmatter block, or ""."""
    match = re.search(rf"^{key}:\s*(.+)$", block, re.MULTILINE)
    if not match:
        return ""
    value = match.group(1).strip()
    # Strip a single layer of matching surrounding quotes, if present.
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    return value


def main(argv):
    root = Path(argv[1]) if len(argv) > 1 else Path(".")
    # One directory deep only: <root>/*/SKILL.md, never a nested references/examples copy.
    files = sorted(root.glob("*/SKILL.md"))
    if not files:
        print(f"No <skill>/SKILL.md files found one level under {root}", file=sys.stderr)
        return 1

    for skill_md in files:
        block_match = _FRONTMATTER.match(skill_md.read_text(encoding="utf-8"))
        block = block_match.group(1) if block_match else ""
        name = _field(block, "name") or skill_md.parent.name
        desc = _field(block, "description")
        print(skill_md.parent)
        print(f"  name: {name}")
        print(f"  desc: {desc}")
        print()

    print(f"{len(files)} skill(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
