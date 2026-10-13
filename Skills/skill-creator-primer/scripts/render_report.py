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

The verdict reads its levels from assess(), one branch per finding kind. A new kind needs a branch there, or it shows
on the page and never moves the verdict.

Three checks after a change, all of them past what a browser screenshot shows:

- Every mark key (marks carry one per finding, joined by |) is matched by one
  lexical no-op or one counted bold span for the same skill.
- Every tag closes, and the shaded line ranges match the text report's numbers.
- Each cell sits in a single grid column; the panel stacks its cells with flex.
"""

import argparse
import datetime
import html
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import validate_skill as vs  # pyright: ignore[reportMissingImports]
from report_assets import CSS, JS  # pyright: ignore[reportMissingImports]
from report_model import (  # pyright: ignore[reportMissingImports]
    BLOCK_LABEL,
    BLOCK_RULE,
    CELLS,
    LEVELS,
    RANK,
    SPEC_SKIPPED,
    VERDICT_REASONS,
    WHY,
    anchor,
    assess,
    brief,
    collect,
    confidence,
    desc_kind,
    load_agent_findings,
    loadable_files,
    overall,
    per_file_tokens,
    spec_findings,
    spec_rows,
    term_key,
    why_for,
    worst_case_load,
    wrapped_by_file,
)

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
]


def e(s):
    return html.escape(str(s), quote=True)


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


def verdict_block(issues, agent_run, spec_skipped):
    """The one rating that judges every cell, the issues it rests on, and each cell's own standing."""
    level = overall(issues)
    word, step, _ = LEVELS[level]
    top = [i for i in issues if i.level == level]
    if level == "judge":
        why = ('<div class="rate">%d to judge, none blocking</div>' % len(top) if top
               else '<div class="rate">nothing flagged</div>')
    else:
        why = '<ul class="reasons">%s%s</ul>' % (
            "".join("<li><b>%s</b> %s</li>" % (e(i.cell), e(i.text)) for i in top[:VERDICT_REASONS]),
            "<li>and %d more</li>" % (len(top) - VERDICT_REASONS) if len(top) > VERDICT_REASONS else "")
    if spec_skipped:
        why += '<div class="note">Spec checks did not run here. Re-run under uv run before trusting a pass.</div>'
    chips = []
    for cell in CELLS:
        if cell == "agent" and not agent_run:
            continue
        mine = [i for i in issues if i.cell == cell]
        fix = sum(1 for i in mine if i.level != "judge")
        counts = ", ".join(x for x in ("%d to fix" % fix if fix else "",
                                       "%d to judge" % (len(mine) - fix) if len(mine) > fix else "") if x)
        cword, cstep, _ = LEVELS[overall(mine)]
        chips.append('<div class="%s"><b>%s</b><u>%s</u><em>%s</em></div>'
                     % (cstep, cword, cell, counts or "clean"))
    count = (' <small>with %d finding%s</small>' % (len(top), "" if len(top) == 1 else "s")
             if level == "fail" else "")
    return ('<div class="verdict %s">%s%s</div>%s<div class="score">%s</div>'
            % (step, word, count, why, "".join(chips)))


def budget_block(load, sized, advice, ceiling, within_budget):
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
    out = ['<div class="rate"><span class="band %s">%s</span> %s tokens worst-case load: %s</div>'
           % (tone, e(rating), load, e(detail)),
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


# One character each, since the count column is fixed-width: a longer suffix wrapped and doubled the row height.
# L lines, w words, c prose cells. The row's own text and the caption say which is which.
UNIT_SUFFIX = {"code": "L", "redundant": "L", "desc": "w", "descw": "w", "table": "c", "wrap": "L"}


def block_rows(found):
    """{(kind, "path:line"): row id} over the block findings, in listed order.

    The one key both directions of the jump agree on: the row carries the id and
    the shaded lines carry it back, so clicking a block in the source lands on the
    row that explains it without either side recomputing the other's ordering.
    """
    # Keyed off `goto`, not the kind: a spec finding has no span, and several of them share an empty `where` that
    # would collapse into one id and put the same anchor on every row.
    return {(f.kind, f.where): "R%d" % i
            for i, f in enumerate(x for x in found if x.kind in BLOCK_RULE and x.goto)}


def _span_row(f, rows):
    # A spec finding has no line to jump to and no measure to print: its count cell carries the severity mark and its
    # row is not clickable, so a click cannot land nowhere.
    count = ("%d%s" % (f.size, UNIT_SUFFIX.get(f.kind, "w")) if f.size
             else ("!" if f.kind == "spec" else "?"))
    goto = ' data-goto="%s"' % f.goto if f.goto else ""
    row_id = rows.get((f.kind, f.where), "")
    # The confidence class, not the kind: the row is ranked and coloured by its step on the ramp, and it is the same
    # class the frequency table below uses, so one set of rules colours both lists.
    return ('<tr class="pick %s %s"%s%s data-rule="%s" data-why="%s" title="%s">'
            '<td class="n">%s</td><td>%s</td><td class="r">%s</td></tr>'
            % (f.kind, f.conf,
               ' id="%s"' % row_id if row_id else "", goto,
               e(BLOCK_RULE.get(f.kind, f.rule)), e(f.why), e(f.why),
               count, e(f.what), e(f.where)))


def structure_block(pct, found, rows):
    """Every finding that names a place rather than a word, in one list, worst
    first.

    One list, not one per kind. Splitting it into headed groups spent two rows on
    saying what the colour already says, and the reader who wants the worst thing
    on the page had to compare across the groups to find it. The rank is the
    confidence ramp - certain, then probable, then possible - so the top row is
    always the one to fix first, whatever kind it happens to be.
    """
    ranked = sorted((f for f in found if f.kind in BLOCK_RULE),
                    key=lambda f: RANK[f.conf or "probable"])  # sorted() is stable: ties keep collect()'s order
    head = '<div class="rate">%s of body words in paragraph prose</div>' % (
        "%d%%" % pct if pct is not None else "no body text")
    if not ranked:
        return head + ('<p class="empty">No text unit at or over %d words, no dense run, no code '
                       'block over %d lines.</p>' % (vs.BLOB_WORDS, vs.CODE_FENCE_LINES))
    return (head + '<div class="scroll"><table>%s</table></div>'
            % "".join(_span_row(f, rows) for f in ranked))


def findings_block(found):
    """Ranked frequency, one row per term: a word is cut everywhere at once.

    The bar is drawn in the row it labels rather than as a chart beside it. Two
    views of the same counts would be the duplication the primer objects to.
    """
    terms = [f for f in found if f.kind == "filler"]
    emphasis = [f for f in found if f.kind == "em"]
    if not terms and not emphasis:
        return ('<p id="why" class="why" hidden></p>'
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
    return (            '<div class="scroll"><table>%s</table></div>'
            '<div class="foot" id="foot"><p id="why" class="why"></p>'
            '<div class="legend">%s</div></div>'
            % (rows, legend))


def goto_for(where, index_of):
    """The anchor an agent finding's path:line lands on, or "" when it names no loadable line."""
    rel, _, line = where.partition(":")
    return anchor(index_of[rel], int(line)) if rel in index_of and line.isdigit() else ""


def agent_block(agent, index_of):
    """The reviewing agent's findings, worst grade first, each row jumping to the line it names."""
    if not agent:
        return '<p class="empty">The agent passed no findings.</p>'
    rows = []
    for a in sorted(agent, key=lambda a: RANK[a.conf]):
        goto = goto_for(a.where, index_of)
        note = "".join(x for x in ("<b>%s</b> " % e(a.cite) if a.cite else "", e(a.fix)) if x)
        rows.append('<tr class="pick agent %s"%s><td class="n">%s</td><td>%s%s</td><td class="r">%s</td></tr>'
                    % (a.conf, ' data-goto="%s"' % goto if goto else "", e(a.grade), e(a.finding),
                       "<small>%s</small>" % note if note else "", e(a.where)))
    return '<div class="scroll"><table>%s</table></div>' % "".join(rows)


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
        _pct, skill_blobs, ref_blobs, long_code, dense, _wrapped = vs._structure(Path(target))
        return {
            "load": worst_case_load(sized),
            "skill": sized.get("SKILL.md", 0),
            "blobs": len(skill_blobs) + len(ref_blobs),
            "dense": len(dense),
            "code": len(long_code),
            "filler": len(vs._filler(Path(target))),
            "when": len(vs._redundant_sections(Path(target))),
            "tables": len(vs._prose_tables(Path(target))),
        }

    was, now = measure(baseline), measure(skill_dir)
    out = [_pair("worst-case load", was["load"], now["load"]),
           _pair("SKILL.md tokens", was["skill"], now["skill"])]
    for key, label in (("when", '"when to use" sections'), ("blobs", "blobs"),
                       ("dense", "dense runs"), ("tables", "prose tables"),
                       ("code", "long code blocks"), ("filler", "lexical no-ops")):
        if was[key] or now[key]:
            out.append(_pair(label, was[key], now[key]))
    return "".join(out)


def marked_source(skill_dir, blobs, long_code, filler, emphasis=None, dense=(), invisible=(),
                  redundant=(), desc_span=None, tables=(), desc_words=0, rows=None, wrapped=()):
    """Every loadable file, one block per line, flagged spans marked in place."""
    spans = {}
    labels = {}
    back = {}  # (rel, line) -> the id of the row that explains this block
    rows = rows or {}
    if desc_span:
        kind = desc_kind(desc_words)
        for n in range(desc_span[0], desc_span[1] + 1):
            spans[("SKILL.md", n)] = kind
            back.setdefault(("SKILL.md", n), rows.get((kind, "SKILL.md:%d" % desc_span[0]), ""))
        labels[("SKILL.md", desc_span[0])] = BLOCK_LABEL[kind] % desc_words
    # First writer wins the line. A "When to use" section leads, because the whole span is going and a blob marked
    # inside it would offer to compress text that should not be there at all; blobs then lead dense runs, so a blob
    # inside a run keeps its own deeper shade.
    for kind, group in (("redundant", redundant), ("blob", blobs), ("code", long_code),
                        ("table", tables), ("dense", dense)):
        for size, rel, start, end, _opening, *rest in group:
            row = rows.get((kind, "%s:%d" % (rel, start)), "")
            for n in range(start, end + 1):
                if spans.setdefault((str(rel), n), kind) == kind:
                    back.setdefault((str(rel), n), row)
            # A dense run's own measure is its unit count, which trails the tuple; every other kind measures by size.
            measure = rest[0] if kind == "dense" and rest else size
            labels.setdefault((str(rel), start), BLOCK_LABEL[kind] % measure)
    # Last, so any other block over the same lines keeps its shade. Every unit jumps back to its file's one row.
    for rel, group in wrapped_by_file(wrapped).items():
        row = rows.get(("wrap", "%s:%d" % (rel, group[0][2])), "")
        for size, _rel, start, end, _opening in group:
            for n in range(start, end + 1):
                if spans.setdefault((rel, n), "wrap") == "wrap":
                    back.setdefault((rel, n), row)
            labels.setdefault((rel, start), BLOCK_LABEL["wrap"] % size)
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
            # A shaded line names the rule before its reason, so hovering or clicking the block answers "which rule"
            # as well as "why" - the rule name is what the reader carries back to the primer.
            why = (' data-why="%s"' % e("%s: %s" % (BLOCK_RULE[kind], WHY[BLOCK_RULE[kind]]))
                   if kind else "")
            if kind:
                conf = "probable" if kind == "descw" else confidence(BLOCK_RULE[kind])
                why += ' data-head="%s" data-conf="%s"' % (BLOCK_RULE[kind], conf)
            label = labels.get((rel, lineno)) if kind else None
            row = back.get((rel, lineno)) if kind else None
            out.append('<span class="l %s%s" id="%s"%s%s%s>%s</span>'
                       % (kind, " lead" if label else "", anchor(index, lineno), why,
                          ' data-label="%s"' % e(label) if label else "",
                          ' data-back="%s"' % e(row) if row else "", marked))
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
            conf = min((confidence(r) for r in rules if r != "bold-emphasis"), key=RANK.__getitem__)
            cls = "inv" if all(r == "invisible" for r in rules) else ""
        # Each invisible character shows as its code point and every other character as itself, so a no-break space
        # inside a bold phrase does not turn the whole phrase into hex. A leading BOM is an empty span; its term
        # carries the code point to show.
        shown = "".join("U+%04X" % ord(c) if vs._INVISIBLE.match(c) else e(c) for c in line[start:end])
        if start == end:
            shown = e(terms[0].split()[0])
        out.append(e(line[at:start]))
        out.append('<mark class="%s" data-conf="%s" data-term="%s" data-why="%s" data-head="%s">%s</mark>'
                   % (cls, conf, e("|".join(term_key(t) for t in terms)), e(why),
                      e(" + ".join(dict.fromkeys(rules))), shown))
        at = end
    out.append(e(line[at:]))
    return "".join(out)


def render(skill_dir, against=None, use_tiktoken=False, agent=None):
    skill_dir = Path(skill_dir).resolve()
    sized = per_file_tokens(skill_dir, use_tiktoken)
    load = worst_case_load(sized)
    pct, skill_blobs, ref_blobs, long_code, dense, wrapped = vs._structure(skill_dir)
    blobs = sorted(skill_blobs + ref_blobs, reverse=True)
    filler = vs._filler(skill_dir)
    emphasis = vs._bold(skill_dir)
    invisible = vs._invisible(skill_dir)
    redundant = vs._redundant_sections(skill_dir)
    tables = vs._prose_tables(skill_dir)
    # (words, (first line, last line), (threshold, what the threshold is called)) or None when the description is
    # inside its ceiling. Reported from the raw source lines so the page can shade the description it is judging.
    description = None
    desc_words = vs.description_word_count(vs.skill_description(skill_dir))
    desc_span = vs.description_span(skill_dir)
    if desc_span and desc_words > vs.DESCRIPTION_WORDS_WARN:
        over = ((vs.DESCRIPTION_WORDS_FAIL, "hard cap") if desc_words > vs.DESCRIPTION_WORDS_FAIL
                else (vs.DESCRIPTION_WORDS_WARN, "ceiling"))
        description = (desc_words, desc_span, over)
    # Invisible characters join the term list in the filler's shape, so they tally, rank and brief like any term;
    # their marks are placed from the spans, as bold's are.
    hits = filler + [("invisible", rel, lineno, name) for rel, lineno, _s, _e, name in invisible]
    index_of = {rel: i for i, (rel, _path) in enumerate(loadable_files(skill_dir))}
    _lines, rating, advice, driver_is_main, within_budget = vs._budget(skill_dir, use_tiktoken)
    ceiling, _justified = vs.declared_token_budget(
        (skill_dir / "SKILL.md").read_text(encoding="utf-8-sig", errors="ignore"))
    spec = spec_findings(skill_dir)
    found = spec_rows(spec, skill_dir) + collect(
        blobs, long_code, hits, index_of, emphasis, dense, redundant, description, tables, wrapped)
    rows = block_rows(found)
    words = sum(len(path.read_text(encoding="utf-8-sig", errors="ignore").split())
                for _rel, path in loadable_files(skill_dir))
    issues = assess((rating, driver_is_main, within_budget, load), found, agent, emphasis, words)
    spec_skipped = isinstance(spec, str) or any(w.startswith(SPEC_SKIPPED) for w in spec[1])

    extra = ""
    if agent is not None:
        extra += ('<section class="cell grow"><h2>Agent findings</h2>%s</section>'
                  % agent_block(agent, index_of))
    if against is not None:
        extra += ('<section class="cell"><h2>Before and after</h2>%s</section>'
                 % compare_block(against, skill_dir, use_tiktoken))

    # Possible findings are counted apart, as the text report prints them: a page of reads is not a page of defects.
    # Both counts read the rows the page lists, so a new rule cannot be subtracted as possible without being counted.
    # Spec rows name the file rather than an instance, and stay out as they always have.
    counted = [f for f in found if f.kind not in ("spec", "specw")]
    maybe = sum(f.n for f in counted if f.possible)
    total = sum(f.n for f in counted) - maybe
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
    <section class="cell"><h2>Verdict</h2>%(verdict)s</section>
    <section class="cell"><h2>Token budget</h2>%(budget)s%(files)s</section>
    %(extra)s
    <section class="cell grow rated"><h2>Structure</h2>%(structure)s</section>
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
        "verdict": verdict_block(issues, agent is not None, spec_skipped),
        "budget": budget_block(load, sized, advice, ceiling, within_budget),
        "files": files_block(sized),
        "structure": structure_block(pct, found, rows),
        "findings": findings_block(found),
        "extra": extra,
        "source": marked_source(skill_dir, blobs, long_code, filler, emphasis, dense, invisible,
                                redundant, desc_span if description else None, tables, desc_words,
                                rows, wrapped),
        "brief": e(brief(skill_dir, load, sized, ceiling, within_budget, spec, found, agent, issues)),
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
    ap.add_argument("--findings", metavar="JSON",
                    help="the reviewing agent's findings, a JSON array (or - for stdin) of "
                         '{"grade": "spec|primer|judgement", "finding": ..., "where": "path:line", '
                         '"fix": ..., "cite": ...}; only grade and finding are required')
    ap.add_argument("-o", "--out", help="output path (default: ~/Downloads, else a temp directory)")
    args = ap.parse_args()

    skill_dir = Path(args.skill_directory)
    if not (skill_dir / "SKILL.md").is_file():
        ap.error(f"no SKILL.md in {skill_dir}")
    if args.against and not (Path(args.against) / "SKILL.md").is_file():
        ap.error(f"no SKILL.md in {args.against}")
    if args.tiktoken:
        vs._tiktoken_encoding()
    agent = None
    if args.findings is not None:
        try:
            agent = load_agent_findings(args.findings)
        except (OSError, ValueError) as err:
            ap.error(str(err))

    name = f"{skill_dir.resolve().name}.skill-report.html"
    # Downloads is where the user looks for a file they did not ask to keep anywhere in particular; the temp directory
    # covers a machine without one.
    downloads = Path.home() / "Downloads"
    out = Path(args.out) if args.out else (downloads if downloads.is_dir() else Path(tempfile.gettempdir())) / name
    if out.is_dir():
        out = out / name  # -o took a directory: name the file rather than refusing
    page = render(skill_dir, args.against, args.tiktoken, agent)
    # A sandboxed agent often sees Downloads but cannot write to it, so the default retries in the temp directory. An
    # explicit -o is the user's choice and is never second-guessed.
    targets = [out] if args.out else [out, Path(tempfile.gettempdir()) / name]
    for target in targets:
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(page, encoding="utf-8")
            out = target
            break
        except OSError as err:
            if target == targets[-1]:
                # One line, naming the fix: a traceback says nothing about which path or what to do.
                print("cannot write %s: %s. Pass -o to choose another path." % (target, err.strerror),
                      file=sys.stderr)
                sys.exit(2)
    print(out.resolve())


if __name__ == "__main__":
    main()
