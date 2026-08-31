#!/usr/bin/env python3
"""Compare check_output.py's register vocabulary against the current load-bearing data.

    refresh_markers.py [--data PATH] [--top N]

Reports only. It never edits check_output.py, because deciding which of a cluster's
high-lift words are style rather than subject matter is a judgement call and the
last curation pass dropped roughly a third of the candidates by hand.

The source is louisabraham.github.io/load-bearing, which re-fits daily from GitHub
pull request descriptions. Get or update the data with:

    git clone https://github.com/louisabraham/load-bearing ~/git/load-bearing
    git -C ~/git/load-bearing pull

Standard library only. Reads analysis.js, which is `window.ANALYSIS = {json};`.
"""

import argparse
import json
import os
import re
import sys

DEFAULT_DATA = os.path.expanduser("~/git/load-bearing/analysis.js")

# Words deliberately excluded during curation: ordinary function words the density
# cannot use, and CI/testing jargon that lifts on the corpus's subject matter
# rather than on style. Listed so a refresh does not keep re-proposing them.
DECLINED = frozenset("""
ever alone rather half whole its every two three own against exactly worth held
stays leaves lives asked caught told says said dropped shipped worse worst cheap
bare eight nine ten eleven twelve thirteen fourteen fourth fifth sixth reds incl
byte-identical bit-identical byte-for-byte byte-identity byte-exact mutation-checked
mutation-verified mutation-tested unit-tested unit-testable held-out wall-clock
goldens mutant mutants re-derived re-derive re-derives re-deriving re-verified
re-measured re-read re-reads re-checked re-confirmed re-runs live-verified pre-fix
post-fix root-caused mid-flight mid-run round-1 round-2 phase-2 fall-through fan-out
hand-written hand-rolled hand-maintained cross-checked back-compat no-ops in-flight
behaviour-preserving fleet-wide fail-loud -only spellings corpus prose idiom census
""".split())


def load(path):
    try:
        raw = open(path, encoding="utf-8").read()
    except OSError as exc:
        sys.exit("%s\n\nClone or update the data first:\n"
                 "    git clone https://github.com/louisabraham/load-bearing "
                 "%s" % (exc, os.path.dirname(path) or "~/git/load-bearing"))
    start, end = raw.index("{"), raw.rstrip().rstrip(";").rindex("}") + 1
    return json.loads(raw[start:end])


def current_groups():
    """Read GROUPS out of check_output.py without importing it."""
    src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "check_output.py"), encoding="utf-8").read()
    body = src.split("GROUPS = {", 1)[1].split("\n}", 1)[0]
    groups = {}
    for name, words in re.findall(r'"([a-z-]+)":\s*"{1,3}(.*?)"{1,3},', body, re.S):
        groups[name] = set(words.split())
    return groups


def main():
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--data", default=DEFAULT_DATA, help="path to analysis.js")
    ap.add_argument("--top", type=int, default=300,
                    help="how far down the lift ranking to look (default 300)")
    args = ap.parse_args()

    data = load(args.data)
    lead = next((c for c in data["components"] if c.get("lead")), None)
    if lead is None:
        sys.exit("no lead component in %s; the daily fit may have failed" % args.data)

    ranked = sorted(zip(lead["word_list"], lead["word_lift"]),
                    key=lambda x: -x[1])[:args.top]
    top = {w for w, _ in ranked}
    groups = current_groups()
    known = set().union(*groups.values()) if groups else set()

    print("data generated %s, %d weeks, %s descriptions"
          % (data.get("generated", "?"), len(data.get("weeks", [])),
             format(data.get("documents", 0), ",")))
    print("lead cluster %.1f%% -> %.1f%% of the sample, %d words ranked, top %d examined\n"
          % (100 * lead["start_share"], 100 * lead["end_share"],
             len(lead["word_list"]), args.top))

    new = [(w, l) for w, l in ranked if w not in known and w not in DECLINED]
    print("CANDIDATES: %d words in the top %d that are neither grouped nor declined."
          % (len(new), args.top))
    print("Judge each one: style keeps, subject matter goes to DECLINED.\n")
    for w, l in new:
        print("  %-22s lift %5.1f" % (w, l))

    gone = sorted(w for w in known if w not in top)
    print("\nDROPPED OUT of the top %d (%d). Falling lift is not itself a reason to "
          "remove one;\nthe list is here so a word that has genuinely stopped being "
          "characteristic can be seen.\n" % (args.top, len(gone)))
    print("  " + ", ".join(gone) if gone else "  none")

    print("\nEdit GROUPS in check_output.py by hand, keep the Tier 2 lists in SKILL.md "
          "in step\n(the group names are shared), then note the change in CHANGELOG.md.")


if __name__ == "__main__":
    main()
