#!/usr/bin/env python3
"""PostToolUse hook for the skill-creator-primer.

After any Edit/Write to a skill's Markdown (SKILL.md or a reference under a directory holding one)
while the primer is active, run validate_skill.py --report-only on that skill and inject the
token-budget and structure report back into the model's context. This is the mechanical replacement
for the user nudging "reduce the word count": the measurement re-enters context on every edit with
no model discipline required. References are included because the load rating is driven by the
largest reference - editing one is exactly when feedback is needed.

Stdlib-only and always exits 0 - a broken report must never block an edit.
"""

import json
import subprocess
import sys
from pathlib import Path

# Housekeeping files never load as skill content (mirrors the validator's
# IGNORED_MD_BASENAMES); edits to them don't change the budget.
IGNORED_MD_BASENAMES = {"changelog.md", "contributing.md", "claude.md", "agents.md", "readme.md"}


def main() -> None:
    payload = json.load(sys.stdin)
    file_path = (payload.get("tool_input") or {}).get("file_path") or ""
    edited = Path(file_path)
    if edited.suffix.lower() != ".md" or edited.name.lower() in IGNORED_MD_BASENAMES:
        return
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
        # The documented shape is the nested hookSpecificOutput.additionalContext;
        # the top-level key is belt-and-braces for versions that read it there.
        # Keep both - extras are ignored, and one of them will land.
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
        # Never fail the edit over a reporting problem, but leave a trace so a
        # validator regression doesn't silently disable the report.
        print(f"hook_report_skill_tokens: {exc}", file=sys.stderr)
