# Musical editing and agent delegation

An edit is a new musical version with a preserved source. YuE2 regenerates audio from the revised score, style and lyrics. It has no waveform inpainting and does not guarantee an identical performance outside the edited bars. Use [generation-and-covers.md](generation-and-covers.md) for the calls and [abc-editing.md](abc-editing.md) for notation, chord vocabulary, harmony judgement and lyric sidecars.

## Define the contract

SKILL.md steps 1-2 cover the baseline render and the invariant classes. Before delegating, pin down what "preserve the melody" means:

- Exact melody and rhythm - fixed: sounding pitch, note onset and duration in the named voices/passages; may change: harmony and arrangement around them.
- Same pitches, revised rhythm - fixed: ordered sounding pitches; may change: rhythm and articulation, each recorded explicitly.
- Recognisable theme - fixed: complete phrase sequence and the named repetitions; may change: listed embellishments only.
- Free adaptation within bounds - fixed: agreed phrases, range, contour, cadences or motifs; may change: the rest, with actual changed notes reported.

State whether tempo, meter, lyrics and instrumental passages may change. A tempo change preserves beat-relative rhythm but changes time in seconds.

For a style change, update the arrangement prompt along with the score. Example: a relaxed modern jazz version requests piano, tenor saxophone, upright bass, brushed drums, no guitar and 88 BPM in the prompt, with `Q:1/4=88` in the score too. Describing an instrument omission does not prove the generated audio omits it; listen for it.

## Delegate a bounded musical task

SKILL.md step 3 lists the inputs and the [edit brief](../assets/edit-brief.md) lists the constraints. Beyond those:

- Edit manifest fields: source hashes, changed bar/beat ranges, chord boundaries, note/rhythm changes, lyric changes, preserved invariants and the invariant-check result.
- Reviewer independence: give a separate reviewer the raw before/after ABC, requests, the user's constraints and available audio. Ask it to identify violations and musical problems from those artefacts before it sees the editor's diagnosis or rationale. Lead with the artefacts rather than "the problem is chord X", and ask for findings rather than endorsement of the proposed repair. Reconcile its findings with the editor's manifest afterwards.
- Without a delegation mechanism, run the edit and review passes yourself as separate steps. CPU score review can overlap other useful work.

## Reharmonise by listening to note spans

[abc-editing.md](abc-editing.md#reharmonisation-and-selective-melodic-editing) holds the chord vocabulary, the per-note judgement and example repairs. In addition:

- Introduce modern colour with a musical direction: secondary dominants into temporary tonal centres, a short ii-V, borrowed minor harmony, a tritone approach or a common-tone connection.
- Repair the smallest relevant span: move a resolution earlier, pick a chord core that supports a held melody pitch, change a bass inversion, or adapt one melodic approach when the contract permits it.
- Treat a sustained melody-voicing collision as a problem even over an altered dominant; its available tensions are not a blanket excuse.

## Worked example: complete theme, modern repeat, solo

This is an example brief, not the default task. It adapts a pop song to jazz with the complete "Twinkle, Twinkle, Little Star" theme stated twice, followed by a tenor saxophone solo. The full six-phrase scale-degree melody is:

```text
1 1 5 5 6 6 5
4 4 3 3 2 2 1
5 5 4 4 3 3 2
5 5 4 4 3 3 2
1 1 5 5 6 6 5
4 4 3 3 2 2 1
```

That is **42 sounding notes per statement, 84 for two complete statements**. These are phrases, not ABC bar lines. In D major, the opening phrase is D-D-A-A-B-B-A, and the next is G-G-F#-F#-E-E-D. Transpose using the active key; do not copy those absolute pitches into an unrelated key.

For this example:

1. Lead into the quotation with a short bridge and a melodic pickup sharing notes with the theme. Adjust the sung words to leave a natural breath and a clear handoff to saxophone.
2. State all six phrases once with clear rhythm and supportive harmony. A conventional quarter-quarter-quarter-quarter-quarter-quarter-half rhythm makes each phrase two 4/4 bars; other rhythms must be intentional.
3. State all six phrases a second time with more adventurous harmony. Keep the melody recognisable, use carefully prepared tonicisations or substitutions, and resolve sustained tensions. If changing the rhythm, retain the full pitch sequence and audit the permitted differences.
4. Develop the material into an eight-bar jazz solo: vary rhythm and register, answer fragments, then move toward a cadence returning to the song.
5. Keep the relaxed 88 BPM arrangement, piano, tenor saxophone, upright bass and brushes. If a short 3/4 transition helps, make the change explicit in both native voice blocks and verify the return to 4/4. Do not insert odd meters merely to make the arrangement seem advanced.

Place the instrumental theme/solo in the native `Ins` melody voice and put appropriate rests in `Vocal`. Retain harmony symbols in the native harmony-bearing voice even during vocal rests. A lyric tag such as `[saxophone solo]` and a matching style description help communicate intent, but are not a sample-accurate scheduling API. Validate all 84 merged note events before assessing the added solo separately.

## Adapt lyrics for singing

Follow the numbered list and sidecar example in [abc-editing.md](abc-editing.md#lyrics-syllables-and-phonemes).

## Render, compare and iterate

1. Run structural checks and the requested event comparisons before inference. Keep the original score and every attempted revision.
2. If the contract permits rhythm or melody changes, review the explicit differences rather than labelling a failed exact comparison "preserved".
3. Render the changed version with a new request and output directory.
4. Listen to full songs as well as excerpts beginning before and ending after the changed passage. Check the entry into the theme, its complete second statement, solo development, return to vocals and English diction where relevant. A same-seed comparison is useful provenance, not a guarantee of controlled acoustic variation.
5. If a requested property fails in the audio, revise and rerender it.
6. Report what is verified symbolically, what was observed by listening and what remains uncertain. Follow [listening-and-evaluation.md](listening-and-evaluation.md) to deliver the audio, actual prompts, score changes and evaluation evidence together.
