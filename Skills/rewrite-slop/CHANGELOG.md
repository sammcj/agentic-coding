# Changelog

<!-- AI agents: After completing changes to this project, add a terse TLDR style bullet describing the change under today's date heading (## YYYY-MM-DD), newest date first. Create the date heading if it does not exist. No versioning is required. -->

## 2026-08-31

Folded in the empirical ranking from louisabraham.github.io/load-bearing (461k GitHub PR descriptions, one vocabulary cluster growing 0.7% -> 36.6% of the corpus between January 2025 and August 2026). The finding that drove the change: the classic slop list (delve, leverage, pivotal, seamlessly) belongs to a *receding* register, and none of those words appear in the growing cluster's top 1000 at all.

- Tier 2 rewritten as "Claude's current register", with four empirically ranked groups: assertive adverbs, absolute negation, code-as-agent verbs, adjudication nouns. Concentration is the tell, so none of it is a blocklist.
- Tier 3 abstract metaphor nouns gained the building/machinery family actually observed in current output: seam, ceiling, floor, lever, rung, ladder, chokepoint, backstop, carve-out, tripwire, machinery, knob.
- `check_output.py` gained a `register` density check, grouped by the same headings Tier 2 uses so the report names which group is over-represented. Two gates must both trip: 4.0 per 1000 words (HEAVY at 10.0) and 4 absolute matches, and it stays quiet under 200 words. On the source corpus that separates 0.3% of January 2025 descriptions from 45.2% of August 2026 ones. The rate alone flagged clean short prose on a single word.
- New `marketing-adjective` rule (comprehensive, robust, seamless, enterprise-grade, scalable, vibrant, groundbreaking and the rest of the receding register). Report-only: several have a literal technical sense.
- `honest` framing widened to thoughts, appraisal, read, verdict, summary, version, breakdown, plus bare "honestly" and "if I'm honest". Tier 1 now owns "honest" outright; Tier 2 no longer restates it.
- `metaphor-tic` now catches hyphenated "smoking-gun" and "corpus"/"corpora" used for an ordinary set of documents.
- REPORT findings print the text that matched, not just the rule name. A rule with eighteen alternations was leaving the agent to reopen the line to find out which one fired.
- `honest-framing` and `chat-residue` now match curly apostrophes, which the sycophancy rules already did. REPORT runs before SAFE straightens them, so "If I'm honest" and "I'll help you" were slipping through in report-only mode.
- `--write` no longer sends a correctly-applied `en-dash-range` fix back for a re-read; the review list now goes through the same SAFE/REVIEW dedup as the report path.
- Phase 0 explains the density line; Phase 4 gained three verify questions (band dropped, metaphor tics, surviving "honest").
- New `references/refresh-vocabulary.md` and `scripts/refresh_markers.py`: how to re-derive the Tier 2 vocabulary when the source ranking moves. The script reports candidates and drop-outs against the live data and edits nothing, since separating style from subject matter is a judgement call. Gated in SKILL.md on the user asking, so it never runs during a rewrite.
- Tier 3 gained realm, emerges (as), poised (to) and revolutionise, from Kobak et al.'s PubMed excess vocabulary (berenslab/llm-excess-vocab, MIT). Ratios on five-figure abstract counts: realm 5.5, revolutionize 5.2, poised 3.6, emerges 3.5, measured against a real pre-2023 human baseline.
- Tier 3 now states that its lists match on meaning, not spelling, and the rewrite keeps the input's own convention. Fixed two rules that carried only one form: "emphasise" and "widely recognised". A single-spelling rule silently passes half its inputs.
- The new `marketing-adjective` alternations write out every -ise/-ize pair.
- Checked the same dataset against Tier 2 and found almost nothing (18 of 106 words at r>=1.5, all at noise-level counts). Its data ends in 2024 and the Tier 2 register grew through 2025 and 2026, so the two sources corroborate the split between the registers rather than overlapping.
- Both scripts pass ruff, pyright and mypy clean. Fixed: two files opened without a context manager, an ambiguous `l` binding, two over-long lines, and the `zip` in `refresh_markers.py` now uses `strict=True` so an index misalignment in upstream data stops rather than truncating. `apply()` binds its loop variables as defaults, and the `zip` in `compare()` is explicitly `strict=False` because a differing block count is the finding there, not an error.
- Recorded why the marketing register was left in Tier 3: of its 52 words only comprehensive, enhance, streamline, seamless and robust appear in the source data at all. The other 47 never clear its 50-account floor, so absence there is a limit of the sample rather than evidence.

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
