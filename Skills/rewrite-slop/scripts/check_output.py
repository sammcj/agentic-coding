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
import re
import sys
import unicodedata
from collections import Counter

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
    # The marketing register: high-lift vocabulary of the load-bearing cluster that
    # is receding (12.1% -> 4.0%). Reported, not swapped, because a few have a
    # literal technical sense (a robust estimator, a scalable queue).
    #
    # Every -ise/-ize alternation is written out. The lists match on meaning, so a
    # rule carrying only one spelling silently passes half its inputs.
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
]

# The register Claude writes in now, ranked empirically at
# louisabraham.github.io/load-bearing. Group names match the Tier 2 headings in
# SKILL.md, and `register` prints them, so the agent is told which group is
# over-represented without re-reading the rubric. Dropped from the source ranking
# are its function words (ever, alone, rather, half) and its CI/testing jargon
# (byte-identical, goldens, wall-clock), which lift on subject matter, not style.
#
# No single one of these is wrong, so there is no per-word rule here.
# Concentration is the signal, which is why this is a density and not a match list.
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
    "structural": """load-bearing seam seams ceiling lever levers wedge wedged rung
        ladder chokepoint backstop tripwire machinery knob carve-out scaffolding
        substrate bedrock nexus flywheel""",
}
MARKERS = {w: g for g, ws in GROUPS.items() for w in ws.split()}

# "no one" is two tokens, so it cannot come from the token list like the rest.
NO_ONE = re.compile(r"\bno one\b")

# Per 1000 words, against the source ranking's own corpus: 99.1% of January 2025
# descriptions sit under ELEVATED and 36.3% of August 2026 ones clear it.
# LEAST is the absolute floor that stops a rate tripping a band on one or two
# words, which a short input otherwise does (60 words carrying one marker is 16.7).
ELEVATED, HEAVY, LEAST, SHORT = 4.0, 10.0, 4, 200

# Matches load-bearing's own tokeniser, so `load-bearing` and `carve-out` survive whole.
TOKEN = re.compile(r"[a-z0-9_/-]*[a-z][a-z0-9_/-]*")

CODE = re.compile(r"```.*?```|~~~.*?~~~|`[^`\n]+`", re.S)


def _code_spans(text):
    return [m.span() for m in CODE.finditer(text)]


def _in_code(pos, spans):
    return any(a <= pos < b for a, b in spans)


def _pos(text, off):
    return text.count("\n", 0, off) + 1, off - text.rfind("\n", 0, off)


def scan(text, *rulesets):
    """Return [(offset, name, matched_text)] for matches outside code, one per offset.

    Deduped because SAFE and REVIEW deliberately overlap: SAFE runs first and
    narrows a case (a numeric en-dash range) that REVIEW would otherwise claim.

    The matched text is carried so REPORT can name the word it objected to: a
    rule like marketing-adjective covers eighteen alternations, and the rule name
    alone leaves the agent to reopen the line to find out which one fired.
    """
    spans = _code_spans(text)
    seen = {}
    for rules in rulesets:
        for name, pat, _ in rules:
            for m in re.finditer(pat, text):
                if not _in_code(m.start(), spans):
                    seen.setdefault(m.start(), (name, " ".join(m.group(0).split())))
    return [(off, name, hit) for off, (name, hit) in sorted(seen.items())]


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

        text = re.sub(pat, sub, text)
    return text


def line_checks(text):
    """Checks needing line context rather than a single regex."""
    out = []
    lines = text.split("\n")
    fenced = False
    for i, line in enumerate(lines):
        if line.lstrip().startswith(("```", "~~~")):
            fenced = not fenced
            continue
        if fenced:
            continue
        stripped = line.strip()
        if stripped == "---":
            nxt = next((n for n in lines[i + 1:] if n.strip()), "")
            if nxt.startswith("#"):
                out.append((i + 1, "break-before-heading"))
        if stripped.startswith("#"):
            words = stripped.lstrip("# ").split()
            if sum(1 for w in words[1:] if re.fullmatch(r"[A-Z][a-z]+", w)) >= 2:
                out.append((i + 1, "title-case-heading"))
        if stripped.startswith("|") and not re.fullmatch(r"[|\s:-]+", stripped):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if any(len(c) > TABLE_CELL_MAX for c in cells):
                out.append((i + 1, "wide-table-cell"))
    return out


def register(text):
    """Density of the current Claude register, by group. Returns ([lines], flagged).

    Two gates, both of which must trip: a rate per 1000 words, and an absolute
    count. The rate alone flags clean short prose carrying one marker.
    """
    prose = CODE.sub(" ", text).lower()
    words = TOKEN.findall(prose)
    if len(words) < SHORT:
        return [], False
    hits = Counter(w for w in words if w in MARKERS)
    hits.update({"no one": len(NO_ONE.findall(prose))})
    total = sum(hits.values())
    rate = 1000 * total / len(words)
    if rate < ELEVATED or total < LEAST:
        return [], False

    by_group = {}
    for word, n in hits.most_common():
        by_group.setdefault(MARKERS.get(word, "negation"), []).append(
            "%s x%d" % (word, n) if n > 1 else word)
    lines = ["register %.1f/1000 %s, %d markers over %d words"
             % (rate, "HEAVY" if rate >= HEAVY else "ELEVATED", total, len(words))]
    for group, words_ in sorted(by_group.items(), key=lambda kv: -len(kv[1])):
        lines.append("  %-13s %s" % (group, ", ".join(words_[:10])))
    return lines, True


def compare(orig, new):
    """Length and code-block passthrough, per Phase 4."""
    ow, nw = len(orig.split()), len(new.split())
    pct = (nw - ow) / ow * 100 if ow else 0.0
    lines = ["words: %d -> %d (%+.1f%%)%s" % (ow, nw, pct, "  LONGER" if nw > ow else "")]
    ob = re.findall(r"```.*?```", orig, re.S)
    nb = re.findall(r"```.*?```", new, re.S)
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
            review = [h for h in scan(text, SAFE, REVIEW) if h[1] in names]
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

        rest = [(_pos(text, o)[0], n, h) for o, n, h in scan(text, REPORT)]
        rest += [(ln, n, "") for ln, n in line_checks(text)]
        for ln, name, hit in sorted(rest):
            print("%s:%d %s %s" % (path, ln, name, hit))
        findings += len(rest)

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
