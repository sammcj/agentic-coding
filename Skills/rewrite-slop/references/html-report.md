# The HTML report

Read this only when the user has asked for a report, a page, or a visual of what was flagged. The rewrite phases never call it, and it changes no text.

## Running it

```
python3 scripts/render_report.py FILE [--against ORIG] [-o OUT]
```

Stdlib only, no network, no build step. It writes one self-contained HTML file and prints the path.

- `FILE` is whichever text the user wants read. If you have just rewritten something and they ask for a report, that is the rewrite, and you pass the original as `--against ORIG` to get the before-and-after block. Same order as `check_output.py --against`.
- Default output replaces the input's extension with `.slop-report.html`, beside the input. Pass `-o` when that would leave a stray file somewhere the user would not want one.
- Do not try to open it yourself. `open` and its equivalents are often sandboxed, and a failed launch reads as a failed report.

## What to hand back

Give the user the path and stop. Do not paste the HTML into the conversation, summarise every finding it already lists, or walk them through the layout: the page exists so they can read it themselves, and repeating it in chat spends the context the page was meant to save.

Two things are worth one line each, because they are judgements the page shows but does not make:

- Which Tier 2 group leads the bars, since that is the group to thin.
- Anything the page cannot know: a flagged term that is correct in context, a long paragraph worth its length.

If the text renders in a narrow column, the source is hard-wrapped and the page is showing it as written. That is not a fault and does not need fixing.

## What is on it

Two columns on one screen. Left, a panel: the register band with a gauge against the calibrated thresholds, one bar per Tier 2 group, the structural findings, and every term ranked by frequency with a search box. Right, the whole input with each flagged span marked in place and shaded by severity.

Clicking a term in either column keeps it selected and fades the rest, so a term in the list can be found in the text and a bad passage traced back to its term.

---

The rest of this file is for editing the skill, not for running the report. Stop here if you were asked for a report.

## Where the design comes from

The board is louisabraham.github.io/load-bearing, borrowed for its interaction rather than its content. That page charts a corpus across twenty months, which a single document has no axis for, so its analysis does not travel. What does: the ruled compartments, the click-to-hold selection, one grey ramp with a single accent reserved for the thing being pointed at, and light only. Keep those four.

Two columns rather than that page's twelve. Twelve suits a board of charts read all at once; this page is one long document and a panel about it, and stacking them put the findings a screen away from the text they point at. The leftover `grid-column: span 12` from the twelve-column version cost an afternoon: with two explicit columns the grid silently manufactures ten implicit ones, and the page stays well-formed while every item lands in the wrong track.

## When you change the detection

The page reads `check_output.py` rather than reimplementing it: `scan_spans` for the marks, `register_stats` for the gauge and bars, `blobs` and `line_checks` for the structure cell, and `SAFE`/`REVIEW`/`REPORT` membership for each mark's severity. A new rule reaches the page with no edit here. A new *kind* of finding, neither span nor line, needs a cell of its own.

Three checks after a change, all of them past what a browser screenshot will show you:

- The page's mark count equals the finding count `check_output.py` prints for the same input.
- Every tag closes.
- No `grid-column: span` is left in the CSS.
