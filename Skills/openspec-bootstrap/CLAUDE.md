# openspec-bootstrap Rules

## Update CHANGELOG.md after changes

After a change that alters how this skill behaves (SKILL.md, assets/config.yaml) - new capability, breaking change, removal, real fix - you MUST add a bullet to `CHANGELOG.md` under today's date heading (`## YYYY-MM-DD`, newest first), creating the heading if absent.

- One line, under 15 words. What changed, not how it was built.
- Skip trivia: wording, formatting, typos, file moves, no-behaviour refactors. Git history covers those.
- Squash changes within the same day (do not add changes to changes).
- Write more than one line only if a future agent couldn't recover the reasoning from the source.
- No version numbers.
- When you add a changelog entry, set `metadata.version` in `SKILL.md` to the same date.
