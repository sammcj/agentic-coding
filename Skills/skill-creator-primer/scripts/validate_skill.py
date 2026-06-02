#!/usr/bin/env python3
# /// script
# dependencies = [
#   "skills-ref @ git+https://github.com/agentskills/agentskills.git#subdirectory=skills-ref",
# ]
# requires-python = ">=3.11"
# ///
"""
Validate a skill against the Agent Skills specification.

Uses the official skills-ref reference library from:
https://github.com/agentskills/agentskills/tree/main/skills-ref

skills-ref's allowlist only knows the Agent Skills spec fields, so it rejects
the Claude Code extension fields (argument-hint, model, etc.) as "unexpected".
We widen the allowlist with those documented extensions before validating, so a
valid Claude Code skill passes while genuine typos are still caught.
See https://code.claude.com/docs/en/skills#frontmatter-reference
"""

import sys
from pathlib import Path

try:
    from skills_ref import validate
    from skills_ref import validator
except ModuleNotFoundError:
    print("Error: skills_ref not found. Run this script with uv:")
    print(f"  uv run {sys.argv[0]} <skill_directory>")
    sys.exit(1)

# Claude Code-specific frontmatter fields not covered by the Agent Skills spec.
CLAUDE_CODE_EXTENSION_FIELDS = {
    "argument-hint",
    "model",
    "effort",
    "context",
    "disable-model-invocation",
    "user-invocable",
    "agent",
}

validator.ALLOWED_FIELDS = validator.ALLOWED_FIELDS | CLAUDE_CODE_EXTENSION_FIELDS


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: uv run validate_skill.py <skill_directory>")
        sys.exit(1)

    skill_path = Path(sys.argv[1])
    errors = validate(skill_path)

    if errors:
        print(f"Validation failed ({len(errors)} error(s)):")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)

    print("Skill is valid!")


if __name__ == "__main__":
    main()
