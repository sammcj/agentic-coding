---
name: ai-changelog
description: Set up an AI-driven changelog system in any project. Creates CHANGELOG.md with an [Unreleased] section for AI agents, a Python version/changelog stamping script (CalVer or SemVer), and build/CI integration. Use when the user wants to add automated changelog management, AI-friendly changelog workflows, version stamping, or set up a changelog system for a new or existing project. Also use when asked to improve an existing changelog process.
allowed-tools: Read Write Edit Bash Glob Grep
---

# AI-Driven Changelog

Set up a changelog system where AI coding agents write entries under `## [Unreleased]` during development, and automation stamps version numbers at release time. No agent ever writes version numbers -- the build process handles that.

## Setup Workflow

1. **Detect the project**: Check for Makefile, Justfile, package.json, Cargo.toml, pyproject.toml, go.mod. Note which config files contain a `"version"` field.

2. **Ask the user**:
   - Versioning scheme? CalVer `YYYY.M.COMMITS` (default) works for most projects. SemVer via manual `--version` override is always available.
   - Include a `## Known Bugs` pinned section? (default: yes)
   - Set up GitHub Actions integration? (default: skip unless asked)

3. **Generate CHANGELOG.md**: Read `references/changelog-template.md` for the template. If a CHANGELOG.md already exists, do NOT overwrite it -- insert the `## [Unreleased]` structure and HTML comment above existing entries.

4. **Copy `scripts/version.py`**: Copy from this skill's `scripts/version.py` into the target project's `scripts/` directory. Make it executable (`chmod +x`).

5. **Add build integration**: Read `references/build-integration.md` for patterns. Add `stamp-version` and `version` targets to the project's existing build system. If no build system exists, create a minimal Makefile.

6. **Update CLAUDE.md**: Read `references/claude-md-snippet.md` for the exact text. Insert the changelog update step into the project's development workflow. If no CLAUDE.md exists, create one with a Development Workflow section.

7. **Verify**: Run `uv run scripts/version.py version` to confirm CalVer computation works. Run `uv run scripts/version.py stamp --dry-run` to preview the stamp operation.

## Project Detection

| Indicator | Config files to stamp | Build integration |
|---|---|---|
| `Makefile` | depends on project | Add make targets |
| `Justfile` | depends on project | Add just recipes |
| `package.json` | `package.json` | Add npm scripts or Makefile |
| `Cargo.toml` | `Cargo.toml` | Makefile wrapper |
| `pyproject.toml` | `pyproject.toml` | Makefile wrapper |
| `go.mod` | none (use ldflags) | Makefile wrapper |
| None | none | Create minimal Makefile |

## How the Script Works

`scripts/version.py` subcommands:
- `version` -- prints CalVer to stdout (for piping)
- `stamp` -- replaces `## [Unreleased]` with `## [VERSION] - DATE`, re-inserts fresh `## [Unreleased]`, and stamps version into auto-discovered config files

Flags: `--version X.Y.Z` (manual override), `--dry-run`, `--changelog-only`, `--no-changelog`

Run via `uv run scripts/version.py stamp` (or `python3 scripts/version.py stamp` if uv is unavailable -- the script has no external dependencies).

## Gotchas

- **Never overwrite existing changelog history.** If a CHANGELOG.md exists with content, merge the `[Unreleased]` structure into it rather than replacing the file.
- **Empty Unreleased section**: The stamp script intentionally skips stamping if `[Unreleased]` has no content. This prevents empty version entries.
- **`fetch-depth: 0` in CI**: CalVer uses `git rev-list --count HEAD`. Shallow clones produce wrong commit counts. Always set `fetch-depth: 0` in checkout steps.
- **The HTML comment is the agent's instruction source.** The `<!-- AI agents: ... -->` comment in CHANGELOG.md tells future agents how to write entries. Do not omit it.
- **Known Bugs stays pinned.** The stamp script preserves `## Known Bugs` above `## [Unreleased]`. If you add it, agents should maintain it there.
- **Config file stamping is first-match-only for TOML.** The regex replaces only the first `version = "..."` line, which is the package version. Dependency versions are unaffected.
- **SemVer projects**: CalVer is the default, but any project can use SemVer by always passing `--version X.Y.Z` explicitly (from a VERSION file, git tag, or manual input).
