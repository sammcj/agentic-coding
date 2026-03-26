# Changelog Template

Generate this as the project's `CHANGELOG.md`. Adapt the comment text if the project has specific conventions.

```markdown
# Changelog

<!-- AI agents: add entries under the ## [Unreleased] header. Do NOT add version numbers or dates. Do NOT duplicate headings. The ## Known Bugs section must always stay pinned above ## [Unreleased]. Group entries under ### Added, ### Changed, ### Fixed, or ### Removed. Combine or update items refined within the same session. If the file exceeds 2000 lines, truncate the oldest releases. -->

## Known Bugs

## [Unreleased]
```

## Entry format

Each entry is a concise bullet point under a category heading:

```markdown
## [Unreleased]

### Added

- New feature description

### Changed

- What changed and why

### Fixed

- What was broken and how it was fixed

### Removed

- What was removed and why
```

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
