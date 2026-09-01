#!/usr/bin/env python3
"""Sentence-shape checks for the rewrite-slop skill. Standard library only.

Everything here reads sentences rather than words, which a regex over the whole text cannot: a landing sentence is short
only relative to the paragraph it closes, a contrast pair is two sentences, parataxis is a distribution. check_output.py
imports this and prints what it returns; nothing here prints or reads a file.

Every span check here is POSSIBLE rather than probable (see check_output.POSSIBLE): each shape is also ordinary prose in
small doses, so the span is evidence and the document-level band is the finding.
"""

import re
import statistics
from collections import Counter

# A closing sentence this short, after sentences this long on average, is the profundity beat: "That is the whole
# trick." One per document is style. LANDING_REST keeps a paragraph of short sentences from qualifying on its own last
# one. Two sentences is enough: "If we need hosted mode later, the data layer should let us swap engines. It is a
# different product." is the beat at its shortest.
LANDING_MAX, LANDING_REST, LANDING_SENTENCES = 6, 12, 2
# Closers opening on the same two words this many times are a trailer convention, and none of them counts.
TRAILER_RUN = 3

# "What we gain is small. What we pay is not." The second sentence is the elided half of a contrast, and a predicate
# left off after "not" is the figure's own marker. CONTRAST_MAX keeps the match to the clipped form.
CONTRAST_MAX = 8

# Three sentences opening on the same word is the pattern; two is coincidence.
ANAPHORA_RUN = 3

# Parataxis: sentences of one clause each, set side by side with full stops where a subordinator would have joined
# them. Sentence length is NOT the measure. Measured on fresh model output, the lengths vary widely (a four-word punch
# after a twenty-word sentence is the same register); what is missing is subordination. A unit needs FLAT_SENTENCES to
# count, its mean must sit in the band a system prompt asking for "about 20 words" lands in (a list of six-word facts
# is not prose), and FLAT_SUBORD is the subordinators per sentence at or below which it is unjoined.
FLAT_SENTENCES, FLAT_SUBORD = 3, 0.0
FLAT_MEAN_LOW, FLAT_MEAN_HIGH = 9, 30
# Over 524 markdown files on this machine, a third of measurable paragraphs carrying no subordinator is the median, so
# the share alone separates nothing. The measurement is printed as an indicator once FLAT_MEASURED paragraphs exist to
# take a share of, and banded UNJOINED only at FLAT_SHARE with at least FLAT_LEAST such paragraphs.
FLAT_MEASURED, FLAT_LEAST, FLAT_SHARE = 6, 4, 0.6

# A landing sentence is a possible span on its own, and a habit at this rate: per 1000 words, with a floor so a short
# document cannot band on one.
LANDING_RATE, LANDING_LEAST = 1.5, 3

_SUBORD = re.compile(r"\b(?:because|although|though|while|whereas|since|unless|which|who|whose|whom|if|when|whenever"
                     r"|after|before|until|so that|as long as|even if|provided|where)\b", re.IGNORECASE)

# Sentence ends: terminal punctuation followed by space and a capital, digit or opening quote, or the end of the unit.
# Abbreviations and initials are checked separately against the text before the stop.
_END = re.compile(r"[.!?]+[\"'”’)\]]*(?=\s+[\"'“‘(\[]?[A-Z0-9]|\s*$)")
# No single-letter initial: "plan B." and "option A." end sentences in technical prose far more often than "J. Smith"
# occurs in it, and a regex cannot tell the two apart. No digit either, since "in 2024." ends a sentence and _END
# already refuses "3.10" on the missing space.
_ABBR = re.compile(r"\b(?:e\.g|i\.e|vs|etc|cf|approx|no|fig|dr|mr|mrs|ms|st|jr|sr|inc|ltd|co|dept|est)\.$",
                   re.IGNORECASE)
_LEAD = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(?:\[[ xX]\]\s*)?|^\s*>\s*|^\s*")
_WORD = re.compile(r"\S+")
_FIRST = re.compile(r"[\"'“‘(\[*_`]*([A-Za-z][\w'’-]*)")
_LINK = re.compile(r"\]\(|https?://")

# A colon counts as the end: "What we pay is not:" before a list is the same clipped figure.
_ELIDED = re.compile(r"\b(?:is|are|was|were|does|do|did|has|have|will|can|should|would)\s+not[.!:]?$", re.IGNORECASE)
_TAG = re.compile(r",\s*(?:and|but|which|though|or)\s+(?:we|it|they|you|i|that|this|he|she)\s+"
                  r"(?:should|do|does|did|is|are|was|were|will|can|could|would|has|have|had|must)"
                  r"(?:\s+not|n['’]t)?[.!?]?[\"'”’]?$", re.IGNORECASE)

CODE = re.compile(r"```.*?```|~~~.*?~~~|`[^`\n]+`", re.DOTALL)


def _mask(text):
    """Code replaced by a same-length run of `x`, so offsets hold and a dotted identifier is one word, not a stop."""
    return CODE.sub(lambda m: "x" * (m.end() - m.start()), text)


def sentences(text, start, end):
    """[(start, end, words)] for the sentences of text[start:end], offsets into `text`."""
    body = _mask(text)[start:end]
    lead = _LEAD.match(body)
    at = lead.end() if lead else 0
    out = []
    for m in _END.finditer(body):
        if m.end() <= at:
            continue
        chunk = body[at:m.end()]
        if _ABBR.search(chunk.rstrip("\"'”’)]").rstrip()) and m.end() < len(body):
            continue
        words = len(_WORD.findall(chunk))
        if words:
            out.append((start + at, start + m.end(), words))
        at = m.end()
        while at < len(body) and body[at].isspace():
            at += 1
    tail = body[at:]
    if tail.strip():
        out.append((start + at, start + len(body), len(_WORD.findall(tail))))
    return out


def line_offsets(text):
    """Start offset of each line, 1-indexed, with one past the end."""
    at, out = 0, {}
    n = 0
    for n, line in enumerate(text.splitlines(), start=1):
        out[n] = at
        at += len(line) + 1
    out[n + 1] = at
    return out


def _unit_span(text, at, unit):
    """Character span of a Unit, trailing newline excluded."""
    start = at[unit.start]
    end = at[unit.end + 1] - 1 if unit.end + 1 in at else len(text)
    return start, end


def _first_word(text, s, e):
    m = _FIRST.match(text[s:e].lstrip())
    return m.group(1).lower() if m else ""


def spans(text, units):
    """[(start, end, name, hit)] for the sentence-shaped tells, in the shape scan_spans returns.

    landing-sentence  a short closer after long sentences
    contrast-pair     a clipped "X is Y. Z is not." pair
    tag-clause        a sentence ending on ", and we should"
    anaphora          three or more sentences in a row opening on the same word
    """
    at = line_offsets(text)
    out, closers = [], []
    for u in units:
        s, e = _unit_span(text, at, u)
        sents = sentences(text, s, e)
        if not sents:
            continue

        if not u.listed and len(sents) >= LANDING_SENTENCES:
            *rest, (ls, le, lw) = sents
            closer = text[ls:le].strip()
            # A colon is a list being introduced, and a link is a pointer ("Source: [...]"), not a paragraph landed.
            if (lw <= LANDING_MAX and not closer.endswith(":") and not _LINK.search(closer)
                    and statistics.mean(w for _, _, w in rest) >= LANDING_REST):
                closers.append((ls, le, closer))

        for cs, ce, cw in sents[1:]:  # never the first sentence: the pair needs a sentence to contrast with
            if cw <= CONTRAST_MAX and _ELIDED.search(text[cs:ce].strip()):
                out.append((cs, ce, "contrast-pair", text[cs:ce].strip()))

        for ss, se, _ in sents:
            if (m := _TAG.search(text[ss:se].strip())):
                out.append((ss + m.start(), se, "tag-clause", text[ss:se].strip()[m.start():].strip()))

        run, word = [], ""
        for ss, se, _ in [*sents, (e, e, 0)]:
            w = _first_word(text, ss, se) if se > ss else ""
            if w and w == word:
                run.append((ss, se))
                continue
            if len(run) >= ANAPHORA_RUN:
                out.append((run[0][0], run[-1][1], "anaphora", word))
            run, word = [(ss, se)], w

    # A closer that opens the same way at the end of several paragraphs is a trailer the document uses as structure
    # ("Depends on M1.", "Depends on nothing."), not a beat performed once. The beat is what the rule is for.
    opening = Counter(_opening(c) for _, _, c in closers)
    out += [(ls, le, "landing-sentence", c) for ls, le, c in closers if opening[_opening(c)] < TRAILER_RUN]
    return sorted(out)


def _opening(closer):
    return " ".join(closer.lower().split()[:2])


def flat_units(text, units):
    """Every unit with enough sentences to measure: [(flat, start_line, end_line, sentences, mean, subord)].

    All of them, not only the flat ones, so the band can take a share. List items count: a changelog or a review
    written as multi-sentence bullets is where the register lives.
    """
    at = line_offsets(text)
    out = []
    for u in units:
        s, e = _unit_span(text, at, u)
        sents = sentences(text, s, e)
        if len(sents) < FLAT_SENTENCES:
            continue
        mean = statistics.mean(w for _, _, w in sents)
        subord = sum(len(_SUBORD.findall(text[ss:se])) for ss, se, _ in sents) / len(sents)
        flat = FLAT_MEAN_LOW <= mean <= FLAT_MEAN_HIGH and subord <= FLAT_SUBORD
        out.append((flat, u.start, u.end, len(sents), mean, subord))
    return out


def parataxis_stats(text, units):
    """Document-level parataxis measurement, or None with too few paragraphs to take a share of.

    {"flat": [(start, end, sentences, mean)], "measured": n, "share": 0.0-1.0, "band": "UNJOINED" or ""}. An empty band
    is the indicator without the verdict: printed as possible, for the reader to weigh.
    """
    measured = flat_units(text, units)
    if len(measured) < FLAT_MEASURED:
        return None
    flat = [(s, e, n, mean) for ok, s, e, n, mean, _ in measured if ok]
    share = len(flat) / len(measured)
    band = "UNJOINED" if len(flat) >= FLAT_LEAST and share >= FLAT_SHARE else ""
    return {"flat": flat, "measured": len(measured), "share": share, "band": band}


def landing_stats(text, units, found=None):
    """Landing sentences as a rate, or None below the gates. {"rate", "total", "words", "band": "HABIT"}."""
    found = spans(text, units) if found is None else found
    hits = [f for f in found if f[2] == "landing-sentence"]
    words = len(_WORD.findall(CODE.sub(" ", text)))
    if not words or len(hits) < LANDING_LEAST:
        return None
    rate = 1000 * len(hits) / words
    if rate < LANDING_RATE:
        return None
    return {"rate": rate, "total": len(hits), "words": words, "band": "HABIT"}


# Specifics a rewrite tends to add: the skill forbids new facts, so each of these in the rewrite and absent from the
# original is a fact to check against it. Not every hit is new: "three" rewritten as "3", or "it was found" as "we
# found", trips the pattern with nothing invented, which is why the anecdote shapes are the narrative ones only.
_NUMBER = re.compile(r"(?<![\w.])\d[\d,.]*%?(?![\w.])")
_WHEN = re.compile(r"\b(?:last (?:week|month|year|night|time)|yesterday|the other day|(?:a few|several|two|three) "
                   r"(?:weeks|months|days|years) (?:ago|back)|recently|earlier this (?:week|month|year)|this morning)\b",
                   re.IGNORECASE)
_ANECDOTE = re.compile(r"\b(?:I|we) (?:only )?(?:noticed|ran into|hit|spotted|realised|realized|stumbled)\b"
                       r"|\b(?:I|we) \w+ (?:this |it )?while (?:writing|testing|debugging|reviewing)\b"
                       r"|\bin my experience\b|\bthe hard way\b", re.IGNORECASE)
# Mid-sentence only, after a lowercase word or a comma: a sentence-initial capital is grammar, and an all-caps name
# (AWS) or one after a colon is not seen. The rubric says "mid-sentence name" for that reason.
_PROPER = re.compile(r"(?<=[a-z,;] )[A-Z][a-z]{2,}(?:[ -][A-Z][a-z]+)*")


def new_specifics(orig, new):
    """[(start, end, name, hit)] in `new` that `orig` does not contain: numbers, relative time, anecdote, proper nouns.

    Numbers are compared with thousands separators removed. Proper nouns are compared case-insensitively.
    """
    have = orig.lower()
    have_words = set(re.findall(r"[a-z][\w'’-]*", have))
    digits = orig.replace(",", "")
    code = [m.span() for m in CODE.finditer(new)]

    def outside(pos):
        return not any(a <= pos < b for a, b in code)

    out = []
    for m in _NUMBER.finditer(new):
        if outside(m.start()) and m.group(0).rstrip(".,").replace(",", "") not in digits:
            out.append((m.start(), m.end(), "new-number", m.group(0)))
    for pat, name in ((_WHEN, "new-time"), (_ANECDOTE, "new-anecdote")):
        for m in pat.finditer(new):
            if outside(m.start()) and m.group(0).lower() not in have:
                out.append((m.start(), m.end(), name, m.group(0)))
    for m in _PROPER.finditer(new):
        if outside(m.start()) and m.group(0).lower() not in have_words and m.group(0).lower() not in have:
            out.append((m.start(), m.end(), "new-name", m.group(0)))
    return sorted(out)
