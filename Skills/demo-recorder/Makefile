# Run from anywhere with: make -f <skill-dir>/Makefile <target> DEMO=path/to/demo.mjs
# Outputs land in OUT (default ~/Downloads/demo-recorder/<demo name>, or <demo name>-<TAKE>).
.PHONY: help install need-demo need-demos record encode narrate voices fit fitted dub demo each join check

SKILL := $(patsubst %/,%,$(dir $(realpath $(lastword $(MAKEFILE_LIST)))))
S := $(SKILL)/scripts
SELF := $(MAKE) -f "$(SKILL)/Makefile"
ROOT ?= $(HOME)/Downloads/demo-recorder
# A take is a second cut of the same demos (another voice, say) with its own recordings, clips and pacing.
SUFFIX := $(if $(TAKE),-$(TAKE))
NAME = $(basename $(notdir $(DEMO)))
OUT ?= $(ROOT)/$(NAME)$(SUFFIX)
SCRIPT ?= $(basename $(DEMO)).md
AUDIO ?= $(OUT)/audio
# join: the demos to join in sorted order, which cut of each, and where the result goes.
PARTS = $(sort $(wildcard $(DEMOS)))
CUT ?= demo-dubbed.mp4
JOINED ?= $(ROOT)/joined$(SUFFIX).mp4

help:
	@echo "make install                 install Playwright and its Chromium into the skill"
	@echo "make demo DEMO=x.mjs         record, encode, narrate and dub into OUT (default $(ROOT)/<name>)"
	@echo "make record DEMO=x.mjs       record only: frames/, frames.ffconcat, scenes.json"
	@echo "make encode DEMO=x.mjs       encode only: demo.mp4, timings.tsv, stills/"
	@echo "make narrate DEMO=x.mjs      text-to-speech each section of x.md into AUDIO (needs Cloney)"
	@echo "make voices                  list Cloney characters, engines and references"
	@echo "make fit DEMO=x.mjs          write OUT/pace.json so each scene's pauses fit its clip on the next record"
	@echo "make fitted DEMO=x.mjs       narrate, fit, record again, encode and dub; needs one earlier record"
	@echo "make dub DEMO=x.mjs          lay AUDIO's clips (1.wav, 2.wav...) over demo.mp4, one per scene"
	@echo "make each DO='record encode' DEMOS='demos/*.mjs'   run targets for every demo in turn"
	@echo "make join DEMOS='demos/*.mjs'   join each demo's CUT (default demo-dubbed.mp4) into JOINED (default $(ROOT)/joined.mp4)"
	@echo "TAKE=<label> on any target keeps a second cut apart in $(ROOT)/<name>-<label>, e.g. one per voice"
	@echo "Example demo: $(SKILL)/assets/examples/openspeccer.mjs; narrate takes VOICE, ENGINE etc, see $(S)/narrate.sh --help"

install:
	cd "$(SKILL)" && npm install && npx playwright install chromium

need-demo:
	@[ -n "$(DEMO)" ] || { echo "set DEMO=path/to/demo.mjs" >&2; exit 1; }

need-demos:
	@[ -n "$(PARTS)" ] || { echo "set DEMOS to the demo scripts, e.g. DEMOS='demos/*.mjs'" >&2; exit 1; }

record: need-demo
	@[ -d "$(SKILL)/node_modules/playwright" ] || $(SELF) install
	node "$(S)/record.mjs" "$(DEMO)" "$(OUT)"

encode: need-demo
	"$(S)/encode.sh" "$(OUT)"

narrate: need-demo
	"$(S)/narrate.sh" "$(SCRIPT)" "$(AUDIO)" "$(OUT)/timings.tsv"

voices:
	"$(S)/narrate.sh" --list

fit: need-demo
	node "$(S)/fit.mjs" "$(OUT)" "$(AUDIO)"

# The second narrate re-fits the cached clips to the new scene lengths; it renders nothing.
fitted: need-demo
	$(SELF) narrate fit record encode
	$(SELF) narrate dub

dub: need-demo
	"$(S)/dub.sh" "$(OUT)" "$(AUDIO)"

demo: record encode narrate dub

each: need-demos
	@[ -n "$(DO)" ] || { echo "set DO to the targets to run, e.g. DO='record encode'" >&2; exit 1; }
	@for d in $(PARTS); do echo "== $$d"; $(SELF) $(DO) DEMO="$$d" || exit 1; done

join: need-demos
	"$(S)/join.sh" "$(JOINED)" $(foreach d,$(PARTS),"$(ROOT)/$(basename $(notdir $(d)))$(SUFFIX)/$(CUT)")

.NOTPARALLEL: # each step reads the previous one's output

check:
	shellcheck "$(S)"/*.sh
	node --check "$(S)/record.mjs" && node --check "$(S)/fit.mjs" && node --check "$(S)/lib/recorder.mjs"
