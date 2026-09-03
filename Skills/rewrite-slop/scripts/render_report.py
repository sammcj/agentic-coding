#!/usr/bin/env python3
"""Render one input's check_output findings as a single self-contained HTML page.

Optional. Nothing in the rewrite phases calls this; it exists for reading a long input, or for showing someone else what
was flagged and where.

The board is the one at louisabraham.github.io/load-bearing, borrowed for its interaction rather than its content: that
page charts a corpus over twenty months, which a single document has no axis for. What carries over is clicking a term
to hold it selected while everything else responds, and light-only Bauhaus because a dark ground would invert the
premise.

    python3 render_report.py FILE [FILE ...] [--against ORIG] [-o OUT]
"""

import argparse
import datetime
import html
import os
import sys
from typing import NamedTuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import check_output as co
import syntax

# How sure the checker is, per rule. SAFE and REVIEW are mechanical (a smart quote is a smart quote), REPORT is a
# pattern the reader confirms, and POSSIBLE carries a caveat whatever list the rule came from. The sentence-shape rules
# from syntax.py are only in POSSIBLE.
CONFIDENCE: dict[str, str] = {}
for _rules, _how in ((co.SAFE, "certain"), (co.REVIEW, "certain"), (co.REPORT, "probable")):
    for _rule in _rules:
        CONFIDENCE.setdefault(_rule[0], _how)
for _name in co.POSSIBLE:
    CONFIDENCE[_name] = "possible"

# The key under the findings, pale to red. The page is read away from the rubric.
LEGEND = [
    ("possible", "maybe"),
    ("probable", "likely"),
    ("certain", "slopperific"),
]

# The copied brief is read by an agent with a context budget, so it stays about a page: the kinds worth acting on, with
# a few instances of each to find them by.
BRIEF_MAX, BRIEF_EXAMPLES = 12, 6

# Line-level rule names say nothing to someone reading the page without the rubric open beside it.
EXPLAIN = {
    "break-before-heading": "--- rule sitting directly above a heading",
    "title-case-heading": "heading Written In Title Case",
    "wide-table-cell": "table cell holding prose",
}

# One line per rule, saying what it caught and why that is worth changing. The page is read away from the rubric, and a
# rule name alone leaves the reader to guess whether a hit is a typographic artefact or a habit of thought.
WHY = {
    "arrow-bullet": "An arrow used as a bullet. Use a list.",
    "chat-residue": "Assistant talk left in the draft. The reader is not in a chat.",
    "cite-marker": "A citation marker from the tool that generated this, not from the source.",
    "corpus-noun": "\"Corpus\" for an ordinary set of documents. Say what they are.",
    "emphasis-verb": "Underscores, emphasises: a verb standing in for \"shows\". Say what it shows.",
    "landing-sentence": "A short closing sentence performing profundity after longer ones. Cut it, "
                        "or fold it into the sentence before.",
    "contrast-pair": "\"X is Y. Z is not.\" with the predicate clipped off for effect. Say what Z is.",
    "tag-clause": "A sentence ending on \", and we should\": an afterthought tagged on for "
                  "rhythm. End on the claim.",
    "anaphora": "Three or more sentences in a row opening on the same word. Vary one.",
    "landing-habit": "Short closers at a rate that makes them the habit rather than the "
                     "emphasis: over %.1f per 1000 words." % syntax.LANDING_RATE,
    "flat": "A paragraph with no subordinate clause: one idea per sentence, set side by side. "
            "A third of paragraphs like this is ordinary; the tell is most of them.",
    "new-number": "A number the original does not contain. The rewrite may not add facts.",
    "new-time": "A \"last week\" the original does not contain. The rewrite may not add facts.",
    "new-anecdote": "An \"I noticed\" the original does not contain. The rewrite may not add facts.",
    "new-name": "A name the original does not contain. The rewrite may not add facts.",
    "double-dash": "Two hyphens standing in for a dash. Repunctuate the sentence.",
    "ellipsis": "A trailing-off ellipsis. Finish the sentence or cut it.",
    "em-dash": "An em dash. Comma, full stop or brackets, as the sentence needs.",
    "emoji": "An emoji in expository prose.",
    "en-dash": "An en dash outside a numeric range.",
    "en-dash-range": "An en dash in a numeric range. A hyphen carries it.",
    "filler-verb": "A verb that sounds like work and does none. Say the action.",
    "honest-framing": "Framing an answer as the honest one implies the others were not.",
    "json-tail": "A fragment of the generating tool's output, left in the text.",
    "marketing-adjective": "Praise in place of a fact. State what it does.",
    "math-unicode": "Unicode maths characters used as bold or italic. Use markdown.",
    "metaphor-tic": "A figure this model reaches for by habit rather than by fit.",
    "nbsp": "A non-breaking space where an ordinary one belongs.",
    "negation-antithesis": "\"Not X, it's Y\". Reversing it reads as well, so it carries "
                           "no information. Make the positive claim.",
    "opener-filler": "An opening that delays the sentence. Start at the claim.",
    "padding": "Collapses to one word, or none, with nothing lost.",
    "phrase-swap": "A long phrase with a one-word equivalent.",
    "placeholder": "A placeholder that was never filled in.",
    "us-spelling": "American spelling. A model writes it whatever convention "
                   "the document is in. Ignore this on a document written for "
                   "an American reader; otherwise match the rest of the text.",
    "private-use": "A private-use codepoint, which renders differently everywhere.",
    "puffery": "Says the thing is impressive instead of saying what it does.",
    "smart-quote": "A curly quote. Straight quotes survive copy and paste.",
    "sycophancy": "Praise for the reader's question. Answer it instead.",
    "times-sign": "A multiplication sign in prose. Use x.",
    "utm-llm": "A tracking parameter naming the model that wrote this.",
    "weasel-source": "Attribution to nobody. Name the source or drop the claim.",
    # Tier 2 groups. None of these words is wrong on its own, which is the whole point of measuring them as a rate, so
    # each line says what the concentration of them is doing rather than condemning the word.
    "code-as-agent": "Code given intent, as though it decides and refuses: \"the check "
                     "refuses\", \"the cache holds\", \"the contract survives\". Occasionally "
                     "apt, tiring in quantity. Say what runs.",
    "adverbs": "Adverbs asserting that a claim is solid: plainly, genuinely, precisely, "
               "demonstrably. Delete one. If the claim survives intact, it was emphasis "
               "rather than evidence.",
    "negation": "Absolute negation: never, nothing, nobody, none. Each is a total claim, "
                "and in quantity they promise more certainty than the text has.",
    "adjudication": "The vocabulary of a court, applied to code: verdict, ruling, premise, "
                    "refusal, remedy. Fine in a document about decisions, a costume "
                    "elsewhere.",
    "structural": "Building and machinery metaphors: load-bearing, seam, chokepoint, "
                  "backstop, lever. Literal use is exempt; the tell is reaching for them "
                  "to describe abstractions.",
    # block and line findings
    "blob": "A paragraph long enough to hide its own argument. Cut or split it.",
    "dense": "Long paragraphs or bullets back to back, with no heading or table "
             "between them for the eye to rest on. Usually none is long enough to "
             "report on its own: %d paragraphs of %d words, or %d bullets of %d, "
             "since a bullet promised to be short. Cut inside the run, or break it "
             "where the argument turns."
             % (co.DENSE_RUN, co.DENSE_WORDS, co.DENSE_LIST_RUN, co.DENSE_LIST_WORDS),
    "table": "A table holding prose. Tables are for structured data.",
    "hard-wrapped": "Line breaks inserted by hand. They reflow the whole paragraph "
                    "in every later diff, and markdown ignores them.",
    "bold-emphasis": "Bold dropped into running sentences. Emphasis works by being "
                     "rare, so when everything is bold nothing is. Bold that opens a "
                     "line is a label and does not count. HEAVY is more than %.0f per "
                     "1000 words; ABUSED is %.0f, or paragraphs and table rows that "
                     "carry two bolds each, where neither can stand out."
                     % (co.BOLD_RATE, co.BOLD_ABUSED),
    "break-before-heading": "A --- above heading after heading is a claude.ai habit.",
    "title-case-heading": "Title case in a heading. Sentence case reads as written, "
                          "not as published.",
}


def why(rule):
    """The reason, with the caveat appended for a rule that is only possibly a tell."""
    text = WHY.get(rule, "")
    if rule in co.POSSIBLE:
        text = "%s Possible only: %s." % (text, co.POSSIBLE[rule])
    return text.strip()


def all_spans(text):
    """Regex spans and sentence-shape spans together, one list for the marks and the tally."""
    return sorted(co.scan_spans(text, co.SAFE, co.REVIEW, co.REPORT) + co.shape_spans(text))

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
/* `hidden` alone loses to the display rules below, and the panel is a flex box. */
[hidden] { display: none !important; }
html { -webkit-text-size-adjust: 100%; -moz-text-size-adjust: 100%; text-size-adjust: 100%; }
body { margin: 0; background: var(--ground); color: var(--ink);
       font: 400 16px/1.5 var(--grotesk); -webkit-font-smoothing: antialiased;
       overflow: hidden; }
:focus-visible { outline: 3px solid var(--accent); outline-offset: 2px; }

/* The panel beside the document, not above it: a term is clicked in the findings
   and read in the text, and a stacked board put the two an entire screen apart.
   Each column scrolls on its own so neither scrolls the other away. */
.board { display: grid; grid-template-columns: minmax(440px, 41%) 1fr;
         grid-template-rows: auto minmax(0, 1fr) auto;
         gap: var(--rule); padding: var(--rule); height: 100vh; }
.cell { border: var(--rule) solid var(--ink); padding: 14px 16px; min-width: 0; }
/* The panel does not scroll; the findings cell inside it takes the slack and
   scrolls, so each column shows exactly one scrollbar and the register stays put. */
.panel { display: flex; flex-direction: column; gap: var(--rule);
         min-height: 0; overflow: hidden; }
.grow { flex: 1; min-height: 0; display: flex; flex-direction: column; }
.doc { min-height: 0; overflow: auto; }
header, footer, .tabs { grid-column: 1 / -1; }
header { display: flex; align-items: center; justify-content: space-between; gap: 32px; }
header .stats { flex: 1; max-width: 680px; }
/* Several files share one board: a tab each, one file on screen at a time, the
   tab carrying the verdict so the set can be compared without switching. */
.board.many { grid-template-rows: auto auto minmax(0, 1fr) auto; }
.tabs { display: flex; flex-wrap: wrap; gap: 6px; padding: 8px 16px; }
.tabs button { text-transform: none; letter-spacing: 0; font-size: 12px; }
.tabs button em { font-style: normal; margin-left: 8px; color: var(--muted);
                  font-size: 10px; letter-spacing: 0.1em; text-transform: uppercase; }
.tabs button em.sloppy, .tabs button em.elevated { color: var(--accent); }
.tabs button.on, .tabs button:hover { background: var(--ink); border-color: var(--ink); color: #fff; }
.tabs button.on em, .tabs button:hover em { color: #fff; opacity: 0.7; }

@media (max-width: 900px) {
  body { overflow: auto; }
  .board, .board.many { grid-template-columns: 1fr; grid-template-rows: none; height: auto; }
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

button { border: 1px solid var(--ink); background: var(--ground); color: var(--ink);
         font: 400 10px/1 var(--mono); letter-spacing: 0.1em; text-transform: uppercase;
         padding: 4px 9px; cursor: pointer; white-space: nowrap; }
button:hover { background: var(--accent); border-color: var(--accent); color: #fff; }
button.done { background: var(--ink); border-color: var(--ink); color: #fff; }

input { width: 100%; border: var(--rule) solid var(--ink); background: var(--ground);
        color: var(--ink); font: 400 12px var(--mono); padding: 7px 9px;
        margin-bottom: 10px; letter-spacing: 0.08em; }
input::placeholder { color: var(--muted); text-transform: uppercase; }
tr.gone { display: none; }

footer { display: flex; align-items: center; gap: 14px;
         font: 400 10px var(--mono); letter-spacing: 0.1em; color: var(--muted);
         padding: 7px 16px; border: var(--rule) solid var(--ink); text-transform: uppercase; }
footer .end { margin-left: auto; }

/* the verdict, set at the size of the finding it is */
.band { font: 700 46px/1 var(--grotesk); letter-spacing: -0.02em; }
.band.sloppy, .band.elevated { color: var(--accent); }
.band.minor { color: var(--likely-rule); }
.rate { font: 400 13px var(--mono); color: var(--muted); margin-top: 6px; }
.gauge { display: flex; height: 22px; border: var(--rule) solid var(--ink);
         margin-top: 14px; position: relative; }
.gauge s { text-decoration: none; display: block; height: 100%; }
.gauge b { position: absolute; top: -5px; bottom: -5px; width: 3px; margin-left: -1px;
           background: var(--accent); }
.ticks { display: flex; justify-content: space-between;
         font: 400 11px var(--mono); color: var(--muted); margin-top: 4px; }

/* group bars: one grey ramp, the accent reserved for the group that leads */
.bar { display: grid; grid-template-columns: 108px 1fr 34px; align-items: center;
       gap: 8px; margin-bottom: 7px; font: 400 12px var(--mono); }
.bar { cursor: help; }
.bar u { text-decoration: none; color: var(--muted);
         border-bottom: 1px dotted #c4c4c4; }
.bar s { text-decoration: none; height: 13px; background: #d4d4d4; display: block; }
/* The accent marks the group to thin. Set explicitly: as `:first-of-type` it
   matched the verdict div above these rows and never reached a bar at all. */
.bar.lead s { background: var(--accent); }
.bar em { font-style: normal; text-align: right; color: var(--muted); }

table { border-collapse: collapse; width: 100%; font: 400 13px var(--mono); }
td { padding: 3px 6px 3px 0; vertical-align: top; border-bottom: 1px solid #ececec; }
td.n { width: 34px; color: var(--muted); text-align: right; }
td.r { color: var(--muted); text-align: right; white-space: nowrap; }
tr.pick { cursor: pointer; }
tr.pick:hover td { background: var(--fill); }
.scroll { flex: 1; min-height: 90px; overflow: auto; }

/* The frequency chart sits in its own narrow column. At 30% it was mostly empty
   space on every block row, which carries no bar, and squeezed the description
   it was supposed to sit beside into three words a line. */
td.f { width: 76px; }
td.f s { display: block; height: 11px; background: #d4d4d4; text-decoration: none; }
tr.pick:first-child td.f s { background: var(--accent); }
/* The description takes whatever the three measured columns leave. */
td.d { width: 100%; }

/* before and after: a glance, so a small table rather than a bar per figure */
table.diff { width: auto; font: 400 12px var(--mono); }
table.diff th { font-weight: 400; color: var(--muted); text-align: right; padding: 0 12px 3px 0; }
table.diff td { padding: 2px 12px 2px 0; border: 0; text-align: right; }
table.diff td:first-child { text-align: left; color: var(--muted); }
.cut { color: var(--accent); }
.diff-head { font: 400 12px var(--mono); color: var(--muted); margin: 10px 0 0; }
.added { margin: 4px 0 0; padding-left: 18px; color: var(--ink); font: 400 12px var(--mono); }
.added b { color: var(--accent); font-weight: 700; }

.why { font: 400 12px/1.45 var(--mono); color: var(--ink); margin: 12px 0 0;
       padding: 9px 11px; background: #f4f4f4; border-left: var(--rule) solid var(--ink);
       min-height: 3.2em; }
.why.idle { color: var(--muted); border-left-color: #d4d4d4; }
.legend { display: flex; gap: 16px; font: 400 11px var(--mono);
          color: var(--muted); margin-top: 12px; flex-wrap: wrap; }
.key { display: inline-block; width: 22px; height: 11px; margin-right: 5px;
       vertical-align: -1px; }
/* One ramp from pale yellow to red by confidence. The key swatches match the marks;
   the underline is the same rule in each step's colour and carries no meaning of
   its own. */
.k-possible { background: var(--maybe); box-shadow: inset 0 -3px 0 var(--maybe-rule); }
.k-probable { background: var(--likely); box-shadow: inset 0 -3px 0 var(--likely-rule); }
.k-certain { background: var(--fill); box-shadow: inset 0 -3px 0 var(--accent); }
.legend b { font-weight: 700; color: var(--ink); letter-spacing: 0.1em; text-transform: uppercase; }

pre { margin: 0; font: 400 13px/1.65 var(--mono); white-space: pre-wrap;
      word-wrap: break-word; }
/* The brief, kept hidden as the copy source and revealed only if the clipboard
   refuses, so there is still something to select by hand. */
.brief { margin: var(--rule); padding: 14px 16px; border: var(--rule) solid var(--ink); }
body.spill { overflow: auto; }
/* A block finding is shaded rather than underlined, and named in its own margin,
   because what is wrong with it is its extent. */
.block { display: block; border-left: var(--rule) solid #b9b9b9; padding-left: 10px;
         margin: 2px 0 2px -12px; position: relative; }
.block::after { content: attr(data-label); position: absolute; right: 0; top: 0;
                font: 400 10px var(--mono); letter-spacing: 0.08em; color: var(--muted);
                background: var(--ground); padding-left: 8px; text-transform: uppercase; }
/* Block shades sit on the same ramp as the marks, lighter so the paragraph inside
   stays readable: a dense run and an unjoined paragraph are possible (yellow), a
   long paragraph and a prose table are probable (orange). A run often contains a
   blob, which keeps its own deeper shade inside it. The margin label says which. */
.block.dense, .block.flat { background: #fffbe6; border-left-color: var(--maybe-rule); }
.block.blob, .block.table { background: #ffe4bd; border-left-color: var(--likely-rule); }
.block.flash { animation: flash 1.1s ease-out; }
@keyframes flash { from { background: var(--fill); border-left-color: var(--accent); } }
@media (prefers-reduced-motion: reduce) { .block.flash { animation: none; } }
/* the block kinds keep their step of the ramp where they are listed, too */
tr.pick.blob td.n, tr.pick.table td.n { color: var(--likely-rule); }
tr.pick.dense td.n, tr.pick.flat td.n { color: var(--maybe-rule); }

/* The hard wrap, shown where it happens: invisible in rendered markdown, and it
   reflows the whole paragraph in every later diff. */
.wrap { display: inline-block; width: 0; overflow: visible; font-style: normal; }
.wrap::before { content: "\\21B5"; color: var(--accent); font-weight: 700;
                padding-left: 4px; font-size: 1.1em; }

mark { color: inherit; padding: 0 1px; cursor: pointer; }
/* Filled at every step, pale to red: a dotted rule on plain ground could not be
   seen at reading distance. */
mark[data-conf="possible"] { background: var(--maybe); box-shadow: inset 0 -3px 0 var(--maybe-rule); }
mark[data-conf="probable"] { background: var(--likely); box-shadow: inset 0 -3px 0 var(--likely-rule); }
mark[data-conf="certain"] { background: var(--fill); box-shadow: inset 0 -3px 0 var(--accent); }
tr.pick.possible td.n::before { content: "?"; color: var(--muted); margin-right: 3px; }
/* Mid-sentence bold is a density, not a defect at the span, so it takes the
   blue of the findings count rather than competing with the severity ramp. */
mark.em { background: #e9eff9; box-shadow: inset 0 -3px 0 #1a4fa0; }
/* a chosen term holds; everything else recedes rather than disappears */
body.sel mark { background: transparent; box-shadow: none; color: #a8a8a8; }
body.sel mark.on { background: var(--accent); color: #fff; box-shadow: none; }
body.sel tr.pick { opacity: 0.35; }
body.sel tr.pick.on { opacity: 1; }
body.sel tr.pick.on td { background: var(--fill); }
.empty { color: var(--muted); font: 400 13px var(--mono); }
"""

JS = """
var body = document.body, sel = null, cur = '0', pinned = '';
var idle = (document.querySelector('.why') || {}).textContent || '';
/* Everything about one file carries its index, so the file on screen is a
   selector prefix and a switch is one pass over the page. */
function q(s) { return document.querySelector('[data-file="' + cur + '"] ' + s); }
function brief() { return document.querySelector('.brief[data-brief="' + cur + '"]'); }
function say(text) {
  var why = q('.why');
  if (!why) return;
  why.textContent = text || pinned || idle;
  why.classList.toggle('idle', !(text || pinned));
}
say('');
function show(i) {
  if (sel) choose(sel);
  cur = i;
  pinned = '';
  document.querySelectorAll('[data-file]').forEach(function (el) { el.hidden = el.dataset.file !== i; });
  document.querySelectorAll('[data-tab]').forEach(function (el) { el.classList.toggle('on', el.dataset.tab === i); });
  document.querySelectorAll('.brief').forEach(function (el) { el.hidden = true; });
  body.classList.remove('spill');
  say('');
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
  document.querySelectorAll('[data-term]').forEach(function (el) {
    el.classList.toggle('on', sel !== null && el.dataset.term === sel);
  });
  if (sel) {
    var first = q('mark.on');
    if (first) first.scrollIntoView({block: 'center', behavior: 'smooth'});
  }
}
document.addEventListener('click', function (e) {
  var tab = e.target.closest('[data-tab]');
  if (tab) { show(tab.dataset.tab); return; }
  var go = e.target.closest('[data-goto]');
  if (go) {
    pinned = go.dataset.why || '';
    say('');
    var block = document.getElementById(go.dataset.goto);
    if (block) {
      block.scrollIntoView({block: 'center', behavior: 'smooth'});
      block.classList.remove('flash');
      void block.offsetWidth;
      block.classList.add('flash');
    }
    return;
  }
  var el = e.target.closest('[data-term]');
  if (el) {
    choose(el.dataset.term);
    pinned = sel ? (el.dataset.why || '') : '';
    say('');
  } else if (sel) {
    choose(sel);
    pinned = '';
    say('');
  }
});
document.addEventListener('keydown', function (e) {
  var box = q('.find');
  if (e.key === 'Escape' && sel) choose(sel);
  else if (e.key === '/' && box && document.activeElement !== box) { e.preventDefault(); box.focus(); }
});
document.querySelectorAll('.find').forEach(function (box) {
  var rows = box.parentNode.querySelectorAll('tr.pick');
  box.addEventListener('input', function () {
    var want = box.value.trim().toLowerCase();
    rows.forEach(function (tr) {
      tr.classList.toggle('gone', want !== '' && tr.dataset.term.indexOf(want) === -1);
    });
  });
  box.addEventListener('click', function (e) { e.stopPropagation(); });
});

var copy = document.getElementById('copy');
function flashed(ok) {
  var stash = brief();
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
  ta.value = brief().textContent;
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
    navigator.clipboard.writeText(brief().textContent).then(function () { flashed(true); },
                                                          bySelection);
  } else bySelection();
});
"""


def e(s):
    return html.escape(str(s), quote=True)


line_offsets = syntax.line_offsets


class Block(NamedTuple):
    """A finding with a line range instead of a word: shaded, and listed once."""

    start: int  # character offsets, for marking the text
    end: int
    kind: str  # blob | table
    label: str  # what it is, in the margin of the document
    measure: str  # its extent, which is why it is worth fixing
    where: str


def blocks(text):
    """Long paragraphs and prose tables, as ranges to shade.

    Listing a wide table once per row, as the per-line rule did, buried a 776-line document under 135 identical entries.
    """
    at = line_offsets(text)

    def end_of(ln):
        return at.get(ln + 1, len(text))

    out = []
    for words, start, opening, last in co.blobs(text):
        out.append(Block(at[start], end_of(last), "blob", opening,
                         "%dw" % words, "L%d-%d" % (start, last)))
    for start, last, count, words, longest, listed in co.dense_runs(text):
        out.append(Block(at[start], end_of(last), "dense",
                         "%d consecutive long %s, longest %dw"
                         % (count, "bullets" if listed else "paragraphs", longest),
                         "%dw" % words, "L%d-%d" % (start, last)))
    for start, last, wide in co.tables(text):
        out.append(Block(at[start], end_of(last), "table",
                         "table, %d prose cell%s" % (wide, "" if wide == 1 else "s"),
                         "%dc" % wide, "L%d-%d" % (start, last)))
    # Shaded only once the document bands: below that, a third of paragraphs unjoined is what prose looks like.
    if (flat := co.parataxis_stats(text)) and flat["band"]:
        for start, last, n, _ in flat["flat"]:
            out.append(Block(at[start], end_of(last), "flat",
                             "no subordinate clause, %d sentences" % n,
                             "%ds" % n, "L%d-%d" % (start, last)))
    return sorted(out)


def marked(text, spans, text_blocks=(), wrap_points=(), ids=None, emphasis=()):
    """The input with flagged spans wrapped, blocks shaded and hard wraps shown.

    Built in one pass over sorted cut points so a span inside a shaded block still gets its own mark, rather than one
    pass per layer fighting the others.

    Mid-sentence bold is its own layer rather than another entry in `spans`: it shares the marking but not the ranking,
    since a hundred distinct bolded phrases would be a hundred rows in a list meant to name habits.
    """
    opens = {}
    for i, b in enumerate(text_blocks):
        anchor = ' id="%s"' % e(ids[i]) if ids else ""
        # data-why, so hovering the shaded paragraph says what it is, as hovering a mark does.
        opens.setdefault(b.start, []).append(
            ('<div class="block %s"%s data-label="%s" data-why="%s" title="%s">'
             % (b.kind, anchor, e("%s  %s" % (b.measure, b.kind)),
                e("%s: %s" % (b.label, why(b.kind))), e("%s: %s" % (b.kind, why(b.kind)))), b.end))
    wrap_at = set(wrap_points)

    # Marks cannot nest in a single pass, and a landing sentence can hold a chat-residue phrase ("Happy to change it.").
    # Probable spans are placed first and a possible span overlapping one is not marked; it keeps its row in the list.
    span_at = {}
    placed = []
    for s, en, name, hit in sorted(spans, key=lambda x: (CONFIDENCE.get(x[2]) == "possible", x[0])):
        if any(s < b and a < en for a, b in placed):
            continue
        span_at[s] = (en, name, hit, "")
        placed.append((s, en))
    # A bold span holding a flagged word ("**load-bearing**") would nest one mark inside another, which the single pass
    # cannot close; the rule already has its own row, so the narrower finding keeps the mark.
    for start, end, body in emphasis:
        if not any(start < e and s < end for s, e, _, _ in spans):
            span_at.setdefault(start, (end, "bold-emphasis", body, " em"))

    out, at, closing = [], 0, []
    cuts = sorted({0, len(text)} | set(opens) | {b.end for b in text_blocks} | wrap_at
                  | set(span_at) | {v[0] for v in span_at.values()})

    for cut in cuts:
        out.append(e(text[at:cut]))
        at = cut
        while closing and closing[-1] <= cut:
            closing.pop()
            out.append("</div>")
        for tag, end in opens.get(cut, []):
            out.append(tag)
            closing.append(end)
            closing.sort(reverse=True)
        if cut in wrap_at:
            # The newline itself stays; the glyph only makes it visible.
            out.append('<i class="wrap" title="hard wrap"></i>')
        if cut in span_at:
            end, name, hit, kind = span_at[cut]
            # Landing sentences select as one term, so the habit row and each closer's row hold all of them, as bold
            # does: the rate is the finding, and one closer on its own is not.
            term = name if kind or name == "landing-sentence" else hit.lower()
            out.append('<mark class="%s" data-conf="%s" data-term="%s" data-why="%s" '
                       'title="%s">%s</mark>'
                       % (kind.strip(), CONFIDENCE.get(name, "probable"), e(term),
                          e(why(name)), e("%s: %s" % (name, why(name))), e(text[cut:end])))
            at = end
    out.append(e(text[at:]))
    out.append("</div>" * len(closing))
    return "".join(out)


def gauge(rate):
    """The three bands as ground, the measurement as a needle on them.

    A filled bar said nothing once the rate passed the end of the scale: at 22.5 on a scale to 20 it was a solid block
    of accent, pinned at 100%. The scale now stretches to hold the value, and the needle is the only accent on it.
    """
    full = max(co.SLOPPY * 2, rate * 1.08)
    zones = ((co.ELEVATED, "#ececec"), (co.SLOPPY, "#d4d4d4"), (full, "#b9b9b9"))
    bands, at = [], 0.0
    for upto, colour in zones:
        bands.append('<s style="width:%.2f%%;background:%s"></s>'
                     % (100.0 * (upto - at) / full, colour))
        at = upto
    return ('<div class="gauge">%s<b style="left:%.2f%%"></b></div>'
            '<div class="ticks"><span>0</span><span>%g elevated</span>'
            '<span>%g sloppy</span><span>%g</span></div>'
            % ("".join(bands), 100.0 * min(rate, full) / full,
               co.ELEVATED, co.SLOPPY, round(full)))


def headline(stats, nfindings, possible):
    """The document's verdict: the register band when it has one, else MINOR SLOP while anything at all was found,
    and CLEAN only when nothing was. A register below its gate said CLEAN over a page of findings."""
    if stats:
        return stats["band"]
    return "MINOR SLOP" if nfindings or possible else "CLEAN"


def verdict(stats, nwords, nfindings, possible):
    word = headline(stats, nfindings, possible)
    if not stats:
        what = ("register under %.1f/1000, or fewer than %d markers, or under %d words"
                % (co.ELEVATED, co.LEAST, co.SHORT))
        if word != "CLEAN":
            what += "; %d finding%s%s remain%s" % (nfindings, "" if nfindings == 1 else "s",
                                                   ", %d possible" % possible if possible else "",
                                                   "s" if nfindings + possible == 1 else "")
        return ('<div class="band %s">%s</div><div class="rate">%s</div>%s'
                % (word.split()[0].lower(), word, what, gauge(0)))
    return ('<div class="band %s">%s</div><div class="rate">%.1f per 1000 words, '
            '%d markers over %d</div>%s'
            % (word.lower(), word, stats["rate"], stats["total"], nwords, gauge(stats["rate"])))


def groups_block(stats):
    """Bars under the verdict. Silent when clean: the verdict already said so."""
    if not stats:
        return ""
    top = max(sum(n for _, n in pairs) for _, pairs in stats["groups"])
    rows = []
    for i, (group, pairs) in enumerate(stats["groups"]):
        n = sum(c for _, c in pairs)
        words = ", ".join(w for w, _ in pairs[:8])
        rows.append('<div class="bar%s" data-why="%s" title="%s"><u>%s</u>'
                    '<s style="width:%.1f%%"></s><em>%d</em></div>'
                    % (" lead" if i == 0 else "", e("%s  Here: %s." % (WHY.get(group, ""), words)),
                       e(WHY.get(group, group)), e(group), 100.0 * n / top, n))
    return '<h2 class="sub">By group</h2>%s' % "".join(rows)


def tally(spans):
    """{term: (rule name, count)}, one entry per term rather than per hit."""
    terms = {}
    for _, _, name, hit in spans:
        key = hit.lower()
        seen, count = terms.get(key, (name, 0))
        terms[key] = (seen, count + 1)
    return terms


class Finding(NamedTuple):
    """One entry in the findings list, in the form the page and the brief share.

    Both read this list rather than each walking the checker again, so the brief cannot disagree with the page it was
    copied from.
    """

    rule: str  # what fired; also the grouping key in the brief
    n: int  # how many, counted in `unit`
    unit: str  # what n counts, so the brief can say "3 paragraphs"
    example: str  # the term itself, or the lines it sits on
    cell: str  # the count as the page prints it: 412w, 3p, 12
    what: str  # middle column
    where: str  # right column
    note: str = ""  # a band or verdict the count alone does not carry
    term: str = ""  # selection and search key
    goto: str = ""  # block id, for rows that scroll the document
    kind: str = ""  # blob | table | flat | possible, so the row keeps its colour
    pick: bool = False  # clickable, and subject to the search box
    bar: float = -1.0  # frequency bar width, terms only

    @property
    def why(self):
        return why(self.rule)

    @property
    def possible(self):
        return self.rule in co.POSSIBLE or self.kind == "possible"


def findings(text, spans, text_blocks, ids):
    """Every finding in one ranked list, blocks above terms.

    Split across two cells, a document whose problem was structure showed two rows under "findings" and eighteen under
    "structure". They are one list of things to fix, so they are one list.

    Terms carry a frequency bar in the row they label, rather than a chart beside it: two views of the same counts is
    the duplication this skill exists to flag. Blocks carry their extent instead, which is what makes them worth fixing.
    """
    out = []
    for i, b in enumerate(text_blocks):
        if b.kind == "flat":
            continue  # listed once as the aggregate row below, since the share is the finding
        out.append(Finding(rule=b.kind, n=1,
                           unit={"blob": "paragraph", "dense": "run"}.get(
                               b.kind, "prose table"),
                           example=b.where, cell=b.measure, what=b.label, where=b.where,
                           term=b.label.lower(), goto=ids[i], kind=b.kind, pick=True))

    if (em := co.bold_stats(text)):
        where = ", ".join("L%d" % n for n in em["lines"][:co.LOCATIONS_MAX])
        if len(em["lines"]) > co.LOCATIONS_MAX:
            where += ", +%d" % (len(em["lines"]) - co.LOCATIONS_MAX)
        out.append(Finding(rule="bold-emphasis", n=em["total"], unit="span",
                           example=", ".join(w for w, _ in em["worst"][:4]),
                           cell="%dx" % em["total"],
                           what="%s: %.1f mid-sentence bolds per 1000 words "
                                "(heavy over %.0f, abused at %.0f), %d of %d "
                                "paragraphs and table rows carrying two or more"
                                % (em["band"], em["rate"], co.BOLD_RATE,
                                   co.BOLD_ABUSED, em["crowded"], em["units"]),
                           note=em["band"], where=where,
                           term="bold-emphasis", pick=True))

    if (lb := syntax.landing_stats(text, co.units(text), spans)):
        out.append(Finding(rule="landing-habit", n=lb["total"], unit="short closer",
                           example="%d closers" % lb["total"], cell="%dx" % lb["total"],
                           what="%s: %.1f short closing sentences per 1000 words (habit at %.1f)"
                                % (lb["band"], lb["rate"], syntax.LANDING_RATE),
                           note=lb["band"], where="landing-sentence", term="landing-sentence",
                           pick=True))

    # Listed whenever there is enough to measure and something measured flat; banded only past the share, and below
    # the band it is a possible row. Banded, it scrolls to the first shaded paragraph.
    if (flat := co.parataxis_stats(text)) and flat["flat"]:
        where = ", ".join("L%d" % s for s, _, _, _ in flat["flat"][:co.LOCATIONS_MAX])
        first = next((ids[i] for i, b in enumerate(text_blocks) if b.kind == "flat"), "")
        out.append(Finding(rule="flat", n=len(flat["flat"]), unit="paragraph",
                           example=where, cell="%dp" % len(flat["flat"]),
                           what="%s%d of %d measured paragraphs with no subordinate clause "
                                "(a third is ordinary)"
                                % (flat["band"] + ": " if flat["band"] else "",
                                   len(flat["flat"]), flat["measured"]),
                           note=flat["band"], where=where, term="flat", goto=first,
                           kind="flat" if flat["band"] else "possible", pick=bool(first)))

    points, wrapped, total = co.wraps(text)
    if wrapped:
        out.append(Finding(rule="hard-wrapped", n=wrapped, unit="paragraph",
                           example="%d breaks" % len(points), cell="%dp" % wrapped,
                           what="paragraphs wrapped by hand, of %d, at %d breaks"
                                % (total, len(points)),
                           where="hard-wrapped", term="hard-wrapped"))

    # Grouped by rule, like the terms below: five title-case headings are one habit to drop, not five findings.
    at_line: dict[str, list[int]] = {}
    for line, name in co.line_checks(text):
        at_line.setdefault(name, []).append(line)
    for name, lines in sorted(at_line.items()):
        where = ", ".join("L%d" % n for n in lines[:co.LOCATIONS_MAX])
        if len(lines) > co.LOCATIONS_MAX:
            where += ", +%d" % (len(lines) - co.LOCATIONS_MAX)
        out.append(Finding(rule=name, n=len(lines), unit="occurrence", example=where,
                           cell="%d" % len(lines), what=EXPLAIN.get(name, name),
                           where=where, term=name))

    terms = tally(spans)
    # Possible terms rank below every probable one, whatever their count: a page of "?" rows above the defects would
    # invert what the split is for.
    ranked = sorted(terms.items(), key=lambda kv: (kv[1][0] in co.POSSIBLE, -kv[1][1], kv[0]))
    top = max((c for _, (_, c) in ranked), default=1)
    for term, (name, count) in ranked:
        out.append(Finding(rule=name, n=count, unit="use", example=term,
                           cell="%d" % count, what=term, where=name,
                           term=name if name == "landing-sentence" else term,
                           kind="possible" if name in co.POSSIBLE else "",
                           pick=True, bar=100.0 * count / top))
    return out


def _row(f):
    cls = " ".join(x for x in ("pick" if f.pick else "", f.kind) if x)
    attrs = ' class="%s"' % cls if cls else ""
    if f.goto:
        attrs += ' data-goto="%s"' % e(f.goto)
    if f.term:
        attrs += ' data-term="%s"' % e(f.term)
    bar = '<s style="width:%.1f%%"></s>' % f.bar if f.bar >= 0 else ""
    return ('<tr%s data-why="%s" title="%s"><td class="n">%s</td><td class="f">%s</td>'
            '<td class="d">%s</td><td class="r">%s</td></tr>'
            % (attrs, e(f.why), e(f.why or f.rule), e(f.cell), bar, e(f.what), e(f.where)))


def findings_block(found):
    rows = [_row(f) for f in found]

    if not rows:
        return '<p class="empty">Nothing flagged.</p>'
    legend = "<b>Confidence</b>" + "".join(
        '<span><i class="key k-%s"></i>%s, %s</span>' % (s, s, e(d)) for s, d in LEGEND)
    # The caption holds the description of whatever is hovered or chosen, so the reason a thing is flagged does not
    # depend on finding a tooltip.
    return ('<input class="find" placeholder="Search for a finding..." autocomplete="off">'
            '<div class="scroll"><table>%s</table></div>'
            '<p class="why">Hover or click a finding for what it is and why.</p>'
            '<div class="legend">%s</div>'
            % ("".join(rows), legend))


def brief(path, stats, nwords, found):
    """The findings as text, sized to paste into another agent.

    Grouped by rule and carrying each rule's reason. A list of bare rule names leaves the receiving agent guessing, and
    one rule is one habit to drop however many times it fired.

    Lines are separated by a blank one, never wrapped: the brief is pasted into something that may render it as
    markdown, where a wrap reflows anyway.
    """
    out = ["Slop check of %s. Rewrite to fix the following. Keep the facts and the "
           "meaning, and do not make it longer." % os.path.basename(path), ""]
    if stats:
        group, pairs = stats["groups"][0]
        out += ["Register: %s. %.1f marker words per 1000 (elevated at %.1f, sloppy at "
                "%.1f), %d markers over %d words."
                % (stats["band"], stats["rate"], co.ELEVATED, co.SLOPPY,
                   stats["total"], nwords), "",
                "Heaviest group: %s, %d hits (%s). %s"
                % (group, sum(n for _, n in pairs), ", ".join(w for w, _ in pairs[:6]),
                   WHY.get(group, ""))]
    else:
        out.append("Verdict: %s. Register under %.1f marker words per 1000 over %d words."
                   % (headline(stats, sum(1 for f in found if not f.possible),
                               sum(1 for f in found if f.possible)), co.ELEVATED, nwords))

    groups: dict[str, tuple] = {}
    for f in found:
        n, unit, note, seen, maybe = groups.get(f.rule, (0, f.unit, f.note, [], f.possible))
        if f.example not in seen and len(seen) < BRIEF_EXAMPLES:
            seen.append(f.example)
        groups[f.rule] = (n + f.n, unit, note, seen, maybe)

    if not groups:
        out += ["", "Nothing else flagged."]
        return "\n".join(out)

    # Two lists, so the receiving agent fixes one and reads the other. The caveat travels with each possible rule,
    # since the agent has the file but not this page.
    for maybe, head in ((False, "Findings, fix these:"), (True, "Possible, read before changing:")):
        rows = [(r, g) for r, g in groups.items() if g[4] == maybe]
        if not rows:
            continue
        out += ["", head]
        for rule, (n, unit, note, seen, _) in rows[:BRIEF_MAX]:
            out.append("- %s, %d %s%s (%s): %s"
                       % (rule, n, unit if n == 1 else unit + "s",
                          ", " + note if note else "", ", ".join(seen), why(rule)))
        if len(rows) > BRIEF_MAX:
            out.append("- and %d further kinds, listed in the report." % (len(rows) - BRIEF_MAX))
    return "\n".join(out)


def _delta(was, now):
    if not was:
        return ""
    pct = (now - was) / was * 100
    return '<span class="%s">%+.0f%%</span>' % ("cut" if now < was else "", pct)


def compare_block(orig, new):
    """Before and after as one small table: words, hits by confidence, register rate.

    Only rendered when an original was passed. A row of figures, not a bar per row: at five pairs of bars it took the
    height of the register cell for a comparison the reader glances at once.
    """
    before = tally(all_spans(orig))
    after = tally(all_spans(new))

    def by_conf(terms, how):
        return sum(n for name, n in terms.values() if CONFIDENCE.get(name) == how)

    rows = [("words", len(orig.split()), len(new.split()))]
    for how, _ in reversed(LEGEND):
        was, now = by_conf(before, how), by_conf(after, how)
        if was or now:
            rows.append((how + " hits", was, now))
    ob, nb = co.register_stats(orig), co.register_stats(new)
    if ob or nb:
        rows.append(("register per 1000", round(ob["rate"] if ob else 0), round(nb["rate"] if nb else 0)))
    out = ['<table class="diff"><tr><th></th><th>before</th><th>after</th><th></th></tr>%s</table>'
           % "".join('<tr><td>%s</td><td>%d</td><td>%d</td><td>%s</td></tr>'
                     % (e(label), was, now, _delta(was, now)) for label, was, now in rows)]
    # Specifics the rewrite added are listed, not counted: each is a fact to check against the original.
    added = syntax.new_specifics(orig, new)
    if added:
        at = line_offsets(new)
        items = "".join("<li><b>%s</b> %s, L%d</li>"
                        % (e(hit), e(name), max(n for n, off in at.items() if off <= start))
                        for start, _, name, hit in added[:BRIEF_EXAMPLES * 2])
        more = len(added) - BRIEF_EXAMPLES * 2
        out.append('<p class="diff-head">not in the original</p><ul class="added">%s%s</ul>'
                   % (items, "<li>and %d more</li>" % more if more > 0 else ""))
    return "".join(out)


def page(path, text, against, prefix):
    """One file's share of the board: everything that is about the file rather than the run."""
    spans = all_spans(text)
    stats = co.register_stats(text)
    nwords = len(text.split())
    text_blocks = blocks(text)
    ids = ["%sb%d" % (prefix, i) for i in range(len(text_blocks))]
    found = findings(text, spans, text_blocks, ids)

    extra = ""
    if against is not None:
        extra = ('<section class="cell"><h2>Before and after</h2>%s</section>'
                 % compare_block(against, text))

    # Markers rather than distinct terms in the third slot: on a document whose problem is register rather than
    # vocabulary, "4 flagged spans, 2 terms" read as a clean bill while the register line underneath said SLOPPY.
    # Possible spans are counted apart, as check_output prints them: a page of reads is not a page of defects.
    maybe = sum(1 for s in spans if s[2] in co.POSSIBLE)
    nfindings = len(spans) - maybe + sum(1 for b in text_blocks if b.kind != "flat") + len(co.line_checks(text)) + sum(
        1 for f in found if f.rule in ("hard-wrapped", "bold-emphasis", "landing-habit"))
    strip = "".join(
        '<div><i style="background:%s"></i><b>%s</b><u>%s</u></div>' % (colour, e(n), e(label))
        for colour, n, label in (
            ("#de301e", "%d" % nwords, "words"),
            ("#1a4fa0", "%d" % nfindings, "findings" + (", %d possible" % maybe if maybe else "")),
            ("#e8b400", "%d" % (stats["total"] if stats else 0), "register markers"),
        ))

    return {
        "name": e(os.path.basename(path)),
        "band": headline(stats, nfindings, maybe),
        "strip": strip,
        "verdict": verdict(stats, nwords, nfindings, maybe),
        "groups": groups_block(stats),
        "findings": findings_block(found),
        "brief": e(brief(path, stats, nwords, found)),
        "extra": extra,
        "text": marked(text, spans, text_blocks, co.wraps(text)[0], ids,
                       (co.bold_stats(text) or {}).get("spans", ())),
    }


def render(inputs, against=None):
    """One board for every (path, text) given.

    Several files share the page rather than getting one each: a tab per file, one on screen at a time, the tab
    carrying the verdict so the set reads at a glance. Merging the texts was the other way, and it has no honest
    register: a rate over three documents describes none of them.
    """
    pages = [page(path, text, against, "f%d" % i) for i, (path, text) in enumerate(inputs)]
    many = len(pages) > 1

    def each(fmt):
        return "".join(fmt % dict(p, i=i, hide=" hidden" if i else "") for i, p in enumerate(pages))

    tabs = ""
    if many:
        tabs = '<nav class="cell tabs">%s</nav>' % "".join(
            '<button data-tab="%d"%s>%s<em class="%s">%s</em></button>'
            % (i, ' class="on"' if i == 0 else "", p["name"], p["band"].split()[0].lower(), p["band"])
            for i, p in enumerate(pages))

    return """<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>slop report: %(title)s</title>
<style>%(css)s</style>
<div class="board%(many)s">
  <header class="cell">
    <h1>The <span>slop</span> in %(title)s</h1>
    %(strips)s
  </header>
  %(tabs)s
  %(files)s
  <footer><span>generated %(when)s</span>
    <button id="copy" data-why="Copies these findings as text, each with its reason, to paste into a coding agent.">Copy brief</button>
    <span class="end">rewrite-slop</span></footer>
</div>
%(briefs)s
<script>%(js)s</script>
""" % {
        "title": "%d files" % len(pages) if many else pages[0]["name"],
        "many": " many" if many else "",
        "css": CSS, "js": JS,
        "when": datetime.datetime.now().astimezone().date().isoformat(),
        "strips": each('<div class="stats" data-file="%(i)d"%(hide)s>%(strip)s</div>'),
        "tabs": tabs,
        "files": each('<div class="panel" data-file="%(i)d"%(hide)s>'
                      '<section class="cell"><h2>Verdict</h2>%(verdict)s%(groups)s</section>%(extra)s'
                      '<section class="cell grow"><h2>Findings</h2>%(findings)s</section></div>'
                      '<section class="cell doc" data-file="%(i)d"%(hide)s><h2>The text</h2><pre>%(text)s</pre></section>'),
        "briefs": each('<pre class="brief" data-brief="%(i)d" hidden>%(brief)s</pre>'),
    }


def main():
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("files", nargs="+", help="text to report on; several share one page, a tab each")
    ap.add_argument("--against", metavar="ORIG", help="original file, for the before-and-after block")
    ap.add_argument("-o", "--out", help="output path (default: alongside the input; slop-report.html "
                                        "beside the first of several)")
    args = ap.parse_args()

    try:
        against = None
        if args.against:
            with open(args.against, encoding="utf-8") as fh:
                against = fh.read()
        inputs = []
        for path in args.files:
            with open(path, encoding="utf-8") as fh:
                inputs.append((path, fh.read()))
    except OSError as err:
        ap.error("%s: %s" % (err.filename, err.strerror))

    if len(inputs) > 1:
        out = args.out or os.path.join(os.path.dirname(args.files[0]), "slop-report.html")
    else:
        out = args.out or os.path.splitext(args.files[0])[0] + ".slop-report.html"
    try:
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(render(inputs, against))
    except OSError as err:
        # The default output sits beside the input, which is often read-only.
        ap.error("cannot write %s: %s. Pass -o to choose another path." % (err.filename, err.strerror))
    print(out)


if __name__ == "__main__":
    main()
