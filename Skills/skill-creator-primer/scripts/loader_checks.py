#!/usr/bin/env python3
"""What agent loaders do to a skill beyond the spec: text Claude Code rewrites, and what Codex and Copilot drop."""

# Behaviours taken from SkillEvaluator's harness profiles (github.com/NVIDIA/SkillEvaluator), verified upstream on
# 2026-11-01 against Claude Code 2.1.316, Codex 0.166.0 and Copilot CLI 1.0.105. Each finding names the upstream rule
# ID so it can be re-read against its source when a loader changes. Stdlib-only: the post-edit hook runs this.

import re
from collections import Counter
from pathlib import Path

CODEX_SHELL_READ_BYTES = 40_000  # CX-SHELL-READ: past this Codex keeps only the start and end of a shell read
FRONTMATTER_FIELD_CHARS = 200  # CC-FM-STRIPPED: upstream's floor for text long enough to be an instruction
# A skill that takes arguments rarely takes more than ten, so in one a larger number, or one with a decimal or
# thousands part, is read as an amount of money.
MAX_ARGUMENT_INDEX = 9
LOCATIONS_MAX = 6  # enough to find the pattern; the rest is the same fix repeated

_FRONTMATTER = re.compile(r"^---\r?\n(.*?)\r?\n---", re.DOTALL)
# Claude Code's own pattern, plus a trailing group that marks an amount of money ($4.50, $1,000).
_DOLLAR_N = re.compile(r"(?<!\\)\$(\d+)(?!\w)([.,]\d)?")
_TOP_LEVEL_KEY = re.compile(r"^[\"']?([A-Za-z_][\w-]*)[\"']?[ \t]*:", re.MULTILINE)
# A mapping needs a key separator (a colon followed by a space or the line end), so `Bash(git:*) Read` on a
# continuation line stays a string.
_ALLOWED_TOOLS_MAP = re.compile(
    r"^allowed-tools[ \t]*:[ \t]*(?:\{|(?:#[^\n]*)?\r?\n(?:[ \t]*\r?\n)*[ \t]+[^-\s#][^\n]*?:(?:[ \t]|\r?$))",
    re.MULTILINE,
)
_ARGUMENT_FIELDS = {"argument-hint", "arguments"}
_NOT_SHIPPED_DIRS = {"node_modules", "__pycache__", "venv"}
# Assembled so this file never holds the literal placeholders: a loader would substitute them if the text were ever
# quoted into a skill body.
_SKILL_DIR_PLACEHOLDER = "$" + "{CLAUDE_SKILL_DIR}"
_ARGUMENTS_PLACEHOLDER = "$" + "ARGUMENTS"


def manifest_name(skill_dir: Path) -> str | None:
    """The manifest's name on disk when it is not exactly SKILL.md, else None. A case-insensitive filesystem (macOS)
    opens skill.md as SKILL.md, so only the directory listing shows the difference. [CC-CASING, CX-CASING, CP-CASING]"""
    try:
        names = [p.name for p in Path(skill_dir).iterdir()]
    except OSError:
        return None
    if "SKILL.md" in names:
        return None
    return next((n for n in names if n.lower() == "skill.md"), None)


def _shown(items: list) -> str:
    more = f" +{len(items) - LOCATIONS_MAX} more" if len(items) > LOCATIONS_MAX else ""
    return ", ".join(str(item) for item in items[:LOCATIONS_MAX]) + more


def findings(skill_dir: Path, md_files: list[Path], portable: bool = True) -> tuple[list[str], list[str]]:
    """Return (facts, portability) report lines. Facts change what Claude Code delivers; portability lines matter only
    when the skill must run on Codex or GitHub Copilot, and portable=False skips them and their walk of the skill tree.
    md_files is the Markdown the skill loads, SKILL.md included."""
    skill_dir = Path(skill_dir).resolve()
    skill_md = skill_dir / "SKILL.md"
    facts: list[str] = []
    portability: list[str] = []
    try:
        raw = skill_md.read_bytes()
    except OSError:
        return facts, portability
    text = raw.decode("utf-8-sig", errors="ignore")
    match = _FRONTMATTER.match(text)
    block = match.group(1) if match else ""
    body = text[match.end() :] if match else text
    first_line = text.count("\n", 0, match.end()) + 1 if match else 1
    body_lines = list(enumerate(body.splitlines(), first_line))
    keys = Counter(_TOP_LEVEL_KEY.findall(block))

    # A skill that takes no arguments has no use for $N, so every one is a rewrite waiting to happen (a price, an awk
    # field). One that does take arguments (it declares them, or its body uses the arguments placeholder) keeps its
    # placeholders; only an amount of money is flagged.
    takes_arguments = bool(_ARGUMENT_FIELDS & set(keys)) or _ARGUMENTS_PLACEHOLDER in body
    dollar_lines = [
        number
        for number, line in body_lines
        if any(
            not takes_arguments or hit.group(2) or int(hit.group(1)) > MAX_ARGUMENT_INDEX
            for hit in _DOLLAR_N.finditer(line)
        )
    ]
    if dollar_lines:
        facts.append(
            f"  Dollar-digit tokens (SKILL.md lines {_shown(dollar_lines)}) - when the skill is invoked with that many "
            "arguments, Claude Code replaces a dollar sign followed by a number with the argument, in prose and in "
            "code fences alike, so a price or an awk field reaches the agent rewritten. Word the amount ('USD 5'), "
            "move the snippet into a script file, or put a backslash before the dollar sign (Claude Code's escape; "
            "other agents show the backslash) [CC-DOLLAR-N]"
        )

    # Claude Code substitutes the skill-directory placeholder in the SKILL.md body only, so a hit there is a
    # portability matter while one in the frontmatter or a reference reaches every agent unexpanded.
    manifest_hits = [number for number, line in enumerate(text.splitlines(), 1) if _SKILL_DIR_PLACEHOLDER in line]
    frontmatter_hits = [number for number in manifest_hits if number < first_line]
    if frontmatter_hits:
        facts.append(
            f"  Skill-directory placeholder in frontmatter (SKILL.md lines {_shown(frontmatter_hits)}) - Claude Code "
            "builds have expanded it empty in a hook command; give the full path"
        )
    reference_hits = [
        # A reference can sit outside the skill folder; it is named by its full path, as the token report names it.
        f"{path.relative_to(skill_dir) if path.is_relative_to(skill_dir) else path}:{number}"
        for path in md_files
        if not path.samefile(skill_md)
        for number, line in enumerate(path.read_text(encoding="utf-8-sig", errors="ignore").splitlines(), 1)
        if _SKILL_DIR_PLACEHOLDER in line
    ]
    if reference_hits:
        facts.append(
            f"  Skill-directory placeholder in a reference ({_shown(reference_hits)}) - no loader substitutes it "
            "outside SKILL.md, so the agent reads it as literal text; give the path relative to the skill folder"
        )
    if not portable:
        return facts, portability

    body_hits = [number for number in manifest_hits if number >= first_line]
    if body_hits:
        portability.append(
            f"  Skill-directory placeholder (SKILL.md lines {_shown(body_hits)}) - Claude Code substitutes it; Codex "
            "and Copilot pass it through as literal text. Give the path relative to the skill folder "
            "[CX-SKILL-DIR, CP-SKILL-DIR]"
        )

    duplicates = sorted(key for key, count in keys.items() if count > 1)
    if duplicates:
        portability.append(
            f"  Duplicate frontmatter keys ({', '.join(duplicates)}) - Codex and Copilot drop the skill; Claude Code "
            "keeps the last value [CX-STRICT-YAML, CP-STRICT-YAML]"
        )
    if _ALLOWED_TOOLS_MAP.search(block):
        portability.append(
            "  allowed-tools is a mapping - Copilot drops the skill; give a list or a space-separated string "
            "[CP-ALLOWED-TOOLS-MAP]"
        )
    if skill_md.is_symlink():
        portability.append(
            "  SKILL.md is a symlink - Codex skips a symlinked manifest (a symlinked skill folder is fine); copy the "
            "file in [CX-SYMLINK-FILE]"
        )
    arguments_lines = [number for number, line in body_lines if _ARGUMENTS_PLACEHOLDER in line]
    if arguments_lines:
        portability.append(
            f"  Arguments placeholder (SKILL.md lines {_shown(arguments_lines)}) - Codex and Copilot pass it through "
            "as literal text; say in words what input the skill expects [CX-ARGUMENTS, CP-ARGUMENTS]"
        )
    # Exact case and a real file, as Codex requires before it loads one; dependency and hidden folders are not shipped.
    nested = sorted(
        str(path.relative_to(skill_dir))
        for path in skill_dir.rglob("*")  # a literal pattern would match skill.md on a case-insensitive filesystem
        if path.name == "SKILL.md"
        and path.parent != skill_dir
        and not path.is_symlink()
        and not any(part.startswith(".") or part in _NOT_SHIPPED_DIRS for part in path.relative_to(skill_dir).parts)
    )
    if nested:
        portability.append(
            f"  Nested manifests ({_shown(nested)}) - Codex lists each as a second skill and Copilot ignores them; "
            "rename the file or move it out of the skill [CX-NESTED, CP-NESTED]"
        )
    if len(raw) > CODEX_SHELL_READ_BYTES:
        portability.append(
            f"  SKILL.md is {len(raw):,} bytes - past {CODEX_SHELL_READ_BYTES:,} Codex may truncate it, keeping only "
            "the start and end when the agent opens it through the shell [CX-SHELL-READ]"
        )
    return facts, portability
