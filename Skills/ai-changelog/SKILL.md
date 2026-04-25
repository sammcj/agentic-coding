---
name: ai-changelog
description: Set up an AI-driven changelog system in any project. Creates CHANGELOG.md with an [Unreleased] section for AI agents, a Python version/changelog stamping script (CalVer or SemVer), and build/CI integration. Use when the user wants to add automated changelog management, AI-friendly changelog workflows, version stamping, or set up a changelog system for a new or existing project. Also use when asked to improve an existing changelog process.
allowed-tools: Read Write Edit Bash Glob Grep
---

# AI-Driven Changelog

Set up a changelog system where AI coding agents write entries under `## [Unreleased]` during development, and automation stamps version numbers at release time. No agent ever writes version numbers; the build process handles that.

## Setup workflow

1. **Detect the build system**: Check for Makefile, Justfile, package.json, Cargo.toml, pyproject.toml, go.mod. Note which config files contain a `"version"` field.

2. **Detect the versioning scheme** by inspecting (highest confidence first):
   - `CHANGELOG.md` heading style: `## [YYYY.M.N]` headings → CalVer; `## [X.Y.Z]` headings or prose mentioning "SemVer" → SemVer
   - Git tags from `git tag --list | head`: `vX.Y.Z` → SemVer; `YYYY.M.N` → CalVer
   - `VERSION` file with content matching `^[0-9]+\.[0-9]+\.[0-9]+` → SemVer
   - Manifest version field (`package.json`, `Cargo.toml`, `pyproject.toml`) matching `X.Y.Z` → SemVer

   If signals are absent or contradictory, ask the user. Suggest SemVer for projects with established version history (existing tags, manifest versions, prior changelog entries) and CalVer for greenfield projects where automatic versioning is preferable. Each scheme has trade-offs documented in its reference file.

3. **Read the scheme reference** that matches the chosen scheme. It contains the build integration recipes, CLAUDE.md snippet, GitHub Actions pattern, and scheme-specific gotchas:
   - CalVer → `references/calver.md`
   - SemVer → `references/semver.md`

4. **Ask the user** about optional features:
   - Pinned `## Known Bugs` section above `## [Unreleased]`? (default: yes)
   - GitHub Actions release workflow integration? (default: skip unless asked)

5. **Generate or update CHANGELOG.md** using `references/changelog-template.md`. If a CHANGELOG.md already exists, do NOT overwrite it; insert the HTML comment and the `## [Unreleased]` (and optional `## Known Bugs`) structure above existing entries.

6. **Copy `scripts/version.py`** from this skill into the target project's `scripts/` directory. Make it executable (`chmod +x`).

7. **Apply the scheme reference**: follow the build-integration recipe from the chosen reference file. Add targets to the existing build system, or create a minimal Makefile if none exists.

8. **Update CLAUDE.md** with the snippet from the chosen scheme reference. Insert into the project's development workflow section, or create one.

9. **Verify**:
   - CalVer: `uv run scripts/version.py version` should print today's CalVer; then `uv run scripts/version.py stamp --dry-run` previews the stamp
   - SemVer: `uv run scripts/version.py stamp --version <current-version> --dry-run --changelog-only` previews the stamp without touching the canonical version source

## Project detection

| Indicator | Config files to stamp | Build integration |
|---|---|---|
| `Makefile` | depends on project | Add make targets |
| `Justfile` | depends on project | Add just recipes |
| `package.json` | `package.json` | Add npm scripts or Makefile |
| `Cargo.toml` | `Cargo.toml` | Makefile wrapper |
| `pyproject.toml` | `pyproject.toml` | Makefile wrapper |
| `go.mod` | `VERSION` (if present) or none | Makefile wrapper |
| `VERSION` file | `VERSION` | Makefile wrapper |
| None | none | Create minimal Makefile |

## How the script works

`scripts/version.py` subcommands:
- `version`: prints today's CalVer to stdout (CalVer projects only)
- `stamp`: replaces `## [Unreleased]` with `## [VERSION] - DATE`, re-inserts a fresh `## [Unreleased]`, and stamps version into auto-discovered config files (`package.json`, `Cargo.toml`, `pyproject.toml`, `tauri.conf.json`, `VERSION`)

Flags: `--version X.Y.Z` (required for SemVer; optional override for CalVer), `--dry-run`, `--changelog-only`, `--no-changelog`.

The script is scheme-agnostic. With no `--version`, it auto-computes CalVer; with `--version`, it stamps whatever string you give it. Validation lives in the build system, so SemVer recipes always pass `--version` and reject malformed input before invoking the script. See `references/semver.md` for why this split matters.

Run via `uv run scripts/version.py stamp` or `python3 scripts/version.py stamp` (no external dependencies).

## Gotchas

- **Never overwrite existing changelog history.** If a CHANGELOG.md exists with content, merge the `[Unreleased]` structure into it rather than replacing the file.
- **Empty Unreleased section**: stamping is a no-op if `[Unreleased]` has no content. This prevents empty version entries.
- **`fetch-depth: 0` in CI for CalVer**: CalVer uses `git rev-list --count HEAD`. Shallow clones produce wrong commit counts.
- **The HTML comment is the agent's instruction source.** The `<!-- AI agents: ... -->` comment in CHANGELOG.md tells future agents how to write entries. Don't omit it.
- **Known Bugs stays pinned.** The stamp script preserves `## Known Bugs` above `## [Unreleased]`. If you add it, agents should maintain it there.
- **SemVer + auto-CalVer = silent footgun.** If a Makefile in a SemVer project calls `python3 scripts/version.py stamp` without `--version`, the script auto-computes CalVer and writes that into the changelog. The recipes in `references/semver.md` always pass `--version`; preserve that contract in any custom integration.
- **Config file stamping is first-match-only for TOML.** The regex replaces only the first `version = "..."` line, which is the package version. Dependency versions are unaffected.
- **VERSION file stamping requires existing semver-shaped content.** The script's `VERSION` handler only rewrites the file if its current content matches `^\d+\.\d+\.\d+`. Build numbers, tag-prefixed versions, or other formats are left alone.
