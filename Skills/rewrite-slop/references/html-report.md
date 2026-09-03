# The HTML report

Read this only when the user has said "slopsummary", or asked for a report, a page, or a visual of what was flagged. The rewrite phases never call it, and it changes no text.

## Running it

```
python3 scripts/render_report.py FILE [FILE ...] [--against ORIG] [-o OUT]
```

Stdlib only, no network, no build step. It writes one self-contained HTML file per input and prints each path.

- `FILE` is whichever text the user wants read. If you have just rewritten something and they ask for a report, that is the rewrite, and you pass the original as `--against ORIG` to get the before-and-after block. Same order as `check_output.py --against`.
- Several files get a page each, in one run. `--against` then compares every one of them to the same original, which suits two candidate rewrites of one draft and nothing else.
- Default output replaces the input's extension with `.slop-report.html`, beside the input. Pass `-o` when that would leave a stray file somewhere the user would not want one. With several files `-o` names a directory, created if missing.
- Do not try to open it yourself. `open` and its equivalents are often sandboxed, and a failed launch reads as a failed report.

## What to hand back

Give the user the path and stop. Do not paste the HTML into the conversation, summarise every finding it already lists, or walk them through the layout: the page exists so they can read it themselves, and repeating it in chat spends the context the page was meant to save.

Two things are worth one line each, because they are judgements the page shows but does not make:

- Which Tier 2 group leads the bars, since that is the group to thin.
- Anything the page cannot know: a flagged term that is correct in context, a long paragraph worth its length.

If the text renders in a narrow column, the source is hard-wrapped and the page is showing it as written. That is not a fault and does not need fixing.

## What is on it

Two columns on one screen. Left, a panel: the verdict (the register band when it has one, MINOR SLOP while anything at all was found, CLEAN only when nothing was), a needle on the calibrated thresholds, one bar per Tier 2 group with the accent on the group to thin, and one searchable list of every finding. Right, the whole input, marked up.

The findings list is one list on purpose. Long paragraphs, prose tables, hard-wrapping and the line-level findings sit at the top, measured by their extent; the terms follow, ranked by count with a bar in each row. Split into two cells, a document whose problem was structure showed two rows under findings and eighteen under structure.

Clicking a term keeps it selected and fades the rest, so a term in the list can be found in the text and a bad passage traced back to its term. Clicking a block scrolls the document to it.

Every finding carries one line on what it is and why it is worth changing, shown on hover over a mark or a row and held in the caption under the list while something is selected. The text lives in `WHY` in `render_report.py`; a new rule wants an entry there, or it reaches the page as a bare rule name.

Copy brief, in the footer, puts the same findings on the clipboard as about a page of text: the register band, the heaviest group, then one line per rule with its count, a few instances, and the reason. It is written to be pasted straight into a coding agent that has the file but not the report. Mention the button when the user's aim is to hand the work to another agent.

Four kinds of mark in the document, because not every finding is a word:

- Flagged spans shaded on one ramp from pale yellow to red by slop confidence, which the key under the findings names: possible (a caveat applies), probable (the reader confirms), certain (mechanical, and `--write` fixes most of them).
- Block findings shaded on the same ramp, lighter: dense runs and unjoined paragraphs in the yellow of possible, long paragraphs and prose tables in the orange of probable, each labelled in its own margin. What is wrong with these is their extent, so they are shaded rather than underlined, and each is listed once. The rule that reported a wide cell per row buried a 776-line document under 135 identical entries.
- A `↵` at each hard wrap, since the break is invisible in rendered markdown and reflows the whole paragraph in every later diff. A markdown paragraph renders as one line however it is typed, so every break inside one was put there by hand; the only test is a length floor, which separates a wrap from a deliberately short line.
- Mid-sentence bold in blue rather than the severity ramp, since no single one of them is the defect. Clicking the row holds all of them at once, which is the only way to see the density the band is naming.
- Possible findings at the pale yellow end of that ramp, and `?` before their count in the list, where they rank below every probable row. Their reason ends with the caveat. Paragraphs with no subordinate clause are shaded only once the document bands UNJOINED.

The brief splits the same way: "Findings, fix these" and "Possible, read before changing", each possible rule carrying its caveat. With `--against`, and only then, a small before-and-after table sits between the register and the findings, and under it a list of each number, mid-sentence name, relative time and "I noticed" the rewrite added.

---

The rest of this file is for editing the skill, not for running the report. Stop here if you were asked for a report.

## Where the design comes from

The board is louisabraham.github.io/load-bearing, borrowed for its interaction rather than its content. That page charts a corpus across twenty months, which a single document has no axis for, so its analysis does not travel. What does: the ruled compartments, the click-to-hold selection, one grey ramp with a single accent reserved for the thing being pointed at, and light only. Keep those four.

Two columns rather than that page's twelve. Twelve suits a board of charts read all at once; this page is one long document and a panel about it, and stacking them put the findings a screen away from the text they point at. The leftover `grid-column: span 12` from the twelve-column version cost an afternoon: with two explicit columns the grid silently manufactures ten implicit ones, and the page stays well-formed while every item lands in the wrong track.

## When you change the detection

The page reads `check_output.py` rather than reimplementing it: `scan_spans` and `shape_spans` for the marks, `register_stats` for the gauge and bars, `blobs`, `tables`, `wraps`, `parataxis_stats` and `line_checks` for the structure cell and the block shading, `SAFE`/`REVIEW`/`REPORT`/`POSSIBLE` membership for each mark's confidence (certain, certain, probable, possible). A new rule reaches the page with no edit here; a new possible rule needs only its caveat in `POSSIBLE`.

The findings list and the copied brief are two renderings of one list of `Finding`s, so a rule cannot appear in one and not the other.

A new block-level finding is a paragraph unit test, not a regex. `units()` is the one markdown walker, and `blobs`, `_wrapped` and the block shading all read it; a second walker would drift from it on fences, indented code and list markers, which took three separate fixes to get right the first time.

Four checks after a change, all of them past what a browser screenshot will show you:

- The page's mark count equals the finding count `check_output.py` prints for the same input.
- Its shaded blocks and `¬` glyphs likewise equal `blobs` + `tables` and `wraps`.
- Every tag closes.
- No `grid-column: span` is left in the CSS.
