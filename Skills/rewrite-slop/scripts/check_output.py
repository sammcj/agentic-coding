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

Matches inside fenced blocks and inline code are always skipped. Quoted speech is
NOT detected, which is why the phrase swaps sit in REVIEW rather than SAFE: a swap
that lands inside a quotation has to be undone by hand.
"""

import argparse
import re
import sys
import unicodedata

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
    ("chat-residue", r"\b(?:Let me|I'll help you|I hope this helps|Let me know if|Happy to|I'd be happy to|Feel free to|Would you like me to)\b|\b(?:Perfect|Excellent|Great question)!", None),
    ("metaphor-tic", r"\b(?:smoking gun|load[- ]bearing)\b", None),
    # Fixed puffery phrases only. Single adjectives (robust, vibrant) stay in the
    # Tier 3 rubric, where surrounding context decides whether they are decorative.
    ("puffery", r"(?i)\b(?:nestled in the heart of|stands? as a testament to|marks? a pivotal moment|represents? a significant shift|indelible mark|stunning natural beauty|diverse array|rich tapestry|ever[- ]evolving landscape|remains limitless)\b", None),
    # Both apostrophe forms, since REPORT runs before SAFE has straightened them.
    ("sycophancy", r"(?i)\byou(?:['’]re| are)\s+(?:absolutely\s+|completely\s+|totally\s+|quite\s+|so\s+)?(?:right|correct)\b", None),
    ("sycophancy", r"(?i)\b(?:that['’]?s a (?:great|good|fair) (?:question|point)|(?:great|excellent|fair|good) point|good catch|you raise a)\b", None),
    # "honest" earns its place only when its removal changes the meaning.
    ("honest-framing", r"(?i)\b(?:to be honest|being honest|in all honesty|honest truth)\b", None),
    ("honest-framing", r"(?i)\bhonest\s+(?:take|feedback|account|review|assessment|answer|opinion|recommendation|reasoning|analysis|limits?|view|conversation)\b", None),
    ("emoji", r"[\U0001f300-\U0001faff☀-➿]", None),
]

CODE = re.compile(r"```.*?```|~~~.*?~~~|`[^`\n]+`", re.S)


def _code_spans(text):
    return [m.span() for m in CODE.finditer(text)]


def _in_code(pos, spans):
    return any(a <= pos < b for a, b in spans)


def _pos(text, off):
    return text.count("\n", 0, off) + 1, off - text.rfind("\n", 0, off)


def scan(text, *rulesets):
    """Return [(offset, name)] for every match outside code, one hit per offset.

    Deduped because SAFE and REVIEW deliberately overlap: SAFE runs first and
    narrows a case (a numeric en-dash range) that REVIEW would otherwise claim.
    """
    spans = _code_spans(text)
    seen = {}
    for rules in rulesets:
        for name, pat, _ in rules:
            for m in re.finditer(pat, text):
                if not _in_code(m.start(), spans):
                    seen.setdefault(m.start(), name)
    return sorted(seen.items())


def apply(text: str, rules, counts) -> str:
    for name, pat, repl in rules:
        spans = _code_spans(text)

        def sub(m):
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


def compare(orig, new):
    """Length and code-block passthrough, per Phase 4."""
    ow, nw = len(orig.split()), len(new.split())
    pct = (nw - ow) / ow * 100 if ow else 0.0
    lines = ["words: %d -> %d (%+.1f%%)%s" % (ow, nw, pct, "  LONGER" if nw > ow else "")]
    ob = re.findall(r"```.*?```", orig, re.S)
    nb = re.findall(r"```.*?```", new, re.S)
    same = sum(1 for a, b in zip(ob, nb) if a == b)
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
            review = scan(text, REVIEW)
            new = apply(apply(text, SAFE, counts), REVIEW, counts)
            if new != text:
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(new)
            print("%s: %d fixed (%s)" % (path, sum(counts.values()), summarise(counts) or "none"))
            for off, name in review:
                print("%s:%d:%d %s  fixed, re-read" % ((path,) + _pos(text, off) + (name,)))
            text = new
        else:
            for off, name in scan(text, SAFE, REVIEW):
                print("%s:%d:%d %s" % ((path,) + _pos(text, off) + (name,)))
                findings += 1

        rest = [(_pos(text, o)[0], n) for o, n in scan(text, REPORT)] + line_checks(text)
        for ln, name in sorted(rest):
            print("%s:%d %s" % (path, ln, name))
        findings += len(rest)

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
