---
name: demo-recorder
description: Use when the user wants a scripted screen-recording demo video of a web app, a narration script or text-to-speech voice-over for one, or a dubbed cut.
metadata:
  version: 2026-10-09
---

Drives headless Chromium through a scripted walkthrough, encodes a silent 3K 60fps `demo.mp4`, then optionally voices the narration with Cloney and dubs it on. Below, `$M` means `make -f <this-skill-dir>/Makefile`; run it from the directory holding `demos/`; output goes to `~/Downloads/demo-recorder/<demo>/` unless `OUT=` says otherwise. `$M help` lists the targets; each script in `scripts/` takes `--help`.

## Workflow

1. Create a task per step below, phrased with its completion criterion, then work them to completion.
2. Write `demos/<demo>.mjs` exporting `options`, `setup()`, `run(h, ctx)` and `teardown(ctx)`, modelled on `assets/examples/openspeccer.mjs`; the `h` helpers are in `scripts/lib/recorder.mjs`.
3. In `setup()`, record against a throwaway copy of the target so on-camera edits leave the user's repo untouched.
4. Call `h.scene("<name>")` at the start of each narrated section.
5. Write `demos/<demo>.md`: one `## N. Title` section per scene in recording order, an `_On screen: ..._` note, then the spoken text at about 2.2 words per second of scene (example: `assets/examples/openspeccer.md`).
6. Run `$M record encode DEMO=demos/<demo>.mjs`. Done when `~/Downloads/demo-recorder/<demo>/timings.tsv` lists every scene and you have viewed every image in `~/Downloads/demo-recorder/<demo>/stills/`.
7. Fix what the stills show (missed click, wrong tab, personal paths via `options.hide`), then repeat step 6.
8. Ask which Cloney character and engine to use (offer `$M voices`; defaults are in `scripts/narrate.sh --help`), unless the user records clips themselves as `N.wav` in `~/Downloads/demo-recorder/<demo>/audio/`.
9. Run `$M narrate DEMO=demos/<demo>.mjs VOICE=<character> ENGINE=<engine>`. Done when no row says FAILED or "runs past scene"; trim the text of any that do and re-run.
10. Run `$M dub DEMO=demos/<demo>.mjs`. Done when its table has no `(no clip)` row; then report `~/Downloads/demo-recorder/<demo>/demo-dubbed.mp4`.

## Gotchas

- Chromium needs its own sandbox and Cloney needs Metal; both fail inside the agent sandbox, so run `record` and `narrate` unsandboxed.
- `record` installs Playwright into the skill directory on first run; that needs network access.
- Check clips with `ffprobe` and `ffmpeg -af volumedetect`; never play audio, leave listening to the user.
- Breeze takes 35-75 s per clip. `narrate.sh` caches renders and re-renders only sections whose text or voice changed, so edit and re-run freely. Delete `~/Downloads/demo-recorder/<demo>/audio/.narrate/N.*` to re-render one clip; `FORCE=1` re-renders all.
- Pass `VOICE`/`ENGINE` on every `narrate` for a non-default voice; omitting them re-renders every clip in the default voice.
- Without Cloney, `narrate` and `dub` skip with a message; `$M demo` still produces the silent cut.
- `dub.sh` pairs clip `N.wav` with the Nth scene in `timings.tsv`; keep section numbers in scene order.
- The cursor is an injected overlay that only moves on mouse events; `h.moveTo` onto whatever the narration names, and `h.wait` before the next `h.scene` so the narration has room.
- Keep spaces out of the `DEMO` path; make splits it and mangles the output folder name.
- `~/Downloads/demo-recorder/<demo>/frames/` runs to about 800 MB per 90 s; offer to delete it once the cut is final.
