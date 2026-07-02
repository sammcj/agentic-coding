#!/usr/bin/env python3
# /// script
# dependencies = [
#   "skills-ref @ git+https://github.com/agentskills/agentskills.git#subdirectory=skills-ref",
#   "pyyaml>=6",
# ]
# requires-python = ">=3.11"
# ///
"""
Validate a skill against the Agent Skills specification.

Uses the official skills-ref reference library for the actual spec checks
(https://github.com/agentskills/agentskills/tree/main/skills-ref), with two
deliberate adaptations for how Netwealth authors skills:

1. Frontmatter is parsed with standard PyYAML, not skills-ref's StrictYAML loader.
   StrictYAML rejects flow-style arrays ("allowed-tools: [Read]") on style grounds,
   but those are valid YAML, valid per the spec, and exactly what the real consumers
   (Claude Code, Copilot) accept and what this repo's generator emits. PyYAML matches
   the real loaders, so a compliant skill no longer fails on a style preference.

2. skills-ref's field allowlist only knows the six Agent Skills spec fields, so it
   errors on every Claude Code extension field (argument-hint, model, when_to_use, ...)
   and goes stale as Claude Code adds more. So we run the spec's real checks (name,
   description, compatibility, dir match) as hard errors via validator.validate_metadata,
   and downgrade unknown-field detection to a WARNING: documented extensions pass clean,
   newer/community fields don't block, and typos still surface as a visible warning.

Field list verified against the official docs:
https://code.claude.com/docs/en/skills#frontmatter-reference

On a valid skill it also prints a token-budget estimate across the Markdown that
SKILL.md references (transitively), using the chars/N heuristic below; pass
--tiktoken to count with the real tokeniser instead.
"""

import argparse
import re
import sys
from pathlib import Path

try:
    import yaml
except ModuleNotFoundError:
    print("Error: dependencies not found. Run this script with uv:")
    print(f"  uv run {sys.argv[0]} <skill_directory>")
    sys.exit(1)

_FRONTMATTER_RE = re.compile(r"^---\r?\n(.*?)\r?\n---", re.DOTALL)

# Token-budget estimate. The chars/N heuristic is a dependency-free stand-in for a
# real tokeniser; N is calibrated against tiktoken's o200k_base BPE (a reproducible
# proxy for Claude's unpublished tokeniser), measured at ~4.12 chars/token over ~60
# sampled skills. This is the single calibration source: toolkit's corpus checks
# import estimate_tokens from here rather than keeping their own. Pass --tiktoken to
# count with the real tokeniser instead (needs tiktoken: run via `uv run --with tiktoken`).
CHARS_PER_TOKEN = 4.12
TIKTOKEN_ENCODING = "o200k_base"
_TOKEN_RATINGS = ((5_000, "Great"), (9_000, "Good"), (12_000, "OK"))
_MD_REF = re.compile(r"[\w./-]+\.md")


def referenced_md_files(skill_dir: Path) -> list[Path]:
    """Markdown files reachable from SKILL.md by following .md references.

    Starts at SKILL.md and transitively adds any .md path it mentions, resolved
    against the skill root and the referencing file. Markdown that nothing links to
    (a stray README.md, scratch notes beside the skill) is excluded, matching what
    actually loads into an agent's context.
    """
    skill_dir = Path(skill_dir).resolve()
    seen: set[Path] = set()
    queue = [skill_dir / "SKILL.md"]
    while queue:
        current = queue.pop().resolve()
        if current in seen or not current.is_file():
            continue
        seen.add(current)
        text = current.read_text(encoding="utf-8", errors="ignore")
        for match in _MD_REF.finditer(text):
            for base in (skill_dir, current.parent):
                candidate = (base / match.group(0)).resolve()
                if candidate.is_file() and candidate not in seen:
                    queue.append(candidate)
    return sorted(seen)


def estimate_tokens(text: str) -> int:
    """Estimate tokens for a string via the calibrated chars/N heuristic."""
    return round(len(text) / CHARS_PER_TOKEN)


def tiktoken_tokens(text: str) -> int:
    """Count tokens exactly with tiktoken's o200k_base BPE. Needs the tiktoken
    package; exits with a hint when it is missing."""
    try:
        import tiktoken  # pyright: ignore[reportMissingImports]  # opt-in: uv run --with tiktoken
    except ModuleNotFoundError:
        print("Error: tiktoken not installed. Run it with the package available:")
        print(f"  uv run --with tiktoken {sys.argv[0]} <skill_directory> --tiktoken")
        sys.exit(1)
    return len(tiktoken.get_encoding(TIKTOKEN_ENCODING).encode(text))


def token_rating(tokens: int) -> str:
    """Map a token count to a budget rating label."""
    for ceiling, label in _TOKEN_RATINGS:
        if tokens <= ceiling:
            return label
    return "Poor"


def token_report(skill_dir: Path, use_tiktoken: bool = False) -> str:
    """One-line token-budget estimate across a skill's referenced Markdown."""
    files = referenced_md_files(skill_dir)
    text = "".join(f.read_text(encoding="utf-8", errors="ignore") for f in files)
    if use_tiktoken:
        tokens = tiktoken_tokens(text)
        method = f"tiktoken {TIKTOKEN_ENCODING}"
    else:
        tokens = estimate_tokens(text)
        method = f"estimate, chars/{CHARS_PER_TOKEN} heuristic"
    return (
        f"Tokens: {tokens} across {len(files)} referenced .md file(s) "
        f"[{token_rating(tokens)}] ({method})"
    )


def parse_frontmatter(text: str) -> dict:
    """Parse a SKILL.md's leading YAML frontmatter with a standard YAML loader.

    Raises ValueError if there is no frontmatter block or it is not a mapping, and
    propagates yaml.YAMLError for malformed YAML (e.g. an unquoted description with a
    bare colon, which is a genuine error the real loaders would also reject).
    """
    match = _FRONTMATTER_RE.match(text)
    if match is None:
        raise ValueError("No YAML frontmatter block found at the top of SKILL.md")
    data = yaml.safe_load(match.group(1))
    if not isinstance(data, dict):
        raise ValueError("Frontmatter is not a YAML mapping")
    return data


# Claude Code extension fields documented at code.claude.com/docs/en/skills
# (verified 2026-07). Valid in Claude Code but outside the cross-vendor spec.
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
    "paths",
    "hooks",
    "shell",
}


def _load_skills_ref():
    """Import skills-ref lazily, so the token estimator and frontmatter parser
    work without it; only the spec validation needs it. Exit with the run-via-uv
    hint when it is missing."""
    try:
        from skills_ref import validator  # pyright: ignore[reportMissingImports]  # PEP 723 dep
        from skills_ref.parser import find_skill_md  # pyright: ignore[reportMissingImports]
    except ModuleNotFoundError:
        print("Error: dependencies not found. Run this script with uv:")
        print(f"  uv run {sys.argv[0]} <skill_directory>")
        sys.exit(1)
    return validator, find_skill_md


def lint(skill_dir: Path) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for a skill directory."""
    skill_dir = Path(skill_dir)

    if not skill_dir.exists():
        return [f"Path does not exist: {skill_dir}"], []
    if not skill_dir.is_dir():
        return [f"Not a directory: {skill_dir}"], []

    validator, find_skill_md = _load_skills_ref()

    # Agent Skills spec fields (cross-vendor), sourced from skills-ref's own
    # allowlist so it tracks the reference library: name, description, license,
    # allowed-tools, metadata, compatibility.
    spec_fields = set(validator.ALLOWED_FIELDS)
    known_fields = spec_fields | CLAUDE_CODE_FIELDS

    skill_md = find_skill_md(skill_dir)
    if skill_md is None:
        return ["Missing required file: SKILL.md"], []

    try:
        metadata = parse_frontmatter(skill_md.read_text())
    except (yaml.YAMLError, ValueError) as e:
        return [f"Invalid YAML frontmatter: {e}"], []

    # Unknown fields are warnings, not errors: a typo, or a field newer than this
    # linter. Either way, surface it without failing the build.
    warnings = [
        f"Unrecognised frontmatter field '{field}' "
        "(typo, or newer than this linter knows). "
        "See https://code.claude.com/docs/en/skills#frontmatter-reference"
        for field in sorted(set(metadata) - known_fields)
    ]

    # Run the spec's real checks as hard errors. Strip non-spec fields first so
    # skills-ref's own allowlist doesn't re-flag the extensions we just allowed.
    spec_metadata = {k: v for k, v in metadata.items() if k in spec_fields}
    errors = validator.validate_metadata(spec_metadata, skill_dir)

    return errors, warnings


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate a skill against the Agent Skills spec and report its token budget."
    )
    parser.add_argument("skill_directory")
    parser.add_argument(
        "--tiktoken",
        action="store_true",
        help="count tokens with the tiktoken BPE tokeniser instead of the chars/N "
        "heuristic (needs the tiktoken package; run via `uv run --with tiktoken`)",
    )
    args = parser.parse_args()

    skill_dir = Path(args.skill_directory)
    errors, warnings = lint(skill_dir)

    for warning in warnings:
        print(f"Warning: {warning}")

    if errors:
        print(f"Validation failed ({len(errors)} error(s)):")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)

    print(token_report(skill_dir, use_tiktoken=args.tiktoken))
    print("Skill is valid!" if not warnings else "Skill is valid (with warnings).")


if __name__ == "__main__":
    main()
