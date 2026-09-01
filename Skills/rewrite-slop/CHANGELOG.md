# Changelog

<!-- AI agents: After completing changes to this project, add a terse TLDR style bullet describing the change under today's date heading (## YYYY-MM-DD), newest date first. Create the date heading if it does not exist. No versioning is required. -->

## 2026-09-02

Reviewed against fresh Fable 5.1 output (1.6k words, five genres): zero hits on the classic vocabulary, register ELEVATED at 6.3/1000, and the live tells were sentence-shaped (short closers, clipped contrasts, tag clauses, invented anecdotes). Everything below follows from that.

**Confidence tier**

- Every finding is possible, probable or certain. `POSSIBLE` in `check_output.py` maps a rule name to a one-line caveat; membership is the whole mechanism, so reclassifying a rule is one line. SAFE and REVIEW rules are certain, REPORT rules probable.
- Text output prints possible rules after the rest under `? possible, read before deciding:`, each rule's caveat once above its hits, every line prefixed `?`. The tally counts them apart (`4 findings, 6 possible`) and they never set the exit code.
- Reclassified as possible: `weasel-source` (now case-insensitive, since "Studies show" opens the sentence), `us-spelling`, and two rules split out so the caveat does not soften their neighbours: `corpus-noun` from `metaphor-tic`, `emphasis-verb` (emphasise, underscore) from `filler-verb`. `underscore` needs its verb-with-object shape, so a double underscore stops firing.
- Rubric: Phase 0 and Phase 4 say a plain finding is a fix and a `?` finding is a read decided against its caveat.

**Sentence-shape tells** (new `scripts/syntax.py`, all in `POSSIBLE`)

- Module wiring: `syntax.py` takes the `units` list as a parameter rather than importing `check_output`, which avoids the circular import. `check_output.py` wraps it as `shape_spans(text)` and `parataxis_stats(text)` and adds the spans to the REPORT grouping; `render_report.py` reads `all_spans()` (regex plus shape) for marks and tally. `line_offsets` lives in `syntax.py` and the report imports it.
- Sentence splitter: ends on `.!?` followed by a capital, digit or opening quote, or the end of the unit. Abbreviation list (e.g., i.e., vs, etc, Dr, Mr, Inc...) only. No single-letter initial, because "plan B." ends a sentence far more often than "J. Smith" appears in technical prose; no digit, because "in 2024." ends a sentence and "3.10" is already refused on the missing space. Inline code is masked to same-length `x` runs so offsets hold and `foo.bar()` is one word.
- `landing-sentence`: a closer of `LANDING_MAX` 6 words or fewer, after sentences averaging `LANDING_REST` 12 or more, in a paragraph of 2 or more sentences ("Not Postgres.", "It is a different product."). Not counted: list items, a closer ending in a colon, one carrying a link ("Source: [...]"), or closers opening on the same two words at the end of `TRAILER_RUN` 3 or more paragraphs ("Depends on M1."), which are structure. Banded `landing HABIT` at `LANDING_RATE` 1.5 per 1000 words with at least `LANDING_LEAST` 3, which promotes it to a finding.
- `contrast-pair`: a sentence of `CONTRAST_MAX` 8 words or fewer, not the first in its paragraph, ending `is|are|does|... not` before `.`, `!` or `:` ("What we gain is small. What we pay is not:").
- `tag-clause`: a sentence ending `, and|but|which|though|or` + pronoun + auxiliary (", and we should.", ", which it does.").
- `anaphora`: `ANAPHORA_RUN` 3 consecutive sentences in one paragraph opening on the same word.
- `parataxis`: the share of measurable paragraphs (`FLAT_SENTENCES` 3 or more sentences, mean 9 to 30 words, list items included) with no subordinator (because, although, which, if, when, ...). Sentence length is not the measure: model output varies length widely (four-word punch after a twenty-word sentence) and lacks subordination instead. Printed as a measurement, counted as nothing, once `FLAT_MEASURED` 6 paragraphs exist; banded `UNJOINED` at `FLAT_SHARE` 0.6 with at least `FLAT_LEAST` 4.
- Calibration: 524 local markdown files of 200+ words (personal notes, installed skills, 400 random files under ~/git, node_modules and vendor excluded) against the Fable samples. Landing bands 2% of the corpus and the samples; contrast pairs and tag clauses appear in under 1%; a third of paragraphs unjoined is the corpus median, and the band takes 3%. The first parataxis measure, sentence-length coefficient of variation, banded 20% and did not separate the samples, and was dropped.
- Rubric: Tier 3 syntax tells gain elided contrast pairs, tag clauses and parataxis; sourcing gains invented specificity ("which got us rate-limited last week": a model taught that concrete beats abstract makes the concrete up).

**New specifics under `--against`**

- `new-number`, `new-name`, `new-time`, `new-anecdote`: numbers (thousands separators ignored), mid-sentence proper nouns, relative time ("last week", "the other day") and discovery narrative ("I only noticed", "we ran into", "the hard way") in the rewrite that the original lacks. Each is a fact to check against the original, and Phase 4 says so: "three" as "3" or "it was found" as "we found" is the same fact. The anecdote shapes are narrative only; "found", "saw", "measured" were dropped because de-nominalising a passive produces them.

**Report**

- Marks run on one ramp from pale yellow to red by slop confidence, and the key under the findings is headed "Slop confidence" with possible, probable and certain in those words. The old safe/review/report labels described what the script did, not what the reader should think. Block shading sits on the same ramp a shade lighter: dense runs and unjoined paragraphs in the yellow of possible, long paragraphs and prose tables in the orange of probable. No grey anywhere a finding is marked; a dotted rule for possible could not be seen at reading distance, and the underline carries no meaning of its own. Orange was darkened once because it read as the yellow.
- Possible rows carry `?` before their count, rank below every probable row whatever their count, and their reason (`why()`) ends with the caveat. The brief splits into "Findings, fix these" and "Possible, read before changing", caveat included, since the receiving agent has the file but not the page.
- Shaded blocks carry `data-why`, so hovering one shows its reason in the caption as hovering a mark does.
- Marks cannot nest in the single-pass marker, and a landing sentence can hold a chat-residue phrase: probable spans are placed first and a possible span overlapping one is not marked, keeping its row. Landing sentences select as one term, so the habit row and each closer's row hold all of them, as bold does.
- Unjoined paragraphs are shaded only once banded, and listed once as the aggregate row rather than once per block; the findings count in the strip excludes possible spans and those blocks, so it agrees with the text tally.
- Before and after, shown only with `--against`, is one small table of figures with a delta column instead of five pairs of bars, with the added specifics listed under it.

**Vocabulary**

- "Nothing collapses." joins `metaphor-tic` as a certain finding: the landing sentence at its most reflexive.
- `WEIGHTS` beside `MARKERS`: "earns" (and earn, earned, earning, now all in the code-as-agent group) counts double in the register rate. The count gate stays raw, so a weighted word cannot band a short document by itself, and the per-word counts under the band are what was found. A weighted word must also be in `GROUPS`; refresh-vocabulary.md says so.

**Tests**

- `scripts/test_syntax.py`: catch and keep cases per shape rule, sentence-splitter cases (abbreviation, decimal, year, single letter, inline code), the new-specifics check and its de-nominalised keep case, the emphasis-verb split, "Nothing collapses.", the earns weight, a banded and an unbanded parataxis document, and the printed `?` block and tally.

## 2026-09-01

**Dense runs**

- New `dense-run` finding: consecutive units each dense but typically none long enough to be a `long-paragraph`. Three paragraphs at 90 words, or two list items at 70. A heading, fence, table or quote between them ends the run; a blank line does not, since a run of paragraphs is the finding.
- List items count at a lower floor and after fewer of them. A bullet promises to be short, so a run of 90-word bullets breaks its own contract in a way the same run of paragraphs does not.
- A blob does not end a run, because the stretch is a wall whether or not one member also overruns; the finding carries the longest member so the two are told apart. In the report the run shades grey around the blob's red rather than replacing it.
- `Unit` carries whether it is a list item, which `units()` knew and dropped.
- Flags 2% of the same 413 files.

**Bold, measured**

- New `bold` density check, mechanising a Tier 4 rubric line that had nothing behind it. Emphasis works by being rare, so the finding is a rate rather than a list of spans: mid-sentence bolds per 1000 words, banded HEAVY over 8.0 and ABUSED at 20.0. Both gates trip first, as with `register`, so a short file cannot band on one span.
- Bold that opens a line is a label and is exempt at any volume, including a bullet lead, `**Date:** 2026-09-01`, a bold line standing in for a heading, and a task-list checkbox. Measured across 413 markdown files on this machine, that split is what separates the habit from ordinary use; the rule flags 8% of them and calls 2% abused.
- The other road to ABUSED is crowding: three or more reading chunks carrying two bolds each, and a twentieth of the document. A table row counts as a chunk. On the report that prompted this, every one of its 129 mid-sentence bolds sat in a prose table cell, which `units` skips, so paragraphs alone measured zero.
- Marked in the report in blue rather than on the severity ramp, since no single one of them is the defect, and held together when the row is clicked, which is the only way to see the density the band names. Below the gates nothing is marked at all.
- `bold_stats` matches the raw text and skips code the way `scan_spans` does. Substituting code away first, as the word count still does, collapses each span to one character and moves every offset after it: the marks landed on words several sentences from the bold they described.
- Long paragraphs are shaded red rather than grey, so the two block kinds read as findings rather than as one finding and one aside.

**American spelling**

- New `us-spelling` rule in REPORT, in eight patterns. A model writes American spelling whatever convention the document keeps to, which makes a stray `color` in an Australian document a tell of the same kind as a stray em dash.
- Reported, never swapped. The word can be right as a proper noun (the Australian Labor Party, the World Health Organization) and `licence`/`practice` turn on noun versus verb, which no pattern can see. `program` and `artifact` are left out, being what Australian technical writing uses.
- `scripts/test_us_spelling.py` holds 147 words the rules must catch and 190 they must not, importing the patterns rather than copying them. The second list is the point. It is why the -our stems take no `ous` ending, and why the -ize rule keys on the letter before `iz` never being `s` or `i`.
- Tier 3 said to keep the input's own spelling convention, now true only for a document written for an American reader. Both paragraphs are one.

**Register bands**

- The register's upper band reads `SLOPPY` rather than `HEAVY`. The bold check keeps its own `HEAVY`, one band under `ABUSED`, so the two scales no longer share a label: a register reading and a bold reading measure different things and sat next to each other in the report saying the same word.
- Renamed through the threshold constant, the gauge ticks, the band's CSS class and the copied brief, so the report and the text it hands to an agent agree.

**Comment width**

- `ruff.toml` sets `line-length = 120`, and the comments and docstrings in `scripts/` are rewrapped to it. E501 stays unselected, because the rule tables put one detection rule on one line.
- Usage blocks, examples and rule tables keep the shape they were given: only paragraphs whose later lines are unindented, unbulleted and not introduced by a colon were reflowed. Both scripts produce byte-identical output to before the rewrap.
- `render_report.py` reports a missing input file, and an output path it cannot write, as one line each instead of a traceback. The write error names `-o` as the fix, since the default output sits beside the input and that directory is often read-only.
- The `nbsp` and `private-use` patterns are written as `\uXXXX` escapes. Their literal form is invisible in an editor and does not survive a copy through anything that normalises whitespace; one such round trip had already emptied both character classes, silently disabling the rules.

**Copy brief**

- A button in the report's footer copies the findings as about a page of text: the register band, the heaviest Tier 2 group with the words that put it there, then one line per rule carrying its count, up to six instances, and the reason it is worth changing. Written to be pasted into a coding agent that has the file but not the page, so it opens with what to do and names the file it applies to. Capped at twelve kinds, with the remainder counted rather than dropped silently.
- Grouped by rule, since one rule is one habit to drop however many times it fired, and a list of bare rule names leaves the receiving agent guessing.
- The list and the brief are now two renderings of one list of `Finding`s. Building the brief from a second walk of the checker would let the two disagree about the document they describe.
- `navigator.clipboard` is not there to call on every browser under `file://`, so a hidden textarea and `execCommand` stand behind it, and the brief is revealed to select by hand if both refuse.
- The brief's own lines are separated by a blank one rather than wrapped, since whatever it is pasted into may render it as markdown. It was reporting itself as hard-wrapped.

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
- The Tier 2 group names carry the same, plus the words that put them there. `code-as-agent` means nothing without the rubric open. Each says what the concentration is doing rather than condemning the word, since no word in these groups is wrong on its own.
- New `ruff.toml`. The scripts were clean only under a hand-passed ignore list, so the same run in an editor produced 67 warnings. UP031, SIM905 and RUF001 are ignored with the reason stated in the file; E5 is left out of the select because the rule tables put one detection rule on one line. Fixed the three RUF005 sites rather than ignoring them. Ruff's own UP031 fix was rejected: it writes `.format()` rather than f-strings and reaches 27 of 67 sites, which would leave the same function written two ways.

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
