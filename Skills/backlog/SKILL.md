---
name: backlog
description: Use when the user wants to add a bug or feature to the backlog, or list or triage the backlog. Not for PRDs or specs.
---

# Backlog

## Destination

First match wins:

1. `BACKLOG.md` or `docs/BACKLOG.md` -> local file.
2. The user's own repo, not a fork -> GitHub.
3. Otherwise ask. Create no backlog file unless the user picks one.

Categories: `bug`, `enhancement`, `chore` (refactor, dependencies, CI, build, tests), `documentation`.

Local:

- Category as a title prefix, e.g. `[bug]`. Find dupes with grep.
- Add a section, or a new file continuing the existing numbering (`0001-slug.md`).

GitHub:

- Category is an existing label (`gh label list`). Ask before creating one.
- Dupes: `gh issue list --search "<keywords>"`. List: `gh issue list --limit 50 --json number,title,labels,createdAt`.
- Add: write the body to a file in a `mktemp -d` directory, then `gh issue create --body-file <file>`.

## Add

1. Search for dupes first. On a near match, ask: update it or file new.
2. Guess the category. Ask at most one question in total, only when scope or category is ambiguous.
3. File it. Reply with the URL or path only.

## Review

1. List open items, grouped by category, oldest first: number, title, age.
2. Offer, letting the user choose:
   - **Triage**: relabel, close stale items, merge dupes. Confirm each close.
   - **Pick one**: load the item and stop. If `openspec/` exists, end with `Next: /opsx:propose from #<n>`.
   - **Themes**: cluster related items, suggest groupings.

## Notes

- Keep the contents concise, quick and easy to read.
