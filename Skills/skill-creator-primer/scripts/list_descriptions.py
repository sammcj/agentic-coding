#!/usr/bin/env python3
"""List each skill's directory, name and description one level under a root, read from its SKILL.md frontmatter."""

import argparse
import re
import sys
from pathlib import Path

# A line-oriented read rather than a YAML parser: descriptions in this ecosystem are single-line, and this is a listing
# aid for review, not a strict parser. Keeps the script stdlib-only.
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


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "root", nargs="?", default=".", help="directory holding <skill>/SKILL.md entries (default: %(default)s)"
    )
    root = Path(p.parse_args(argv).root)
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
    raise SystemExit(main())
