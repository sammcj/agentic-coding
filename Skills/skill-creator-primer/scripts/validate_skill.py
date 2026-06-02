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

skills-ref's allowlist only knows the six Agent Skills spec fields, so it errors
on every Claude Code extension field (argument-hint, model, when_to_use, ...) as
"unexpected". That allowlist also goes stale as Claude Code adds fields. So we
run the spec's real checks (name, description, compatibility, YAML, dir match)
as hard errors, and downgrade unknown-field detection to a WARNING: documented
extensions pass clean, newer/community fields don't block, and typos still show
up as a visible warning. Field list verified against the official docs:
https://code.claude.com/docs/en/skills#frontmatter-reference
"""

import sys
from pathlib import Path

try:
    from skills_ref import validator
    from skills_ref.errors import ParseError
    from skills_ref.parser import find_skill_md, parse_frontmatter
except ModuleNotFoundError:
    print("Error: skills_ref not found. Run this script with uv:")
    print(f"  uv run {sys.argv[0]} <skill_directory>")
    sys.exit(1)

# Agent Skills spec fields (cross-vendor). Sourced from skills-ref's own allowlist
# so it tracks the reference library: name, description, license, allowed-tools,
# metadata, compatibility.
SPEC_FIELDS = set(validator.ALLOWED_FIELDS)

# Claude Code extension fields documented at code.claude.com/docs/en/skills
# (verified 2026-06). Valid in Claude Code but outside the cross-vendor spec.
CLAUDE_CODE_FIELDS = {
    "when_to_use",
    "argument-hint",
    "arguments",
    "disable-model-invocation",
    "user-invocable",
    "allowed-tools",  # also in the spec; listed for completeness
    "disallowed-tools",
    "model",
    "effort",
    "context",
    "agent",
}

KNOWN_FIELDS = SPEC_FIELDS | CLAUDE_CODE_FIELDS


def lint(skill_dir: Path) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for a skill directory."""
    skill_dir = Path(skill_dir)

    if not skill_dir.exists():
        return [f"Path does not exist: {skill_dir}"], []
    if not skill_dir.is_dir():
        return [f"Not a directory: {skill_dir}"], []

    skill_md = find_skill_md(skill_dir)
    if skill_md is None:
        return ["Missing required file: SKILL.md"], []

    try:
        metadata, _ = parse_frontmatter(skill_md.read_text())
    except ParseError as e:
        return [str(e)], []

    # Unknown fields are warnings, not errors: a typo, or a field newer than this
    # linter. Either way, surface it without failing the build.
    warnings = [
        f"Unrecognised frontmatter field '{field}' "
        "(typo, or newer than this linter knows). "
        "See https://code.claude.com/docs/en/skills#frontmatter-reference"
        for field in sorted(set(metadata) - KNOWN_FIELDS)
    ]

    # Run the spec's real checks as hard errors. Strip non-spec fields first so
    # skills-ref's own allowlist doesn't re-flag the extensions we just allowed.
    spec_metadata = {k: v for k, v in metadata.items() if k in SPEC_FIELDS}
    errors = validator.validate_metadata(spec_metadata, skill_dir)

    return errors, warnings


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: uv run validate_skill.py <skill_directory>")
        sys.exit(1)

    errors, warnings = lint(Path(sys.argv[1]))

    for warning in warnings:
        print(f"Warning: {warning}")

    if errors:
        print(f"Validation failed ({len(errors)} error(s)):")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)

    print("Skill is valid!" if not warnings else "Skill is valid (with warnings).")


if __name__ == "__main__":
    main()
