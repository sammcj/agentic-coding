# CLAUDE.md Changelog Snippet

Insert this into the target project's CLAUDE.md development workflow section. Replace `{{STAMP_COMMAND}}` with the appropriate command for the project's build system.

## Snippet

```markdown
- Update `CHANGELOG.md` under the `## [Unreleased]` section with a concise bullet-point summary of changes made, grouped under headings (Added/Changed/Fixed/Removed). Combine or update items refined within the same session. Do NOT add version numbers -- the build process handles that via `{{STAMP_COMMAND}}`, truncate when over 2000 lines
```

## Stamp command by build system

| Build system | `{{STAMP_COMMAND}}` |
|---|---|
| Makefile | `make stamp-version` |
| Justfile | `just stamp-version` |
| package.json scripts | `npm run stamp-version` |
| No build system | `uv run scripts/version.py stamp` |

## Placement

- If the project's CLAUDE.md has a numbered development workflow or checklist, add this as the second-to-last step (before final verification)
- If no workflow section exists, create a `## Development Workflow` section and include this step
- If no CLAUDE.md exists, create one with at minimum a `## Development Workflow` section containing this step
