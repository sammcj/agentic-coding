#!/usr/bin/env python3
"""Mechanical de-slop checks for the rewrite-slop skill. Standard library only.

    check_output.py FILE...                 report findings, fix nothing
    check_output.py --write FILE...         apply SAFE and REVIEW fixes in place
    check_output.py --against ORIG FILE     add length and code-block passthrough checks

Rules live in three lists of (name, pattern, replacement) tuples. To add or drop a
rule, edit one line; nothing else needs to change.

    SAFE    fixed silently, no judgement involved
    REVIEW  fixed with a default, every location printed so the agent re-reads it
    REPORT  detected only, replacement is None

A fourth check, `register`, is a density rather than a match: it measures how much
of the current Claude vocabulary the text carries per 1000 words. See MARKERS.

Matches inside fenced blocks and inline code are always skipped. Quoted speech is
NOT detected, which is why the phrase swaps sit in REVIEW rather than SAFE: a swap
that lands inside a quotation has to be undone by hand.
"""

import argparse
import functools
import re
import sys
import unicodedata
from collections import Counter
from typing import NamedTuple

# Cells longer than this hold prose, not structured data, and the skill's own
# Tier 4 rubric flags tables used for non-tabular comparisons.
TABLE_CELL_MAX = 20


def _swap(word):
    """Replace with `word`, keeping the first letter's case."""
    return lambda m: word.capitalize() if m.group(0)[:1].isupper() else word


def _ascii_math(m):
    """Mathematical bold/italic unicode back to plain ASCII."""
    return unicodedata.normalize("NFKC", m.group(0))


SAFE = [
    ("smart-quote", r"[“”]", '"'),
    ("smart-quote", r"[‘’]", "'"),
    ("ellipsis", r"…", "..."),
    ("nbsp", r"[   ]", " "),
    ("math-unicode", r"[\U0001d400-\U0001d7ff]+", _ascii_math),
    ("private-use", r"[-]+", ""),
    ("arrow-bullet", r"(?m)^(\s*)[→‣▪▸●]\s+", r"\1- "),
    ("en-dash-range", r"(?<=\d)\s*–\s*(?=\d)", "-"),
    ("utm-llm", r"[?&]utm_[a-z_]+=(?:chatgpt\.com|openai|copilot\.com|perplexity\.ai|claude\.ai)\b", ""),
    ("utm-llm", r"[?&]referrer=grok\.com\b", ""),
    ("cite-marker", r"cite.{0,4}turn\d+\w*|\bi?turn\d+(?:image|search|news)\d+\b", ""),
    ("cite-marker", r"oai_citation[^\s)]*|:contentReference\[oaicite:\d+\]\{index=\d+\}", ""),
    ("cite-marker", r"\[(?:attached_file|web):\d+\]|</?grok-card[^>]*>", ""),
    ("json-tail", r'\(\{"attribution":\{"attributableIndex":"[^"]*"\}\}\)', ""),
]

REVIEW = [
    ("em-dash", r"\s*—\s*", ", "),
    ("en-dash", r"\s*–\s*", ", "),
    # word chars either side, so a markdown table separator is never touched
    ("double-dash", r"(?<=\w)\s+--\s+(?=\w)", ", "),
    ("times-sign", r"(?<=\s)×(?=\s)", "x"),
    ("phrase-swap", r"(?i)\bin order to\b", _swap("to")),
    ("phrase-swap", r"(?i)\bdue to the fact that\b", _swap("because")),
    ("phrase-swap", r"(?i)\bin the event that\b", _swap("if")),
    ("phrase-swap", r"(?i)\bat this point in time\b", _swap("now")),
    ("phrase-swap", r"(?i)\butili[sz]e\b", _swap("use")),
    ("phrase-swap", r"(?i)\butili[sz]ing\b", _swap("using")),
    ("phrase-swap", r"(?i)\bnumerous\b", _swap("many")),
    ("phrase-swap", r"(?i)\bprior to\b", _swap("before")),
    ("phrase-swap", r"(?i)\bit is important to note that (\w)", lambda m: m.group(1).upper()),
]

REPORT = [
    ("placeholder", r"\[(?:Your |Insert|Describe|TODO)[^\]]*\]|\bINSERT_[A-Z_0-9]+\b|\b\d{4}-XX-XX\b", None),
    ("opener-filler", r"(?m)(?:^|(?<=\. ))(?:Additionally|Furthermore|Moreover|Notably|Consequently|Accordingly|In conclusion|Overall|In summary|It is worth mentioning|It should be noted)\b", None),
    ("weasel-source", r"\b(?:experts (?:argue|say|note)|studies show|research (?:suggests|shows)|researchers have noted|observers have cited|industry reports suggest|critics contend)\b", None),
    ("chat-residue", r"\b(?:Let me|I['’]ll help you|I hope this helps|Let me know if|Happy to|I['’]d be happy to|Feel free to|Would you like me to)\b|\b(?:Perfect|Excellent|Great question)!", None),
    ("metaphor-tic", r"\b(?:smoking[- ]gun|load[- ]bearing)\b", None),
    # Literal in linguistics and NLP, inflation everywhere else, so it is reported
    # rather than swapped and the agent decides which one it is looking at.
    ("metaphor-tic", r"(?i)\bcorp(?:us|ora)\b", None),
    # Fixed puffery phrases only. Single adjectives (robust, vibrant) stay in the
    # Tier 3 rubric, where surrounding context decides whether they are decorative.
    ("puffery", r"(?i)\b(?:nestled in the heart of|stands? as a testament to|marks? a pivotal moment|represents? a significant shift|indelible mark|stunning natural beauty|diverse array|rich tapestry|ever[- ]evolving landscape|remains limitless)\b", None),
    # Reported, not swapped: a few have a literal technical sense (a robust
    # estimator, a scalable queue). Both spellings, or half the inputs pass.
    ("marketing-adjective", r"(?i)\b(?:comprehensive(?:ly)?|robust|seamless(?:ly)?|enterprise[- ]grade|production[- ]ready|cutting[- ]edge|best[- ]in[- ]class|feature[- ]rich|innovative|pivotal|multifaceted|streamlin(?:ed|ing)|scalable|ai[- ]powered|vibrant|groundbreaking|meticulous|renowned)\b", None),
    # Kobak et al.'s PubMed excess ratios, all on five-figure abstract counts:
    # realm 5.5, revolutionize 5.2, poised 3.6, emerges 3.5.
    ("marketing-adjective", r"(?i)\b(?:revolutioni[sz](?:e|es|ed|ing)|poised to|the realm of|emerges as|emerged as|widely recogni[sz]ed)\b", None),
    # Both apostrophe forms, since REPORT runs before SAFE has straightened them.
    ("sycophancy", r"(?i)\byou(?:['’]re| are)\s+(?:absolutely\s+|completely\s+|totally\s+|quite\s+|so\s+)?(?:right|correct)\b", None),
    ("sycophancy", r"(?i)\b(?:that['’]?s a (?:great|good|fair) (?:question|point)|(?:great|excellent|fair|good) point|good catch|you raise a)\b", None),
    # "honest" earns its place only when its removal changes the meaning.
    ("honest-framing", r"(?i)\b(?:to be honest|being honest|in all honesty|honest truth|if I['’]m honest|honestly speaking)\b", None),
    # Bare "honestly" almost never survives its own deletion test.
    ("honest-framing", r"(?i)\bhonestly\b", None),
    ("honest-framing", r"(?i)\bhonest\s+(?:take|feedback|account|review|assessment|answer|opinion|recommendation|reasoning|analysis|limits?|view|conversation|thoughts?|appraisal|read|verdict|summary|version|breakdown)\b", None),
    ("emoji", r"[\U0001f300-\U0001faff☀-➿]", None),
    # Ported from skill-creator-primer's _FILLER_RULES. "harness" only in its
    # verb-with-object shape, because a test harness is the literal noun.
    ("filler-verb", r"(?i)\b(?:delv(?:e|es|ed|ing)|div(?:e|es|ed|ing) into|leverag(?:e|es|ed|ing)|harness(?:ing)? the|foster(?:s|ed|ing)?|bolster(?:s|ed|ing)?|underscor(?:e|es|ed|ing)|facilitat(?:e|es|ed|ing)|empower(?:s|ed|ing)?|showcas(?:e|es|ed|ing)|garner(?:s|ed|ing)?|exemplif(?:y|ies|ied|ying)|emphasi[sz](?:e|es|ed|ing))\b", None),
    ("negation-antithesis", r"(?i)\bnot (?:just|only|merely|simply)\b[^.\n]{1,60}?\bbut\b|\b(?:it['’]?s|it is|this is|that['’]?s) not\b[^.\n]{1,60}?[,.]\s*(?:it['’]?s|it is)\b|\bthe question is(?:n['’]?t| not)\b[^.\n]{1,60}?[,.]\s*it['’]?s\b", None),
    # Padding: each collapses to one word or none without losing anything.
    ("padding", r"(?i)\b(?:in terms of|with respect to|in the context of|a (?:wide )?(?:variety|range|number) of|a myriad of|the fact that|in order for|for the purpose of|it goes without saying|needless to say|each and every|first and foremost|clear and concise|various different|basic fundamentals?|end result|past history|advance planning)\b", None),
]

# Ranked at louisabraham.github.io/load-bearing. Group names match the Tier 2
# headings in SKILL.md, so `register` can name the over-represented group.
# Concentration is the signal, so this is a density, not a match list.
# See references/refresh-vocabulary.md for what was excluded and why.
GROUPS = {
    "adverbs": """plainly quietly genuinely genuine deliberately deliberate outright
        loudly provably empirically vacuously vacuous legitimately structurally
        precisely demonstrably identically verbatim merely faithful faithfully
        squarely adversarially""",
    "negation": "nothing never nobody nowhere neither none no-one",
    "code-as-agent": """carries carrying carried admits asserts asserted asserting
        rests holds survives survived surviving survive outlives outlived decides
        declares governs forbids agrees disagrees disagreed disagree contradicts
        contradicted contradicting falsified refuted restated restating earns buys
        pays drains bites swallows swallowed degrades escalates short-circuits
        self-heals mints minted stamps stamped refuse refuses refused refusing""",
    "adjudication": """refusal refusals premise ruling precedent verdict verdicts
        obligation caveat remedy symptom asymmetry shortfall hazard idiom
        disagreement""",
    # scaffolding, substrate, bedrock, nexus and flywheel are deliberately absent:
    # they are Tier 3's guessed metaphor nouns, not words the ranking found, so
    # they have no business inflating a density derived from it.
    "structural": """load-bearing seam seams ceiling floor lever levers wedge wedged
        rung ladder chokepoint backstop tripwire machinery knob carve-out""",
}
MARKERS = {w: g for g, ws in GROUPS.items() for w in ws.split()}

# "no one" is two tokens, so it cannot come from the token list like the rest.
NO_ONE = re.compile(r"\bno one\b")

# Per 1000 words. Both gates must trip: LEAST stops a rate banding clean short
# prose on one word. On the source corpus that flags 0.3% of January 2025
# descriptions against 45.2% of August 2026 ones.
ELEVATED, HEAVY, LEAST, SHORT = 4.0, 10.0, 4, 200

# Matches load-bearing's own tokeniser, so `load-bearing` and `carve-out` survive whole.
TOKEN = re.compile(r"[a-z0-9_/-]*[a-z][a-z0-9_/-]*")

# A compression target, not an AI tell: measured on the load-bearing corpus,
# paragraph length does not separate AI from human. 150 rather than the 100
# skill-creator-primer uses, because prose earns longer paragraphs than
# instructions do.
BLOB_WORDS = 150
BLOB_LIST_MAX = 10
LOCATIONS_MAX = 6  # line numbers shown per grouped finding

# A markdown paragraph renders as one line however it is typed, so a paragraph
# arriving as several lines was wrapped by hand. The length floor is all the test
# needs: it separates a wrap from a deliberately short line. Testing the columns
# for consistency instead missed a third of them, because one line ending early
# before a long link is enough to break the pattern while still being a wrap.
WRAP_MIN = 50

# A `---` before a heading is ordinary markdown. What claude.ai does is put one
# above heading after heading, so both a count and a share of the document's
# headings have to trip before it is worth reporting.
BREAK_LEAST, BREAK_SHARE = 3, 0.33
_LIST_MARKER = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s")
_HEADING = re.compile(r"^#{1,6}\s")
_FENCE = re.compile(r"^(`{3,}|~{3,})")

CODE = re.compile(r"```.*?```|~~~.*?~~~|`[^`\n]+`", re.DOTALL)


@functools.cache
def _wrappable(pattern):
    """Let a literal space in a pattern match a hard line-wrap too.

    Prose arrives wrapped, so "the fact that" is regularly split across two
    lines and a literal space would miss it. Two spans are left alone: a
    character class, where `[- ]` must stay two characters, and a lookbehind,
    which Python requires to be fixed width.
    """
    out, klass, i = [], False, 0
    while i < len(pattern):
        c = pattern[i]
        if c == "\\" and i + 1 < len(pattern):
            out.append(pattern[i:i + 2])
            i += 2
            continue
        if not klass and pattern.startswith(("(?<=", "(?<!"), i):
            end, depth = i, 0
            while end < len(pattern):  # copy the assertion verbatim
                if pattern[end] == "\\":
                    end += 1
                elif pattern[end] == "(":
                    depth += 1
                elif pattern[end] == ")":
                    depth -= 1
                    if depth == 0:
                        break
                end += 1
            out.append(pattern[i:end + 1])
            i = end + 1
            continue
        if c == "[":
            klass = True
        elif c == "]":
            klass = False
        # At most one newline: a run spanning a blank line would let a REVIEW swap
        # merge two paragraphs.
        out.append(r"(?:[^\S\n]+|[^\S\n]*\n[^\S\n]*)" if c == " " and not klass else c)
        i += 1
    widened = "".join(out)
    try:
        re.compile(widened)
    except re.error:
        return pattern  # a pattern we cannot widen still has to work as written
    return widened


def _code_spans(text):
    return [m.span() for m in CODE.finditer(text)]


def _in_code(pos, spans):
    return any(a <= pos < b for a, b in spans)


def _pos(text, off):
    return text.count("\n", 0, off) + 1, off - text.rfind("\n", 0, off)


def scan_spans(text, *rulesets):
    """Return [(start, end, name, matched_text)] for matches outside code.

    Deduped because SAFE and REVIEW deliberately overlap: SAFE runs first and
    narrows a case (a numeric en-dash range) that REVIEW would otherwise claim.

    The matched text is carried so REPORT can name the word it objected to: a
    rule like marketing-adjective covers eighteen alternations, and the rule name
    alone leaves the agent to reopen the line to find out which one fired. The
    end offset is carried for the HTML report, which marks the span in place.
    """
    spans = _code_spans(text)
    seen = {}
    for rules in rulesets:
        for name, pat, _ in rules:
            for m in re.finditer(_wrappable(pat), text):
                if not _in_code(m.start(), spans):
                    seen.setdefault(m.start(), (m.end(), name, " ".join(m.group(0).split())))
    # Drop a hit whose span sits inside another's: "marks a pivotal moment" and
    # "pivotal" are one edit, and reporting both spends two lines and two counts.
    out = []
    for off, (end, name, hit) in sorted(seen.items()):
        if any(a <= off and end <= b for a, (b, _, _) in seen.items() if a != off):
            continue
        out.append((off, end, name, hit))
    return out


def scan(text, *rulesets):
    """scan_spans without the end offset, which most callers do not need."""
    return [(off, name, hit) for off, _, name, hit in scan_spans(text, *rulesets)]


def apply(text: str, rules, counts) -> str:
    for name, pat, repl in rules:
        spans = _code_spans(text)

        # Loop variables bound as defaults: re.sub consumes `sub` within this
        # iteration, but binding them makes that independent of the call order.
        def sub(m, name=name, repl=repl, spans=spans):
            if _in_code(m.start(), spans):
                return m.group(0)
            counts[name] = counts.get(name, 0) + 1
            return str(repl(m)) if callable(repl) else m.expand(repl)

        # Same wrap handling as scan, so the review list never names a fix that
        # did not happen. A swap spanning a wrap closes it up; the text is being
        # rewritten anyway and markdown soft-wraps.
        text = re.sub(_wrappable(pat), sub, text)
    return text


def line_checks(text):
    """Checks needing line context rather than a single regex."""
    out, breaks, headings = [], [], 0
    lines = text.split("\n")
    fenced = False
    # A front matter block closes on `---` immediately before the first heading,
    # which is not the decorative break the rule is looking for.
    front = 2 if lines and lines[0].strip() == "---" else 0
    for i, line in enumerate(lines):
        if front and line.strip() == "---":
            front -= 1
            continue
        if line.lstrip().startswith(("```", "~~~")):
            fenced = not fenced
            continue
        if fenced:
            continue
        stripped = line.strip()
        if stripped == "---":
            nxt = next((n for n in lines[i + 1:] if n.strip()), "")
            if nxt.startswith("#"):
                breaks.append(i + 1)
        if stripped.startswith("#"):
            headings += 1
            words = stripped.lstrip("# ").split()
            if sum(1 for w in words[1:] if re.fullmatch(r"[A-Z][a-z]+", w)) >= 2:
                out.append((i + 1, "title-case-heading"))

    # The habit is the fingerprint, not one divider: a horizontal rule is
    # ordinary markdown, and claude.ai's tell is putting one above heading after
    # heading. Both gates, so a long document does not qualify on count alone.
    if len(breaks) >= BREAK_LEAST and headings and len(breaks) / headings >= BREAK_SHARE:
        out += [(ln, "break-before-heading") for ln in breaks]
    return sorted(out)


class Unit(NamedTuple):
    """One prose paragraph or list item, measured whole across its wrapped lines."""

    words: int
    start: int
    opening: str
    end: int
    lengths: tuple  # visible length of each line, for the hard-wrap test


def units(text):
    """Prose paragraph units, skipping code, tables and headings.

    Words are accumulated per unit rather than per line, so a wrapped list item
    lands wholly in its item and a hard-wrapped paragraph is measured whole.

    One walker for three findings. A table scan and a wrap scan each need the
    same fence, indent and list handling, and three copies of it would drift.
    """
    found, unit, start, opening, fence = [], 0, 0, "", False
    lengths, last = [], 0
    indented = re.compile(r"^ {4,}\S")
    blank_before, in_indent = True, False
    lines = text.splitlines()
    # Front matter is a data block, not a paragraph. Its long `description:`
    # followed by another key read as a hard-wrapped paragraph.
    front = 2 if lines and lines[0].strip() == "---" else 0

    def close():
        nonlocal unit, lengths
        if unit:
            found.append(Unit(unit, start, opening, last, tuple(lengths)))
        unit, lengths = 0, []

    for lineno, line in enumerate(lines, start=1):
        s = line.strip()
        if front:
            if s == "---":
                front -= 1
            continue
        if _FENCE.match(s):
            fence = not fence
            close()
            continue
        if fence:
            continue
        # Indented code block: only fences are tracked above, so a long indented
        # listing would otherwise report as one very long paragraph. It opens
        # after a blank line and runs until the indent stops.
        if indented.match(line) and not _LIST_MARKER.match(line) and (blank_before or in_indent):
            close()
            in_indent = True
            continue
        in_indent = False
        blank_before = not s
        if (marker := _LIST_MARKER.match(line)):
            # Starts a new unit rather than skipping: the marker line carries the
            # item's opening words, and its wrapped continuation belongs with it.
            # The bullet itself is not a word.
            close()
            rest = line[marker.end():].split()
            start, opening = lineno, " ".join(rest[:8])
            unit, lengths, last = len(rest), [len(line.rstrip())], lineno
            continue
        if not s or _HEADING.match(s) or s.startswith(("|", ">")):
            close()
            continue
        if unit == 0:
            start, opening = lineno, " ".join(s.split()[:8])
        unit += len(s.split())
        lengths.append(len(line.rstrip()))
        last = lineno
    close()
    return found


def blobs(text):
    """Paragraph units at or over BLOB_WORDS. Returns [(words, line, opening, end)]."""
    found = [(u.words, u.start, u.opening, u.end) for u in units(text) if u.words >= BLOB_WORDS]
    return sorted(found, reverse=True)[:BLOB_LIST_MAX]


def _explicit_break(line):
    """A line break the author asked markdown to keep: two trailing spaces, or a backslash."""
    return line.endswith(("  ", "\\"))


def tables(text):
    """Table blocks holding a cell over TABLE_CELL_MAX. Returns [(start, end, cells)].

    One finding per table rather than per row: a table full of prose is one
    decision, and REPORT.md's 135 offending rows were 9 tables.
    """
    out, start, end, wide, fence = [], 0, 0, 0, False
    for lineno, line in enumerate(text.splitlines() + [""], start=1):
        s = line.strip()
        if _FENCE.match(s):
            fence = not fence
        row = not fence and s.startswith("|")
        if row:
            start = start or lineno
            end = lineno
            if not re.fullmatch(r"[|\s:-]+", s):
                wide += sum(1 for c in s.strip("|").split("|")
                            if len(c.strip()) > TABLE_CELL_MAX)
        elif start:
            if wide:
                out.append((start, end, wide))
            start, end, wide = 0, 0, 0
    return out


def wraps(text):
    """Hard-wrap newline offsets, and how many paragraphs carry one.

    Returns (offsets, wrapped_units, total_units). Decided per break rather than
    per paragraph, so one deliberate short line does not excuse the rest, and
    reported as one document-level count because a wrapped file is wrapped
    throughout: 52 identical findings say nothing that 1 does not.
    """
    lines, starts, at = text.splitlines(), [], 0
    for line in lines:
        starts.append(at)
        at += len(line) + 1

    all_units = units(text)
    offsets, wrapped = [], 0
    for u in all_units:
        found = []
        # Every line but the last: that break is where the wrap happened.
        for ln in range(u.start, u.end):
            raw = lines[ln - 1] if ln - 1 < len(lines) else ""
            if len(raw.rstrip()) >= WRAP_MIN and not _explicit_break(raw):
                found.append(starts[ln - 1] + len(raw))
        if found:
            offsets += found
            wrapped += 1
    return offsets, wrapped, len(all_units)


def register_stats(text):
    """Density of the current Claude register, by group, or None below the gates.

    Two gates, both of which must trip: a rate per 1000 words, and an absolute
    count. The rate alone flags clean short prose carrying one marker.

    Structured rather than formatted because the HTML report reads the same
    measurement, and a second implementation of it would drift from this one.
    """
    prose = CODE.sub(" ", text).lower()
    words = TOKEN.findall(prose)
    if len(words) < SHORT:
        return None
    hits = Counter(w for w in words if w in MARKERS)
    # Assigned, not update()d: Counter.update creates the key even at zero, which
    # would name "no one" as a marker in every report that did not contain it.
    if (spaced := len(NO_ONE.findall(prose))):
        hits["no one"] = spaced
    total = sum(hits.values())
    rate = 1000 * total / len(words)
    if rate < ELEVATED or total < LEAST:
        return None

    by_group = {}
    for word, n in hits.most_common():
        by_group.setdefault(MARKERS.get(word, "negation"), []).append((word, n))
    return {
        "rate": rate,
        "total": total,
        "words": len(words),
        "band": "HEAVY" if rate >= HEAVY else "ELEVATED",
        # By total hits, not by how many distinct words a group used: the group
        # to thin is the one carrying the most weight, and ordering by distinct
        # words put a group of 56 hits below one of 27.
        "groups": sorted(by_group.items(), key=lambda kv: -sum(n for _, n in kv[1])),
    }


def register(text):
    """Register density as report lines. Returns ([lines], flagged)."""
    st = register_stats(text)
    if not st:
        return [], False
    lines = ["register %.1f/1000 %s, %d markers over %d words"
             % (st["rate"], st["band"], st["total"], st["words"])]
    for group, pairs in st["groups"]:
        shown = ["%s x%d" % (w, n) if n > 1 else w for w, n in pairs[:10]]
        lines.append("  %-13s %s" % (group, ", ".join(shown)))
    return lines, True


def compare(orig, new):
    """Length and code-block passthrough, per Phase 4."""
    ow, nw = len(orig.split()), len(new.split())
    pct = (nw - ow) / ow * 100 if ow else 0.0
    lines = ["words: %d -> %d (%+.1f%%)%s" % (ow, nw, pct, "  LONGER" if nw > ow else "")]
    ob = re.findall(r"```.*?```", orig, re.DOTALL)
    nb = re.findall(r"```.*?```", new, re.DOTALL)
    # Not strict: a differing block count is the finding, not an error.
    same = sum(1 for a, b in zip(ob, nb, strict=False) if a == b)
    lines.append("code blocks: %d/%d identical%s" % (same, len(ob), "" if same == len(ob) and len(ob) == len(nb) else "  DIFFER"))
    return lines, nw > ow or ob != nb


def summarise(counts):
    return ", ".join("%s %d" % (k, v) for k, v in sorted(counts.items()))


def main():
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("files", nargs="+")
    ap.add_argument("--write", action="store_true", help="apply SAFE and REVIEW fixes in place")
    ap.add_argument("--against", metavar="ORIG", help="original file, for length and code-block checks")
    args = ap.parse_args()

    findings = 0
    for path in args.files:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()

        if args.write:
            counts = {}
            # Scanned with SAFE so the dedup applies: SAFE narrows a numeric
            # en-dash range that REVIEW would otherwise claim, and a fix that
            # needed no judgement must not be sent back for a re-read.
            names = {r[0] for r in REVIEW}
            # Only en-dash-range narrows a REVIEW rule, so only it takes part in
            # the dedup. Scanning all of SAFE also let nbsp mask an adjacent em
            # dash, applying the fix without listing it for the re-read.
            narrowing = [r for r in SAFE if r[0] == "en-dash-range"]
            review = [h for h in scan(text, narrowing, REVIEW) if h[1] in names]
            new = apply(apply(text, SAFE, counts), REVIEW, counts)
            if new != text:
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(new)
            print("%s: %d fixed (%s)" % (path, sum(counts.values()), summarise(counts) or "none"))
            for off, name, hit in review:
                print("%s:%d:%d %s %s  fixed, re-read" % ((path,) + _pos(text, off) + (name, hit)))
            text = new
        else:
            for off, name, hit in scan(text, SAFE, REVIEW):
                print("%s:%d:%d %s %s" % ((path,) + _pos(text, off) + (name, hit)))
                findings += 1

        # Grouped one line per distinct term, after skill-creator-primer: the
        # agent fixes a word everywhere at once, so ten hits on "comprehensive"
        # is one action, not ten. Locations are still listed, capped.
        rest = [(_pos(text, o)[0], n, h) for o, n, h in scan(text, REPORT)]
        rest += [(ln, n, "") for ln, n in line_checks(text)]
        grouped = {}
        for ln, name, hit in sorted(rest):
            grouped.setdefault((name, hit.lower()), []).append(ln)
        for (name, hit), lines in sorted(grouped.items()):
            where = ", ".join("L%d" % n for n in lines[:LOCATIONS_MAX])
            if len(lines) > LOCATIONS_MAX:
                where += ", +%d more" % (len(lines) - LOCATIONS_MAX)
            count = " x%d" % len(lines) if len(lines) > 1 else ""
            print("%s: %-20s %s%s  (%s)" % (path, name, hit or "-", count, where))
        findings += len(rest)

        for words, ln, opening, end in blobs(text):
            print("%s:%d-%d long-paragraph %d words  \"%s...\""
                  % (path, ln, end, words, opening))
            findings += 1

        for start, end, wide in tables(text):
            print("%s:%d-%d wide-table %d cell%s over %d characters"
                  % (path, start, end, wide, "" if wide == 1 else "s", TABLE_CELL_MAX))
            findings += 1

        _, wrapped, total = wraps(text)
        if wrapped:
            print("%s: hard-wrapped %d of %d paragraphs" % (path, wrapped, total))
            findings += 1

        reg, flagged = register(text)
        for line in reg:
            print("%s: %s" % (path, line))
        findings += flagged

        if args.against:
            with open(args.against, encoding="utf-8") as fh:
                lines, bad = compare(fh.read(), text)
            for line in lines:
                print("%s: %s" % (path, line))
            findings += bad

    print("%d finding%s" % (findings, "" if findings == 1 else "s"))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
