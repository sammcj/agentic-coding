# Dated Setup

Use this for non-code projects: docs repos, writing or notes vaults, content sites, research collections, config-only repos. Also use it for any project that just wants a plain change log with no version numbers (a skill directory, a dotfiles repo). No build system, no `version.py`, no CI. The agent maintains the changelog by hand under date headings.

## How it works

There is no stamping script and no build integration. Whenever an agent makes a change, it adds a terse TLDR bullet under today's date heading (`## YYYY-MM-DD`), newest date first. The agent creates today's heading if it doesn't exist yet. That's the whole workflow.

## CHANGELOG.md

Generate this as the project's `CHANGELOG.md` (use today's real date for the first heading and describe the actual change you just made):

```markdown
# Changelog

<!-- AI agents: After completing changes to this project, add a terse TLDR style bullet describing the change under today's date heading (## YYYY-MM-DD), newest date first. Create the date heading if it does not exist. Log only changes a reader would care about - new capability, changed or broken behaviour, removals, real fixes. Skip cosmetic and housekeeping edits (wording, formatting, typos, file moves); git history covers those. One line per change, aim under 15 words - say what changed, not how it was implemented. Write more only when the change is genuinely complex and the reasoning cannot be recovered from the source or git history. No versioning is required. -->

## 2026-06-30

- Added CHANGELOG.md and CLAUDE.md to track future changes.
```

For an existing CHANGELOG.md, do not overwrite history: insert the HTML comment after the `# Changelog` heading and add today's date heading above the most recent existing entry.

## What to log

Only changes a reader would care about: new capability, changed or broken behaviour, removals, fixes to something that was actually wrong. Skip cosmetic and housekeeping edits - wording tweaks, formatting, typos, comment changes, file moves, test-only churn. Git history already covers those, and they crowd out the entries that matter.

If a day's real changes are all trivial, add no entry for that day.

## Entry format

One bullet per change, terse, under the date heading. Say what changed, not how it was implemented - aim under 15 words. Group with `###` sub-headings only if a single day's entries get long enough to need it:

```markdown
## 2026-06-30

- Rewrote the onboarding guide intro
- Fixed broken links in the API reference
- Removed the deprecated migration page
```

Expand past one line only when the change is genuinely complex and a future agent could not recover the reasoning from the source or git history - a non-obvious constraint, a rejected alternative, an external system's quirk. That is the exception, not the default.

## CLAUDE.md

If the project has no CLAUDE.md, create one (replace `<Project Name>` with the real name):

```markdown
# <Project Name> Rules

## Update CHANGELOG.md after changes

After a change that alters behaviour - new capability, breaking change, removal, real fix - you MUST add a bullet to `CHANGELOG.md` under today's date heading (`## YYYY-MM-DD`, newest first), creating the heading if absent.

- One line, under 15 words. What changed, not how it was built.
- Skip trivia: wording, formatting, typos, file moves, no-behaviour refactors. Git history covers those.
- Write more than one line only if a future agent couldn't recover the reasoning from the source.
- No version numbers.
```

If a CLAUDE.md already exists, append just the `## Update CHANGELOG.md after changes` section to it; don't add a second top-level title. Name the project's own content in the opening line if it helps (e.g. "a change that alters how this skill behaves - SKILL.md, references, scripts").

## Gotchas

- No script means nothing enforces this; the CLAUDE.md instruction is the only mechanism. Keep it terse and imperative so agents actually follow it.
- Agents must use the real current date for the heading, not a guessed or placeholder one.
- If the project later grows a build system and version convention, switch to `calver.md` or `semver.md`; the existing dated entries stay as-is.
