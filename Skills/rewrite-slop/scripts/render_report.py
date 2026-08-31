#!/usr/bin/env python3
"""Render one input's check_output findings as a single self-contained HTML page.

Optional. Nothing in the rewrite phases calls this; it exists for reading a long
input, or for showing someone else what was flagged and where.

The board is the one at louisabraham.github.io/load-bearing, borrowed for its
interaction rather than its content: that page charts a corpus over twenty
months, which a single document has no axis for. What carries over is clicking a
term to hold it selected while everything else responds, and light-only Bauhaus
because a dark ground would invert the premise.

    python3 render_report.py FILE [--against ORIG] [-o OUT]
"""

import argparse
import datetime
import html
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import check_output as co

SEVERITY: dict[str, str] = {}
for _rules, _sev in ((co.SAFE, "safe"), (co.REVIEW, "review"), (co.REPORT, "report")):
    for _rule in _rules:
        SEVERITY.setdefault(_rule[0], _sev)

# What each severity means in the rubric, since the page is read away from it.
LEGEND = [
    ("safe", "applied by --write"),
    ("review", "swapped, but read the line"),
    ("report", "detected only, you decide"),
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

/* The panel beside the document, not above it: a term is clicked in the findings
   and read in the text, and a stacked board put the two an entire screen apart.
   Each column scrolls on its own so neither scrolls the other away. */
.board { display: grid; grid-template-columns: minmax(340px, 32%) 1fr;
         grid-template-rows: auto minmax(0, 1fr) auto;
         gap: var(--rule); padding: var(--rule); height: 100vh; }
.cell { border: var(--rule) solid var(--ink); padding: 14px 16px; min-width: 0; }
/* The panel does not scroll; the findings cell inside it takes the slack and
   scrolls, so each column shows exactly one scrollbar and the register stays put. */
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

/* the verdict, set at the size of the finding it is */
.band { font: 700 46px/1 var(--grotesk); letter-spacing: -0.02em; }
.band.heavy, .band.elevated { color: var(--accent); }
.rate { font: 400 13px var(--mono); color: var(--muted); margin-top: 6px; }
.gauge { position: relative; height: 22px; border: var(--rule) solid var(--ink); margin-top: 14px; }
.gauge i { position: absolute; inset: 0 auto 0 0; background: var(--accent); }
.gauge b { position: absolute; top: -2px; bottom: -2px; width: var(--rule); background: var(--ink); }
.ticks { display: flex; justify-content: space-between;
         font: 400 11px var(--mono); color: var(--muted); margin-top: 4px; }

/* group bars: one grey ramp, the accent reserved for the group that leads */
.bar { display: grid; grid-template-columns: 108px 1fr 34px; align-items: center;
       gap: 8px; margin-bottom: 7px; font: 400 12px var(--mono); }
.bar u { text-decoration: none; color: var(--muted); }
.bar s { text-decoration: none; height: 13px; background: #d4d4d4; display: block; }
.bar:first-of-type s { background: var(--accent); }
.bar em { font-style: normal; text-align: right; color: var(--muted); }

table { border-collapse: collapse; width: 100%; font: 400 13px var(--mono); }
td { padding: 3px 6px 3px 0; vertical-align: top; border-bottom: 1px solid #ececec; }
td.n { width: 34px; color: var(--muted); text-align: right; }
td.r { color: var(--muted); text-align: right; white-space: nowrap; }
tr.pick { cursor: pointer; }
tr.pick:hover td { background: var(--fill); }
.scroll { flex: 1; min-height: 90px; overflow: auto; }

/* the frequency chart, drawn behind the rows it labels rather than beside them */
td.f { width: 40%; }
td.f s { display: block; height: 11px; background: #d4d4d4; text-decoration: none; }
tr.pick:first-child td.f s { background: var(--accent); }

/* before and after: two bars to a pair, the original hollow and the rewrite filled */
.pair { margin-bottom: 12px; font: 400 12px var(--mono); }
.pair u { text-decoration: none; color: var(--muted); }
.pair div { display: grid; grid-template-columns: 1fr 76px; align-items: center;
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
.k-safe { background: #ececec; }
.k-review { background: #ececec; box-shadow: inset 0 -3px 0 #9a9a9a; }
.k-report { background: var(--fill); box-shadow: inset 0 -3px 0 var(--accent); }

pre { margin: 0; font: 400 13px/1.65 var(--mono); white-space: pre-wrap;
      word-wrap: break-word; }
mark { background: #ececec; color: inherit; padding: 0 1px; cursor: pointer; }
mark[data-sev="review"] { box-shadow: inset 0 -3px 0 #9a9a9a; }
mark[data-sev="report"] { background: var(--fill); box-shadow: inset 0 -3px 0 var(--accent); }
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
  document.querySelectorAll('[data-term]').forEach(function (el) {
    el.classList.toggle('on', sel !== null && el.dataset.term === sel);
  });
  if (sel) {
    var first = document.querySelector('mark.on');
    if (first) first.scrollIntoView({block: 'center', behavior: 'smooth'});
  }
}
document.addEventListener('click', function (e) {
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


def marked(text, spans):
    """The input with every flagged span wrapped, escaped around the marks."""
    out, at = [], 0
    for start, end, name, hit in spans:
        out.append(e(text[at:start]))
        out.append('<mark data-sev="%s" data-term="%s" title="%s">%s</mark>'
                   % (SEVERITY.get(name, "report"), e(hit.lower()), e(name), e(text[start:end])))
        at = end
    out.append(e(text[at:]))
    return "".join(out)


def gauge(rate):
    """Position on the calibrated scale, topped out at twice HEAVY."""
    full = co.HEAVY * 2
    pct = min(100.0, 100.0 * rate / full)
    return ('<div class="gauge"><i style="width:%.1f%%"></i>'
            '<b style="left:%.1f%%"></b><b style="left:%.1f%%"></b></div>'
            '<div class="ticks"><span>0</span><span>%g elevated</span>'
            '<span>%g heavy</span><span>%g</span></div>'
            % (pct, 100.0 * co.ELEVATED / full, 100.0 * co.HEAVY / full,
               co.ELEVATED, co.HEAVY, full))


def verdict(stats, nwords):
    if not stats:
        return ('<div class="band">CLEAN</div><div class="rate">'
                'under %.1f/1000, or fewer than %d markers, or under %d words</div>%s'
                % (co.ELEVATED, co.LEAST, co.SHORT, gauge(0)))
    return ('<div class="band %s">%s</div><div class="rate">%.1f per 1000 words, '
            '%d markers over %d</div>%s'
            % (stats["band"].lower(), stats["band"], stats["rate"],
               stats["total"], nwords, gauge(stats["rate"])))


def groups_block(stats):
    """Bars under the verdict. Silent when clean: the verdict already said so."""
    if not stats:
        return ""
    top = max(sum(n for _, n in pairs) for _, pairs in stats["groups"])
    rows = []
    for group, pairs in stats["groups"]:
        n = sum(c for _, c in pairs)
        rows.append('<div class="bar"><u>%s</u><s style="width:%.1f%%"></s><em>%d</em></div>'
                    % (e(group), 100.0 * n / top, n))
    return '<h2 class="sub">By group</h2>%s' % "".join(rows)


def tally(spans):
    """{term: (rule name, count)}, one entry per term rather than per hit."""
    terms = {}
    for _, _, name, hit in spans:
        key = hit.lower()
        seen, count = terms.get(key, (name, 0))
        terms[key] = (seen, count + 1)
    return terms


def findings_block(spans):
    """Ranked frequency, one row per term: a word is fixed everywhere at once.

    The bar is drawn in the row it labels rather than as a chart beside it. Two
    views of the same counts would be the duplication this skill objects to.
    """
    if not spans:
        return '<p class="empty">Nothing flagged.</p>'
    terms = tally(spans)
    ranked = sorted(terms.items(), key=lambda kv: (-kv[1][1], kv[0]))
    top = ranked[0][1][1]
    rows = []
    for term, (name, count) in ranked:
        rows.append('<tr class="pick" data-term="%s"><td class="n">%d</td>'
                    '<td class="f"><s style="width:%.1f%%"></s></td>'
                    '<td>%s</td><td class="r">%s</td></tr>'
                    % (e(term), count, 100.0 * count / top, e(term), e(name)))
    legend = "".join('<span><i class="key k-%s"></i>%s</span>' % (s, e(d)) for s, d in LEGEND)
    return ('<input id="find" placeholder="Search for a term..." autocomplete="off">'
            '<div class="scroll"><table>%s</table></div><div class="legend">%s</div>'
            % ("".join(rows), legend))


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


def compare_block(orig, new):
    """Before and after, per severity and per length."""
    before = tally(co.scan_spans(orig, co.SAFE, co.REVIEW, co.REPORT))
    after = tally(co.scan_spans(new, co.SAFE, co.REVIEW, co.REPORT))

    def by_sev(terms, sev):
        return sum(n for name, n in terms.values() if SEVERITY.get(name) == sev)

    out = [_pair("words", len(orig.split()), len(new.split()))]
    for sev, _ in LEGEND:
        was, now = by_sev(before, sev), by_sev(after, sev)
        if was or now:
            out.append(_pair(sev + " hits", was, now))
    ob, nb = co.register_stats(orig), co.register_stats(new)
    if ob or nb:
        out.append(_pair("register per 1000", round(ob["rate"] if ob else 0),
                         round(nb["rate"] if nb else 0)))
    return "".join(out)


def structure_block(text):
    """Findings addressed by line rather than by span: line_checks and blobs.

    Both live here because neither has a span to mark in the text, and leaving
    line_checks off the page would make it disagree with the text report.
    """
    rows = ['<tr><td class="n">%dw</td><td>%s</td><td class="r">L%d</td></tr>'
            % (words, e(opening), line) for words, line, opening in co.blobs(text)]
    rows += ['<tr><td class="n"></td><td>%s</td><td class="r">L%d</td></tr>'
             % (e(name), line) for line, name in co.line_checks(text)]
    if not rows:
        return ('<p class="empty">No paragraph at or over %d words, nothing at line level.</p>'
                % co.BLOB_WORDS)
    return "<table>%s</table>" % "".join(rows)


def render(path, text, against=None):
    spans = co.scan_spans(text, co.SAFE, co.REVIEW, co.REPORT)
    stats = co.register_stats(text)
    nwords = len(text.split())

    extra = ""
    if against is not None:
        extra = ('<section class="cell w12"><h2>Before and after</h2>%s</section>'
                 % compare_block(against, text))

    strip = "".join(
        '<div><i style="background:%s"></i><b>%s</b><u>%s</u></div>' % (colour, e(n), e(label))
        for colour, n, label in (
            ("#de301e", "%d" % nwords, "words"),
            ("#1a4fa0", "%d" % len(spans), "flagged spans"),
            ("#e8b400", "%d" % len({h.lower() for *_, h in spans}), "distinct terms"),
        ))

    return """<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>slop report: %(name)s</title>
<style>%(css)s</style>
<div class="board">
  <header class="cell">
    <h1>The <span>slop</span> in %(name)s</h1>
    <div class="stats">%(strip)s</div>
  </header>
  <div class="panel">
    <section class="cell"><h2>Register</h2>%(verdict)s%(groups)s</section>
    %(extra)s
    <section class="cell"><h2>Structure</h2>%(paras)s</section>
    <section class="cell grow"><h2>Findings by frequency</h2>%(findings)s</section>
  </div>
  <section class="cell doc"><h2>The text</h2><pre>%(text)s</pre></section>
  <footer><span>generated %(when)s</span><span>rewrite-slop</span></footer>
</div>
<script>%(js)s</script>
""" % {
        "name": e(os.path.basename(path)),
        "css": CSS, "js": JS,
        "strip": strip,
        "when": datetime.datetime.now().astimezone().date().isoformat(),
        "verdict": verdict(stats, nwords),
        "groups": groups_block(stats),
        "findings": findings_block(spans),
        "paras": structure_block(text),
        "extra": extra,
        "text": marked(text, spans),
    }


def main():
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("file")
    ap.add_argument("--against", metavar="ORIG", help="original file, for the length comparison")
    ap.add_argument("-o", "--out", help="output path (default: alongside the input)")
    args = ap.parse_args()

    with open(args.file, encoding="utf-8") as fh:
        text = fh.read()
    against = None
    if args.against:
        with open(args.against, encoding="utf-8") as fh:
            against = fh.read()

    out = args.out or os.path.splitext(args.file)[0] + ".slop-report.html"
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(render(args.file, text, against))
    print(out)


if __name__ == "__main__":
    main()
