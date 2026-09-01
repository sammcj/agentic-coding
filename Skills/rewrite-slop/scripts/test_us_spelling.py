#!/usr/bin/env python3
"""Word lists for the us-spelling rules in check_output.py. Standard library only.

    test_us_spelling.py            exit 0 if every word lands on the right side

Add to KEEP before widening a pattern. A rule that fires on rigorous, sizing or
dialogue costs a reader a lookup every time.
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_output import REPORT

RULES = [re.compile(p) for name, p, _ in REPORT if name == "us-spelling"]

CATCH = """
organize organizes organized organizing organization organizations organizational
realize realized recognize recognized prioritize prioritized customizable
normalize serialize tokenize sanitize optimizer standardization Organization
analyze analyzed analyzing analyzer paralyzed catalyzed
color colors colored coloring colorful colorless behavior behavioral behaviors
favor favors favorite favorites favorable honor honors honorable neighbor
neighborhood humor flavor flavors harbor rumors vapor armor armory endeavor
splendor valor savor savory odor candor clamor demeanor fervor parlor tumor
vigor labor ardor glamor rigor Color Behavior
center centers centered centering theater fiber fibers liter kilometers
caliber somber specter scepter luster maneuver maneuvers maneuvering
catalog catalogs cataloged dialog dialogs monolog epilog analog travelogs
defense defenses defenseless offense offenses pretense
traveled traveling traveler canceled canceling modeled modeling labeled
labeling signaled signaling fueled totaled counseled counselor marvelous
jewelry woolen enrollment fulfillment installment skillful willful distill
instill enroll fulfills
aluminum gray grayish mold molded moldy plow plowed smoldering airplane
aging acknowledgment math sizable practicing
"""

KEEP = """
size sizes sized sizing resize resized resizing downsize upsize oversize
capsize prize prizes prized maize baize seize seizes seized seizing assize
advise advised revise revised surprise comprise compromise exercise
improvise supervise televise franchise merchandise despise chastise incise
organise organised realise recognised prioritise customisable normalise
analyse analysed paralysed catalyse
colour colours coloured behaviour behavioural favour favourite honour
neighbour humour flavour harbour rumour vapour armour endeavour splendour
valour savour odour candour clamour demeanour fervour parlour tumour vigour
labour ardour glamour rigour
humorous vigorous glamorous laborious clamorous odorous rigorous
laboratory laboratories collaborator elaborate major minor senior junior
prior error mirror doctor actor factor motor sector vector monitor
centre centres centred theatre fibre litre kilometre calibre sombre spectre
lustre manoeuvre metre metres meter meters sceptic sceptical
bluster cluster fluster muster
catalogue catalogues dialogue dialogues monologue epilogue analogue
analogous analogy defence offence pretence defensive offensive
travelled travelling traveller cancelled cancelling modelled modelling
labelled labelling signalled fuelled totalled counselled counsellor
marvellous jewellery woollen enrolment fulfilment instalment skilful wilful
installed installing install fulfilled enrolled distilled instilled
aluminium grey greyish mould moulded plough ploughed smouldering aeroplane
ageing acknowledgement maths sizeable practising programs program artifact
artifacts licence license practice
"""


def main():
    if not RULES:
        print("no us-spelling rules found in REPORT")
        return 1

    wrong = 0
    for word in CATCH.split():
        if not any(r.search(word) for r in RULES):
            print("missed    %s" % word)
            wrong += 1
    for word in KEEP.split():
        hit = [i for i, r in enumerate(RULES) if r.search(word)]
        if hit:
            print("false +   %-16s rule %s" % (word, hit))
            wrong += 1

    print("%d must catch, %d must keep, %d wrong"
          % (len(CATCH.split()), len(KEEP.split()), wrong))
    return 1 if wrong else 0


if __name__ == "__main__":
    sys.exit(main())
