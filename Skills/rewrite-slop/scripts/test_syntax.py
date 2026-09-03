#!/usr/bin/env python3
"""Behaviour tests for syntax.py and the possible/probable split in check_output.py. Standard library only.

    test_syntax.py            exit 0 if every case lands on the right side

Each CATCH case is a passage the rule must flag, each KEEP a passage it must leave alone. Add to KEEP before loosening
a pattern.
"""

import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_output as co
import syntax

LONG = "The retry loop now computes its sleep from the attempt number and a cap that tests can shrink."

CATCH = {
    "landing-sentence": [
        f"{LONG} It is a different product.",
        f"{LONG} {LONG} Not Postgres.",
        f"{LONG} That is the whole trick.",
        # two of a kind is still a beat, and a third closer opening differently stays
        "\n\n".join([f"{LONG} Depends on M1.", f"{LONG} Depends on M2.", f"{LONG} Not Postgres."]),
    ],
    "contrast-pair": [
        "What we gain is small. What we pay is not.",
        f"{LONG} What we pay is not:",
        "The old loop honoured the deadline. The new one does not.",
    ],
    "tag-clause": [
        "Manageable if we keep the schema simple, and we should.",
        f"{LONG} The cache is cleared on deploy, which it should.",
        "The test covers the retry path, and it does.",
    ],
    "anaphora": [
        "The parser reads the header. The parser then reads the body. The parser closes the stream.",
        f"It runs once. It runs on a timer. It runs again on failure. {LONG}",
    ],
}

KEEP = {
    "landing-sentence": [
        "Run the tests. Fix the failures. Ship it.",  # all short: no long run to land after
        f"{LONG} The cap is ten seconds and the base is two hundred milliseconds.",
        f"- {LONG} Done.",  # a list item is exempt
        "It is a different product.",  # one sentence is not a paragraph
        f"{LONG} Three tests, in order:",  # a list being introduced
        f"{LONG} Source: [the schema](assets/schema.json).",  # a pointer, not a beat
        # the same trailer closing three paragraphs is the document's structure
        "\n\n".join(f"{LONG} Depends on M{n}." for n in (1, 2, 3)),
    ],
    "contrast-pair": [
        "The old loop honoured the deadline. The new one does not honour it either.",
        "What we pay is not.",  # nothing before it to contrast with
        f"{LONG} This is not a bug in the client.",
    ],
    "tag-clause": [
        "Manageable if we keep the schema simple, and we should keep it simple.",
        "The test covers the retry path, and it does so twice.",
        "We ran it, and it passed.",
    ],
    "anaphora": [
        "The parser reads the header. The parser then reads the body. A stream close follows.",
        "It runs once. Then it runs on a timer.",
    ],
}

SENTENCES = [
    ("Use e.g. the cap. Then stop.", 2),
    ("Version 3.10 shipped. It broke nothing.", 2),
    ("Dr. Smith agreed. So did we.", 2),
    ("Call `foo.bar()` first. Then `baz.qux()`.", 2),
    ("One. Two. Three.", 3),
    ("A sentence with no stop", 1),
    ("We shipped in 2024. The next one is due.", 2),
    ("Use plan B. Then C follows.", 2),
    ("It costs 5. It costs 6.", 2),
]

# Six paragraphs with no subordinate clause band UNJOINED; the same six joined do not.
FLAT = ("The parser reads the header first and keeps the declared length in a local. It then reads that many bytes "
        "of body into a buffer the caller passed in. The stream closes on the last byte and the buffer is returned.\n")
JOINED = ("The parser reads the header first, because the declared length is in it. It then reads the body into a "
          "buffer, which the caller owns. The stream closes when the last byte arrives, so the buffer is complete.\n")

NEW = (
    "The cache is read once. Values expire after a while.",
    "The cache is read twice, which I noticed last week when Redis failed. Values expire after 30 seconds.",
    {"new-anecdote", "new-time", "new-name", "new-number"},
)


def spans_for(text):
    return {name for _, _, name, _ in syntax.spans(text, co.units(text))}


def main():
    wrong = 0
    for rule, cases in CATCH.items():
        for text in cases:
            if rule not in spans_for(text):
                print("MISSED  %-16s %r" % (rule, text))
                wrong += 1
    for rule, cases in KEEP.items():
        for text in cases:
            if rule in spans_for(text):
                print("FALSE   %-16s %r" % (rule, text))
                wrong += 1

    for text, n in SENTENCES:
        got = len(syntax.sentences(text, 0, len(text)))
        if got != n:
            print("SPLIT   expected %d got %d  %r" % (n, got, text))
            wrong += 1

    orig, new, expect = NEW
    got = {name for _, _, name, _ in syntax.new_specifics(orig, new)}
    if got != expect:
        print("NEW     expected %s got %s" % (sorted(expect), sorted(got)))
        wrong += 1
    if syntax.new_specifics(orig, orig):
        print("NEW     the original against itself should add nothing")
        wrong += 1
    # An ordinary rewrite adds nothing: a de-nominalised verb, a numeral for a spelled number, a dropped separator.
    if syntax.new_specifics("Measurements were performed and it was found that 1,000 rows held.",
                            "We measured it and found 1000 rows held."):
        print("NEW     a de-nominalised rewrite flagged as new")
        wrong += 1

    # Parataxis: banded on the flat document, one finding row in the report, and nothing counted on the joined one.
    import render_report as rr
    flat_doc, joined_doc = "\n".join([FLAT] * 6), "\n".join([JOINED] * 6)
    st = co.parataxis_stats(flat_doc)
    if not (st and st["band"]):
        print("FLAT    six unjoined paragraphs did not band")
        wrong += 1
    rows = [f for f in rr.findings(flat_doc, rr.all_spans(flat_doc), rr.blocks(flat_doc), ["b%d" % i for i in range(9)])
            if f.rule == "flat"]
    if len(rows) != 1:
        print("FLAT    expected one flat row in the report, got %d" % len(rows))
        wrong += 1
    st = co.parataxis_stats(joined_doc)
    if st is None or st["band"] or st["flat"]:
        print("FLAT    six joined paragraphs measured as flat: %r" % (st,))
        wrong += 1
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as fh:
        fh.write(joined_doc)
        path = fh.name
    try:
        out = subprocess.run([sys.executable, co.__file__, path], capture_output=True, text=True).stdout
    finally:
        os.unlink(path)
    if "possible" in out.splitlines()[-1] or "? " in out:
        print("OUTPUT  a zero-flat measurement counted as possible:\n%s" % out)
        wrong += 1

    # emphasis-verb split: the literal character is not a filler verb
    hits = {n for _, n, _ in co.scan("A double underscore separates nested keys.", co.REPORT)}
    if "emphasis-verb" in hits or "filler-verb" in hits:
        print("FALSE   emphasis-verb on a literal underscore")
        wrong += 1
    hits = {n for _, n, _ in co.scan("This underscores the need for tests.", co.REPORT)}
    if "emphasis-verb" not in hits:
        print("MISSED  emphasis-verb on 'underscores the need'")
        wrong += 1

    hits = {n for _, n, _ in co.scan("The five ids stay distinct. Nothing collapses.", co.REPORT)}
    if "metaphor-tic" not in hits:
        print("MISSED  metaphor-tic on 'Nothing collapses.'")
        wrong += 1
    hits = {n for _, n, _ in co.scan("The schema is the contract between the two services.", co.REPORT)}
    if "metaphor-tic" not in hits:
        print("MISSED  metaphor-tic on 'is the contract'")
        wrong += 1
    hits = {n for _, n, _ in co.scan("She signed the contract on Monday.", co.REPORT)}
    if "metaphor-tic" in hits:
        print("FALSE   metaphor-tic on a literal contract")
        wrong += 1
    # byte-identical: the first use is a claim, the second is the habit.
    once = "The output is byte-identical to the previous build."
    if "byte-identical" in {n for _, n, _ in co.scan(once, co.REPORT)}:
        print("FALSE   byte-identical on a single use")
        wrong += 1
    if "byte-identical" not in {n for _, n, _ in co.scan(once + " The archive is byte for byte the same.", co.REPORT)}:
        print("MISSED  byte-identical on the second use")
        wrong += 1
    # "earns" weighs double in the register rate and is never a finding on its own.
    base = "The change is small and the tests already cover the path the reader will take through it. " * 12
    plain = co.register_stats(base + "It earns a ticket. " * 3)
    if plain is not None:
        print("EARNS   three uses banded a clean document on their own")
        wrong += 1
    if co.WEIGHTS.get("earns", 1) < 2 or any(w not in co.MARKERS for w in co.WEIGHTS):
        print("EARNS   weight missing or not in GROUPS")
        wrong += 1

    # Every shape rule and every renamed rule is classified, and the split reaches the printed output.
    for name in ("landing-sentence", "contrast-pair", "tag-clause", "anaphora", "corpus-noun", "emphasis-verb"):
        if name not in co.POSSIBLE:
            print("UNCLASSIFIED %s" % name)
            wrong += 1
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as fh:
        fh.write("Let me walk through why the cache is fast enough for every workload we have measured so far. "
                 "Studies show it holds. %s It is a different product.\n" % LONG)
        path = fh.name
    try:
        out = subprocess.run([sys.executable, co.__file__, path], capture_output=True, text=True).stdout
    finally:
        os.unlink(path)
    lines = out.splitlines()
    sure = [ln for ln in lines if "chat-residue" in ln]
    # "Studies show it holds." is four words after a long sentence, so LONG is what the landing sentence follows.
    maybe = [ln for ln in lines if ln.split(": ", 1)[-1].startswith("? ")]
    if not sure or any(ln.split(": ", 1)[-1].startswith("? ") for ln in sure):
        print("OUTPUT  a probable finding printed as possible, or not at all")
        wrong += 1
    if not any("weasel-source" in ln for ln in maybe) or not any("landing-sentence" in ln for ln in maybe):
        print("OUTPUT  possible findings missing from the ? block:\n%s" % out)
        wrong += 1
    if not any(co.POSSIBLE["weasel-source"] in ln for ln in lines):
        print("OUTPUT  caveat not printed")
        wrong += 1
    if not lines[-1].endswith("possible"):
        print("OUTPUT  tally line does not count possible: %r" % lines[-1])
        wrong += 1

    total = sum(map(len, CATCH.values())) + sum(map(len, KEEP.values())) + len(SENTENCES)
    print("%d cases, %d wrong" % (total, wrong))
    return 1 if wrong else 0


if __name__ == "__main__":
    sys.exit(main())
