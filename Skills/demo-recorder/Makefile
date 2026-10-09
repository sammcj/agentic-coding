# Run from anywhere with: make -f <skill-dir>/Makefile <target> DEMO=path/to/demo.mjs
# Outputs land in OUT (default ~/Downloads/demo-recorder/<demo name>).
.PHONY: help install need-demo record encode narrate voices dub demo check

SKILL := $(patsubst %/,%,$(dir $(realpath $(lastword $(MAKEFILE_LIST)))))
S := $(SKILL)/scripts
NAME = $(basename $(notdir $(DEMO)))
OUT ?= $(HOME)/Downloads/demo-recorder/$(NAME)
SCRIPT ?= $(basename $(DEMO)).md
AUDIO ?= $(OUT)/audio

help:
	@echo "make install                 install Playwright and its Chromium into the skill"
	@echo "make demo DEMO=x.mjs         record, encode, narrate and dub into OUT (default ~/Downloads/demo-recorder/<name>)"
	@echo "make record DEMO=x.mjs       record only: frames/, frames.ffconcat, scenes.json"
	@echo "make encode DEMO=x.mjs       encode only: demo.mp4, timings.tsv, stills/"
	@echo "make narrate DEMO=x.mjs      text-to-speech each section of x.md into AUDIO (needs Cloney)"
	@echo "make voices                  list Cloney characters and their engines"
	@echo "make dub DEMO=x.mjs          lay AUDIO's clips (1.wav, 2.wav...) over demo.mp4, one per scene"
	@echo "Example demo: $(SKILL)/assets/examples/openspeccer.mjs; narrate takes VOICE, ENGINE etc, see $(S)/narrate.sh --help"

install:
	cd "$(SKILL)" && npm install && npx playwright install chromium

need-demo:
	@[ -n "$(DEMO)" ] || { echo "set DEMO=path/to/demo.mjs" >&2; exit 1; }

record: need-demo
	@[ -d "$(SKILL)/node_modules/playwright" ] || $(MAKE) -f "$(SKILL)/Makefile" install
	node "$(S)/record.mjs" "$(DEMO)" "$(OUT)"

encode: need-demo
	"$(S)/encode.sh" "$(OUT)"

narrate: need-demo
	"$(S)/narrate.sh" "$(SCRIPT)" "$(AUDIO)" "$(OUT)/timings.tsv"

voices:
	"$(S)/narrate.sh" --list

dub: need-demo
	"$(S)/dub.sh" "$(OUT)" "$(AUDIO)"

demo: record encode narrate dub

.NOTPARALLEL: # each step reads the previous one's output

check:
	shellcheck "$(S)"/*.sh
	node --check "$(S)/record.mjs" && node --check "$(S)/lib/recorder.mjs"
