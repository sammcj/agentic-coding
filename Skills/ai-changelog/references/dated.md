# Dated Setup

Use this for non-code projects: docs repos, writing or notes vaults, content sites, research collections, config-only repos. Also use it for any project that just wants a plain change log with no version numbers (a skill directory, a dotfiles repo). No build system, no `version.py`, no CI. The agent maintains the changelog by hand under date headings.

## How it works

There is no stamping script and no build integration. Whenever an agent makes a change, it adds a terse TLDR bullet under today's date heading (`## YYYY-MM-DD`), newest date first. The agent creates today's heading if it doesn't exist yet. That's the whole workflow.

## CHANGELOG.md

Generate this as the project's `CHANGELOG.md` (use today's real date for the first heading and describe the actual change you just made):

```markdown
# Changelog

<!-- AI agents: After completing changes to this project, add a terse TLDR style bullet describing the change under today's date heading (## YYYY-MM-DD), newest date first. Create the date heading if it does not exist. No versioning is required. -->

## 2026-06-30

- Added CHANGELOG.md and CLAUDE.md to track future changes.
```

For an existing CHANGELOG.md, do not overwrite history: insert the HTML comment after the `# Changelog` heading and add today's date heading above the most recent existing entry.

## Entry format

One bullet per change, terse, under the date heading. Group with `###` sub-headings only if a single day's entries get long enough to need it:

```markdown
## 2026-06-30

- Rewrote the onboarding guide intro
- Fixed broken links in the API reference
- Removed the deprecated migration page
```

## CLAUDE.md

If the project has no CLAUDE.md, create one (replace `<Project Name>` with the real name):

```markdown
# <Project Name> Rules

## Update CHANGELOG.md after changes

After making any change to this project: You MUST update `CHANGELOG.md`:

- Add a concise TLDR of the change(s) as bullet point(s) under today's date heading (`## YYYY-MM-DD`, newest first), creating the heading if it doesn't exist. No versioning is required.
```

If a CLAUDE.md already exists, append just the `## Update CHANGELOG.md after changes` section to it; don't add a second top-level title. Tailor the "any change to this project" phrasing to the project's content if it helps (e.g. "any change to this skill (SKILL.md, references, scripts, evals)").

## Gotchas

- No script means nothing enforces this; the CLAUDE.md instruction is the only mechanism. Keep it terse and imperative so agents actually follow it.
- Agents must use the real current date for the heading, not a guessed or placeholder one.
- If the project later grows a build system and version convention, switch to `calver.md` or `semver.md`; the existing dated entries stay as-is.
