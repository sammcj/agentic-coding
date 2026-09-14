# Listening delivery and reproducible evaluation

Finish with audio the user can play and the exact conditions that produced it.

## Keep listening and scoring versions separate

Decoder choice follows the SKILL.md `YuE2-Vae` vs `YuE2-Vae-legacy` rule. Record full model names, revisions and hashes; the word "legacy" alone does not identify which decoder a score used.

1. Generate the acoustic latents once per song. A musical or lyric edit requires new generation; a decoder change does not.
2. Decode the same saved `latent.npy` for each requested decoder into a new native result directory:

```bash
.venv-yue2/bin/python <skill>/scripts/run_yue2.py decode --source outputs/jazz \
  --output outputs/jazz-evaluation --vae m-a-p/YuE2-Vae-legacy --vae-revision <verified>
```

3. Match the source result's model. Pass verified revisions for Hub models, or local snapshot directories with `--offline` (see `--help`).
4. Keep the source untouched. The new result retains the original request, exact plan/semantic tokens and latents, with the new decoder's identity, configuration and audio hashes.
5. Record the source latent hash and the decode-only operation. Decoder runtime is decode-only timing; report full generation speed only from a full generation run.
6. Never copy an old manifest over new audio, and never keep the listening decoder's identity on the evaluation audio.

A bare FLAC plus a custom decoder manifest is enough for listening. The complete kit's frozen evaluator needs a full native `SongResult.save_artifacts` directory instead: `result.json`, request/config, token arrays, latents and audio hashes.

## Build the listening comparison

- Run `scripts/listen.py` (see `--help`) with fresh output directories. Deliver the generated page alongside direct audio links when the interface supports playback.
- Include the full songs and useful excerpts for long edits. Start excerpts before the edited passage and include its exit; a few isolated notes hide transition problems.
- For a vocal rewrite, include enough verse and chorus to assess words and phrasing. For a theme/solo edit, include both complete theme statements and their continuation, not just the opening motive.
- Retain lossless generated audio even if making MP3 previews. A listening-page conversion is a delivery artefact; the frozen evaluation adapter applies its own recorded preprocessing.
- Never replace, normalise or alter the audio underlying recorded scores when refreshing listening links.
- Listen specifically for melody realisation, chord clashes at sustained notes, instrument choices, lyric omissions/repetitions, pacing, section transitions and the ending.
- If no audio audition capability was available, say which checks were actually performed rather than claiming to have heard the song.

Each listening entry identifies:

- Version and intended change, full style prompt, full lyrics and source/edited ABC.
- Actual model and decoder identity, seed, mode and any parameter overrides.
- Duration, truncation flags, structural/invariant checks and relevant change records.
- The complete audio, any excerpt's start/end times and whether it was normalised or otherwise processed.

## Separate the evidence

Each check supports one claim. Report it as that claim and nothing wider.

- Native ABC inspection - accepted structure, time grid and supported symbols; not pleasant harmony or audible adherence.
- Sounding-note comparison - specified symbolic pitches/onsets/durations preserved; not an identical generated performance or waveform.
- SheetSage2 transcription of generated audio - a diagnostic estimate of realised musical events; not error-free ground truth.
- ASR and phoneme error rate - recognised lyric/phoneme agreement under that protocol; not syllable-to-note synchronisation or correct note timing, and the scalar alone is not lyric verification.
- Audio forced alignment - estimated word/phoneme timing, when checked; not melody or arrangement quality.
- SongBench and other quality/control metrics - their named metric under the recorded evaluator; not proof of a specific instrument, jazz authenticity or universal quality. The global average is not a jazz or harmony-consistency score.
- Listening - the reported audible observations; not an automatic benchmark result or an unperformed preference study.
- A prepare-only validation - the inputs were accepted; not a measured score.
- `complete:true` in an evaluation summary - the requested metrics were produced; not quality acceptance.
- An average from a few self-written prompts, or a personal edit comparison - a small sanity check; not the full benchmark or an independent quality ranking.

Keep a designed lyric-phoneme-note sidecar separate from measured audio alignment. For claims of synchronised pronunciation, retain the aligner's output and review difficult words, melismas and instrumental sections. Keep model generation, benchmark measurement and musical judgement traceable as separate claims.

## Use a separate, complete benchmark package

- The public YuE2 runtime and this skill do not distribute the complete scoring code, evaluator weights or benchmark inputs. There are no `yue2 eval`, `bench` or `verify` commands.
- When a separate evaluation package is available, follow that package's documented entrypoints and frozen asset manifest.
- Before reproducing a published result, require the package's exact dataset/split definitions, preprocessing, decoder identity, scorer revisions and hashes.
- Use benchmark-decoded native result directories from `SongResult.save_artifacts`. Keep the reference lyric language and all attempted modes in the input record.
- If scoring assets are unavailable, deliver the listening and symbolic checks and report evaluation as unavailable. Do not substitute a similarly named metric or fabricate a score.
- Evaluator GPU requirements are separate from the 24 GB YuE2 generation baseline.

## Prepare public listening artefacts deliberately

- `listen.py --help` states what the bundle copies. Exact requests, local model paths and failure messages can still be present in copied files, so review the bundle before sharing it publicly.
- Share only the intended audio, scores, prompts, lyrics and public model identifiers. Omit private paths, account identifiers, raw logs and unrelated sidecars.
- Keep the original native result directory unchanged. Give a sanitised public metadata export its own manifest and hashes; the original generation receipt stays as generated.
- Do not alter or replace the preserved benchmark audio when updating listening previews.

## Report actual outcomes and preserve failed attempts

1. Retain the expected request list before running anything.
2. For each requested mode/version, record success or failure, the failure reason, both truncation flags, decoder identity and every completed metric.
3. Report sample counts and denominators. Keep partial/missing scores visible.
4. Report every mode and the pre-registered seed. Do not silently discard an unsuccessful mode or choose a favourable seed after seeing the scores.
5. For SongBench, retain its seven dimensions and the reported global average: Melody, Arrangement, Musicality, Vocal, Instrumental, Mixing and Structure. Identify the exact version and decoder for each result.
6. For PER, the checked protocol runs four ASR passes. Preserve their transcripts, selected result and first-pass result, and state the protocol when reporting the score. Label a single transcription as a single transcription, not as the four-pass protocol.
7. For revised English lyrics, check the reference language and the actual new lyric text, and inspect residual errors.
8. Report small sanity checks as small sanity checks.
