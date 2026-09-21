# bento-slides skill

Bento source, when cloned, lives at `~/git/bento`; `slides/src/model.ts` is the format and `docs/agents.md` is the source of bento.page/agents.md.

## Conventions

- `references/agents-<version>.md` is a pruned copy of bento.page/agents.md. On refresh: curl the URL, re-apply the cuts listed in its header, rename to the new Bento version, log the read date in CHANGELOG.md.
- `references/format-reference.md` holds what agents.md lacks or gets wrong; correct it there rather than editing the vendored copy beyond `[version]`-tagged fixes.
- `scripts/render_check.mjs` needs a browser and fails inside the Bash sandbox (profile dir blocked); ask the user to run it with `!` when testing.

## Update CHANGELOG.md after changes

After a change that alters how this skill behaves - SKILL.md, references, scripts - you MUST add a bullet to `CHANGELOG.md` under today's date heading (`## YYYY-MM-DD`, newest first), creating the heading if absent.

- One line, under 15 words. What changed, not how it was built.
- Skip trivia: wording, formatting, typos, file moves, no-behaviour refactors. Git history covers those.
- Write more than one line only if a future agent couldn't recover the reasoning from the source.
- Squash changes within the same day (do not add changes to changes).
- No version numbers.
