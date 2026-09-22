# Changelog

<!-- AI agents: After completing changes to this skill, add a terse TLDR style bullet describing the change under today's date heading (## YYYY-MM-DD), newest date first. Create the date heading if it does not exist. Log only changes a reader would care about - new capability, changed or broken behaviour, removals, real fixes. Skip cosmetic and housekeeping edits (wording, formatting, typos, file moves); git history covers those. One line per change, aim under 15 words - say what changed, not how it was implemented. Write more only when the reasoning cannot be recovered from the source or git history. No versioning is required. When refreshing references/agents-<version>.md, log the Bento version and the date it was read. -->

## 2026-09-23

- New decks are written with sharing off (`collab.on:false`, real keys kept); Share turns it on

- `render_check.mjs` warns on 3+ typefaces, missing notes, double page numbers, unrequested motion (`--motion` opts in)
- `render_check.mjs` surfaces `past-margin` and notes when the deck's Bento version differs from the references

## 2026-09-22

- Vendored a pruned bento.page/agents.md as `references/agents-1.2.3.md` (Bento 1.2.3, read 2026-09-22); added `references/format-reference.md`
- Compact authoring form by default; `render_check.mjs --doc --write` expands it through the runtime into the on-disk block
- Compact expansion is theme-blind, and role-placed elements keep only their content
- Animation is opt-in: static decks by default, motion guidance in `references/motion.md`
- Density rules: display vs content tiers, 14px floor, 20px+ body on content slides, fill the band
- Safe editing: close the deck's browser tab first, leave `collab` as found, `--write` drops `collab.sync` and keeps `.bak`
- `render_check.mjs`: DNS off by default, rejects encrypted decks, walks `fx.step` reveals, `text-too-small` and `low-coverage` warnings
