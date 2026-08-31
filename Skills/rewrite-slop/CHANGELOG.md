# Changelog

<!-- AI agents: After completing changes to this project, add a terse TLDR style bullet describing the change under today's date heading (## YYYY-MM-DD), newest date first. Create the date heading if it does not exist. No versioning is required. -->

## 2026-08-31

Rebuilt the detection around two empirical sources, louisabraham.github.io/load-bearing and berenslab/llm-excess-vocab, and borrowed detection from `skill-creator-primer`. The finding behind it: the classic slop list (delve, leverage, pivotal, seamlessly) belongs to a *receding* register, and none of those words appear in the growing cluster's top 1000.

**Tier 2, the current register**

- Rewritten from the load-bearing ranking as five groups: assertive adverbs, absolute negation, code-as-agent verbs, adjudication nouns, structural metaphor nouns. Concentration is the tell, so none of it is a blocklist.
- New `register` density check, grouped under the same names so the report says which group is over-represented. Both gates must trip: 4.0 per 1000 words (HEAVY at 10.0) and 4 matches, quiet under 200 words. Separates 0.3% of January 2025 descriptions from 45.2% of August 2026. The rate alone flagged clean short prose on one word.

**Tier 3, the receding register**

- Gained realm, emerges (as), poised (to), revolutionise, from Kobak et al.'s PubMed excess ratios (real pre-2023 human baseline), plus the building and machinery nouns from load-bearing.
- New `marketing-adjective` rule. Left the rest in place: of Tier 3's 52 words only five appear in the source data, so absence there is a limit of the sample rather than evidence.
- Lists now match on meaning, not spelling. Fixed `emphasise` and `widely recognised`, which carried one form and silently passed half their inputs.

**Verbosity**

- New `padding` rule and a Tier 3 verbosity block: padding phrases, redundant doublets, restatement, paraphrase repetition.
- Dropped the "~10% under" ceiling, which capped compression at a tenth when a bloated input needs a third. The floor is now the last sentence carrying a claim.
- New `long-paragraph` finding at 150 words. A compression target, not a tell: paragraph length does not separate AI from human in the source corpus.

**Ported from skill-creator-primer**

- `filler-verb` and `negation-antithesis` rules, both previously in the rubric with nothing mechanical behind them. Kept the `harness the` refinement.
- Findings grouped one line per term with capped locations: a word is fixed everywhere at once.

**Fixes**

- Multi-word patterns could not match across a hard line-wrap, missing "the fact that" split over two lines. Spaces outside character classes and lookbehinds now match a wrap, at most one newline.
- `negation-antithesis`, `honest-framing` and `chat-residue` missed curly apostrophes, which matters because REPORT runs before SAFE straightens them.
- `blobs()` dropped the words on a list-marker line and started a fresh unit at the wrap.
- `register` named "no one" in every report, because `Counter.update` creates a key at zero.
- Overlapping rules double-reported one edit ("marks a pivotal moment" plus "pivotal"); a contained span is now dropped.
- `--write` could apply an em-dash fix without listing it for the re-read when an nbsp sat at the same offset.
- YAML front matter registered as a `break-before-heading`.
- Indented code blocks counted as prose.
- REPORT findings print the matched text, not just the rule name.
- Tier 1 owns "honest" outright, widened to thoughts, appraisal, verdict and bare "honestly". `metaphor-tic` gained "smoking-gun", "corpus" and "corpora".

**Maintenance**

- New `references/refresh-vocabulary.md` and `scripts/refresh_markers.py` for re-deriving the vocabulary when a source moves. Reports only; gated on the user asking.
- CLAUDE.md names the upstream sources to check, none of them required.
- Both scripts clean under ruff, pyright and mypy. Kept `%` formatting and the space-separated word blocks, which read better than what UP031 and SIM905 want.

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
