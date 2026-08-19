# Changelog

<!-- AI agents: After completing changes to this project, add a terse TLDR style bullet describing the change under today's date heading (## YYYY-MM-DD), newest date first. Create the date heading if it does not exist. No versioning is required. -->

## 2026-08-20

- Added `scripts/check_output.py` (stdlib): SAFE fixes silently, REVIEW fixes and prints each location, REPORT detects only. `--write` to fix, `--against ORIG` for length and code-block passthrough. Skips fenced and inline code.
- Phrase swaps sit in REVIEW: the script cannot see quoted speech.
- New detections: sycophancy openers, honest-framing, fixed puffery phrases, wide table cells.
- Phase 0 and Phase 4 call the script and state it is an indicator, not a review.
- Tier 3: syntax tells (nominalisation, stacked noun phrases, landing sentences, negative anaphora, in-paragraph parallelism, forward references).
- "Puffery" labels all four blocks describing it; "semantic density" names the target in the positive brief.
- Phase 3: sentences with no flagged span pass through unchanged.
- Description made imperative; `→` replaced with `->`.

## 2026-08-19

Merged selected rules from the upstream `unslop` skill (Cursor), then reviewed and compressed.

### Added

- Phase 0: 8 filler-phrase substitutions, never applied inside quotes, code or citations
- Phase 0: round brackets, single hyphens and ordinary colons explicitly permitted
- Tier 3: abstract metaphor nouns (substrate, vector, nexus, flywheel) with plain replacements; terms of art exempt
- Tier 3: generic-docs test for sentences naming a feeling instead of a mechanism. Fix from input facts only, else cut
- Tier 3: colon as mid-sentence connector; explanatory colons stay
- Tier 3: false ranges ("from X to Y" with no shared scale)
- Tier 3: dense sentences, split by cutting clauses, never by restating the subject
- Phase 4: verify questions for metaphor nouns, generic-docs test, colon splices, false ranges, total length

### Changed

- Tier 4: bold-header bullets flag on restatement, not punctuation. Exemption carried into Phase 3 brief and Phase 4
- Length rule now one-directional: never longer than the input
- Stacked-hedge collapse moved from Phase 0 to Tier 3
- Phase 0 no longer offers a colon as an em-dash replacement
- Phase 4 preamble: removed conflicting second instruction
- Six oversized rule blocks restructured into lists, -106 words

### Removed

- Gotchas section; its two unique items folded into Phase 3
- `---` thematic breaks before headings
- Three unnamed-source claims ("reported at 2 to 5x human rate")
- Duplicate "utilise" and "It is important to note that" entries, now owned by Phase 0
