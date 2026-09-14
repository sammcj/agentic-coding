# Generation, covers and reusable stages

- [Choose the conditioning mode](#choose-the-conditioning-mode)
- [Request fields](#request-fields)
- [Generate and save](#generate-and-save)
- [Export, edit and regenerate](#export-edit-and-regenerate)
- [Cover from a score or a recording](#cover-from-a-score-or-a-recording)
- [Preserve exact stage outputs](#preserve-exact-stage-outputs)
- [Decode cached latents](#decode-cached-latents)
- [yue2 CLI equivalents](#yue2-cli-equivalents)
- [CFG, defaults and evaluation scope](#cfg-defaults-and-evaluation-scope)
- [Steer away from generic renditions](#steer-away-from-generic-renditions)

Install and verify snapshots per [models-and-setup.md](models-and-setup.md). Record the package version, model revisions and weight hashes with each run. Validate a new installation with fresh outputs before treating it as a reproduced experiment.

## Choose the conditioning mode

- Generate melody, harmony and audio from text: `full`, omit ABC; YuE2 plans a melody with chords
- Generate a melody and then audio: `melody`, omit ABC; YuE2 plans without chord symbols
- Generate audio directly from text: `off`, ABC must be omitted
- Cover an existing melody in another style: `melody`, supply melody-only ABC with chord symbols removed
- Reharmonise or otherwise edit a score: `full`, supply the edited melody-and-chord ABC

- Each mode selects its own native instruction. Leave that instruction alone and put musical direction in `style`.
- An external ABC input bypasses the symbolic planner and nothing repairs the score. Validate it first per [abc-editing.md](abc-editing.md).

## Request fields

- Accepted: `style`, `lyrics`, `cot`, `seed`, `abc`, `cfg_scale`, `id`, `abc_sampling`, `semantic_sampling`. `tags` is an alias for `style`; if both appear they must agree. `negative_style` needs `assets/negative-style.patch` (install block in [models-and-setup.md](models-and-setup.md#yue2)) and an explicit `cfg_scale` other than 1.
- No field exists for `reference_audio`, `phonemes`, `bpm`, an edit interval or a reference singer.
- Put tempo and meter in the ABC and describe them the same way in `style`.
- Pronunciation and note-alignment instructions belong in validation sidecars. They are not conditioning inputs.
- Request JSON for `scripts/run_yue2.py` and the `yue2` CLI may use `abc_path` relative to the request file. The Python API takes `abc` text.

## Generate and save

- All three modes from one text-only request: `run_yue2.py all-modes`. Keep the full sectioned lyrics in the request.
- Verify Hub revisions independently before passing them. Keep Hub tokens in the authentication environment, out of scripts and manifests.
- `save_artifacts` writes `audio.flac`, `score.abc` when applicable, exact ABC/prefix IDs, semantic tokens, `latent.npy`, the request, configuration, timing, decoder identity and hashes. `song.save("song.flac")` or `.save("song.wav")` writes audio only. MP3 is a separate delivery conversion.
- The Python save methods overwrite existing files. Write every run to a fresh directory; `run_yue2.py` refuses an existing one.
- `status="complete"` does not mean untruncated. Check both ABC and semantic truncation flags, then duration, the ending, audibility and the requested musical behaviour.

## Export, edit and regenerate

1. Plan once: `run_yue2.py plan --cot full`.
2. Keep that directory immutable. Copy `score.abc` to `edits/<name>.abc` and edit the copy.
3. Validate the edit per [abc-editing.md](abc-editing.md).
4. Regenerate: `run_yue2.py generate --cot full --abc-file <edited.abc>` with the revised request.

Regeneration uses the revised musical conditions. It does not promise unchanged waveforms, singer identity or performance outside the edited passage. A fixed seed makes comparisons easier to trace.

## Cover from a score or a recording

- Score cover: `run_yue2.py generate --cot melody --abc-file <melody.abc>` with a validated melody-only ABC and the target lyrics in the request.
- Audio cover: the SKILL.md "Cover a recording" steps. Obtain or check the lyrics separately.
- Source separation, transcription, lyric recognition and score-conditioned generation are separate operations. YuE2 has no audio-upload argument, and its VAE encoder is not a melody transcriber.

## Preserve exact stage outputs

```python
from yue2 import SymbolicPlan, YuE2Pipeline

plan = SymbolicPlan.load("outputs/original_plan")
with YuE2Pipeline.from_pretrained(model, vae=listening_vae, device="cuda", local_files_only=True) as pipe:
    semantic = pipe.generate_semantic(plan)
    latents = pipe.synthesize(semantic)
    audio = pipe.decode(latents)
```

- This continues the saved plan without decoding and retokenising its ABC.
- `SymbolicPlan.load` verifies the manifest and token arrays, so editing a file inside a saved plan fails validation.
- There is no `SemanticResult.load`, `SongResult.load` or partial resume. Stage calls return objects and arrays, so a custom staged runner must save the plan, exact semantic tokens, latent array and provenance itself.
- Changing style, lyrics or ABC needs new semantic generation and synthesis. Cached latents are reusable only when the decoder alone changes.

## Decode cached latents

- Re-decode a verified `SongResult` directory with another decoder: `run_yue2.py decode` (command in [listening-and-evaluation.md](listening-and-evaluation.md)). The script writes the new audio and manifest to a fresh directory, records both decoder identities and checks the latents are unchanged. Keep the two audio files and their manifests separate.
- This loads the decoder without generating a new song. Accepted latent shapes are `[T,64]` and `[1,64,T]`; the output array is samples x two channels.
- `pipe.decode(latents, vae=...)` exists but accepts no separate revision argument. Use a verified local snapshot, or a second pipeline configured with the evaluation VAE.

## yue2 CLI equivalents

Given request JSON containing `id`, `style`, `lyrics` and optionally `seed`:

```bash
yue2 generate --request requests/original.json --cot full --output outputs/full
yue2 generate --request requests/original.json --stage plan --output outputs/plan
yue2 generate --request requests/jazz.json --cot full --abc-file edits/jazz.abc --output outputs/edited
yue2 generate --request requests/cover.json --cot melody --abc-file edits/source_melody.abc --output outputs/cover
yue2 batch --input requests/all.jsonl --output outputs/batch
```

- Output nests under `--output/<request-id>/`.
- Batch requests need unique IDs and run sequentially.
- CLI stages are `plan` and `audio` only. Semantic, synthesis and decode are Python stage calls.

## CFG, defaults and evaluation scope

- Semantic CFG defaults: 1.0 in `full` and `melody` (guidance off), 1.01 in `off`. Set `cfg_scale` in the request (CLI `--cfg-scale`). Each value above 1 costs a second AR forward pass per token.
- With a score, the negative branch keeps the same instruction and exact ABC and drops style and lyrics. With `negative_style` it keeps the lyrics too and swaps the style for the negative text. ABC generation and NAR synthesis have no CFG.
- Sampling defaults: planner temperature 0.7, top_p 0.9, top_k 30, repetition penalty 1.005; semantic temperature 1.0, top_p 0.95, top_k 100, repetition penalty 1.2. Override with `abc_sampling` / `semantic_sampling` objects in the request.
- Standard preset: BF16 AR/NAR, FP32 VAE, 32 midpoint synthesis steps, context 24576. Keep it for reproducible comparisons; a backend or precision change needs its own validation.
- The public runtime provides `yue2 doctor`, `generate`, `batch` and the Python API. Frozen benchmark scoring needs separate code and assets; see [listening-and-evaluation.md](listening-and-evaluation.md).
- SongBench scores, ASR/PER, score checks and listening answer different questions. Report the checks actually run, and retain failures, truncation flags and every requested mode. None alone proves score or phoneme adherence in the audio.

## Steer away from generic renditions

A bare genre label lands on the most common recordings with that label: "black metal" tends toward hard rock or nu-metal, "progressive metal" toward alternative metal. Two mechanisms cause this. The style string conditions the semantic tokens once, with guidance off by default, so nothing amplifies the rare parts of the description. And the planner samples conservatively (temperature 0.7, top_k 30), so the score it writes is a 4/4 verse-chorus template that then fixes melody, harmony, phrase lengths and duration before the style string can act.

Levers, strongest first:

1. Write or edit the ABC. Riff figures, metre, key, phrase lengths, dissonance and section order come from the score, not the prompt.
   - The planner takes tempo and section order from the request ("92 BPM" gave `Q:1/4=93`, lyric tags gave matching `%` sections) and ignores key and metre ("D minor, odd metres 7/8 5/4 and 11/8" gave `K:F#m`, `M:2/4`).
   - Odd groupings, tritones, held drones and long rests survive into the audio; the same words in `style` did not in the runs tried. Drums, production and mix are absent from the score and respond only to the levers below.
   - A chorus that turns pop whatever the prompt says usually has a pop chorus in the score: the vocal leaps up an octave, holds long notes and sits over a major chord (`"Bmaj7"` in a `D#m` song). Keep the chorus vocal inside the verse range, phrase it off the downbeat in the riff's grouping, and put a tritone or the minor tonic under it.
2. Name the instruments as physical objects in `style`, and list their electronic stand-ins in `negative_style`. Under guidance the model drifts to synthetic timbres (synth bass, keyboard pads, vocoder-like vocal layers) unless told otherwise. "real amplified electric guitars through valve amps, fingerstyle electric bass, acoustic drum kit, single dry male baritone lead vocal" with a negative of "backing vocals, vocal harmonies, choir, pitch-shifted vocal effect, synthesizer, synth bass, keyboards, electronic drums" gave the best guitar tone and vocal of eight variants on one score. "wah" reads as a filter sweep and invites synths.
3. Set `cfg_scale` 2.0 with `--abc-file` and a `negative_style` naming the generic neighbour: "pop, mainstream rock, nu-metal, radio-friendly, clean polished production, simple straight rock drumming, chunky power chords, soaring melodic chorus, vocal hook, singalong". Guidance then pushes along the axis between the two descriptions instead of away from the same score with no style or lyrics. On one score and seed: 2.0 without a negative gave prog-pop; 1.5 with a negative gave corny synth keys; 3.0 with a negative gave a doom vocal over a synthetic, muted backing. Compare against the 1.0 baseline with the same seed and score.
4. Write `style` as language first, BPM last, with playing and production vocabulary between: techniques (alternate-picked sixteenths, tom-led patterns with ghost notes), era and room (dry early nineties studio recording, no audience), vocal register and delivery (bass-baritone, half-spoken, restrained). Adjacent sub-genres narrow the distribution; a single label widens it. Words seen to have a generic prior (one run each): "alternative metal" pulled toward nu-metal, "live-room" added crowd noise. Renaming `[Chorus]` to `[Refrain]` (and `% chorus`) did no harm in one run.
5. Loosen the planner: `"abc_sampling": {"temperature": 0.95, "top_k": 50}` produces less template-like scores. Run `plan` several times with different seeds, inspect with `abc_tools.py inspect`, keep the best and edit it.
6. Generate two or three seeds per prompt. Semantic sampling already runs wide (temperature 1.0, top_k 100); seed variance is large and cheap compared with prompt iteration.
7. `cot="off"` skips the planner. The score's template no longer constrains the song, and neither does anything else; use it when the plan itself is the problem and the ABC cannot be written by hand.
