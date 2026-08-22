
## Negative prompting

Available where the frontend exposes it (a ComfyUI workflow with `negative_caption` and `negative_weight` inputs). Everything above still applies to the positive caption; this is an extra axis, not a replacement for writing the caption well.

**Where it acts.** In the autoregressive text encoder, the same stage the caption acts on, before any audio token is emitted. It can therefore move the composition itself - melody, structure, arrangement - not just the tone of the render. The DiT and VAE stage downstream only renders what that stage decided.

**Mechanism.** The encoder already ran classifier-free guidance over a two-row batch: row 0 is the caption, row 1 was a null prompt with every caption and lyric token overwritten by `<|audio_cfg|>`. Guidance is `guided = negative + (positive - negative) * cfg_scale`. The negative caption substitutes real text into that previously-null row. The steering direction is `positive - negative`, so **anything the two captions share cancels and contributes nothing**. That one fact drives everything below.

### Mechanism

The encoder already ran classifier-free guidance over a two-row batch: row 0 is the caption, row 1 was a null prompt with every caption and lyric token overwritten by `<|audio_cfg|>`. Guidance is `guided = negative + (positive - negative) * cfg_scale`. The negative caption substitutes real text into that previously-null row.

The steering direction is `positive - negative`, so **content shared by both captions contributes almost nothing**. Not exactly nothing: the encoder is non-linear, so identical text produces near-identical hidden states rather than mathematically cancelling ones. Treat it as a working model, not an identity. That one fact drives everything below.

### Controls

- `negative_caption` - free text, written as a caption.
- `negative_weight` - 0.0 to 1.0, blending between the null row and the negative row. `0.0` disables it and generation is bit-identical to not using it. `1.0` replaces the null row outright and is the normal setting, the equivalent of a negative prompt in an image model rather than an extreme. Values between are a partial retreat toward having no negative.
- The 1.0 ceiling is deliberate. Above it the blend extrapolates past the negative into embeddings the encoder was never trained on, which degenerates rather than steering harder.
- Push strength is not set by `negative_weight`. It comes from `cfg_scale`, shared with the positive caption.

### What it can and cannot do

Steers away from genres, styles, instruments, production characteristics, arrangement habits and vocal treatments - anything the caption vocabulary expresses. Because it acts before token generation, it changes the composition.

- It is not a filter or a ban list. Nothing is prohibited; the distribution is tilted.
- It cannot override the positive caption. Asking for something in the caption that the negative rejects makes the two fight, with `cfg_scale` mediating. Contradicting your own caption wastes the mechanism.
- **It cannot separate a genre from its neighbours.** Naming a genre drags its whole region of the model's space. Negating `Nu-Metal` also pushes away from metal generally, which subtracts from a Gothic Metal positive rather than protecting it. Same for any adjacent pair.
- It does not operate on lyrics. The negative is read as a caption, so it cannot suppress words or phrases in the sung text.
- It has no effect at weight 0 or with empty text.

### Writing one

Write it as a caption in the same structured format as the positive, with attributes under the heading that owns them: a vocal treatment under `Vocal Details`, a genre on the `Basic Attributes` line. The encoder is a Qwen-based LLM trained on captions in that shape, and it reads the headings.

Two strategies, trading precision against force:

- **Mirrored** - copy the positive caption and change only the clause being negated. Everything identical cancels exactly, leaving a clean single-axis direction. Precise, but the resulting vector is small, so it needs a higher `cfg_scale` to be felt.
- **Minimal** - a short caption in the same shape carrying only the offending attribute. Blunter direction, far more magnitude behind it.

Between the two sits the useful default: write the version of the song you do not want, inverting only the fields that carry the failure mode and leaving the rest out. Each field you invert adds an axis to the vector, so four inverted fields aimed at one target beat eleven aimed at several.

Hold bpm and key identical to the positive. They cancel exactly. A different bpm in the negative steers away from that tempo as well as from the genre, which is rarely what you meant.

### Worked pair

The positive is a Gothic Metal track built on a flat emotional level, a voice that recedes as the band thickens, one-room tracking with nothing fixed afterwards, and a hard stop.

```text
Global Metadata
Basic Attributes: bpm is 92. key is C#, and scale is minor. Gothic Metal / Gothic Rock.
Global Emotional Progression: The piece begins already in motion, a driving figure with no introduction and no atmosphere in front of it. The emotional level does not climb at any point and neither does the volume of the voice. It is set in the first bar and held. Where the guitars thicken, the singer drops further under them rather than rising to meet them, so the widening gap between voice and band is the only development in the piece. The third and sixth sections are the returning ones and each is delivered lower and quieter than the last. The final section returns to the opening figure unchanged while the voice gives up the melody entirely and speaks a single line, and the piece stops abruptly rather than fading.
Application Scenarios & Imagery: A terraced house in the same town some months later, mid-afternoon, the light already going. Equally suited to a scene in which someone performs a small domestic routine correctly and at the usual time for no remaining reason.
Sonics & Production Profile: The record was cut in one room with the band playing together, and the mix keeps that geometry rather than correcting it. The soundstage is tight and forward, with the rhythm section pushed up and the guitars flat and close to the listener. The low end is thick and slightly loose, the midrange is where the weight sits, and the whole balance leans towards drive rather than depth. Compression is audible on the drum bus and nowhere else. Nothing is fixed after the fact, and the imperfections that survive are the reason the weight lands.
Vocal Details
Vocal Gender & Timbre: Singer A (Male). A low clean male voice, plain and unornamented, with a dry grain in it and a narrow working range of about a fifth. It sits close to the microphone and close to speech, the sound of a man saying something difficult quietly and steadily rather than performing it. The tone is even and slightly dull, with no brightness at the top.
Vocal Style: The voice holds one low volume from the first line to the last of this piece. Every line is sung conversationally within a fifth, close to speech, with the ends of phrases allowed to fall away rather than being held, and no note sustained longer than a beat. Phrasing is even and slightly ahead of the beat in the first and fourth sections and falls behind the beat in the returning third and sixth. Each return is delivered lower and quieter than the one before it, so the vocal descends across the song while the band thickens against it. The final line is spoken.
Harmony/Backing Vocals: Singer A doubles himself an octave below on isolated lines only, mixed low and slightly late so the two takes do not lock together. There are no third-based harmony stacks and no choir at any point. A second, quieter spoken take sits beneath a small number of sung lines, close to inaudible, present as texture rather than as a part.
Vocal FX: One microphone close to the singer in the same room as the band and on the same take, with audible drum bleed on the vocal track. A short dark plate reverb is the only treatment, keeping the voice in a stone room rather than a hall, with no delay throw on any line ending. The signal is dry and flat, with breath and lip noise audible between phrases.
Arrangement
Instrument Lifecycle Description (Primary/Secondary Layering):
Primary: A down-tuned rhythm guitar plays a repeating chord figure in steady eighth notes from the first bar to the last, open rather than palm muted, with the gain set lower than the weight suggests so the intervals inside each chord stay audible. Beneath it a second rhythm guitar plays the same figure an octave down with heavy low-end distortion, thick and saturated, entering at the first vocal line and staying for the rest of the piece so the figure is always doubled from below.
Secondary: A third guitar carries the song's melodic hook with the tone rolled off, entering before the first vocal line and taking the melody back every time the voice stops, handing it between them across the whole piece. A single sustained keyboard note sits underneath the returning sections only, held without movement and mixed almost below the guitars. Nothing else is added at any point. No strings, no orchestration and no pad, and the density in the final third comes purely from the existing guitars playing lower and closer together rather than from anything new arriving.
Groove & Foundation Progression: The kit plays straight from the first bar with no introduction, kick and snare rock-solid and unhurried, snare consistent and hats closed and driving. The felt tempo is the same as the stated count throughout, with no half-time passage anywhere. Bass is played with a pick and locked tightly to the kick, moving in simple root and octave motion and never straying above the low register. Fills are minimal and mark only the entry of the recurring section. In the middle section the kit reduces to kick and closed hat with the snare removed entirely, then returns whole. The ending stops on a single beat with no ritardando and no fade.
Embellishments, Textures & Spatial FX: Amp hum sits under the whole piece at a constant low level. String noise and pick attack are left audible. A single low guitar note feeds back at the end of the middle section and is cut off rather than resolved. One dissonant interval sits inside the repeating figure and returns every time it comes round, so the hook is never entirely comfortable. There are no risers, no reverse cymbals, no impacts and no filter sweeps. Reverb is short and consistent across every instrument with no throws and no spatial movement, keeping the whole arrangement flat and close.
```

The negative is the same song made anthemic, aimed at pop rock, nu-metal and generic smooth vocals. Every field is inverted, so the only things cancelling are the tempo, the key and the section headings.
`Primary` - negate what makes nu-metal *not* gothic metal, leaving the down-tuning and gain the positive wants.

```text
Global Metadata
Basic Attributes: bpm is 92. key is C#, and scale is minor. Pop Rock / Alternative Rock / Post-Grunge.
Global Emotional Progression: The piece opens with an atmospheric introduction that sets the mood before the song proper arrives. The emotional level and the volume of the voice climb steadily from there, each section larger than the one before it. Where the guitars thicken the singer rises to meet them, so voice and band grow together and the gap between them closes. The third and sixth sections are the returning ones and each is delivered higher and louder than the last. The final section is the largest in the piece, the full arrangement behind a vocal at its most powerful, and the song fades out.
Application Scenarios & Imagery: A wide aerial shot of a city at night with the lights coming on, or the moment in a montage where the training pays off. Equally suited to a stadium, an advert, or a scene in which someone finally decides to change their life.
Sonics & Production Profile: The record was built up track by track to a grid, and the mix corrects the geometry rather than keeping it. The soundstage is wide and polished, with guitars spread hard and everything sitting in its own cleared space. The low end is tight and controlled, the midrange is scooped out to make room, and the whole balance leans towards size and depth rather than drive. Bus compression and limiting run across the whole mix to hold it loud and even. Timing and tuning are corrected throughout, and every imperfection has been edited out.
Vocal Details
Vocal Gender & Timbre: Singer A (Male). A polished mid-range tenor, bright and open at the top, smooth and even throughout with no grain or roughness anywhere in it. A wide and flexible working range, set back from the microphone and projected out into the room, clearly performed rather than spoken.
Vocal Style: The voice builds in volume from the first line to the last, opening restrained and ending belted at full power. Every line is sung across a wide range, with the ends of phrases held and sustained across several beats and decorated with melisma and runs. Phrasing sits locked to the grid throughout with no push or drag anywhere. Each return is delivered higher and louder than the one before it, so the vocal climbs across the song as the band rises with it. Every line is sung, and the last is the biggest.
Harmony/Backing Vocals: Full third-based harmony stacks sit above the lead through every returning section, tightly aligned and spread wide across the stereo field. A gang vocal and a choir enter for the final section to lift it further. Doubles are locked exactly to the lead so the takes read as a single thickened voice.
Vocal FX: A composite vocal comped from many takes, recorded in a separate booth with no bleed from the room. Pitch corrected hard and compressed to a constant level, de-essed and brightened, with a long bright hall reverb and delay throws on the ends of lines. Doubles and harmony stacks are spread wide with heavy stereo movement. No breath or lip noise survives anywhere.
Arrangement
Instrument Lifecycle Description (Primary/Secondary Layering):
Primary: A rhythm guitar plays syncopated stop-start accents that drop to silence under the vocal and slam back in for each returning section, the midrange scooped out to make room. The figure bounces on the off-beat and is built from short punctuating stabs rather than a sustained chord shape, changing at every section rather than repeating.
Secondary: Synth pads and string arrangements arrive to lift each returning section, widening the arrangement every time it comes round. Sampled effects and turntable scratches punctuate the transitions. New elements are introduced at every section boundary to keep the arrangement escalating, and the density in the final third comes from layers stacked on top rather than from the existing instruments.
Groove & Foundation Progression: The kit enters after an introductory build rather than from the first bar, with a syncopated groove locked to the riff accents and open hats driving the returning sections. A half-time breakdown drops the piece into its heaviest passage before the final section. Fills are frequent and large, marking every transition, and the felt tempo pushes forward through the climbs. Bass follows the guitar riff rhythmically rather than the kick, with octave pops and slides carrying it up out of the low register. The ending arrives on a large fill and fades out.
Embellishments, Textures & Spatial FX: Risers, reverse cymbals, impacts and filter sweeps mark every section boundary. Reverb throws and spatial movement widen the arrangement through the returning sections, with gated ambience on the drums. Amp hum, string noise and pick attack have been cleaned out entirely. The repeating figure is entirely consonant, resolving comfortably every time it comes round, and every held note resolves rather than being cut.
```

What each inverted field is doing:

- `Global Emotional Progression` - the flat held level and hard stop against build-to-a-big-final-chorus-and-fade. The main anti-pop-rock axis.
- `Vocal Style`, `Harmony/Backing Vocals` and `Vocal FX` - three fields carrying the anti-smooth-vocal load together: belted and grid-locked, stacked thirds and a choir, comped and tuned and drenched. If the vocal lands but something else drifts, cut the negative back to these three.
- `Application Scenarios & Imagery` - the quiet lever. The positive is small and domestic; the inversion is the anthemic sync-licence register pop rock lives in, so negating it pushes on the whole song's posture rather than on any one instrument.
- `Sonics & Production Profile` - one room kept as it played against a grid-built mix with every imperfection edited out.
- The Arrangement fields - a repeating figure and audible hum against stop-start scooped-mid riffing, pads and strings arriving on cue, and risers on every boundary.

On the `Basic Attributes` line only the genre clause does any work; bpm, key and scale are unchanged and contribute nothing. Every other field is fully inverted and each adds its own axis. No negation word appears anywhere in it - every line is phrased as the thing being steered away from.

### What has no effect, or backfires

- **Negation words backfire.** Write `Post-Grunge`, never `no post-grunge` / `avoid` / `without`. The slot already means "away from this", so a negated phrase steers away from the absence of the thing.
- **Naming an adjacent genre backfires.** It subtracts the shared region, taking your target genre with it. Negate distinctives instead.
- **Bare keyword lists are weak.** Against a long structured caption, `nu-metal, pop` makes the difference vector encode "not a prose caption" more than "not nu-metal".
- **Markdown does nothing.** `clean_caption()` strips headers, bullets, bold and emphasis before tokenising.
- **Text identical to the positive does nothing useful.** Only the differing clauses steer, which is the point of the mirrored strategy rather than a flaw.
- **Overlong text is truncated** at the token length of the positive caption plus lyrics, keeping the front and discarding the rest. A warning goes to the ComfyUI log. The budget is generous in practice.

### Recipe

1. Start minimal at weight 1.0 to confirm the effect is audible.
2. **Tune the negative at `top_k` 50 and change one variable at a time.** Raising `top_k` admits lower-probability tokens at every AR step; if the negative has tilted the distribution off-target, a wider pool lets the result travel further down that slope. Diagnose the negative first, widen afterwards.
3. Move to the field-by-field inversion once you know what you are steering. A near-total inversion carries plenty of magnitude on its own, so leave `cfg_scale` at 1.7; a strictly mirrored negative changing one clause needs it raised to compensate for the smaller vector. Raising it tightens adherence to the positive at the same time, which is a second effect you may not want.
4. If the result goes stiff or thin, drop the weight to 0.6-0.8 rather than lowering `cfg_scale`.
5. If one failure mode survives, cut the fields that are not fighting it. A shorter negative concentrates the vector instead of spreading it across five axes.

### Diagnosing a bad result

- **It drifted to an unrelated genre.** Cluster drag. Something in the negative is subtracting a region the positive depends on - check the genre line first, then any instrument or production wording the two captions have in common. Raising `top_k` makes this worse and is often what exposes it.
- **It came out as noise, buzzing or glitching rather than music.** Not the negative. Check the sampler: `_cfg_pp` variants reinterpret the guidance scale and expect `cfg` near 1.0, so they degenerate at 1.7. `euler` and `euler_ancestral` are safe.
- **Nothing changed at all.** Either the weight is 0, the text is empty, or the negative is too close to the positive to produce a usable difference.
