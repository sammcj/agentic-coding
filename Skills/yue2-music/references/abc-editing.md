# Edit the score while preserving its musical meaning

- [Native format](#native-format)
- [Accidentals and ties need musical interpretation](#accidentals-and-ties-need-musical-interpretation)
- [Portable inspection and cover preparation](#portable-inspection-and-cover-preparation)
- [Reharmonisation and selective melodic editing](#reharmonisation-and-selective-melodic-editing)
- [Lyrics, syllables and phonemes](#lyrics-syllables-and-phonemes)
- [Native serialisation, rendering and audio checks](#native-serialisation-rendering-and-audio-checks)

Start from the plan's `score.abc`, or SheetSage2's exported `score.abc` when covering a recording. Keep the source untouched and write a new edited file. Model-generated plans and transcriptions contain mistakes; inspect them before treating them as a musical reference.

`scripts/abc_tools.py` is a standard-library implementation of a **bounded native ABC dialect**. It checks structure and exact symbolic melody. It does not cover the entire ABC standard, force the generator to follow the score, or measure perceptual harmony.

## Native format

Preserve the source's format, key, register, voices and section boundaries. The key is not fixed to D. A typical header:

```abc
X:1
T:
M:4/4
L:1/32
Q:1/4=88
V: Vocal clef=treble name="Vocal Melody" snm="Vocal"
V: Ins clef=treble name="Ins Melody" snm="Inst."
K:G
% verse
V: Vocal
"Gmaj7"B8d8"Am7"c8A8|"D7"F16"G"G16|
V: Ins
Z2|
```

- This is a two-bar format example, not a complete song.
- Both parts are monophonic melody lines. `Ins` holds an instrumental theme or solo; it is not a chord-voicing staff.
- Harmony is written as quoted symbols in `Vocal`, including while that part rests.
- The exporter groups one to four measures at a time: a `V: Vocal` block then a `V: Ins` block. `% verse`, `% chorus`, `% bridge`, `% interlude` and similar comments delimit structure.
- A meter or key change starts a new group with matching `M:` or `K:` fields in both voice blocks. An inline `[K:...]` change may sit inside a measure, but both voices must change key at the same musical time.
- `L:1/32` is common, not universal; the exporter picks the denominator its rhythmic grid needs. Preserve the exported `L:`.
- The helper accepts `L:1/<power of two>` through 1/1024, fractional meters such as `3/4`, `6/8` and `7/8`, standard major/minor keys, and a positive integer quarter-note tempo.

With `L:1/32`:

| Notation | Meaning |
|---|---|
| `C` / `C2` / `C8` | C4 for one thirty-second / one sixteenth / one quarter note |
| `c`, `c'`, `C,` | C5, C6, C3 |
| `z8` | Quarter-note rest |
| `Z`, `Z2`, `Z3`, `Z4` | One, two, three, four complete resting measures in the current meter |
| `C8-C8` | One half-note C, with no new attack on the second token |
| `"Am7"z16` | A minor seventh chord starts here; the melody rests for half a note |
| `^F`, `_B`, `=F`, `^^F`, `__B` | Sharp, flat, natural, double sharp, double flat |

- A 4/4 bar totals 32 units; 3/4 and 6/8 each total 24; 3/8 totals 12.
- Full-bar `Z` rests count measures, not `L:` units. Over a harmonic or key change, write ordinary rests with the event at its correct onset instead of a compressed rest.
- Supported duration multipliers: `1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48`. Write 10 units as `C8-C2`, or `z8z2` for a rest.
- A chord change inside a held note splits the notation with a tie, for example `"C"E16-"Am7"E16`. Without the tie the second `E` is a new attack.
- A rest cannot be tied, a tie must join equal sounding pitches, and a score cannot end with an unresolved tie.

## Accidentals and ties need musical interpretation

- Pitches are relative to the active key. In `K:D`, an unmarked `F` sounds F-sharp and `C` sounds C-sharp.
- Accidentals stay active through the bar and reset at its boundary or at a key change.
- **The native export/render convention propagates an accidental by letter across octaves.** After `^F`, both later `F` and `f` are sharp in that bar. Some general-purpose ABC implementations differ, so keep using this helper (or the native serialiser) rather than swapping in another parser.
- A tied, unmarked continuation across a barline keeps the preceding note's pitch. Its following untied notes use the new bar's accidental state. In C major, `^F32-|F8F24|` is a five-quarter F-sharp followed by a three-quarter F-natural.
- Repeating the explicit accidental on the continuation is clearer and matches the native writer when needed. An explicit contradictory accidental must fail validation.
- Count **sounding notes after merging ties**, not raw ABC note tokens. A chord-only edit can add tied tokens without adding melody notes. Replacing `C8-C8` with `C8C8` changes articulation even though the pitch sequence looks the same.

## Portable inspection and cover preparation

Run from this skill's directory, or adjust the script path:

```bash
python3 <skill>/scripts/abc_tools.py inspect source.abc --output source-inspection.json
python3 <skill>/scripts/abc_tools.py strip-chords source.abc cover.abc
python3 <skill>/scripts/abc_tools.py compare source.abc cover.abc
```

- `strip-chords` validates input and output, removes only supported quoted chord symbols from music lines, and verifies that all sounding notes, onsets, durations, meters and tempo are unchanged. Quoted voice names in the header are preserved. It refuses to overwrite an existing output.
- The default keeps **both** melodies, including instrumental themes and solos. To preserve one part only, select it explicitly:

```bash
python3 <skill>/scripts/abc_tools.py strip-chords source.abc vocal-cover.abc --keep-voice Vocal
python3 <skill>/scripts/abc_tools.py compare source.abc vocal-cover.abc --voices Vocal
```

- With `--keep-voice`, the unselected voice is replaced with rests on the same time grid and the two-voice format stays intact. `--keep-voice Ins` retains the instrumental melody. Keep `Ins` unless the task specifically asks for the vocal line alone; "cover" by itself is not a reason to discard it.
- Supply the chord-free ABC with `cot="melody"`, the target style and the target lyrics; see [generation-and-covers.md](generation-and-covers.md).
- Inspection JSON includes exact quarter-note fractions, MIDI pitches, merged note durations, per-voice bar grids, chord onsets, key changes and nominal duration.
- From Python, `parse_abc(text)` returns a score exposing `.voices["Vocal"].chords` and `.voices["Ins"].chords` without loading any models.
- The helper rejects unsupported material rather than guessing its timing: tuplets, grace notes, polyphonic note stacks, repeat signs, alternate endings, slurs, broken rhythms, decorations, lyric `w:` fields, custom voices/directives, and unsupported key modes or chord qualities. Rebuild such material into the native dialect deliberately. A rejection means "outside this helper's scope"; it does not establish that a score is invalid under the full ABC standard.

## Reharmonisation and selective melodic editing

The native quoted chord vocabulary:

```text
major (no suffix), m, dim, aug, 7, maj7, m7, dim7, m7b5,
sus4, sus2, 6, m6, 7sus4, m(maj7)
```

- Roots and optional slash basses use note names: `Dbaug`, `F#m7/C#`, `Gm6/Bb`, `A7/E`. Double accidentals are supported where a spelling requires them.
- `C:maj`, numbered slash degrees, `C13`, `A7alt`, `Cmaj9` and arbitrary annotations are not native chord symbols. For advanced harmony use a supported chord core and describe the voicing in the style prompt; the prompt's richer voicings are a generative request, not a guarantee.

When choosing chords:

- Mark sustained notes, strong-beat notes, cadences and phrase boundaries in both the sung melody and the instrumental solo. For each, examine the chord active **during that note**, its duration, the bass movement, adjacent melody pitches and where the tension resolves.
- A tension that works on a short approach note can sound harsh when held for two beats.
- Review the bass line, guide-tone motion and transitions into and out of any tonicisation.
- Preserve successful colours rather than replacing every non-chord tone.

Examples of targeted repairs, each dependent on context:

- A sustained A over `Db7` may clash with the chord's A-flat fifth. `Dbaug` retains the chromatic bass while including A; a prompt asking for an omitted fifth is less explicit than a suitable supported chord core.
- Sustained F-sharp over `Eb7` combines a minor third with the major third G. `Ebm7` can preserve the E-flat bass and directly support that melody tone.
- A tritone substitute can work as a brief approach but needs earlier resolution when the next strong melody note arrives. Moving the chord boundary may preserve more colour than replacing the whole bar.

These are musical options, not unconditional substitution rules. Recheck the surrounding progression, especially after changing one chord's third or fifth. Judge jazz non-chord tones case by case; a blanket "all melody notes must be chord tones" rule is wrong for the idiom.

For a strict reharmonisation:

```bash
python3 <skill>/scripts/abc_tools.py inspect edited.abc --output edited-inspection.json
python3 <skill>/scripts/abc_tools.py compare source.abc edited.abc --output melody-invariants.json
```

- By default `compare` requires the same quarter-note tempo. Add `--allow-tempo-change` to permit an intentional tempo change while keeping pitches, relative note timing and bar meters.
- If melodic or metrical adaptation is authorised, a comparison failure can be expected. Record the precise changed passages and assess the still-fixed parts separately. The helper does not judge whether a change is musically good or waive differences.
- For a quoted theme, verify the complete intended phrase sequence and repetitions; a repeated opening motive is not the complete theme.

## Lyrics, syllables and phonemes

The generation API accepts lyrics and ABC, with no forced phoneme-to-note alignment channel. Keep alignment records in sidecar JSON/Markdown and leave the model's ABC free of phoneme annotations and `w:` fields.

1. When changing language, adapt the lyrics for singing rather than translating word for word.
2. Use the final score's resolved vocal notes to map every sung syllable to its intended note or contiguous melisma.
3. Map consonants to attacks and releases; sustain vowels across melismas. One phoneme does not equal one note.
4. Check lexical stress, short-note consonant density, long-note vowel choice, breathing rests, pickup syllables and section tags. A changed English lyric usually needs stress and vowel-duration adjustment even when its syllable count matches the old text.
5. Revise wording or rhythm where the contract allows.
6. Record the actual dictionary pronunciation rather than guessing phonemes. Preserve the selected pronunciations and their provenance, and flag out-of-vocabulary words for manual review.
7. Record in the sidecar: section, lyric line, word/syllable, phonemes, stress, selected voice, note indices with an explicit index base, pitches, planned onset/duration and any manual choices. Validate that every intended vocal note and syllable is accounted for.

```json
{
  "voice": "Vocal",
  "note_index_base": 0,
  "word": "light",
  "syllable": "light",
  "phonemes": ["L", "AY1", "T"],
  "stress": 1,
  "note_indices": [20, 21],
  "articulation": "Attack L once; sustain AY across both notes; release T at the end"
}
```

The sidecar proves a designed symbolic fit, not that the generated performance realises it. Listen for dropped or repeated words, use ASR/PER as a separate pronunciation diagnostic, and use audio alignment if claiming measured synchronisation.

## Native serialisation, rendering and audio checks

- The published [SheetSage2 notation module](https://huggingface.co/m-a-p/SheetSage2/blob/main/notation_sheetsage2.py) provides `score_to_abc(score)` and `validate_serialized_abc(text, score)`. The latter requires the original structured `RebuiltAbcScore` with its event arrays; **it is not a free-text `validate_abc(text)` API**.
- The public remote-code model release is not an installable `sheetsage2_infer` parser package.
- When editing structured musical events inside that implementation, rebuild with its native serialiser and retain its validation results. The portable helper here does not reproduce that reconstruction check.

For a visual check, the downloaded SheetSage2 release renders an edited ABC without a model load:

```bash
.venv-sheetsage2/bin/python models/SheetSage2/setup_render.py
.venv-sheetsage2/bin/python models/SheetSage2/render.py --abc edited.abc --output rendered-edit --score pdf,svg
```

- `setup_render.py` installs optional rendering dependencies; the ABC helper needs none of them.
- The release's audio renderer plays supplied MIDI. Rendering edited ABC with old MIDI previews the old note timing and content, so regenerate the MIDI before using it as evidence for an edit.
- Direct instrumental rendering does not test YuE2 audio adherence.

Finish with three distinct checks: native-dialect structure, the intended symbolic musical invariants, and the generated sound. Listen especially to the changed bars and their transitions. Save source and edited ABC, prompts, lyrics, decoder identity, seeds, validation records and audio. Transcribing the result with SheetSage2 is a further diagnostic; its transcription errors are not definitive generator errors.
