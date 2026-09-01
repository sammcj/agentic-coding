# Changelog

<!-- AI agents: After completing changes to this project, add a terse TLDR style bullet describing the change under today's date heading (## YYYY-MM-DD), newest date first. Create the date heading if it does not exist. No versioning is required. -->

## 2026-08-31

Rebuilt the detection around two empirical sources, louisabraham.github.io/load-bearing and berenslab/llm-excess-vocab, and borrowed detection from `skill-creator-primer`. The finding behind it: the classic slop list (delve, leverage, pivotal, seamlessly) belongs to a _receding_ register, and none of those words appear in the growing cluster's top 1000.

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
- `break-before-heading` fired on a single `---`, which is just a horizontal rule. Gated on both a count and a share of the document's headings, since what claude.ai does is put one above heading after heading. Rubric updated to match.
- Indented code blocks counted as prose.
- REPORT findings print the matched text, not just the rule name.
- Tier 1 owns "honest" outright, widened to thoughts, appraisal, verdict and bare "honestly". `metaphor-tic` gained "smoking-gun", "corpus" and "corpora".

**HTML report (optional)**

- New `scripts/render_report.py` and `references/html-report.md`: one self-contained page per input, stdlib only, no network or build step. Gated in SKILL.md on the user asking, one line.
- "slopsummary" triggers the report. In the frontmatter as well as the body, since the body only reaches an agent that has already loaded the skill.
- The reference is written for the agent running it, not for a reader of the page: which file is `FILE`, not to try opening it, and to hand back the path rather than narrating the findings the page already lists. The layout description is trimmed to the two judgements the page shows but does not make. Maintenance notes sit below a marked break.
- Shows the register gauge against the calibrated thresholds, a bar per Tier 2 group, every term ranked by frequency with a search box, the structural findings, and the whole input with each flagged span marked in place. Clicking a term holds it selected and fades the rest.
- `--against ORIG` adds paired before-and-after bars for word count, hits per severity, and register rate.
- Two columns filling one screen, the panel of instruments beside the document rather than above it, each scrolling on its own. Stacked, clicking a term scrolled the text a screen away from the findings list that pointed at it.
- Borrowed from louisabraham.github.io/load-bearing: the ruled compartments, click-to-hold selection, one grey ramp with a single accent, light only. None of its analysis carries over, since a single document has no time axis.
- `register()` split into `register_stats()` plus formatting, and `scan()` into a projection of `scan_spans()`, so the page reads the same measurement rather than a second implementation of it.

**Negation-antithesis, widened**

- Caught 6 of 17 phrasings of "it's not X, it's Y". Now 36 of 36 across a test set, with no false positive on the skill's own prose or a 776-line sample. What makes it decidable is not the negation, which ordinary prose is full of, but the positive re-assertion after it: a pronoun and copula echoing the clause just denied, a preposition that repeats, or the same verb with the same subject.
- Three discriminators, each from a real false positive. The denied half carries no conjunction, so "not among them, and stays a separate file. It is..." is two statements rather than a denial and its replacement. A bare preposition after the negation means place or relation, not identity, unless it repeats: "not among them" continues, "not about speed, it's about clarity" is the figure. And `but` needs its own marker, because a bare "not X, but Y" cannot be told from ordinary contrast without knowing whether a finite verb follows it: "not the count, but the trend" and "not warm, but the test still passes" are the same shape to a regex. Only the marked forms are matched: the adverb, the repeated subordinator, `rather`, `so much as`.
- SKILL.md used the figure itself, in the line banning dashes.

**Findings carry their reason**

- One line per rule saying what it caught and why it is worth changing, on hover over a mark or a row, and in a caption under the list that holds while a finding is selected. A rule name alone left the reader to guess whether a hit was a typographic artefact or a habit of thought.

**Block findings, after a 776-line report the page had little to say about**

- `wide-table-cell` reported once per row: a real document produced 135 identical entries and drowned everything else. Now one `wide-table` finding per table, with the count of prose cells. That document went from 143 findings to 22.
- New `hard-wrapped` detection. A markdown paragraph renders as one line however it is typed, so a paragraph arriving as several lines was wrapped by hand: the test is a length floor per break, nothing more. Testing the columns for consistency first missed 30 of 82 paragraphs, because one line ending early before a long link breaks the pattern while still being a wrap. Reported once for the document with a count, and marked in the text at each break, since the wrap is invisible in rendered markdown and reflows the whole paragraph in every later diff.
- `units()` skips YAML front matter, which was reporting `description:` plus the next key as a wrapped paragraph.
- Long paragraphs and prose tables are now shaded in the document rather than only listed, and `blobs` carries its end line to make that possible. What is wrong with them is their extent, so an underline could not show it.
- The headline strip counts findings and register markers, not spans and distinct terms. On a document whose problem is register, "4 flagged spans, 2 terms" read as a clean bill directly above a HEAVY verdict.
- Findings and Structure merged into one searchable list, blocks above terms. Separate, the same document put two rows in one cell and eighteen in the other. Clicking a block now scrolls the document to it.
- Every row carries its count: paragraphs for the wrap finding, occurrences for the line-level rules, which are now grouped by rule the way the terms are. Line rules also carry a plain-English label, since `break-before-heading` names nothing to a reader without the rubric open.
- The gauge is three bands with a needle on them. As a filled bar it said nothing once the rate passed the end of the scale: 22.5 on a scale to 20 was a solid block of accent at 100%, and the scale now stretches to hold the value.
- Register groups sort by total hits, not by how many distinct words they used, so the order matches the bars: a group of 56 was sitting below one of 27.
- The accent now reaches the leading group bar. As `:first-of-type` it matched the verdict div above the bars and coloured nothing.
- One markdown walker, `units()`, now backs the blob, table and wrap findings. It was buried inside `blobs()`, and a table scan and a wrap scan would each have copied its fence, indented-code and list-marker handling.

**Maintenance**

- New `references/refresh-vocabulary.md` and `scripts/refresh_markers.py` for re-deriving the vocabulary when a source moves. Reports only; gated on the user asking.
- Ran the checker over its own references. Both scored HEAVY and both now pass: marker words that were being mentioned rather than used are backticked so the inline-code skip catches them, and the rest was ordinary prose that thinned. SKILL.md still scores HEAVY by construction, since the rubric lists the vocabulary it detects.
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
