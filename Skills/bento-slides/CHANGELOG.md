# Changelog

<!-- AI agents: After completing changes to this skill, add a terse TLDR style bullet describing the change under today's date heading (## YYYY-MM-DD), newest date first. Create the date heading if it does not exist. Log only changes a reader would care about - new capability, changed or broken behaviour, removals, real fixes. Skip cosmetic and housekeeping edits (wording, formatting, typos, file moves); git history covers those. One line per change, aim under 15 words - say what changed, not how it was implemented. Write more only when the change is genuinely complex and the reasoning cannot be recovered from the source or git history. No versioning is required. When refreshing references/agents-<version>.md, log the Bento version and the date it was read. -->

## 2026-09-22

- Vendored a pruned bento.page/agents.md as `references/agents-1.2.3.md` (Bento 1.2.3, read 2026-09-22)
- Added `references/format-reference.md`: 1.0.19 to 1.2.3 fields, fx vocabulary, text/chart/morph rules, window.bento signatures
- Compact authoring form is now the default; on-disk block still holds the full document
- `render_check.mjs`: `--doc` loads full or compact JSON via loadDoc and prints dropped keys; `--write` splices the expanded document back
- `render_check.mjs`: `text-too-small` and `low-coverage` warnings; `--min-font`, `--min-cover`; dropped keys fail the run
- `render_check.mjs`: refuses encrypted decks; hidden slides no longer overshoot the page walk
- Density rules: display vs content band tiers, 16px body / 14px floor, fill the band then choose gaps
- Workflow: ask the user to close the deck in the browser before editing (save and autosave restore both clobber)
- Collab step corrected: leave `collab` untouched, point at View-only copy or Reset access; deleting keys severs the owner
- Gotchas corrected: `{{date:PATTERN}}` pins format, `muted` defaults on, morph swaps content at frame one, builtin fonts need no bytes
- Gotcha added: role-placed compact elements keep only their content; `fx`, fonts and colours on them are discarded silently
- Feature map gained `unnumbered` builds, code elements, connectors
- Gotcha added: bullets are `<ul><li>` in `html`; glyph bullets and `md` bullets wrap badly
- Animation is now opt-in: static decks by default, all motion guidance moved to `references/motion.md`
- Compact expansion is theme-blind: free-placed text needs explicit `fontFamily`, `color`, `align`, `valign`
- `render_check.mjs`: presses through `fx.step` reveals per page; `--write` restores `template` and `layouts`; invisible hit rects no longer mask low coverage
- Gotchas added: `line` shapes draw 2px minimum, table header always bold, chart `show` flags unread, `theme.chartPalette`
- Density: aim for 20px+ body on content slides
- `render_check.mjs`: boots with DNS off so shared decks never join their room (`--online` opts out); `--margin` flag
- `render_check.mjs --write`: keeps `<path>.bak`, carries input `collab` through minus `sync` (stale stamp resurrects deleted elements)
- Close-deck guidance explains the `collab.sync` merge and the Discard/Reset access recovery
- Gotchas added: lists cost height, `fit:"contain"` boxes lie to margin and coverage checks, `measure()` ignores `letterSpacing`
- Added CHANGELOG.md and CLAUDE.md
