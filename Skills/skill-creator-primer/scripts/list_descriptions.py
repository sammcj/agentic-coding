#!/usr/bin/env python3
"""List each skill's directory, name and description one level under a root, read from its SKILL.md frontmatter."""

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

# Skill-list limits from SkillEvaluator's harness profiles (github.com/NVIDIA/SkillEvaluator, verified upstream on
# 2026-11-01). Claude Code gives the list 1% of the context window at 4 characters per token, so this is what a
# 200k-token window holds; Codex gives 2%. [CC-LIST-BUDGET, CX-LIST-BUDGET]
LIST_BUDGET_CHARS = 8_000
COPILOT_FULL_DESCRIPTIONS = 32  # CP-LIST-BUDGET: later skills are listed by name only

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

    total = 0
    by_name = defaultdict(list)
    for skill_md in files:
        block_match = _FRONTMATTER.match(skill_md.read_text(encoding="utf-8"))
        block = block_match.group(1) if block_match else ""
        name = _field(block, "name") or skill_md.parent.name
        desc = _field(block, "description")
        print(skill_md.parent)
        print(f"  name: {name}")
        print(f"  desc: {desc}")
        print()
        total += len(desc)
        by_name[name].append(skill_md.parent.name)

    print(f"{len(files)} skill(s), {total:,} description characters.")
    if total > LIST_BUDGET_CHARS:
        print(
            f"Over {LIST_BUDGET_CHARS:,} characters: Claude Code shortens descriptions in its skill list at a 200k-token "
            f"context window (Codex at {LIST_BUDGET_CHARS * 2:,}; both budgets grow with the window). Shorten "
            "descriptions, trigger first."
        )
    if len(files) > COPILOT_FULL_DESCRIPTIONS:
        print(
            f"Over {COPILOT_FULL_DESCRIPTIONS} skills: GitHub Copilot gives full descriptions to the first "
            f"{COPILOT_FULL_DESCRIPTIONS} only and lists the rest by name."
        )
    for name, dirs in sorted(by_name.items()):
        if len(dirs) > 1:
            print(f"Duplicate name '{name}': {', '.join(dirs)} - a loader uses one copy or lists both.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
