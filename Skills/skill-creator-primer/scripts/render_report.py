#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml", "skills-ref"]
# ///
"""Render one skill's validate_skill findings as a single self-contained HTML page.

The page reads validate_skill rather than reimplementing it, so a new threshold
or rule reaches the page with no edit here; a new *kind* of finding, neither
line-span nor term, needs a cell of its own. Three contracts hold the page to
the detector:

- _structure returns each unit as (size, path, first line, last line, opening),
  and a dense run as the same five fields plus (count, longest, listed). The
  last line is what lets the page shade a whole unit; drop it and the shading
  falls back to the opening line alone.
- mark_line places each term by offset over vs._filler_scan's output. Searching
  the raw line for the matched text instead would mark occurrences the detector
  excluded: a word inside backticks, or a sentence-initial rule matching
  mid-sentence.
- _bold and _invisible hand over their spans already placed, and marked_source
  marks those and no others. Rescanning the page's text for bold would mark the
  bullet leads the rate deliberately exempts, and the row would then name a
  count the document disagrees with. Bold is one row however many spans it
  covers: it is a rate, so its bar reads against BOLD_ABUSED rather than
  against the term counts.

Confidence is read off the validator too. A rule in vs.POSSIBLE is possible
(yellow, marked ?, ranked last, split out of the brief with its caveat); an
invisible character is certain (red); everything else is probable (orange),
since the validator never gates on a word a skill may mean literally. Bold is a
density rather than a mark of any confidence and keeps its own blue.

Three checks after a change, all of them past what a browser screenshot shows:

- Every mark key (marks carry one per finding, joined by |) is matched by one
  lexical no-op or one counted bold span for the same skill.
- Every tag closes, and the shaded line ranges match the text report's numbers.
- Each cell sits in a single grid column; the panel stacks its cells with flex.
"""

import argparse
import contextlib
import datetime
import html
import io
import os
import sys
import tempfile
from pathlib import Path
from typing import NamedTuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import validate_skill as vs  # pyright: ignore[reportMissingImports]

# The gauge tops out past the Poor floor so a badly over-budget skill still has bar left to grow into rather than
# pinning at full and hiding how far over it is.
GAUGE_CEILING = int(vs._TOKEN_RATINGS[-1][0] * 1.5)

# What each colour on the document means, since the page is read away from the primer. One ramp from pale yellow to
# red by confidence; the two kinds outside it keep their own swatch.
LEGEND = [
    ("possible", "read before changing"),
    ("probable", "likely a defect"),
    ("certain", "fix it"),
]
KINDS = [
    ("em", "bold mid-sentence - a density, not a defect at the span"),
    ("code", f"fenced block over {vs.CODE_FENCE_LINES} lines - move it to scripts/"),
]
RANK = {"certain": 0, "probable": 1, "possible": 2}


def why_for(rule):
    """The rule's reason, with its caveat if it has one. The caveat travels with the reason everywhere the reason
    goes: caption, tooltip, mark and brief."""
    text = WHY.get(rule, "")
    if rule in vs.POSSIBLE:
        text = "%s Possible only: %s." % (text, vs.POSSIBLE[rule])
    return text


def confidence(rule):
    """What the reader should think of a mark: possible carries a caveat from the validator, certain cannot be
    argued with, and the rest is probable."""
    if rule in vs.POSSIBLE:
        return "possible"
    return "certain" if rule in vs.CERTAIN else "probable"

# The copied brief is read by an agent with a context budget, so it stays about a page: the kinds worth acting on, with
# a few instances of each to find them by.
BRIEF_MAX, BRIEF_EXAMPLES = 12, 6

# A rule name says nothing to someone reading the page without the primer open beside it, and nothing to an agent handed
# the brief. One line per kind: what it caught, and what to do instead.
WHY = {
    "opener": "A discourse marker opening a sentence. It announces a turn the "
              "sentence already makes. Delete it and start on the claim.",
    "puffery": "An adjective asserting quality instead of stating it. It survives "
               "the deletion test nowhere: cut it, or replace it with the measurement.",
    "filler-verb": "A verb reaching for weight it does not carry. Name the action: "
                   "'use', 'add', 'read', 'run'.",
    "metaphor-tic": "A figure the model reaches for by habit. Say what the thing is or does.",
    "byte-identical": "\"Byte-identical\" more than once. Say it once, or say what was compared.",
    "negation-antithesis": "A not-X-but-Y contrast. Apply the swap test - if the "
                           "reversal reads as well, the contrast carries nothing. "
                           "State the claim directly.",
    "americanism": "An American spelling. Australian English is the house style, so "
                   "use the -ise, -our, -re or doubled-l form. Words whose Australian "
                   "form turns on noun versus verb, and technical terms spelled -iz- "
                   "everywhere, are not flagged.",
    "blob": f"A text unit of {vs.BLOB_WORDS}+ words, in any shape. Long enough to "
            "bury the instruction inside it, so the agent acts on the prose it "
            "remembers. Split it into steps, or cut it.",
    "dense-run": f"{vs.DENSE_RUN}+ consecutive units of {vs.DENSE_WORDS}+ words, or "
                 f"{vs.DENSE_LIST_RUN}+ list items of {vs.DENSE_LIST_WORDS}+, not every one "
                 "of them a blob. A wall with nowhere to rest: split it, or cut the units "
                 "that restate one another.",
    "invisible": "A character that renders as nothing or as an ordinary space - a "
                 "no-break space, a zero-width space, a private-use glyph - usually "
                 "pasted in from a web page. It breaks a command or a trigger phrase "
                 "it sits in, and no editor shows it. Replace it with a plain space, "
                 "or delete it.",
    "code": f"A fenced block over {vs.CODE_FENCE_LINES} lines. Scripts belong in "
            "scripts/ and templates in assets/, where they cost nothing until run.",
    "bold-emphasis": "Bold dropped into running sentences. Emphasis works by being "
                     "rare, so when everything is bold nothing is, and the one "
                     "instruction the skill needed to land stops standing out. "
                     "Bold that opens a line is a label and is exempt: keep it for "
                     "a bullet lead, and let the sentence carry the rest.",
    "load": "Worst-case load is SKILL.md plus the largest reference - what one "
            "branch firing costs. Move branch-only content into references/, and "
            "delete lines the agent would obey anyway.",
    "spec-error": "A violation of the Agent Skills spec. The skill will not load "
                  "or will fail validation until it is fixed.",
    "spec-warning": "Valid, but flagged: usually an unrecognised frontmatter field "
                    "or a description over its word ceiling.",
}


class Finding(NamedTuple):
    """One entry in the findings list, in the form the page and the brief share.

    Both read this list rather than each walking the validator again, so the
    brief cannot disagree with the page it was copied from.
    """

    rule: str  # what fired; also the grouping key in the brief
    n: int  # how many, counted in `unit`
    unit: str  # what n counts, so the brief can say "3 text units"
    example: str  # the term itself, or where the block sits
    kind: str  # blob | code | filler, which cell shows it
    what: str  # middle column: the term, or the unit's opening words
    size: int  # the count as the page prints it: 412w, 14L, 3
    where: str = ""  # right column: path:line
    term: str = ""  # selection and search key, terms only
    goto: str = ""  # anchor id, for rows that scroll the document
    share: float = 0.0  # bar width 0..1, for a row measured against a threshold
                        # rather than against the other rows' counts

    @property
    def why(self):
        return why_for(self.rule)

    @property
    def possible(self):
        return self.rule in vs.POSSIBLE

    @property
    def conf(self):
        """The row's step on the ramp; bold has none, being a density rather than a defect at any span."""
        return "" if self.kind == "em" else confidence(self.rule)

CSS = """
:root {
  color-scheme: only light;
  --grotesk: "Helvetica Neue", Helvetica, Roboto, ui-sans-serif, system-ui, Arial, sans-serif;
  --mono: ui-monospace, "SF Mono", SFMono-Regular, Menlo, Consolas, monospace;
  --ground: #fff; --ink: #0d0d0d; --muted: #5f5f5f;
  --accent: #de301e; --fill: #de301e1f; --rule: 2px;
  /* the mark ramp by confidence: possible in pale yellow, probable in orange, certain in the accent red */
  --maybe: #fff4c2; --maybe-rule: #e6c200;
  --likely: #ffc978; --likely-rule: #e07a0c;
}
* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; -moz-text-size-adjust: 100%; text-size-adjust: 100%; }
body { margin: 0; background: var(--ground); color: var(--ink);
       font: 400 16px/1.5 var(--grotesk); -webkit-font-smoothing: antialiased;
       overflow: hidden; }
:focus-visible { outline: 3px solid var(--accent); outline-offset: 2px; }

/* The panel beside the skill, not above it: a term is clicked in the findings
   and read in the source, and a stacked board put the two an entire screen
   apart. Each column scrolls on its own so neither scrolls the other away. */
.board { display: grid; grid-template-columns: minmax(440px, 41%) 1fr;
         grid-template-rows: auto minmax(0, 1fr) auto;
         gap: var(--rule); padding: var(--rule); height: 100vh; }
.cell { border: var(--rule) solid var(--ink); padding: 14px 16px; min-width: 0; }
/* The panel does not scroll; the findings cell inside it takes the slack and
   scrolls, so each column shows exactly one scrollbar and the budget stays put. */
.panel { display: flex; flex-direction: column; gap: var(--rule);
         min-height: 0; overflow: hidden; }
.grow { flex: 1; min-height: 0; display: flex; flex-direction: column; }
.doc { min-height: 0; overflow: auto; }
header, footer { grid-column: 1 / -1; }
header { display: flex; align-items: center; justify-content: space-between; gap: 32px; }
header .stats { flex: 1; max-width: 680px; }

@media (max-width: 900px) {
  body { overflow: auto; }
  .board { grid-template-columns: 1fr; grid-template-rows: none; height: auto; }
  .panel, .doc, .scroll { overflow: visible; }
  .grow { flex: none; }
  header { display: block; }
  header .stats { max-width: none; margin-top: 16px; }
}

h1 { font: 700 27px/1.1 var(--grotesk); margin: 0; letter-spacing: -0.02em;
     text-transform: uppercase; }
h1 span { background: var(--accent); color: #fff; padding: 0 6px; }
h2 { font: 700 11px/1 var(--grotesk); letter-spacing: 0.14em; text-transform: uppercase;
     margin: 0 0 12px; color: var(--muted); }
h2.sub { margin: 20px 0 10px; padding-top: 14px; border-top: 1px solid #ececec; }

/* the stat strip: a coloured rule over each figure, small caps under it */
.stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 22px; }
.stats div i { display: block; height: 5px; margin-bottom: 10px; }
.stats div b { font: 700 25px/1 var(--grotesk); letter-spacing: -0.01em; }
.stats div u { display: block; text-decoration: none; margin-top: 5px;
               font: 400 10px var(--mono); letter-spacing: 0.1em; color: var(--muted); }

input { width: 100%; border: var(--rule) solid var(--ink); background: var(--ground);
        color: var(--ink); font: 400 12px var(--mono); padding: 7px 9px;
        margin-bottom: 10px; letter-spacing: 0.08em; }
input::placeholder { color: var(--muted); text-transform: uppercase; }
tr.gone { display: none; }

footer { display: flex; align-items: center; gap: 14px;
         font: 400 10px var(--mono); letter-spacing: 0.1em; color: var(--muted);
         padding: 7px 16px; border: var(--rule) solid var(--ink); text-transform: uppercase; }
footer .end { margin-left: auto; }

/* the rating, set at the size of the finding it is */
.band { font: 700 46px/1 var(--grotesk); letter-spacing: -0.02em; }
.band.ok, .band.poor { color: var(--accent); }
.rate { font: 400 13px var(--mono); color: var(--muted); margin-top: 6px; }
.note { font: 400 12px/1.5 var(--mono); color: var(--ink); margin-top: 10px;
        border-left: var(--rule) solid var(--accent); padding-left: 9px; }
.gauge { position: relative; height: 22px; border: var(--rule) solid var(--ink); margin-top: 14px; }
.gauge i { position: absolute; inset: 0 auto 0 0; background: var(--accent); }
.gauge b { position: absolute; top: -2px; bottom: -2px; width: var(--rule); background: var(--ink); }
.ticks { display: flex; justify-content: space-between;
         font: 400 11px var(--mono); color: var(--muted); margin-top: 4px; }

/* per-file bars: one grey ramp, the accent reserved for the file that leads */
.bar { display: grid; grid-template-columns: 190px 1fr 44px; align-items: center;
       gap: 8px; margin-bottom: 7px; font: 400 12px var(--mono); }
.bar u { text-decoration: none; color: var(--muted); overflow: hidden;
         text-overflow: ellipsis; white-space: nowrap; }
.bar s { text-decoration: none; height: 13px; background: #d4d4d4; display: block; }
/* The accent marks the file to cut. Set explicitly: as `:first-of-type` it
   matched the band div above these rows and never reached a bar at all. */
.bar.lead s { background: var(--accent); }
.bar em { font-style: normal; text-align: right; color: var(--muted); }

table { border-collapse: collapse; width: 100%; font: 400 13px var(--mono); }
td { padding: 3px 6px 3px 0; vertical-align: top; border-bottom: 1px solid #ececec; }
td.n { width: 46px; color: var(--muted); text-align: right; }
td.r { color: var(--muted); text-align: right; white-space: nowrap; }
tr.pick { cursor: pointer; }
tr.pick:hover td { background: var(--fill); }
.scroll { flex: 1; min-height: 90px; overflow: auto; }

/* the frequency chart, drawn behind the rows it labels rather than beside them */
td.f { width: 26%; }
td.f s { display: block; height: 11px; background: #d4d4d4; text-decoration: none; }
tr.pick:first-child td.f s { background: var(--accent); }

/* spec findings: errors carry the accent, warnings the grey ramp */
ul.spec { list-style: none; margin: 0; padding: 0;
          font: 400 12px/1.5 var(--mono); }
ul.spec li { padding: 5px 0 5px 9px; border-left: var(--rule) solid #d4d4d4;
             margin-bottom: 6px; }
ul.spec li.bad { border-left-color: var(--accent); }

/* before and after: two bars to a pair, the baseline hollow and the current filled */
.pair { margin-bottom: 12px; font: 400 12px var(--mono); }
.pair u { text-decoration: none; color: var(--muted); }
.pair div { display: grid; grid-template-columns: 1fr 96px; align-items: center;
            gap: 8px; margin-top: 4px; }
.pair s { text-decoration: none; height: 13px; display: block; min-width: 1px; }
.pair .was s { background: transparent; border: var(--rule) solid #9a9a9a; }
.pair .now s { background: var(--accent); }
.pair em { font-style: normal; color: var(--muted); }
.cut { color: var(--accent); }

/* The caption under the list: the reason for whatever is hovered or chosen. */
.why { font: 400 12px/1.45 var(--mono); margin: 12px 0 0;
       border-top: 1px solid #ececec; padding-top: 10px; min-height: 3.2em; }
.why.idle { color: var(--muted); }

/* Sized to sit on the footer rule beside the date, not to stand over it. */
button { font: 400 10px/1 var(--mono); letter-spacing: 0.1em; text-transform: uppercase;
         border: 1px solid var(--ink); background: var(--ground);
         color: var(--ink); padding: 4px 9px; cursor: pointer; white-space: nowrap; }
button:hover { background: var(--accent); border-color: var(--accent); color: #fff; }
button.done { background: var(--ink); border-color: var(--ink); color: var(--ground); }
/* The brief, kept hidden as the copy source and revealed only if the clipboard
   refuses, so there is still something to select by hand. */
#brief { margin: var(--rule); padding: 14px 16px; border: var(--rule) solid var(--ink); }
body.spill { overflow: auto; }

.legend { display: flex; gap: 16px; font: 400 11px var(--mono);
          color: var(--muted); margin-top: 12px; flex-wrap: wrap; }
.key { display: inline-block; width: 22px; height: 11px; margin-right: 5px;
       vertical-align: -1px; }
/* The key swatches match the marks; the underline is the same rule in each step's colour and carries no meaning
   of its own. A dotted rule on plain ground could not be seen at reading distance. */
.k-possible { background: var(--maybe); box-shadow: inset 0 -3px 0 var(--maybe-rule); }
.k-probable { background: var(--likely); box-shadow: inset 0 -3px 0 var(--likely-rule); }
.k-certain { background: var(--fill); box-shadow: inset 0 -3px 0 var(--accent); }
.k-code { background: #f4f4f4; box-shadow: inset 0 -3px 0 #9a9a9a; }
.k-em { background: #e9eff9; box-shadow: inset 0 -3px 0 #1a4fa0; }
.legend b { font-weight: 700; color: var(--ink); letter-spacing: 0.1em; text-transform: uppercase; }

/* the source, one block per line so a flagged unit shades over its whole span */
/* The heading scrolls with its file. Pinned, it detached from the text it names
   and read as a stray bar over the document. */
h3.file { font: 700 11px/1 var(--mono); letter-spacing: 0.1em; text-transform: uppercase;
          margin: 22px 0 8px; padding: 7px 0; color: var(--ink);
          border-bottom: var(--rule) solid var(--ink); background: var(--ground); }
h3.file:first-of-type { margin-top: 0; }
pre { margin: 0; font: 400 13px/1.65 var(--mono); white-space: pre-wrap;
      word-wrap: break-word; }
.l { display: block; padding: 0 6px; border-left: var(--rule) solid transparent; }
.l:empty { height: 1.65em; }
/* Block shades sit on the same ramp as the marks, a shade lighter so the text inside stays readable: a dense run
   is possible (yellow), a blob probable (orange). A run often contains a blob, which keeps its deeper shade inside
   it. Code is not on the ramp - a long fence is a placement finding, not a prose one. */
.l.dense { background: #fffbe6; border-left-color: var(--maybe-rule); }
.l.blob { background: #ffe4bd; border-left-color: var(--likely-rule); }
.l.code { background: #f4f4f4; border-left-color: #9a9a9a; }
tr.pick.dense td.n { color: var(--maybe-rule); }
tr.pick.blob td.n { color: var(--likely-rule); }
mark { color: inherit; padding: 0 1px; cursor: pointer; }
mark[data-conf="possible"] { background: var(--maybe); box-shadow: inset 0 -3px 0 var(--maybe-rule); }
mark[data-conf="probable"] { background: var(--likely); box-shadow: inset 0 -3px 0 var(--likely-rule); }
mark[data-conf="certain"] { background: var(--fill); box-shadow: inset 0 -3px 0 var(--accent); }
/* An invisible character is shown as its code point, or the mark would be as invisible as the character. */
mark.inv { font: 400 10px var(--mono); letter-spacing: 0.06em; padding: 0 3px; vertical-align: 1px; }
tr.pick.possible td.n::before { content: "?"; color: var(--muted); margin-right: 3px; }
/* Mid-sentence bold is a density, not a defect at the span, so it takes the blue
   of the file count rather than competing with the severity ramp. */
mark.em { background: #e9eff9; box-shadow: inset 0 -3px 0 #1a4fa0; }
tr.pick.em td.n { color: #1a4fa0; }
/* a chosen term holds; everything else recedes rather than disappears */
body.sel mark { background: transparent; box-shadow: none; color: #a8a8a8; }
body.sel mark.on { background: var(--accent); color: #fff; box-shadow: none; }
body.sel tr.pick { opacity: 0.35; }
body.sel tr.pick.on { opacity: 1; }
body.sel tr.pick.on td { background: var(--fill); }
.empty { color: var(--muted); font: 400 13px var(--mono); }
"""

JS = """
var body = document.body, sel = null;
var why = document.getElementById('why'), idle = why.textContent, pinned = '';
why.classList.add('idle');
function say(text) {
  why.textContent = text || pinned || idle;
  why.classList.toggle('idle', !(text || pinned));
}
document.addEventListener('mouseover', function (e) {
  var el = e.target.closest('[data-why]');
  if (el) say(el.dataset.why);
});
document.addEventListener('mouseout', function (e) {
  if (e.target.closest('[data-why]')) say('');
});
function choose(term) {
  sel = (sel === term) ? null : term;
  body.classList.toggle('sel', sel !== null);
  // A mark carries every term that matched its span, so membership, not equality
  document.querySelectorAll('[data-term]').forEach(function (el) {
    el.classList.toggle('on', sel !== null && el.dataset.term.split('|').indexOf(sel) !== -1);
  });
  if (sel) {
    var first = document.querySelector('mark.on');
    if (first) first.scrollIntoView({block: 'center', behavior: 'smooth'});
  }
}
document.addEventListener('click', function (e) {
  var go = e.target.closest('[data-goto]');
  if (go) {
    pinned = go.dataset.why || '';
    say('');
    var line = document.getElementById(go.dataset.goto);
    if (line) line.scrollIntoView({block: 'center', behavior: 'smooth'});
    return;
  }
  var el = e.target.closest('[data-term]');
  // A shared mark's key holds every term that matched it; select by the first,
  // or the joined key would match nothing.
  if (el) { pinned = el.dataset.why || ''; say(''); choose(el.dataset.term.split('|')[0]); }
  else if (sel) { pinned = ''; say(''); choose(sel); }
});
document.addEventListener('keydown', function (e) {
  if (e.key === 'Escape' && sel) { pinned = ''; say(''); choose(sel); }
  else if (e.key === '/' && document.activeElement !== box) { e.preventDefault(); box.focus(); }
});
var box = document.getElementById('find');
box.addEventListener('input', function () {
  var q = box.value.trim().toLowerCase();
  // Structure rows are pickable but carry no term, so the key may be absent
  document.querySelectorAll('tr.pick').forEach(function (tr) {
    var key = tr.dataset.term || '';
    tr.classList.toggle('gone', q !== '' && key.indexOf(q) === -1);
  });
});
box.addEventListener('click', function (e) { e.stopPropagation(); });

var copy = document.getElementById('copy'), stash = document.getElementById('brief');
function flashed(ok) {
  if (!ok) { stash.hidden = false; body.classList.add('spill'); stash.scrollIntoView(); }
  copy.textContent = ok ? 'Copied' : 'Copy failed, brief below';
  copy.classList.add('done');
  setTimeout(function () {
    copy.textContent = 'Copy brief';
    copy.classList.remove('done');
  }, 1800);
}
/* file:// is not a secure context in every browser, so the clipboard API is not
   always there to call. */
function bySelection() {
  var ta = document.createElement('textarea'), ok = false;
  ta.value = stash.textContent;
  ta.style.cssText = 'position:fixed;top:0;left:0;opacity:0';
  document.body.appendChild(ta);
  ta.select();
  try { ok = document.execCommand('copy'); } catch (err) { ok = false; }
  document.body.removeChild(ta);
  flashed(ok);
}
copy.addEventListener('click', function (e) {
  e.stopPropagation();
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(stash.textContent).then(function () { flashed(true); },
                                                          bySelection);
  } else bySelection();
});
"""


def e(s):
    return html.escape(str(s), quote=True)


def term_key(hit):
    """The term a finding is grouped under. Matches validate_skill's own grouping
    so the ranked list and the marks in the source agree on what is one term."""
    return " ".join(str(hit).split()[:8]).lower()


def anchor(index, lineno):
    """DOM id for one source line, keyed by the file's position in the load order.

    Keyed by position rather than by path so two paths differing only in
    punctuation cannot collide on one id and send a jump to the wrong file.
    """
    return "L-%d-%d" % (index, lineno)


def loadable_files(skill_dir):
    """[(relative path, path)] over the Markdown that actually loads, in load order.

    The single source of the relative path every other function keys on.
    """
    root = Path(skill_dir).resolve()
    return [(str(p.relative_to(root) if p.is_relative_to(root) else p), p)
            for p in vs.referenced_md_files(skill_dir)]


def per_file_tokens(skill_dir, use_tiktoken=False):
    """{relative path: tokens} over the Markdown that actually loads, largest first."""
    count = vs.tiktoken_tokens if use_tiktoken else vs.estimate_tokens
    sized = {rel: count(path.read_text(encoding="utf-8-sig", errors="ignore"))
             for rel, path in loadable_files(skill_dir)}
    return dict(sorted(sized.items(), key=lambda kv: (-kv[1], kv[0])))


def worst_case_load(sized):
    """SKILL.md plus the largest reference - the figure the rating gate judges."""
    main = sized.get("SKILL.md", 0)
    refs = [n for name, n in sized.items() if name != "SKILL.md"]
    return main + (max(refs) if refs else 0)


def spec_findings(skill_dir):
    """(errors, warnings) from the spec checks, or the name of the missing dependency.

    Caught rather than predicted, because an import probe cannot see either
    failure: lint() exits the process when skills-ref is absent, and raises a
    plain ImportError when it is present but partial. Both would otherwise lose
    the whole page over one cell.

    The description-length rule is the primer's own, not the spec's, and needs
    only PyYAML - so it still runs when skills-ref is missing. Routing it solely
    through lint() meant a 119-word description reported nothing at all on a
    machine without an optional third-party install, which is the one finding on
    this page that costs every agent context on every turn.
    """
    if vs.yaml is None:
        return "PyYAML"
    try:
        # lint() prints its own install hint on the way out; the CLI's stdout is the report path alone, so the hint is
        # swallowed and restated in the cell.
        with contextlib.redirect_stdout(io.StringIO()):
            return vs.lint(Path(skill_dir))
    except (SystemExit, ImportError):
        errors, warnings = vs.description_findings(vs.skill_description(skill_dir))
        warnings.append("Spec checks skipped: skills-ref is not installed, so only the primer's own "
                        "description rule ran. Re-run under uv run for the rest.")
        return errors, warnings


def gauge(load):
    """Position on the rating scale, topped out past the Poor floor."""
    pct = min(100.0, 100.0 * load / GAUGE_CEILING)
    marks = "".join('<b style="left:%.1f%%"></b>' % (100.0 * ceiling / GAUGE_CEILING)
                    for ceiling, _ in vs._TOKEN_RATINGS)
    ticks = "".join("<span>%s</span>" % e("%s %d" % (label.lower(), ceiling))
                    for ceiling, label in vs._TOKEN_RATINGS)
    return ('<div class="gauge"><i style="width:%.1f%%"></i>%s</div>'
            '<div class="ticks"><span>0</span>%s<span>%d</span></div>'
            % (pct, marks, ticks, GAUGE_CEILING))


def verdict(load, sized, advice, ceiling, within_budget):
    rating = vs.token_rating(load)
    main = sized.get("SKILL.md", 0)
    # Ties break on iteration order, matching how _budget picks its driver file, so the page and the text report never
    # name different references.
    refs = [(name, n) for name, n in sized.items() if name != "SKILL.md"]
    biggest = max(refs, key=lambda kv: kv[1], default=("", 0))
    detail = ("SKILL.md %d + largest reference %s %d" % (main, biggest[0], biggest[1])
              if biggest[0] else "SKILL.md %d, no referenced files" % main)
    # A skill inside a justified ceiling passes the validator's gate, so the band is set in the passing treatment rather
    # than contradicting its own note.
    tone = "good" if within_budget else rating.lower()
    out = ['<div class="band %s">%s</div>' % (tone, e(rating.upper())),
           '<div class="rate">%s tokens worst-case load: %s</div>' % (load, e(detail)),
           gauge(load)]
    if within_budget:
        out.append('<div class="note">Within the declared max-load-tokens %d.</div>' % ceiling)
    elif advice:
        out.append('<div class="note">%s</div>' % e(advice))
    return "".join(out)


def files_block(sized):
    """Bars under the rating: what each loadable file costs."""
    if not sized:
        return ""
    top = max(sized.values()) or 1
    rows = "".join('<div class="bar%s"><u>%s</u><s style="width:%.1f%%"></s><em>%d</em></div>'
                   % (" lead" if i == 0 else "", e(name), 100.0 * n / top, n)
                   for i, (name, n) in enumerate(sized.items()))
    return '<h2 class="sub">Tokens by file</h2>%s' % rows


def spec_block(findings):
    if isinstance(findings, str):
        return ('<p class="empty">Spec checks skipped: %s is not installed. '
                'Re-run the report with <code>uv run</code> to fill this in.</p>' % e(findings))
    errors, warnings = findings
    if not errors and not warnings:
        return '<p class="empty">No spec errors or warnings.</p>'
    items = ['<li class="bad">%s</li>' % e(x) for x in errors]
    items += ["<li>%s</li>" % e(x) for x in warnings]
    return '<ul class="spec">%s</ul>' % "".join(items)


def structure_block(pct, found):
    """Findings addressed by line span rather than by term: blobs and code fences.

    Both live here because neither is a term to rank in the frequency list, and
    each row carries the anchor of the line it starts on so it can be jumped to.
    """
    rows = "".join(
        '<tr class="pick %s%s" data-goto="%s" data-why="%s" title="%s">'
        '<td class="n">%d%s</td><td>%s</td><td class="r">%s</td></tr>'
        % (f.kind, " possible" if f.possible else "", f.goto, e(f.why), e(f.why), f.size,
           "L" if f.kind == "code" else "w", e(f.what), e(f.where))
        for f in found if f.kind in ("blob", "code", "dense"))
    head = '<div class="rate">%s of body words in paragraph prose</div>' % (
        "%d%%" % pct if pct is not None else "no body text")
    if not rows:
        return head + ('<p class="empty">No text unit at or over %d words, no dense run, no code '
                       'block over %d lines.</p>' % (vs.BLOB_WORDS, vs.CODE_FENCE_LINES))
    return head + '<h2 class="sub">Units to compress</h2><table>%s</table>' % rows


def tally(filler):
    """{term: (category, count)}, one entry per term rather than per hit."""
    terms = {}
    for category, _rel, _line, hit in filler:
        key = term_key(hit)
        seen, count = terms.get(key, (category, 0))
        terms[key] = (seen, count + 1)
    return terms


def collect(blobs, long_code, filler, index_of, emphasis=None, dense=()):
    """Every finding as one ranked list: blocks first, then terms by frequency.

    The two panel cells filter this list and the brief groups it, so a finding
    can never appear on the page in a form the copied text disagrees with.

    Terms rank by confidence before count: a certain finding leads however
    rare, and a possible one sits below every probable one however common,
    since a page of "?" rows above the defects would bury them.

    Bold is one row however many spans it covers: it is a rate, and a hundred
    distinct bolded phrases would be a hundred rows in a list meant to name
    habits. It heads the frequency table for the same reason - it is the one
    finding there that describes the whole document rather than a word in it.
    """
    found = []
    if emphasis:
        found.append(Finding(
            rule="bold-emphasis", n=emphasis["total"], unit="span",
            # The band leads the example so the brief carries it too, rather than the page and the copied text
            # disagreeing about how bad it is.
            example="%s %.1f/1000 words; %s"
                    % (emphasis["band"], emphasis["rate"],
                       ", ".join(w for w, _ in emphasis["worst"][:3])),
            kind="em",
            what="%s: %.1f mid-sentence bolds per 1000 words (sloppy over %.0f, "
                 "abused at %.0f)" % (emphasis["band"], emphasis["rate"],
                                      vs.BOLD_RATE, vs.BOLD_ABUSED),
            size=emphasis["total"], term="bold-emphasis",
            where="%s:%d" % emphasis["where"][0],
            share=min(1.0, emphasis["rate"] / vs.BOLD_ABUSED),
        ))
    for kind, group, unit in (("blob", blobs, "text unit"), ("code", long_code, "code block")):
        for size, rel, start, _end, opening in group:
            found.append(Finding(
                rule=kind, n=1, unit=unit, example=f"{rel}:{start}", kind=kind,
                what=" ".join(opening.split()[:9]), size=size, where=f"{rel}:{start}",
                goto=anchor(index_of.get(str(rel), 0), start),
            ))
    for size, rel, start, _end, opening, count, longest, listed in dense:
        found.append(Finding(
            rule="dense-run", n=1, unit="run", example=f"{rel}:{start}", kind="dense",
            what="%d %s, longest %dw: %s" % (count, "list items" if listed else "units", longest,
                                             " ".join(opening.split()[:6])),
            size=size, where=f"{rel}:{start}", goto=anchor(index_of.get(str(rel), 0), start),
        ))
    where = {}
    for _category, rel, line, hit in filler:
        where.setdefault(term_key(hit), f"{rel}:{line}")
    ranked = sorted(tally(filler).items(),
                    key=lambda kv: (RANK[confidence(kv[1][0])], -kv[1][1], kv[0]))
    for term, (category, count) in ranked:
        found.append(Finding(
            rule=category, n=count, unit="use", example=term, kind="filler",
            what=term, size=count, where=where.get(term, ""), term=term,
        ))
    return found


def findings_block(found):
    """Ranked frequency, one row per term: a word is cut everywhere at once.

    The bar is drawn in the row it labels rather than as a chart beside it. Two
    views of the same counts would be the duplication the primer objects to.
    """
    terms = [f for f in found if f.kind == "filler"]
    emphasis = [f for f in found if f.kind == "em"]
    if not terms and not emphasis:
        return ('<input id="find" hidden><p id="why" class="why" hidden></p>'
                '<p class="empty">No lexical no-ops, American spellings, bold abuse or invisible '
                'characters found.</p>')
    # The bold row's bar reads against the abuse threshold, not against the term counts: a rate of 6 and a word used 6
    # times are not the same measurement, and sharing one scale would let the larger number silently set the other's.
    rows = "".join('<tr class="pick em" data-term="%s" data-why="%s" title="%s">'
                   '<td class="n">%d</td>'
                   '<td class="f"><s style="width:%.1f%%"></s></td>'
                   '<td>%s</td><td class="r">%s</td></tr>'
                   % (e(f.term), e(f.why), e(f.why), f.size,
                      100.0 * f.share, e(f.what), e(f.rule))
                   for f in emphasis)
    top = max((f.size for f in terms), default=1)
    rows += "".join('<tr class="pick %s" data-term="%s" data-why="%s" title="%s">'
                    '<td class="n">%d</td>'
                    '<td class="f"><s style="width:%.1f%%"></s></td>'
                    '<td>%s</td><td class="r">%s</td></tr>'
                    % (f.conf, e(f.term), e(f.why), e(f.why), f.size,
                       100.0 * f.size / top, e(f.what), e(f.rule))
                    for f in terms)
    legend = "<b>Confidence</b>" + "".join(
        '<span><i class="key k-%s"></i>%s, %s</span>' % (k, k, e(d)) for k, d in LEGEND)
    legend += "".join('<span><i class="key k-%s"></i>%s</span>' % (k, e(d)) for k, d in KINDS)
    # The caption holds the reason for whatever is hovered or chosen, so why a thing is flagged does not depend on
    # finding a tooltip.
    return ('<input id="find" placeholder="Search for a term..." autocomplete="off">'
            '<div class="scroll"><table>%s</table></div>'
            '<p id="why" class="why">Hover or click a finding for what it is and why.</p>'
            '<div class="legend">%s</div>'
            % (rows, legend))


def brief(skill_dir, load, sized, ceiling, within_budget, spec, found):
    """The findings as text, sized to paste into another agent.

    Grouped by rule and carrying each rule's reason. A list of bare rule names
    leaves the receiving agent guessing, and one rule is one habit to drop
    however many times it fired.

    Lines are separated by a blank one, never wrapped: the brief is pasted into
    something that may render it as markdown, where a wrap reflows anyway.
    """
    rating = vs.token_rating(load)
    out = ["Skill report for %s. Load the skill-creator-primer skill, then fix the "
           "following. Cut words, not behaviour: every instruction the skill carries "
           "has to survive." % os.path.basename(str(skill_dir)), ""]

    budget = ("Budget: %s. Worst-case load %d tokens (SKILL.md plus the largest "
              "reference) across %d file(s) that load."
              % (rating, load, len(sized)))
    if within_budget:
        budget += " Within the declared max-load-tokens %d." % ceiling
    elif rating in ("OK", "Poor"):
        budget += " " + WHY["load"]
    out += [budget, ""]

    if isinstance(spec, tuple):
        errors, warnings = spec
        if errors or warnings:
            out.append("Spec: %d error(s), %d warning(s)." % (len(errors), len(warnings)))
            out += ["- %s" % x for x in list(errors) + list(warnings)]
        else:
            out.append("Spec: clean.")
    else:
        out.append("Spec: not checked, %s was not installed." % spec)
    out.append("")

    groups = {}
    for f in found:
        n, unit, seen, why = groups.get(f.rule, (0, f.unit, [], f.why))
        if f.example not in seen and len(seen) < BRIEF_EXAMPLES:
            seen.append(f.example)
        groups[f.rule] = (n + f.n, unit, seen, why)

    if not groups:
        out.append("Nothing else flagged.")
        return "\n".join(out)

    # Two lists, so the receiving agent fixes one and reads the other. The caveat travels in each possible rule's
    # reason, since that agent has the file but not the page.
    shown = list(groups.items())[:BRIEF_MAX]
    for maybe, head in ((False, "Findings, fix these:"), (True, "Possible, read before changing:")):
        picked = [(rule, g) for rule, g in shown if (rule in vs.POSSIBLE) == maybe]
        if not picked:
            continue
        out.append(head)
        for rule, (n, unit, seen, why) in picked:
            out.append("- %s, %d %s (%s): %s"
                       % (rule, n, unit if n == 1 else unit + "s", ", ".join(seen), why))
    if len(groups) > BRIEF_MAX:
        out.append("- and %d further kinds, listed in the report."
                   % (len(groups) - BRIEF_MAX))
    return "\n".join(out)


def _pair(label, was, now, unit=""):
    scale = max(was, now) or 1
    delta = ""
    if was:
        pct = (now - was) / was * 100
        delta = ' <span class="%s">%+.0f%%</span>' % ("cut" if now < was else "", pct)
    return ('<div class="pair"><u>%s</u>'
            '<div class="was"><s style="width:%.1f%%"></s><em>%d%s before</em></div>'
            '<div class="now"><s style="width:%.1f%%"></s><em>%d%s after%s</em></div></div>'
            % (e(label), 100.0 * was / scale, was, unit,
               100.0 * now / scale, now, unit, delta))


def compare_block(baseline, skill_dir, use_tiktoken=False):
    """Before and after against another copy of the skill: a worktree, or a
    pre-compression snapshot. Same measurements, both sides."""
    def measure(target):
        sized = per_file_tokens(target, use_tiktoken)
        _pct, skill_blobs, ref_blobs, long_code, dense = vs._structure(Path(target))
        return {
            "load": worst_case_load(sized),
            "skill": sized.get("SKILL.md", 0),
            "blobs": len(skill_blobs) + len(ref_blobs),
            "dense": len(dense),
            "code": len(long_code),
            "filler": len(vs._filler(Path(target))),
        }

    was, now = measure(baseline), measure(skill_dir)
    out = [_pair("worst-case load", was["load"], now["load"]),
           _pair("SKILL.md tokens", was["skill"], now["skill"])]
    for key, label in (("blobs", "blobs"), ("dense", "dense runs"), ("code", "long code blocks"),
                       ("filler", "lexical no-ops")):
        if was[key] or now[key]:
            out.append(_pair(label, was[key], now[key]))
    return "".join(out)


BLOCK_RULE = {"blob": "blob", "code": "code", "dense": "dense-run"}


def marked_source(skill_dir, blobs, long_code, filler, emphasis=None, dense=(), invisible=()):
    """Every loadable file, one block per line, flagged spans marked in place."""
    spans = {}
    # Blobs are placed before dense runs, so a blob inside a run keeps its own deeper shade.
    for kind, group in (("blob", blobs), ("code", long_code), ("dense", dense)):
        for _size, rel, start, end, _opening, *_ in group:
            for n in range(start, end + 1):
                spans.setdefault((str(rel), n), kind)
    # Only lines the detector reported are re-scanned for spans, so the page can never mark a line the text report left
    # out.
    flagged = {(str(rel), lineno) for _category, rel, lineno, _hit in filler}
    # Bold spans arrive already placed, from the scan that counted them: the page marks the ones the rate is made of,
    # not every bold it can find, so the exempt bullet leads stay unmarked.
    bold = {}
    for rel, lineno, start, end, _phrase in (emphasis or {}).get("spans", ()):
        bold.setdefault((rel, lineno), []).append(
            (start, end, "bold-emphasis", "bold-emphasis"))
        flagged.add((rel, lineno))
    for rel, lineno, start, end, name in invisible:
        bold.setdefault((rel, lineno), []).append((start, end, name, "invisible"))
        flagged.add((rel, lineno))

    out = []
    for index, (rel, path) in enumerate(loadable_files(skill_dir)):
        out.append('<h3 class="file">%s</h3><pre>' % e(rel))
        text = path.read_text(encoding="utf-8-sig", errors="ignore")
        for lineno, line in enumerate(text.splitlines(), start=1):
            marked = (mark_line(line, bold.get((rel, lineno), ()))
                      if (rel, lineno) in flagged else e(line))
            kind = spans.get((rel, lineno), "")
            # A shaded line carries its reason, so hovering the block answers what is wrong with it as a mark does.
            why = ' data-why="%s"' % e(WHY[BLOCK_RULE[kind]]) if kind else ""
            out.append('<span class="l %s" id="%s"%s>%s</span>'
                       % (kind, anchor(index, lineno), why, marked))
        out.append("</pre>")
    return "".join(out)


def filler_spans(line):
    """(start, end, term, rule) for every lexical no-op on one raw source line.

    Runs the detector's own rules over the text the detector scanned, via its
    _filler_scan, then maps each match back onto the raw line. Marking by offset
    rather than by searching for the matched text is what keeps the page from
    flagging an occurrence the detector excluded: a word inside backticks, or a
    sentence-initial rule matching mid-sentence.
    """
    lead = len(line) - len(line.lstrip())
    scan = vs._filler_scan(line)
    found = []
    for category, pattern in vs._ALL_TEXT_RULES:
        for hit in pattern.finditer(scan):
            raw = hit.group(0)
            at = lead + hit.start()
            found.append((at + len(raw) - len(raw.lstrip()), at + len(raw.rstrip()),
                          raw.strip(), category))
    return sorted(found)


def mark_line(line, extra=()):
    """Escape one source line, wrapping each span the detector flagged on it.

    `extra` carries spans placed elsewhere - bold, scanned across the whole skill
    - in the same (start, end, term, rule) shape, so one pass marks both layers
    rather than two passes fighting over the same offsets.

    Two rules matching overlapping text share one mark, which carries both terms
    so either row in the frequency table still has something to highlight. A row
    with no mark to reach would fade the whole document and select nothing. A
    bold wrapping a flagged word is exactly that case: one mark, both keys.

    Each mark also carries its rule's reason, so clicking a word in the document
    answers what is wrong with it without a trip back to the list.
    """
    spans = sorted(list(filler_spans(line)) + list(extra))
    if not spans:
        return e(line)
    kept = []
    for start, end, term, rule in spans:
        if kept and start < kept[-1][1]:
            # The mark covers both, or a bold opening first would cut a longer no-op off at its closing asterisks.
            kept[-1][1] = max(kept[-1][1], end)
            kept[-1][2].append(term)
            kept[-1][3].append(rule)
        else:
            kept.append([start, end, [term], [rule]])
    out, at = [], 0
    for start, end, terms, rules in kept:
        why = " ".join(dict.fromkeys(why_for(r) for r in rules)).strip()
        # Only a mark that is bold and nothing else takes the bold styling: where a no-op sits inside one, the narrower
        # finding is the one to fix. A shared mark takes the higher confidence of its rules.
        if all(r == "bold-emphasis" for r in rules):
            cls, conf = "em", ""
        else:
            conf = min((confidence(r) for r in rules if r != "bold-emphasis"), key=RANK.get)
            cls = "inv" if all(r == "invisible" for r in rules) else ""
        # Each invisible character shows as its code point and every other character as itself, so a no-break space
        # inside a bold phrase does not turn the whole phrase into hex. A leading BOM is an empty span; its term
        # carries the code point to show.
        shown = "".join("U+%04X" % ord(c) if vs._INVISIBLE.match(c) else e(c) for c in line[start:end])
        if start == end:
            shown = e(terms[0].split()[0])
        out.append(e(line[at:start]))
        out.append('<mark class="%s" data-conf="%s" data-term="%s" data-why="%s" title="%s">%s</mark>'
                   % (cls, conf, e("|".join(term_key(t) for t in terms)), e(why), e(why), shown))
        at = end
    out.append(e(line[at:]))
    return "".join(out)


def render(skill_dir, against=None, use_tiktoken=False):
    skill_dir = Path(skill_dir).resolve()
    sized = per_file_tokens(skill_dir, use_tiktoken)
    load = worst_case_load(sized)
    pct, skill_blobs, ref_blobs, long_code, dense = vs._structure(skill_dir)
    blobs = sorted(skill_blobs + ref_blobs, reverse=True)
    filler = vs._filler(skill_dir)
    emphasis = vs._bold(skill_dir)
    invisible = vs._invisible(skill_dir)
    # Invisible characters join the term list in the filler's shape, so they tally, rank and brief like any term;
    # their marks are placed from the spans, as bold's are.
    hits = filler + [("invisible", rel, lineno, name) for rel, lineno, _s, _e, name in invisible]
    index_of = {rel: i for i, (rel, _path) in enumerate(loadable_files(skill_dir))}
    _lines, _rating, advice, _driver, within_budget = vs._budget(skill_dir, use_tiktoken)
    ceiling, _justified = vs.declared_token_budget(
        (skill_dir / "SKILL.md").read_text(encoding="utf-8-sig", errors="ignore"))
    spec = spec_findings(skill_dir)
    found = collect(blobs, long_code, hits, index_of, emphasis, dense)

    extra = ""
    if against is not None:
        extra = ('<section class="cell"><h2>Before and after</h2>%s</section>'
                 % compare_block(against, skill_dir, use_tiktoken))

    # Possible findings are counted apart, as the text report prints them: a page of reads is not a page of defects.
    maybe = sum(f.n for f in found if f.possible)
    total = (len(blobs) + len(long_code) + len(hits) + len(dense)
             + len((emphasis or {}).get("spans", ())) - maybe)
    strip = "".join(
        '<div><i style="background:%s"></i><b>%s</b><u>%s</u></div>' % (colour, e(n), e(label))
        for colour, n, label in (
            ("#de301e", "%d" % load, "worst-case load"),
            ("#1a4fa0", "%d" % len(sized), "files that load"),
            ("#e8b400", "%d" % total, "findings" + (", %d possible" % maybe if maybe else "")),
        ))

    return """<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>skill report: %(name)s</title>
<style>%(css)s</style>
<div class="board">
  <header class="cell">
    <h1>Skill report: <span>%(name)s</span></h1>
    <div class="stats">%(strip)s</div>
  </header>
  <div class="panel">
    <section class="cell"><h2>Token budget</h2>%(verdict)s%(files)s</section>
    %(extra)s
    <section class="cell"><h2>Spec</h2>%(spec)s</section>
    <section class="cell"><h2>Structure</h2>%(structure)s</section>
    <section class="cell grow"><h2>Wording and emphasis</h2>%(findings)s</section>
  </div>
  <section class="cell doc"><h2>The skill</h2>%(source)s</section>
  <footer><span>generated %(when)s</span>
    <button id="copy" data-why="Copies these findings as text, each with its reason, to paste into a coding agent.">Copy brief</button>
    <span class="end">skill-creator-primer</span></footer>
</div>
<pre id="brief" hidden>%(brief)s</pre>
<script>%(js)s</script>
""" % {
        "name": e(skill_dir.name),
        "css": CSS, "js": JS,
        "strip": strip,
        "when": datetime.datetime.now().astimezone().date().isoformat(),
        "verdict": verdict(load, sized, advice, ceiling, within_budget),
        "files": files_block(sized),
        "spec": spec_block(spec),
        "structure": structure_block(pct, found),
        "findings": findings_block(found),
        "extra": extra,
        "source": marked_source(skill_dir, blobs, long_code, filler, emphasis, dense, invisible),
        "brief": e(brief(skill_dir, load, sized, ceiling, within_budget, spec, found)),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("skill_directory")
    ap.add_argument("--against", metavar="OTHER_DIR",
                    help="another copy of the skill (a worktree, or a pre-compression "
                         "snapshot) to compare against")
    ap.add_argument("--tiktoken", action="store_true",
                    help="count tokens with tiktoken instead of the chars/N heuristic "
                         "(run via `uv run --with tiktoken`)")
    ap.add_argument("-o", "--out", help="output path (default: a temp directory)")
    args = ap.parse_args()

    skill_dir = Path(args.skill_directory)
    if not (skill_dir / "SKILL.md").is_file():
        ap.error(f"no SKILL.md in {skill_dir}")
    if args.against and not (Path(args.against) / "SKILL.md").is_file():
        ap.error(f"no SKILL.md in {args.against}")
    if args.tiktoken:
        vs._tiktoken_encoding()

    name = f"{skill_dir.resolve().name}.skill-report.html"
    out = Path(args.out) if args.out else Path(tempfile.gettempdir()) / name
    if out.is_dir():
        out = out / name  # -o took a directory: name the file rather than refusing
    page = render(skill_dir, args.against, args.tiktoken)
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page, encoding="utf-8")
    except OSError as err:
        # One line, naming the fix: the default output sits in the temp directory, but -o often points somewhere
        # read-only, and a traceback says nothing about which path or what to do.
        print("cannot write %s: %s. Pass -o to choose another path." % (out, err.strerror), file=sys.stderr)
        sys.exit(2)
    print(out.resolve())


if __name__ == "__main__":
    main()
