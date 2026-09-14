---
name: yue2-music
description: Use when generating songs with YuE2, covering a recording via SheetSage2 audio-to-ABC, editing a score or lyrics with melody preservation, or building a reproducible listening comparison of YuE2 output
disable-model-invocation: true
---

# YuE2 Music

Turn a musical request into a reproducible song and an audible comparison. Retain the original song and its plan before changing anything.

## Choose the workflow

- Generate with editable melody and harmony: YuE2 `cot="full"` -> ABC -> song
- Generate with a melody plan and free accompaniment: YuE2 `cot="melody"` -> chord-free ABC -> song
- Generate without symbolic planning: YuE2 `cot="off"` -> song (no editable ABC)
- Cover a recording: SheetSage2 -> inspect and correct ABC -> strip chords -> YuE2 `melody`
- Cover an ABC melody: inspect or convert native ABC -> strip chords -> YuE2 `melody`
- Change harmony, instruments, tempo, structure or lyrics: copy the full plan -> edit ABC or text -> regenerate
- Agentic editing: export plan and baseline -> bounded editing agent -> check invariants -> render -> compare
- Analyse continuous musical features: MERT2, see [models-and-setup.md](references/models-and-setup.md#optional-mert-representations)

## Set up

Read [models-and-setup.md](references/models-and-setup.md) for model IDs, install pins and licences.

1. Work from a project directory, never inside this skill folder. `<skill>` in commands below is this skill's directory.
2. Create `.venv-yue2` in the project and install the YuE2 runtime from the official GitHub repository source.
3. Create `.venv-sheetsage2` separately (dependency pins differ) and download the SheetSage2 snapshot to `models/SheetSage2`.
4. Record every model revision you download.
5. Run on the supported baseline: one request at a time, BF16-capable NVIDIA GPU with 24 GB VRAM, default YuE2 settings. On Apple Silicon follow the MPS section of models-and-setup.md; scripts auto-detect the device.
6. Scripts default to Hub model IDs; see each script's `--help` for local snapshot and revision flags. Use a fresh output directory per run.

## Generate and retain the plan

Copy [assets/prompt.json](assets/prompt.json) to `requests/<id>.json` and edit it. Put genre, instruments, vocal character, language and tempo in `style`; put section tags and the actual words in `lyrics`. Keep implementation notes out of lyrics.

```bash
.venv-yue2/bin/python <skill>/scripts/run_yue2.py generate --request requests/song.json --output outputs/pop
.venv-yue2/bin/python <skill>/scripts/run_yue2.py all-modes --request requests/song.json --output outputs/modes
.venv-yue2/bin/python <skill>/scripts/run_yue2.py plan --request requests/song.json --output outputs/plan
```

Inspect `result.json`, truncation, `score.abc`, `request.json` and audio. The helper saves native artefacts including exact tokens and `latent.npy`; keep them. Preserve every requested mode and every failure. A playable file does not establish musical quality.

Read [generation-and-covers.md](references/generation-and-covers.md) for the Python interface, exact plan continuation, CFG, sampling and cached decoding. For a niche or extreme genre, or when a result sounds like the mainstream version of what was asked, apply its "Steer away from generic renditions" section before changing the prompt again.

## Cover a recording

1. Transcribe in the SheetSage2 environment. Select the vocal melody or the full lead melody including instrumental passages.
2. Inspect warnings. Correct missed notes, meter or key before attributing errors to YuE2. Preserve source audio and raw transcription.
3. Export chord-free ABC. When dropping a part, select the retained voice explicitly; stripping chords alone should preserve both melodic voices and their rests.
4. Render with `cot="melody"`, target style and suitable lyrics. To retain the original harmony as well, transcribe in full and use `cot="full"`.

```bash
.venv-sheetsage2/bin/python <skill>/scripts/transcribe.py reference.wav --task melody-full --output outputs/transcription
python3 <skill>/scripts/abc_tools.py strip-chords outputs/transcription/score.abc outputs/cover.abc

# The request supplies target style and lyrics.
.venv-yue2/bin/python <skill>/scripts/run_yue2.py generate --request requests/cover.json --cot melody \
  --abc-file outputs/cover.abc --output outputs/cover-song
```

## Edit or delegate an edit

Read [editing-workflows.md](references/editing-workflows.md) and [abc-editing.md](references/abc-editing.md) before changing a score. Create a task per step below, each with its completion criterion, then work them to completion.

1. Render a baseline from the full plan. Freeze its directory.
2. Define invariants: exact pitches; pitch plus rhythm; contour only; or bounded melodic adaptation. Name the voices, passages, lyrics, instruments, tempo, meter and structure covered.
3. Delegate when possible: fill in the [edit brief](assets/edit-brief.md) and give a score-editing agent the raw ABC, prompt, lyrics and requested change. Request a new ABC, revised style or lyrics as needed, and an edit manifest. Give a separate reviewer the before/after artefacts and constraints. Without delegation, perform each stage yourself. Keep model generation sequential per GPU.
4. Check musical events, not character strings: ties, accidentals and compressed rests matter.

   ```bash
   python3 <skill>/scripts/abc_tools.py inspect edits/jazz.abc
   python3 <skill>/scripts/abc_tools.py compare outputs/plan/score.abc edits/jazz.abc --voices Vocal
   .venv-yue2/bin/python <skill>/scripts/run_yue2.py generate --request edits/jazz.json --cot full \
     --abc-file edits/jazz.abc --output outputs/jazz
   ```

   Add `--allow-tempo-change` for intentional tempo changes. Exact comparison fails on intentional rhythm changes; audit the permitted differences from its report and label the result accordingly.
5. Regenerate after changing style, lyrics or ABC. Old acoustic latents can be decoded again but do not contain a musical or lyric edit.
6. Compare full songs and short passages around the edit. Revise when the requested effect fails. Retain each attempt with its actual prompt.

For lyric translation, follow the syllable mapping steps in abc-editing.md and keep the sidecar. Use ASR/PER and listening as separate evidence.

## Deliver an audible result

Read [listening-and-evaluation.md](references/listening-and-evaluation.md).

```bash
python3 <skill>/scripts/listen.py outputs/pop outputs/jazz --output outputs/comparison
```

This builds a local HTML player with each score engraved (abcjs, as on the YuE2 demo page); notes turn red as the recording plays. Nothing is uploaded; the only fetch is the pinned abcjs build, avoided with `--abcjs <file>` or `--no-notation`. Return playable audio, full prompt and lyrics, before/after ABC, invariant checks and requested evaluations. Keep model and decoder identity and failures visible. Deliver edit manifests and comparison reports alongside the page.

## Gotchas

- Public MERT feature tensors are not YuE2 codec tokens. YuE2 has no audio-reference, phoneme-alignment or local-inpainting argument; condition through style, lyrics and ABC only.
- `YuE2-Vae` is for listening. `YuE2-Vae-legacy` is for reproducing the supplied benchmark protocol. Keep decoded files separate; the name "legacy" says nothing about which is newer or better.
- On OOM, free allocations or move to suitable hardware and report the change. Shortening the song or lowering inference settings without saying so hides the failure.
- Song length follows the planned score, not the prompt. "Short song" in `style` or few lyric lines still yields a 4-6 minute plan padded with interlude until the token cap. To control length, run `plan`, trim `score.abc` to the wanted bars (`abc_tools.py inspect` reports nominal seconds), end on a held note so the song does not stop mid-riff, and regenerate with `--abc-file`.
- `cfg_scale` defaults to 1.0 in `full` and `melody` (1.01 in `off`), which is guidance off: the style string conditions the semantic tokens once and nothing amplifies it. A genre label alone yields its most common form. Raise `cfg_scale`, add `negative_style`, and write the score yourself; see generation-and-covers.md.
- `run_yue2.py` has no resume; after an interrupted run, rerun into a fresh directory. The upstream `yue2 --resume` flag reuses a completed matching result only.
- Keep an edited score connected through `--abc-file` or request `abc_path`. A request with `abc: null` and no file generates a fresh plan and discards the edit.
- Load unchanged plans with `SymbolicPlan.load`; submit modified ABC as a new input.
- `cot="melody"` does not strip chord symbols; run `abc_tools.py strip-chords` first.
- Melody conditioning supplies a symbolic melody. It does not preserve the source singer's identity or waveform.
- There is no `phonemes` request field. The syllable sidecar is bookkeeping, not acoustic alignment.
- An ABC check or SongBench score does not show exact note realisation, instrument removal or sample-accurate preservation. Listen.
