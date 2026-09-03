#!/usr/bin/env python3
"""PostToolUse hook: after an Edit/Write to a skill's SKILL.md or a reference, return validate_skill.py's --report-only output as additionalContext so the token budget re-enters the model's context on every edit."""

import json
import subprocess
import sys
from pathlib import Path

# Housekeeping files never load as skill content (mirrors the validator's IGNORED_MD_BASENAMES); edits to them don't
# change the budget.
IGNORED_MD_BASENAMES = {"changelog.md", "contributing.md", "claude.md", "agents.md", "readme.md"}


def main() -> None:
    payload = json.load(sys.stdin)
    file_path = (payload.get("tool_input") or {}).get("file_path") or ""
    edited = Path(file_path)
    if edited.suffix.lower() != ".md" or edited.name.lower() in IGNORED_MD_BASENAMES:
        return
    # Any .md under a skill counts, not only SKILL.md: the load rating is driven by the largest reference, so editing
    # one is exactly when feedback is needed.
    skill_dir = next((p for p in edited.parents if (p / "SKILL.md").is_file()), None)
    if skill_dir is None:
        return

    validator = Path(__file__).resolve().parent / "validate_skill.py"
    result = subprocess.run(
        [sys.executable, str(validator), str(skill_dir), "--report-only"],
        capture_output=True,
        text=True,
        timeout=30,  # generous for a local file scan; prevents a hung hook stalling the session
    )
    report = (result.stdout or "").strip()
    if report:
        context = f"Skill token budget after edit:\n{report}"
        # The documented shape is the nested hookSpecificOutput.additionalContext; the top-level key is belt-and-braces
        # for versions that read it there. Keep both - extras are ignored, and one of them will land.
        print(
            json.dumps(
                {
                    "additionalContext": context,
                    "hookSpecificOutput": {
                        "hookEventName": "PostToolUse",
                        "additionalContext": context,
                    },
                }
            )
        )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # Never fail the edit over a reporting problem, but leave a trace so a validator regression doesn't silently
        # disable the report.
        print(f"hook_report_skill_tokens: {exc}", file=sys.stderr)
