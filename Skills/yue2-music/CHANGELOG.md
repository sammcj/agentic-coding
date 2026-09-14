# Changelog

<!-- AI agents: log reader-visible changes only, one line each under a date heading (newest first). Squash same-day edits. No version numbers. -->

## 2026-09-14

- "Steer away from generic renditions" section in generation-and-covers.md; `assets/negative-style.patch` adds a `negative_style` request field (CFG negative branch keeps lyrics and ABC, swaps the style); `run_yue2.py` accepts `negative_style`, `abc_sampling`, `semantic_sampling`
- `run_yue2.py` records the command line, cwd and wall time (model load time for generate/plan); `listen.py` shows them with the per-stage timing under "Generation"
- Apple Silicon: MPS section in models-and-setup.md, `assets/mps-performance.patch` (bmm attention, int8 AR linears, `quantization="auto"` default), `run_yue2.py --device` defaults to `auto`
- Gotcha added: song length follows the planned score; trim ABC and regenerate to control it
- `listen.py` engraves each score with abcjs and highlights notes as the audio plays (`scripts/score-view.js`); `--no-notation` and `--abcjs` flags
- SKILL.md restructured: routing bullets, numbered setup with a single project-directory convention (`.venv-yue2`, `.venv-sheetsage2`, `models/SheetSage2`, `<skill>` scripts), Gotchas section; licence paragraph and pipeline diagram removed
- Description rewritten as one trigger per branch
- `agents/openai.yaml` (Codex-only) removed
- `assets/edit-brief.md` is now a template with `{goal}` and `{instrumentation}` placeholders
- References: Python blocks re-implementing `run_yue2.py` subcommands removed; repeated `model.transcribe()` examples collapsed to one; tables of contents added; prose tables and instruction paragraphs converted to bullets and steps
- Edit branch deduplicated: lyric mapping and chord-choice guidance live in abc-editing.md, editing-workflows.md keeps the contract bullets, manifest fields, reviewer blinding and worked example
- VAE rule, `--resume` note, `abc: null` gotcha, `listen.py` usage and snapshot flags stated once (SKILL.md or script `--help`)
- Australian English spelling throughout
