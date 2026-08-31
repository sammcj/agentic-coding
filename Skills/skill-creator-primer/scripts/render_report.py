#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml", "skills-ref"]
# ///
"""Render one skill's validate_skill findings as a single self-contained HTML page.

Optional. Nothing in the primer's workflow calls this; it exists for reading a
large skill, or for showing someone else what was flagged and where.

    uv run render_report.py SKILL_DIR [--against OTHER_DIR] [-o OUT]

Every cell but one is stdlib-only and needs no network: run it with plain python3
and the spec cell says which dependency is missing instead of failing the render.

The page reads validate_skill rather than reimplementing it: referenced_md_files
and estimate_tokens for the bars, _TOKEN_RATINGS and token_rating for the gauge
and band, _budget for the cure line and the declared ceiling, _structure for the
blob and code spans, _filler and _filler_scan for the marks and the ranked list,
and lint for the spec cell. A new threshold or rule reaches the page with no edit
here. A new *kind* of finding, neither line-span nor term, needs a cell of its own.

Two contracts hold the page to the detector:

- _structure returns each unit as (size, path, first line, last line, opening).
  The last line is what lets the page shade a whole unit; drop it and the shading
  falls back to the opening line alone.
- mark_line places each term by offset over vs._filler_scan's output. Searching
  the raw line for the matched text instead would mark occurrences the detector
  excluded: a word inside backticks, or a sentence-initial rule matching
  mid-sentence.

Three checks after a change, all of them past what a browser screenshot shows:

- The page's mark count equals the lexical no-op count validate_skill.py
  --report-only prints for the same skill, except where overlapping rules share
  a mark.
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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import validate_skill as vs  # noqa: E402  # pyright: ignore[reportMissingImports]

# The gauge tops out past the Poor floor so a badly over-budget skill still has
# bar left to grow into rather than pinning at full and hiding how far over it is.
GAUGE_CEILING = int(vs._TOKEN_RATINGS[-1][0] * 1.5)

# What each mark on the document means, since the page is read away from the primer.
LEGEND = [
    ("filler", "lexical no-op - cut the word"),
    ("blob", f"text unit of {vs.BLOB_WORDS}+ words - compress it"),
    ("code", f"fenced block over {vs.CODE_FENCE_LINES} lines - move it to scripts/"),
]

CSS = """
:root {
  color-scheme: only light;
  --grotesk: "Helvetica Neue", Helvetica, Roboto, ui-sans-serif, system-ui, Arial, sans-serif;
  --mono: ui-monospace, "SF Mono", SFMono-Regular, Menlo, Consolas, monospace;
  --ground: #fff; --ink: #0d0d0d; --muted: #5f5f5f;
  --accent: #de301e; --fill: #de301e1f; --rule: 2px;
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

footer { display: flex; justify-content: space-between;
         font: 400 10px var(--mono); letter-spacing: 0.1em; color: var(--muted);
         padding: 10px 16px; border: var(--rule) solid var(--ink); text-transform: uppercase; }

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
.bar:first-of-type s { background: var(--accent); }
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

.legend { display: flex; gap: 16px; font: 400 11px var(--mono);
          color: var(--muted); margin-top: 12px; flex-wrap: wrap; }
.key { display: inline-block; width: 22px; height: 11px; margin-right: 5px;
       vertical-align: -1px; }
.k-filler { background: #ececec; box-shadow: inset 0 -3px 0 var(--accent); }
.k-blob { background: var(--fill); }
.k-code { background: #ececec; }

/* the source, one block per line so a flagged unit shades over its whole span */
h3.file { font: 700 11px/1 var(--mono); letter-spacing: 0.1em; text-transform: uppercase;
          margin: 22px 0 8px; padding: 7px 0; color: var(--ink);
          border-bottom: var(--rule) solid var(--ink); position: sticky; top: 0;
          background: var(--ground); z-index: 1; }
h3.file:first-of-type { margin-top: 0; }
pre { margin: 0; font: 400 13px/1.65 var(--mono); white-space: pre-wrap;
      word-wrap: break-word; }
.l { display: block; padding: 0 6px; border-left: var(--rule) solid transparent; }
.l:empty { height: 1.65em; }
.l.blob { background: var(--fill); border-left-color: var(--accent); }
.l.code { background: #f4f4f4; border-left-color: #9a9a9a; }
mark { background: #ececec; color: inherit; padding: 0 1px; cursor: pointer;
       box-shadow: inset 0 -3px 0 var(--accent); }
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
  var goto = e.target.closest('[data-goto]');
  if (goto) {
    var line = document.getElementById(goto.dataset.goto);
    if (line) line.scrollIntoView({block: 'center', behavior: 'smooth'});
    return;
  }
  var el = e.target.closest('[data-term]');
  if (el) choose(el.dataset.term);
  else if (sel) choose(sel);
});
document.addEventListener('keydown', function (e) {
  if (e.key === 'Escape' && sel) choose(sel);
  else if (e.key === '/' && document.activeElement !== box) { e.preventDefault(); box.focus(); }
});
var box = document.getElementById('find');
box.addEventListener('input', function () {
  var q = box.value.trim().toLowerCase();
  document.querySelectorAll('tr.pick').forEach(function (tr) {
    tr.classList.toggle('gone', q !== '' && tr.dataset.term.indexOf(q) === -1);
  });
});
box.addEventListener('click', function (e) { e.stopPropagation(); });
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
    """
    if vs.yaml is None:
        return "PyYAML"
    try:
        # lint() prints its own install hint on the way out; the CLI's stdout is
        # the report path alone, so the hint is swallowed and restated in the cell.
        with contextlib.redirect_stdout(io.StringIO()):
            return vs.lint(Path(skill_dir))
    except (SystemExit, ImportError):
        return "skills-ref"


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
    # Ties break on iteration order, matching how _budget picks its driver file,
    # so the page and the text report never name different references.
    refs = [(name, n) for name, n in sized.items() if name != "SKILL.md"]
    biggest = max(refs, key=lambda kv: kv[1], default=("", 0))
    detail = ("SKILL.md %d + largest reference %s %d" % (main, biggest[0], biggest[1])
              if biggest[0] else "SKILL.md %d, no referenced files" % main)
    # A skill inside a justified ceiling passes the validator's gate, so the band
    # is set in the passing treatment rather than contradicting its own note.
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
    rows = "".join('<div class="bar"><u>%s</u><s style="width:%.1f%%"></s><em>%d</em></div>'
                   % (e(name), 100.0 * n / top, n) for name, n in sized.items())
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


def structure_block(pct, blobs, long_code, index_of):
    """Findings addressed by line span rather than by term: blobs and code fences.

    Both live here because neither is a term to rank in the frequency list, and
    each row carries the anchor of the line it starts on so it can be jumped to.
    """
    def rows_for(group, unit):
        return "".join(
            '<tr class="pick" data-goto="%s"><td class="n">%d%s</td><td>%s</td>'
            '<td class="r">%s:%d</td></tr>'
            % (anchor(index_of.get(str(rel), 0), start), size, unit,
               e(" ".join(opening.split()[:9])), e(rel), start)
            for size, rel, start, _end, opening in group)

    rows = rows_for(blobs, "w") + rows_for(long_code, "L")
    head = '<div class="rate">%s of body words in paragraph prose</div>' % (
        "%d%%" % pct if pct is not None else "no body text")
    if not rows:
        return head + ('<p class="empty">No text unit at or over %d words, no code block '
                       'over %d lines.</p>' % (vs.BLOB_WORDS, vs.CODE_FENCE_LINES))
    return head + '<h2 class="sub">Units to compress</h2><table>%s</table>' % rows


def tally(filler):
    """{term: (category, count)}, one entry per term rather than per hit."""
    terms = {}
    for category, _rel, _line, hit in filler:
        key = term_key(hit)
        seen, count = terms.get(key, (category, 0))
        terms[key] = (seen, count + 1)
    return terms


def findings_block(filler):
    """Ranked frequency, one row per term: a word is cut everywhere at once.

    The bar is drawn in the row it labels rather than as a chart beside it. Two
    views of the same counts would be the duplication the primer objects to.
    """
    if not filler:
        return ('<input id="find" hidden><p class="empty">No lexical no-ops found.</p>')
    ranked = sorted(tally(filler).items(), key=lambda kv: (-kv[1][1], kv[0]))
    top = ranked[0][1][1]
    rows = "".join('<tr class="pick" data-term="%s"><td class="n">%d</td>'
                   '<td class="f"><s style="width:%.1f%%"></s></td>'
                   '<td>%s</td><td class="r">%s</td></tr>'
                   % (e(term), count, 100.0 * count / top, e(term), e(category))
                   for term, (category, count) in ranked)
    legend = "".join('<span><i class="key k-%s"></i>%s</span>' % (k, e(d)) for k, d in LEGEND)
    return ('<input id="find" placeholder="Search for a term..." autocomplete="off">'
            '<div class="scroll"><table>%s</table></div><div class="legend">%s</div>'
            % (rows, legend))


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
        _pct, skill_blobs, ref_blobs, long_code = vs._structure(Path(target))
        return {
            "load": worst_case_load(sized),
            "skill": sized.get("SKILL.md", 0),
            "blobs": len(skill_blobs) + len(ref_blobs),
            "code": len(long_code),
            "filler": len(vs._filler(Path(target))),
        }

    was, now = measure(baseline), measure(skill_dir)
    out = [_pair("worst-case load", was["load"], now["load"]),
           _pair("SKILL.md tokens", was["skill"], now["skill"])]
    for key, label in (("blobs", "blobs"), ("code", "long code blocks"), ("filler", "lexical no-ops")):
        if was[key] or now[key]:
            out.append(_pair(label, was[key], now[key]))
    return "".join(out)


def marked_source(skill_dir, blobs, long_code, filler):
    """Every loadable file, one block per line, flagged spans marked in place."""
    spans = {}
    for kind, group in (("blob", blobs), ("code", long_code)):
        for _size, rel, start, end, _opening in group:
            for n in range(start, end + 1):
                spans.setdefault((str(rel), n), kind)
    # Only lines the detector reported are re-scanned for spans, so the page can
    # never mark a line the text report left out.
    flagged = {(str(rel), lineno) for _category, rel, lineno, _hit in filler}

    out = []
    for index, (rel, path) in enumerate(loadable_files(skill_dir)):
        out.append('<h3 class="file">%s</h3><pre>' % e(rel))
        text = path.read_text(encoding="utf-8-sig", errors="ignore")
        for lineno, line in enumerate(text.splitlines(), start=1):
            marked = mark_line(line) if (rel, lineno) in flagged else e(line)
            out.append('<span class="l %s" id="%s">%s</span>'
                       % (spans.get((rel, lineno), ""), anchor(index, lineno), marked))
        out.append("</pre>")
    return "".join(out)


def filler_spans(line):
    """(start, end, term) for every lexical no-op on one raw source line.

    Runs the detector's own rules over the text the detector scanned, via its
    _filler_scan, then maps each match back onto the raw line. Marking by offset
    rather than by searching for the matched text is what keeps the page from
    flagging an occurrence the detector excluded: a word inside backticks, or a
    sentence-initial rule matching mid-sentence.
    """
    lead = len(line) - len(line.lstrip())
    scan = vs._filler_scan(line)
    found = []
    for _category, pattern in vs._FILLER_RULES:
        for hit in pattern.finditer(scan):
            raw = hit.group(0)
            at = lead + hit.start()
            found.append((at + len(raw) - len(raw.lstrip()), at + len(raw.rstrip()), raw.strip()))
    return sorted(found)


def mark_line(line):
    """Escape one source line, wrapping each span the detector flagged on it.

    Two rules matching overlapping text share one mark, which carries both terms
    so either row in the frequency table still has something to highlight. A row
    with no mark to reach would fade the whole document and select nothing.
    """
    spans = filler_spans(line)
    if not spans:
        return e(line)
    kept = []
    for start, end, term in spans:
        if kept and start < kept[-1][1]:
            kept[-1][2].append(term)
        else:
            kept.append([start, end, [term]])
    out, at = [], 0
    for start, end, terms in kept:
        out.append(e(line[at:start]))
        out.append('<mark data-term="%s">%s</mark>'
                   % (e("|".join(term_key(t) for t in terms)), e(line[start:end])))
        at = end
    out.append(e(line[at:]))
    return "".join(out)


def render(skill_dir, against=None, use_tiktoken=False):
    skill_dir = Path(skill_dir).resolve()
    sized = per_file_tokens(skill_dir, use_tiktoken)
    load = worst_case_load(sized)
    pct, skill_blobs, ref_blobs, long_code = vs._structure(skill_dir)
    blobs = sorted(skill_blobs + ref_blobs, reverse=True)
    filler = vs._filler(skill_dir)
    index_of = {rel: i for i, (rel, _path) in enumerate(loadable_files(skill_dir))}
    _lines, _rating, advice, _driver, within_budget = vs._budget(skill_dir, use_tiktoken)
    ceiling, _justified = vs.declared_token_budget(
        (skill_dir / "SKILL.md").read_text(encoding="utf-8-sig", errors="ignore"))

    extra = ""
    if against is not None:
        extra = ('<section class="cell"><h2>Before and after</h2>%s</section>'
                 % compare_block(against, skill_dir, use_tiktoken))

    strip = "".join(
        '<div><i style="background:%s"></i><b>%s</b><u>%s</u></div>' % (colour, e(n), e(label))
        for colour, n, label in (
            ("#de301e", "%d" % load, "worst-case load"),
            ("#1a4fa0", "%d" % len(sized), "files that load"),
            ("#e8b400", "%d" % (len(blobs) + len(long_code) + len(filler)), "findings"),
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
    <section class="cell grow"><h2>Lexical no-ops by frequency</h2>%(findings)s</section>
  </div>
  <section class="cell doc"><h2>The skill</h2>%(source)s</section>
  <footer><span>generated %(when)s</span><span>skill-creator-primer</span></footer>
</div>
<script>%(js)s</script>
""" % {
        "name": e(skill_dir.name),
        "css": CSS, "js": JS,
        "strip": strip,
        "when": datetime.datetime.now().astimezone().date().isoformat(),
        "verdict": verdict(load, sized, advice, ceiling, within_budget),
        "files": files_block(sized),
        "spec": spec_block(spec_findings(skill_dir)),
        "structure": structure_block(pct, blobs, long_code, index_of),
        "findings": findings_block(filler),
        "extra": extra,
        "source": marked_source(skill_dir, blobs, long_code, filler),
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
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(skill_dir, args.against, args.tiktoken), encoding="utf-8")
    print(out.resolve())


if __name__ == "__main__":
    main()
