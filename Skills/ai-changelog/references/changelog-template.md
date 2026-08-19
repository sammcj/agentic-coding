# Changelog Template

Generate this as the project's `CHANGELOG.md`. Adapt the comment text if the project has specific conventions.

```markdown
# Changelog

<!-- AI agents: add entries under the ## [Unreleased] header. Do NOT add version numbers or dates. Do NOT duplicate headings. The ## Known Bugs section must always stay pinned above ## [Unreleased]. Group entries under ### Added, ### Changed, ### Fixed, or ### Removed. Log only changes a reader would care about - new capability, changed or breaking behaviour, removals, real fixes. Skip cosmetic and housekeeping edits (wording, formatting, typos, refactors with no behaviour change, test-only churn); git history covers those. Combine or update items refined within the same session. Keep each entry to one terse line saying what changed - aim under 15 words. Write more only when the change is genuinely complex and the reasoning cannot be recovered from the code or git history. If the file exceeds 2000 lines, truncate the oldest releases. -->

## Known Bugs

## [Unreleased]
```

## What to log

Only changes a reader would care about: new capability, changed or breaking behaviour, removals, fixes to something that was actually wrong, security issues, deprecations.

Skip: wording and formatting tweaks, typos, comment changes, file moves, dependency bumps with no user-visible effect, internal refactors that change no behaviour, test-only churn. Git history already covers those, and they crowd out the entries that matter. If a session produced only trivial changes, add no entry.

## Entry format

Each entry is a concise bullet point under a category heading:

```markdown
## [Unreleased]

### Added

- New feature concise description

### Changed

- What changed and why

### Fixed

- What was broken and how it was fixed

### Removed

- What was removed and why
```

## Entry length

One line per change. Say what changed, not how it was implemented. Aim under 15 words.

Too long:

```markdown
- Refactored the config loader to use a two-pass approach where the first pass collects all keys and the second pass resolves interpolations, fixing the ordering issue where a key referencing a later key resolved to an empty string
```

Right:

```markdown
- Config interpolation now resolves forward references
```

Expand past one line only when the change is genuinely complex and a future agent could not recover the reasoning from the code or git history - a non-obvious constraint, a rejected alternative, an external system's quirk. That is the exception, not the default. Most changes, including most refactors and bug fixes, get one line.

For security or critical fixes, use bold severity prefixes for scanability:

```markdown
### Fixed

- **Security**: Shell injection in env command via unescaped quotes
- **Critical**: TUI dead-end state when pressing 'o'
- Regular bug fix description
```

## Adapting for existing projects

If the project already has a CHANGELOG.md:
1. Do not overwrite existing history
2. Insert the HTML comment block after the `# Changelog` heading
3. Add `## Known Bugs` and `## [Unreleased]` sections above the first versioned entry
4. Preserve all existing versioned entries below
