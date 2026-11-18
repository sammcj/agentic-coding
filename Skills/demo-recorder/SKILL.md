---
name: demo-recorder
description: Use when the user wants a scripted screen-recording demo video of a web app, a narration script or text-to-speech voice-over for one, or a dubbed cut.
metadata:
  version: 2026-11-18
---

Drives headless Chromium through a scripted walkthrough, encodes a silent 3K 60fps `demo.mp4`, then optionally voices the narration with Cloney, fits the recording to the voice and dubs it on. Below, `$M` means `make -f <this-skill-dir>/Makefile` and `<out>` means `~/Downloads/demo-recorder/<demo>/`; run `$M` from the directory holding `demos/`. `$M help` lists the targets and variables; each script in `scripts/` takes `--help`.

## Workflow

1. Create a task per step below, phrased with its completion criterion, then work them to completion.
2. Write `demos/<demo>.mjs` exporting `options`, `setup()`, `run(h, ctx)` and `teardown(ctx)`, modelled on `assets/examples/openspeccer.mjs`; the `h` helpers are in `scripts/lib/recorder.mjs`.
3. In `setup()`, record against a throwaway copy of the target so on-camera edits leave the user's repo untouched.
4. Call `h.scene("<name>")` at the start of each narrated section, and put an `h.wait` after each thing the narration names.
5. Write `demos/<demo>.md`: one `## N. Title` section per scene in recording order, an `_On screen: ..._` note, then the spoken text (example: `assets/examples/openspeccer.md`). Each sentence describes what is on screen while it is spoken. A section with no spoken text is a silent scene.
6. Run `$M record encode DEMO=demos/<demo>.mjs`. Done when `<out>/timings.tsv` lists every scene and you have viewed every image in `<out>/stills/`.
7. Fix what the stills show (missed click, wrong tab, personal paths via `options.hide`), then repeat step 6.
8. Spell-check the narration, show the user its full text and get their approval. Done when they approve. Audio renders are slow and a reworded section re-renders, so no audio is rendered before this.
9. Ask which Cloney character and engine to use (offer `$M voices`; defaults are in `scripts/narrate.sh --help`), unless the user records clips themselves as `N.wav` in `<out>/audio/`. If a `cloney` skill is available, activate it first; otherwise `cloney --help` covers the CLI.
10. Run `$M fitted DEMO=demos/<demo>.mjs VOICE=<character> ENGINE=<engine>`. It renders the clips, scales each scene's `h.wait` pauses so the scene ends just after its clip, records again and dubs. Done when the narrate table has no FAILED row, the fit table has no note asking for more or fewer actions, and the dub table has no "runs past scene" and no `(no clip)` row other than silent scenes.
11. View the new images in `<out>/stills/`, then report `<out>/demo-dubbed.mp4`.

## Longer videos and more voices

- **Segments:** write one demo per segment so each re-records alone. `$M each DO="record encode" DEMOS="demos/*.mjs"` runs targets for every demo; `$M join DEMOS="demos/*.mjs"` joins the cuts in filename order without re-encoding.
- **Another voice:** add `TAKE=<label>` to every command. A take has its own recording, clips and cut in `<out>-<label>/`, because a fitted recording suits one voice.
- **Unattended runs:** one `$M each DO=fitted ...` per take is one command to approve. A chain of separate commands stalls at the first unanswered prompt.

## Gotchas

- Chromium needs its own sandbox and Cloney needs Metal; both fail inside the agent sandbox, so run `record`, `narrate` and `fitted` unsandboxed.
- `record` installs Playwright into the skill directory on first run; that needs network access.
- Check clips with `ffprobe` and `ffmpeg -af volumedetect`; never play audio, leave listening to the user.
- Voices speak at 2 to 3.5 words per second, so a scene's length comes from `fit`, measured from the rendered clip. `fit` scales `h.wait` only; a scene with no `h.wait` cannot be fitted.
- A re-take of one scene: edit its text and run `$M fitted` again. `narrate.sh` re-renders only sections whose text or voice changed; `FORCE=1` re-renders all.
- Pass `VOICE`/`ENGINE` on every `narrate` and `fitted` for a non-default voice; omitting them re-renders every clip in the default voice.
- `narrate` transcribes every take and rejects one that says the wrong words (a fresh run usually fixes it); `TAKES=3` keeps the shortest that passes. `VERIFY=0` skips the check.
- Without Cloney, `narrate` and `dub` skip with a message; `$M demo` still produces the silent cut.
- `dub.sh` pairs clip `N.wav` with the Nth scene in `timings.tsv`; keep section numbers in scene order.
- The cursor is an injected overlay that only moves on mouse events; `h.moveTo` onto whatever the narration names. `h.cursor(false)` hides it on a slide.
- Small app text: `h.zoom(1.25)` after the page loads enlarges that page and keeps the cursor aligned.
- Title cards, slides and mocked screens are local HTML files opened with `h.page.goto` on a `file://` URL. Wait for the first screen to load before the first `h.scene`: the video opens on that frame, which is also its share preview.
- Keep spaces out of the `DEMO` path; make splits it and mangles the output folder name.
- `<out>/frames/` runs to about 800 MB per 90 s; offer to delete it once the cut is final.
