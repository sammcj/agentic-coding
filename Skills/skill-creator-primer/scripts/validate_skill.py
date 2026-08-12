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
deliberate adaptations for how skills are authored in practice:

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

3. The primer's description word-count rule is enforced on top of the spec checks:
   a warning outside the 30-55 aim, a hard error over 65.

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

# yaml is only needed for the spec checks (lint); the token/structure reports
# are stdlib-only so --report-only runs with plain python3 (the post-edit hook
# relies on this). The missing-dep error is raised where lint needs it.
try:
    import yaml
except ModuleNotFoundError:
    yaml = None

_FRONTMATTER_RE = re.compile(r"^---\r?\n(.*?)\r?\n---", re.DOTALL)

# Description word-count rule from the primer's Skill Description Checklist:
# aim for 30-55 words, hard cap 65. Descriptions share the agent's always-loaded
# token budget with every other skill, so length is policed mechanically here
# rather than by eyeballing.
DESCRIPTION_WORDS_MIN = 30
DESCRIPTION_WORDS_WARN = 55
DESCRIPTION_WORDS_FAIL = 65


def description_word_count(description: str) -> int:
    """Count words as whitespace tokens containing at least one alphanumeric
    character, so markdown dashes and bare punctuation don't inflate the count."""
    return sum(1 for token in str(description).split() if any(c.isalnum() for c in token))

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

# Fence handling follows CommonMark: an opener is 3+ backticks or tildes (info
# string allowed), the closer is the same character, at least as long, alone on
# its line. Matching opener to closer stops ``` examples inside a ````/~~~
# fence from toggling state.
_FENCE_OPEN = re.compile(r"^(`{3,}|~{3,})")


def _fence_open(stripped: str) -> str | None:
    """The fence marker if this stripped line opens a fence, else None."""
    m = _FENCE_OPEN.match(stripped)
    return m.group(1) if m else None


def _fence_close(stripped: str, marker: str) -> bool:
    """True if this stripped line closes a fence opened with `marker`."""
    return stripped.startswith(marker) and stripped == stripped[:1] * len(stripped)

# Repo housekeeping files are never loaded as skill content, so prose mentions of
# them (e.g. a "DO NOT create README.md, CHANGELOG.md..." list) must not drag them
# into the token count. Matched on basename, case-insensitively.
IGNORED_MD_BASENAMES = {"changelog.md", "contributing.md", "claude.md", "agents.md", "readme.md"}


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
        text = current.read_text(encoding="utf-8-sig", errors="ignore")
        fence: str | None = None
        for line in text.splitlines():
            stripped = line.strip()
            if fence is not None:
                # .md mentions inside fenced code are example text, not loads
                if _fence_close(stripped, fence):
                    fence = None
                continue
            if (opened := _fence_open(stripped)) is not None:
                fence = opened
                continue
            for match in _MD_REF.finditer(line):
                ref = match.group(0)
                if Path(ref).name.lower() in IGNORED_MD_BASENAMES:
                    continue
                hits = [c for base in (skill_dir, current.parent) if (c := (base / ref).resolve()).is_file()]
                if not hits and "/" not in ref:
                    # Bare-basename fallback: prose often names a reference without
                    # its directory ("see api-design.md" with references/ implied).
                    # The agent would find and load it, so count every match.
                    # Compared by name, not passed to rglob as a pattern, so glob
                    # metacharacters in a filename can't break the walk.
                    hits = [p.resolve() for p in skill_dir.rglob("*") if p.name == ref and p.is_file()]
                for candidate in hits:
                    if candidate not in seen:
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


def _budget(skill_dir: Path, use_tiktoken: bool = False) -> tuple[list[str], str, str]:
    """Token-budget estimate across a skill's referenced Markdown.

    Returns (report lines, rating label, advice). The rating judges the
    worst-case load - SKILL.md plus the largest single reference, which is what
    one branch firing costs - not the corpus total, which would penalise
    progressive disclosure (many small branch-gated references are the cure). The rating doubles as the verbosity gate: main()
    downgrades "OK" to a warning and "Poor" to a hard error, so the budget is
    enforced by exit code rather than by the agent's discipline. advice names
    the file driving an OK/Poor rating and its cure; empty at Great/Good.
    """
    count = tiktoken_tokens if use_tiktoken else estimate_tokens
    method = f"tiktoken {TIKTOKEN_ENCODING}" if use_tiktoken else f"estimate, chars/{CHARS_PER_TOKEN} heuristic"
    skill_root = Path(skill_dir).resolve()
    skill_md = skill_root / "SKILL.md"
    per_file = {
        f: count(f.read_text(encoding="utf-8-sig", errors="ignore"))
        for f in referenced_md_files(skill_dir)
    }
    main = per_file.get(skill_md, 0)
    refs = {f: n for f, n in per_file.items() if f != skill_md}
    total = main + sum(refs.values())
    big_rel: Path | str = ""
    if refs:
        big_path, big_tokens = max(refs.items(), key=lambda kv: kv[1])
        big_rel = big_path.relative_to(skill_root) if big_path.is_relative_to(skill_root) else big_path
        load = main + big_tokens
        rating = token_rating(load)
        lines = [
            f"Tokens: worst-case load {load} [{rating}] = SKILL.md {main} + largest reference {big_rel} {big_tokens}",
            f"  corpus total {total} across {len(refs)} referenced .md file(s) ({method})",
        ]
        driver_is_main = main >= big_tokens
    else:
        load = main
        rating = token_rating(load)
        lines = [f"Tokens: SKILL.md {main} [{rating}], no referenced .md files ({method})"]
        driver_is_main = True
    advice = ""
    if rating in ("OK", "Poor"):
        cure = (
            "move branch-only content out of SKILL.md into references/ and delete no-op lines"
            if driver_is_main
            else f"{big_rel} loads whole when its branch fires - split it by sub-branch or thin it"
        )
        bound = "(>12k)" if rating == "Poor" else "(9k-12k; aim for Good, <9k)"
        advice = f"Worst-case load rating is {rating} {bound}: {cure}"
    return lines, rating, advice


# Structure measurement: how much of the body is paragraph prose vs structured
# text (lists, tables, headings, blockquotes). Purely informational - no
# threshold gate - because prose-shape gates are gameable and legitimate skills
# differ in how much conceptual prose they need. Surfacing the measurement lets
# the reviewing agent judge; the hard gate stays on total tokens above.
#
# Blob detection is form-invariant: the unit is any contiguous run of non-fence
# body text, and each list marker, table row, and blockquote line starts a new
# unit. Moving words between a paragraph, a bullet, a quote, or a table cell
# never changes the count - only deleting words does - so the report can't be
# satisfied by reshaping prose into an exempt container.
_LIST_MARKER = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s")
_HEADING = re.compile(r"^#{1,6}\s")

# A text unit this size (~6-8 sentences) is a "blob": prose long enough that
# instructions are likely buried in it. Calibrated against real skills: the
# 80-95 band flagged mostly dense-but-earned units, unambiguous waffle started
# past ~100. Reported as compression targets, never gated - see above.
BLOB_WORDS = 100
BLOB_LIST_MAX = 5  # keep the report line readable; the count still shows the rest

# The load rating deliberately trusts references (only the largest one counts),
# so this is the counterweight: a blob or two in references is normal
# conceptual prose, three or more signals systemic waffle rather than an
# outlier, and earns a warning pointing at the compression pass.
REF_BLOB_WARN = 3

# Single commands and short examples belong inline; a fenced block past this
# many lines is script-shaped, and the primer's "Do not add inline scripts
# within markdown" rule puts scripts in scripts/ (templates in assets/). A
# signal, not a fact: a long example or template can be legitimate.
CODE_FENCE_LINES = 10


def _structure(skill_dir: Path) -> tuple[int | None, list, list, list]:
    """Scan a skill's referenced Markdown for prose shape. Returns
    (percent of body words in paragraph prose or None if no body,
    blobs in SKILL.md, blobs in referenced files, over-length code blocks);
    blob and code entries are (size, relative path, 1-based line, opening text),
    largest first."""
    para_words = struct_words = 0
    units: list[tuple[int, str, int, str]] = []  # (words, relative path, 1-based line, opening words)
    long_code: list[tuple[int, str, int, str]] = []  # (lines, relative path, 1-based line, first code line)
    skill_root = Path(skill_dir).resolve()
    for path in referenced_md_files(skill_dir):
        text = path.read_text(encoding="utf-8-sig", errors="ignore")
        match = _FRONTMATTER_RE.match(text)
        body = text[match.end():] if match else text
        first_line = (text[: match.end()].count("\n") + 1) if match else 1
        rel = path.relative_to(skill_root) if path.is_relative_to(skill_root) else path
        fence: str | None = None  # open fence marker, None outside fences
        unit = 0  # words in the unit being accumulated
        unit_line = 0
        unit_is_para = False
        unit_open = ""  # first words of the unit, for the report quote

        def close() -> None:
            nonlocal unit
            if unit:
                units.append((unit, str(rel), unit_line, unit_open))
            unit = 0

        fence_start = fence_lines = 0
        fence_first = ""
        for lineno, line in enumerate(body.splitlines(), start=first_line):
            stripped = line.strip()
            if fence is not None:
                if _fence_close(stripped, fence):
                    if fence_lines > CODE_FENCE_LINES:
                        long_code.append((fence_lines, str(rel), fence_start, fence_first))
                    fence = None
                else:
                    fence_lines += 1
                    if not fence_first and stripped:
                        fence_first = stripped
                continue
            if (opened := _fence_open(stripped)) is not None:
                fence = opened
                fence_start, fence_lines, fence_first = lineno, 0, ""
                close()
                continue
            if not stripped:
                close()
                continue
            words = len(stripped.split())
            if _HEADING.match(stripped):
                close()
                struct_words += words
            elif _LIST_MARKER.match(line):
                close()
                unit, unit_line, unit_is_para, unit_open = words, lineno, False, stripped
                struct_words += words
            elif stripped.startswith("|") or stripped.startswith(">"):
                close()
                unit, unit_line, unit_is_para, unit_open = words, lineno, False, stripped
                struct_words += words
                close()  # one unit per row/quote line
            else:
                if unit == 0:
                    unit_line, unit_is_para, unit_open = lineno, True, stripped
                unit += words
                # a wrapped continuation belongs to its list item, not to prose
                para_words += words if unit_is_para else 0
                struct_words += 0 if unit_is_para else words
        close()
        if fence is not None and fence_lines > CODE_FENCE_LINES:
            # unterminated fence: still report it rather than losing it silently
            long_code.append((fence_lines, str(rel), fence_start, fence_first))
    body_words = para_words + struct_words
    pct = round(100 * para_words / body_words) if body_words else None
    blobs = sorted((u for u in units if u[0] >= BLOB_WORDS), reverse=True)
    skill_blobs = [b for b in blobs if b[1] == "SKILL.md"]
    ref_blobs = [b for b in blobs if b[1] != "SKILL.md"]
    return pct, skill_blobs, ref_blobs, sorted(long_code, reverse=True)


def _listing(group: list, unit: str) -> list[str]:
    """Indented finding lines: 'path:line (Nw) "opening words..."'."""
    out = [
        f'    {path}:{lineno} ({size}{unit}) "{" ".join(opening.split()[:8])}..."'
        for size, path, lineno, opening in group[:BLOB_LIST_MAX]
    ]
    if len(group) > BLOB_LIST_MAX:
        out.append(f"    ... +{len(group) - BLOB_LIST_MAX} more")
    return out


def build_report(skill_dir: Path, use_tiktoken: bool = False) -> tuple[str, str, str]:
    """Sectioned report that routes the reading agent's attention: FACTS are
    always-loaded costs to fix, SIGNALS are branch-loaded findings to judge,
    INFO is context. Returns (text, rating, advice); main() enforces the
    rating by exit code (Poor fails, OK warns)."""
    budget_lines, rating, advice = _budget(skill_dir, use_tiktoken)
    pct, skill_blobs, ref_blobs, long_code = _structure(skill_dir)

    facts: list[str] = []
    if advice:
        facts.append(f"  {advice}")
    if skill_blobs:
        facts.append(f"  Blobs in SKILL.md ({len(skill_blobs)} text units of {BLOB_WORDS}+ words):")
        facts.extend(_listing(skill_blobs, "w"))

    signals: list[str] = []
    if ref_blobs:
        signals.append(f"  Blobs in references ({len(ref_blobs)} text units of {BLOB_WORDS}+ words):")
        signals.extend(_listing(ref_blobs, "w"))
        if len(ref_blobs) >= REF_BLOB_WARN:
            signals.append(
                "  References must stay tight - the load rating trusts them; "
                "run the compression pass over the waffle."
            )
    if long_code:
        signals.append(
            f"  Code blocks over {CODE_FENCE_LINES} lines ({len(long_code)}) - "
            "inline scripts belong in scripts/, templates in assets/:"
        )
        signals.extend(_listing(long_code, " lines"))

    out = list(budget_lines)
    if facts:
        out.append("FACTS (always-loaded cost - fix these):")
        out.extend(facts)
    if signals:
        out.append("SIGNALS (branch-loaded - judge each: earned detail or waffle?):")
        out.extend(signals)
    out.append("INFO:")
    if pct is not None:
        out.append(f"  Structure: {pct}% of body words in paragraph prose")
    if skill_blobs or ref_blobs:
        out.append(
            f"  A blob is any text unit of {BLOB_WORDS}+ words, any shape (paragraph, "
            "list item, quote, table row); shrink by deleting words, not by reshaping."
        )
    if not facts and not signals:
        out.append("  No blobs or oversized code blocks found.")
    return "\n".join(out), rating, advice


def parse_frontmatter(text: str) -> dict:
    """Parse a SKILL.md's leading YAML frontmatter with a standard YAML loader.

    Raises ValueError if there is no frontmatter block or it is not a mapping, and
    propagates yaml.YAMLError for malformed YAML (e.g. an unquoted description with a
    bare colon, which is a genuine error the real loaders would also reject).
    """
    assert yaml is not None  # callers guard via lint()'s dependency check
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
    if yaml is None:
        print("Error: dependencies not found. Run this script with uv:")
        print(f"  uv run {sys.argv[0]} <skill_directory>")
        sys.exit(1)

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
        metadata = parse_frontmatter(skill_md.read_text(encoding="utf-8-sig", errors="ignore"))
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

    words = description_word_count(metadata.get("description") or "")
    if words > DESCRIPTION_WORDS_FAIL:
        errors.append(
            f"Description is {words} words; the checklist caps it at "
            f"{DESCRIPTION_WORDS_FAIL} (aim for {DESCRIPTION_WORDS_MIN}-{DESCRIPTION_WORDS_WARN})"
        )
    elif words > DESCRIPTION_WORDS_WARN:
        warnings.append(
            f"Description is {words} words; aim for {DESCRIPTION_WORDS_MIN}-{DESCRIPTION_WORDS_WARN} "
            f"(hard cap {DESCRIPTION_WORDS_FAIL})"
        )
    elif 0 < words < DESCRIPTION_WORDS_MIN:
        warnings.append(
            f"Description is {words} words; aim for {DESCRIPTION_WORDS_MIN}-{DESCRIPTION_WORDS_WARN} - "
            "very short descriptions risk under-triggering"
        )

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
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="print the token-budget and structure reports and skip the spec "
        "checks; stdlib-only, so it runs with plain python3 (used by the "
        "post-edit hook)",
    )
    args = parser.parse_args()

    skill_dir = Path(args.skill_directory)
    if not skill_dir.is_dir():
        print(f"Error: directory does not exist: {skill_dir}")
        sys.exit(1)
    if not (skill_dir / "SKILL.md").is_file():
        print(f"Error: no SKILL.md in {skill_dir}")
        sys.exit(1)

    report_text, rating, advice = build_report(skill_dir, use_tiktoken=args.tiktoken)

    if args.report_only:
        print(report_text)
        sys.exit(1 if rating == "Poor" else 0)

    errors, warnings = lint(skill_dir)

    # Token-budget gate on the worst-case load (see _budget): "Poor" fails the
    # build; "OK" warns via the report's FACTS section. Ratings and cures live
    # in the primer's "Validating a Skill" and "Failure Modes" sections.
    if rating == "Poor":
        errors.append(advice)

    for warning in warnings:
        print(f"Warning: {warning}")

    print(report_text)
    if errors:
        print(f"Validation failed ({len(errors)} error(s)):")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)

    clean = not warnings and rating in ("Great", "Good")
    print("Skill is valid!" if clean else "Skill is valid (with warnings).")


if __name__ == "__main__":
    main()
