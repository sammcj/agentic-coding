# MiniMax Music 3 Prompt Guide

MiniMax Music 3 generates a complete song (up to ~5 minutes, 32kHz stereo) from two separate text inputs: a **Caption** and **Lyrics**. The caption was trained on a rigid structured format - three headings and eleven labelled fields, in a fixed order. Every one of the model's 1,000 published reference captions uses that exact field set, so the labels are part of the prompt text you paste into the caption box. A free-form paragraph is accepted but gives up section-level control.

## Contents

- [Contents](#contents)
- [The two inputs](#the-two-inputs)
- [Pre-flight check](#pre-flight-check)
- [Caption skeleton](#caption-skeleton)
- [Field lengths](#field-lengths)
- [Global Metadata](#global-metadata)
- [Vocal Details](#vocal-details)
- [Arrangement](#arrangement)
- [Lyrics input](#lyrics-input)
- [Duration is a ceiling](#duration-is-a-ceiling)
- [Genre routing](#genre-routing)
- [Priors and how to override them](#priors-and-how-to-override-them)
- [Negative prompting](#negative-prompting)
- [Corpus craft patterns](#corpus-craft-patterns)
- [Series and album consistency](#series-and-album-consistency)
- [Official template library](#official-template-library)
- [Resolving conflicts](#resolving-conflicts)
- [ComfyUI specifics](#comfyui-specifics)
- [Worked example](#worked-example)
- [Think carefully about how your lyrics will match the music](#think-carefully-about-how-your-lyrics-will-match-the-music)
- [Review checklist](#review-checklist)
- [Delegating parallel songwriting to sub-agents](#delegating-parallel-songwriting-to-sub-agents)
- [Iteratively improving or varying a song](#iteratively-improving-or-varying-a-song)

## The two inputs

| Input | Carries | Never carries |
| - | - | - |
| Caption | Style, tempo, key, emotional arc, production, vocal identity, instrument timeline | Lyric lines or paraphrases of them, song title, bracket tags |
| Lyrics | Sung words plus `[Section]` tags | Style or production instructions |

The split is strict: structure comes from the lyric tags, sound comes from the caption. Bracket tags appear nowhere in the caption; the caption names sections in prose ("the second chorus", "the bridge").

## Pre-flight check

The model knows the styles in its 1,000 published training captions. A genre term or production phrase that appears nowhere in them carries no signal, and the encoder falls back on whatever neighbourhood the rest of the caption points at. Run this before writing, not after a take comes back wrong.

1. Check every genre term destined for `Basic Attributes` against the corpus, and every distinctive production phrase you plan to lean on.
2. Check what the chosen BPM implies. Tempo selects a style neighbourhood on its own, so a slow guitar brief lands in blues rock and a 128 BPM brief lands in dance.
3. For anything the corpus does not contain, describe the machinery instead of naming it, and expect the Arrangement fields to carry more weight than usual.

```sh
git clone --depth 1 https://github.com/MiniMax-AI/MiniMax-Music3.git
cd MiniMax-Music3/skills/music-caption-rewriter
rg -icl '^Basic Attributes:.*<term>' templates | wc -l   # does it route
rg -icl '<term>' templates | wc -l                        # has the model heard it described
```

Counts, tempo neighbourhoods, the zero-coverage list and the substitutes for absent styles are in [minimax-music-3-corpus.md](minimax-music-3-corpus.md). Known traps worth memorising: `Progressive` is house music in this corpus, `psychedelic` appears zero times, and `tape echo`, `mellotron`, `phaser` and `vocoder` are all absent.

## Caption skeleton

Plain text, no markdown, headings on their own lines, one field per line in this order:

```text
Global Metadata
Basic Attributes: bpm is 92. key is D, and scale is minor. Indie Pop / Dream Pop.
Global Emotional Progression: ...
Application Scenarios & Imagery: ...
Sonics & Production Profile: ...
Vocal Details
Vocal Gender & Timbre: ...
Vocal Style: ...
Harmony/Backing Vocals: ...
Vocal FX: ...
Arrangement
Instrument Lifecycle Description (Primary/Secondary Layering):
Primary: ...
Secondary: ...
Groove & Foundation Progression: ...
Embellishments, Textures & Spatial FX: ...
```

`Instrument Lifecycle Description (Primary/Secondary Layering):` has no text of its own - it is a header for the `Primary:` and `Secondary:` lines beneath it.

The three headings are optional; the eleven labels are what the encoder keys on. A supported alternative runs each group as a single paragraph with its labels inline and joins the three paragraphs with newlines. One field per line is easier to revise.

## Field lengths

Typical ranges in the reference corpus; whole caption 420-720 words (corpus median ~570). Under-filling a field is what makes output generic.

| Field | Words |
| - | - |
| Basic Attributes | 13-18 (one line) |
| Global Emotional Progression | 45-80 |
| Application Scenarios & Imagery | 20-45 |
| Sonics & Production Profile | 40-75 |
| Vocal Gender & Timbre | 20-55 |
| Vocal Style | 30-70 |
| Harmony/Backing Vocals | 17-60 |
| Vocal FX | 25-65 |
| Primary | 25-50 |
| Secondary | 35-75 |
| Groove & Foundation Progression | 40-95 |
| Embellishments, Textures & Spatial FX | 40-65 |

## Global Metadata

Prefer concrete musical changes over decorative prose. Default to approximately 250-450 English words unless the user requests another length.

**Basic Attributes** - the one field with fixed phrasing. Exact BPM, key, scale, then genre and subgenres separated by ` / `:

```text
Basic Attributes: bpm is 74. key is Bb, and scale is minor. Contemporary R&B / Alternative Soul.
```

Give a BPM and key even when the user did not name one - pick values idiomatic for the genre and keep the rest of the caption consistent with them (a 162 BPM trap groove described as half-time, a 74 BPM ballad with slow harmonic rhythm). Two or three genre terms locate the style; more than three blurs it.

**Global Emotional Progression** - how feeling moves from open to close, tied to what causes it (dynamic swell, arrangement thinning, a key lift). Name the beginning state, the change, and the ending state.

**Application Scenarios & Imagery** - the listening scenario and visual world in one or two sentences: where this plays, what it scores. This is the field that carries mood imagery, which keeps the other fields technical.

**Sonics & Production Profile** - soundstage width, frequency balance, dynamic aesthetic, compression character, era of production. Describe what is audible rather than naming gear.

## Vocal Details

**Vocal Gender & Timbre** - open with the singer roster, then the voice. Two accepted forms:

```text
Vocal Gender & Timbre: Singer A (Male). The vocalist possesses a deep, resonant baritone with a velvety texture and a warm lower register.
Vocal Gender & Timbre: Singer A (Female) and Singer B (Male). Singer A possesses a bright, agile mezzo-soprano; Singer B answers with a smoky lower tenor.
```

`Singer A` / `Singer B` are stable IDs - reuse them in `Vocal Style`, `Harmony/Backing Vocals` and `Arrangement` to say who sings which section. Voice type (soprano, mezzo, tenor, baritone) plus two or three texture words does more work than adjective stacking.

**Vocal Style** - delivery and how it develops: conversational vs projected, breath, rasp onset, vibrato, melisma, phrasing against the beat, register shifts between verse and chorus, ad-libs. Say where each change happens.

**Harmony/Backing Vocals** - stacks, octave doubles, call-and-response, choir, gang vocals, and which sections they enter. `No distinct backing vocals or harmony layers are present` when the lead carries it alone - the field is never left blank.

**Vocal FX** - reverb type and size, delay, doubling, saturation, pitch treatment, filtering. State restraint explicitly when the style wants a raw voice.

Instrumental track: write `Instrumental, no vocals.` in `Vocal Gender & Timbre`, name the instrument carrying the lead melodic role, then keep the remaining three vocal fields consistent with that. Keep these statements flat and short - enumerating every vocal type in order to negate it ("no sung, chanted, hummed or whispered delivery") stacks vocal tokens the encoder reads as evidence for a voice. The caption alone does not hold the line either; the lyrics box needs [tag-only structure](#lyrics-input). An explicit instrumental request stays instrumental - do not add a vocal line to fill the section.

## Arrangement

**Primary** - the one or two instruments that hold the harmonic and rhythmic centre, plus when they enter and exit. Include their playing technique, not just the instrument name.

**Secondary** - supporting layers and their lifecycle across the song: what joins at the pre-chorus, what drops for the bridge, what returns doubled in the final chorus. This is where section-level control lives, so it is usually the longest instrument field. `No secondary melodic or harmonic instruments are introduced` is a valid, deliberate answer.

**Groove & Foundation Progression** - drums and bass as a developing system: kick and snare pattern, hat subdivision, bass articulation and register, fills and their placement, half-time or double-time shifts, where the groove drops out entirely. Trace it section by section.

**Embellishments, Textures & Spatial FX** - fills, risers, impacts, vinyl noise, string squeaks, pads, panning moves, reverb throws, filter sweeps, silence used as an effect.

Across all four fields, write instrument behaviour as a timeline with plausible entrances and exits. A static list of equipment gives the model nothing to develop.

## Lyrics input

Tags are the executable structure; the lyric text supplies words and mood only.

```text
[Intro]
[Verse]
Streetlights blur across the windscreen
...
[Pre-Chorus]
...
[Chorus]
...
[Instrumental]
[Outro]
```

- Supported tags: `[intro]`, `[verse]`, `[pre-chorus]`, `[chorus]`, `[post-chorus]`, `[bridge]`, `[instrumental]`, `[solo]`, `[outro]`. Write them lowercase; case is not significant.
- Every tag sits alone on its own line. Words never share a line with a tag.
- `[instrumental]` and `[solo]` take no lyric lines - describe what plays there in the caption's Arrangement fields.
- Never leave the lyrics input empty. A blank box is rejected outright by some frontends, and the model reads an unstructured one as licence to improvise syllables.
- Match total lyric volume to `max_duration`, budgeting 12-16 sung words per 10 seconds. Structure sizing: 30 seconds or less takes one verse and one chorus; around 60 seconds takes verse / pre-chorus / chorus / verse / chorus; 120 seconds and over takes the full structure with a bridge and an outro.
- When the user attaches a musical instruction to a tag ("[Bridge] - drums drop out"), move it into the matching part of the Arrangement description and leave the lyrics input clean.

**An instrumental track still needs a populated lyrics input.** The box is the structure input, not only the words input. Left empty, the model has no section map and fills the space with improvised syllables that come back as singing in an invented language; the caption's vocal fields do not prevent this on their own. `[instrumental]` alone covers a short piece. Past roughly two minutes, write the whole structure as tag-only lines with no words beneath any of them, enough sections to span `max_duration`:

```text
[intro]
[instrumental]
[instrumental]
[bridge]
[instrumental]
[solo]
[outro]
```

Repeated `[instrumental]` tags are how a long instrumental gets its sections; `[bridge]` marks a breakdown or contrasting passage and `[solo]` a lead-instrument feature. Keep the tag count and order consistent with the entrances and exits in the caption's Arrangement fields - a caption tracing seven sections against two tags in the lyrics box is a conflict the model resolves by inventing material.

Scale the tag count to the target length. A tag-only section renders at roughly 8-12 seconds, and the rate falls toward the low end as the tag count rises, so budget generously: seven tags returns around 90 seconds and twenty returns around three minutes. See [Duration is a ceiling](#duration-is-a-ceiling).

There is no model-level instrumental flag. The caption half of the instruction is `Instrumental, no vocals.` in `Vocal Gender & Timbre` followed by the instrument carrying the lead melodic role; the tag-only lyrics input is the other half.

## Duration is a ceiling

`max_duration` caps the generation; it does not set the length. The autoregressive stage emits an end-of-audio token when it judges the piece finished, and that decision comes from the prompt. A 280-second request returning 84 seconds is the model ending early, not the setting failing.

What actually sets length:

- Tag count. Each section tag is a unit of time the model has to fill; a sung section runs longer than a tag-only one. Tag-only sections land around 8-12 seconds each, and the per-section rate compresses as the count rises rather than scaling linearly, so a long piece needs proportionally more tags than the arithmetic suggests.
- Lyric volume within each section, at 12-16 sung words per 10 seconds.
- Section timings named in the caption's emotional, groove and embellishment fields, which have to agree with the tag count. A caption describing a four-minute arc over seven empty tags gets resolved as a short piece.

When output is short, add tags before touching anything else, then re-check that the Arrangement timeline still describes the same number of sections.

## Genre routing

The 1,000 templates are indexed as 18 style families, and the router over them encodes which words count as genre evidence. The same rules decide what belongs on the `Basic Attributes` line.

- `ballad`, `emotional`, `epic`, `modern`, `dark` and `cinematic` are modifiers. None selects a family on its own, and using one as a genre term hands the family choice back to the model.
- Route on the genre name first, then groove evidence (swing, trap, four-on-the-floor, breakbeat, acoustic strumming), then core instrumentation and vocal delivery, then cultural or market context. Mood and imagery come last, and a brief offering only mood should stay conservative.
- Fusion is ordered: `X with Y influences` and `X / Y` both mean primary X, secondary Y unless the brief weights them equally. The secondary style supplies one dimension only - instrumentation, groove, vocal treatment, cultural colour, arrangement or production - and never overrides an explicit tempo, vocal or exclusion.
- Two families is the ceiling. A third style stays a ranking cue rather than becoming a third term on the `Basic Attributes` line.
- Normalise spelling before writing the line: `Hip Hop`/`Hip-Hop`, `Dance Pop`/`Dance-Pop`, `Synth Pop`/`Synth-Pop`, `R&B`/`R'n'B`. Chinese-language briefs normalise too - 华语流行 and 国语流行 to Mandopop or C-pop, 粤语流行 to Cantopop, 国风流行 to East Asian pop with optional roots colour, 氛围 R&B to Alternative R&B, 朋克流行 to Pop-Punk. 电影感 and 史诗感 are modifiers; 燃, 炸 and 强烈 are energy cues carrying no genre.
- Write the caption in English whatever language the brief arrives in, unless the user asks otherwise. Lyrics stay in the language the song is sung in.

Family boundaries that the corpus decides differently from ordinary usage:

- East Asian modern vs ballad/heritage: electronic, R&B, hip-hop, dance, funk, rock or metal production is modern; acoustic, orchestral or conventional ballad writing is heritage. Guofeng stays East Asian pop while the songwriting is pop, and moves to roots only when traditional instruments are structural rather than decorative.
- Cinematic pop ballad vs cinematic orchestral: a song is the ballad family; a score whose identity is orchestra, trailer or choir is the orchestral one.
- Electronic synth/ambient pop vs club: drops, club grooves and festival energy route to club, everything else electronic stays synth pop. Groove-led pop is dance-pop/nu-disco; house, trance, hardstyle and festival drops are club.
- Metal vs pop/alternative rock is decided by heavy-metal technique, not by volume or distortion alone.
- Contemporary folk vs roots/traditional: heritage, regional, Celtic or maritime identity routes to roots.
- Jazz/swing vs traditional vocal/stage: a dominant rhythm section or big-band language is jazz; a crooner without those cues is stage.
- Modern R&B vs soul/blues/gospel: classic soul stays in the older family, and lo-fi R&B usually takes hip-hop as its secondary.

Family size tracks how much training signal a genre term carries. Metal (78 cards), East Asian modern (75), pop/alternative rock (75), hip-hop (74) and East Asian heritage (72) are dense; club EDM, roots/traditional and general pop sit at 29 each. In a thin family, describe the machinery rather than trusting the genre name.

Routing only works on territory the corpus holds. Whole traditions are missing from it - progressive, psychedelic, art rock, post-rock, krautrock, the breakbeat lineage, free jazz - and a brief from one of those routes to whatever its tempo and instrumentation resemble instead. Check the term and its tempo band before routing: [minimax-music-3-corpus.md](minimax-music-3-corpus.md).

## Priors and how to override them

The caption format buys section-level control; it does not stop the model reaching for the most common rendering of a style. When a caption is fully compliant but the result has the wrong character - too polished, too radio, too generic - work these levers in order of force rather than adding more adjectives to the field that sounds wrong.

No field binds the model absolutely. Section tags and caption fields are generative conditioning rather than symbolic instruction, so delivered tempo, key, instrumentation and structure can drift from what the caption states, and one caption at two seeds can differ on all four. Re-roll the seed before rewriting a field - a single off-target take is a sample. The same miss across several seeds is a prompt problem, and that is when the levers below apply.

**Genre terms outweigh every prose field.** `Progressive Metal` comes back polished and pitch-corrected; `Alternative Metal` carries nu-metal, which is what its 19 corpus cards contain. Changing the genre line moves the result further than several rounds of vocal-field rewrites.

Terms split into two kinds, and the difference decides how you use them. A term with corpus cards behind it supplies a sound and its priors together, so `Alternative Metal` brings the nu-metal vocal whether or not you wanted it. A term with no cards at all - Noise Rock, Math Rock, Sludge Metal, Art Rock, No Wave, and Progressive Metal itself - summons no radio prior, which is the reason they work as escapes, but supplies no sound either. The result is decided entirely by the arrangement and vocal fields, and by whatever neighbourhood the BPM and instrumentation point at. Use an absent term to withhold a prior, never to specify a style, and check which kind you have before writing the line ([Pre-flight check](#pre-flight-check)).

**Section tags carry performance priors, not just structure.** `[Chorus]` triggers the whole chorus apparatus - a volume lift, doubled vocals, hook-shaped phrasing - and `[Pre-Chorus]` implies a lift into something, with the same effect. Most briefs want exactly that. Where a brief wants nothing pop in the result, or a through-composed shape whose sections develop rather than return, dropping the tags removes the reflex at source: repeated `[Verse]` plus `[Instrumental]`, `[Bridge]` and `[Outro]`, with the caption naming sections in prose as "the first vocal section", "the second", and so on.

Removing the tag leaves the reflex in the words. A refrain that comes back unchanged, even line lengths, and a short imperative alone on its line all get sung as a hook whatever the tag says. Alter the refrain on each return, run the line lengths uneven, and let phrases carry past where a singer would breathe - the lyric-shape patterns under [Corpus craft patterns](#corpus-craft-patterns) are what make repeated verses read as development.

**Effort words render as production.** "Belts", "cracks", "leans in", "pushes hard", "gains intensity" all come back as the polished performance, because that is what an intense vocal usually sounds like on a record. To get weight without gloss, make the band heavier and state that the voice does not follow it: a vocal that moves opposite to the arrangement - quieter as the guitars arrive - is the single most reliable anti-anthem instruction.

**Self-inflicted polish cues.** These read as neutral description but are production flourishes, and each one pulls toward a commercial mix: a slapback or delay throw on a hook word, unison or octave doubles in a chorus, "precise pitching", "controlled", "resonant", "velvety", "full chest projection". For a raw result, none of them belong in the caption.

**Describe the recording chain, not the voice.** "One condenser several feet away, in the same room as the band, on the same take, with bleed into the drum mics, no comping and no overdubs" does more for rawness than any timbre adjective. The same move works for any organic genre: specify how it was captured and what was not fixed afterwards.

**Individual production details are genre flags, and a stack of them outvotes the genre line.** Before writing a field, check the `minimax-music-3-genres.md` reference for what the detail signifies elsewhere - a caption can be dragged into a genre nobody asked for by four or five small choices that each looked neutral. Known offenders: slapback delay reads rockabilly; tambourine plus backbeat plus major key reads country; a male harmony below the lead reads country; root-and-fifth bass reads country; "drawl", "twang" or any regional accent word imports that whole idiom; brushed kit reads jazz; ride bell and rim clicks carrying the time reads jazz combo; hand percussion plus swung hats reads downtempo. Match the accumulated detail to the target or the genre terms will lose.

**Application Scenarios is imagery, not plot.** Setting the scene with the same objects the lyrics use both breaks the no-paraphrase rule and doubles down on whatever genre that scenery belongs to. Describe the listening situation and the emotional register instead.

**Negation is unreliable, and naming evokes.** The encoder handles negation poorly, and an exclusion that names a genre ("no nu-metal bounce") can summon it. Convert most exclusions to positive statements of what does happen, keep two or three high-value ones, and never name the genre being avoided. Where the frontend offers a negative caption, that is the correct home for an exclusion: it names the thing plainly and steers away from it without the naming backfiring. See [Negative prompting](#negative-prompting).

## Negative prompting

Available where the frontend exposes it (a ComfyUI workflow with `negative_caption` and `negative_weight` inputs). Everything above still applies to the positive caption; this is an extra axis, not a replacement for writing the caption well.

**Where it acts.** In the autoregressive text encoder, the same stage the caption acts on, before any audio token is emitted. It can therefore move the composition itself - melody, structure, arrangement - not just the tone of the render. The DiT and VAE stage downstream only renders what that stage decided.

**Mechanism.** The encoder already ran classifier-free guidance over a two-row batch: row 0 is the caption, row 1 was a null prompt with every caption and lyric token overwritten by `<|audio_cfg|>`. Guidance is `guided = negative + (positive - negative) * cfg_scale`. The negative caption substitutes real text into that previously-null row. The steering direction is `positive - negative`, so **anything the two captions share cancels and contributes nothing**. That one fact drives everything below.

### Controls

- `negative_caption` - free text, written as a caption.
- `negative_weight` - 0.0 to 1.0, blending between the null row and the negative row. `0.0` disables it and generation is bit-identical to not using it. `1.0` replaces the null row outright and is the normal setting, the equivalent of a negative prompt in an image model rather than an extreme. Values between are a partial retreat toward having no negative.
- Push strength is not set by `negative_weight`. It comes from `cfg_scale`, shared with the positive caption.

### What it can and cannot do

Steers away from genres, styles, instruments, production characteristics, arrangement habits and vocal treatments - anything the caption vocabulary expresses. Because it acts before token generation, it changes the composition.

- It is not a filter or a ban list. Nothing is prohibited; the distribution is tilted.
- It cannot override the positive caption. Asking for something in the caption that the negative rejects makes the two fight, with `cfg_scale` mediating. Contradicting your own caption wastes the mechanism.
- It does not operate on lyrics. The negative is read as a caption, so it cannot suppress words or phrases in the sung text.
- It has no effect at weight 0 or with empty text.

### Writing one

Write it as a caption in the same structured format as the positive, with attributes under the heading that owns them: a vocal treatment under `Vocal Details`, a genre on the `Basic Attributes` line. The encoder is a Qwen-based LLM trained on captions in that shape, and it reads the headings.

Two strategies, trading precision against force:

- **Mirrored** - copy the positive caption and change only the clause being negated. Everything identical cancels exactly, leaving a clean single-axis direction. Precise, but the resulting vector is small, so it needs a higher `cfg_scale` to be felt.
- **Minimal** - a short caption in the same shape carrying only the offending attribute. Blunter direction, far more magnitude behind it.

Between the two sits the useful default: write the version of the song you do not want, inverting only the fields that carry the failure mode and leaving the rest out. Each field you invert adds an axis to the vector, so four inverted fields aimed at one target beat eleven aimed at several.

Hold bpm and key identical to the positive. They cancel exactly. A different bpm in the negative steers away from that tempo as well as from the genre, which is rarely what you meant.

### Worked negative

Positive caption: 92 BPM C# minor, Gothic / Math / Progressive / Black Metal. A flat emotional level that never climbs, a voice that drops further under the guitars as they thicken, returns delivered lower and quieter each time, an abrupt stop. A low clean male voice within a fifth, close to speech, one microphone in the room with the band and drum bleed on the vocal track. No strings, no pad, density in the final third coming from the existing guitars playing lower.

Aimed at pop rock, nu-metal and generic smooth vocals:

```text
Global Metadata
Basic Attributes: bpm is 92. key is C#, and scale is minor. Pop Rock / Alternative Rock / Nu-Metal.
Global Emotional Progression: The piece opens with an atmospheric introduction that establishes mood before the song proper begins. Intensity and vocal volume climb steadily across the arrangement, each section larger than the one before it. The returning sections are the peaks, delivered higher and louder each time as the singer rises over the thickening guitars to meet them. The final section is the biggest in the piece, with the full arrangement and the vocal at its most powerful, and the song fades out.
Vocal Gender & Timbre: Singer A (Male). A polished mid-range tenor, bright and open at the top, smooth and even throughout with no grain or roughness in it. A wide and flexible working range, projected out into the room and clearly performed rather than spoken.
Vocal Style: The voice builds in volume from the first line to the last, opening restrained and ending belted at full power. Phrase endings are held and sustained across multiple beats, with melisma and vocal runs decorating the ends of lines. The returning sections are sung higher and stronger each time, doubled and stacked with harmony lines above the lead. Every line is sung.
Vocal FX: A composite vocal comped from several takes and recorded separately from the band. Pitch corrected and heavily compressed to a constant level, de-essed and bright, with a long bright hall reverb and delay throws on the ends of lines. Doubles and harmony stacks are spread wide across the stereo field. No breath or lip noise is audible.
Secondary: Synth pads and string arrangements arrive to lift the returning sections, widening the arrangement each time. Downtuned palm-muted guitars with scooped mids drive the heavy sections, and new elements are introduced at every section boundary to keep the arrangement escalating. The density in the final third comes from layers added on top rather than from the existing instruments.
```

Five fields, each inverting one decision:

- `Global Emotional Progression` - the flat held level and abrupt stop against build-to-a-big-final-chorus-and-fade. The main anti-pop-rock axis.
- `Vocal Gender & Timbre` and `Vocal Style` - narrow, dull and close to speech against bright, wide-range and belted with runs and stacked harmonies. The anti-smooth-vocal axis, and the heaviest here because two fields carry it.
- `Vocal FX` - one microphone with room bleed and a short dark plate against comped, tuned, de-essed and drenched. Blocks the polished-record sound that pulls smooth vocals back in.
- `Secondary` - the positive's stated absence of strings and pads against pads and strings arriving on cue, plus downtuned scooped-mid riffing for the nu-metal side.

Note what is not there: no `Application Scenarios`, no `Sonics & Production Profile`, no `Groove`, no `Primary`, and no negation word anywhere.

### What has no effect, or backfires

- **Negation words backfire.** Write `Nu-Metal`, never `no nu-metal` / `avoid nu-metal` / `without nu-metal`. The slot already means "away from this", so a negated phrase steers away from the absence of the thing.
- **Bare keyword lists are weak.** Against a long structured caption, `nu-metal, pop` makes the difference vector encode "not a prose caption" more than "not nu-metal".
- **Markdown does nothing.** `clean_caption()` strips headers, bullets, bold and emphasis before tokenising.
- **Text identical to the positive does nothing.** It cancels exactly. Only the differing clauses steer, which is the point of the mirrored strategy rather than a flaw.
- **Overlong text is silently truncated** at the token length of the positive caption plus lyrics, keeping the front and discarding the rest, with a warning to the ComfyUI log. The budget is generous in practice.

### Recipe

1. Start minimal at weight 1.0 to confirm the effect is audible.
2. Move to the field-by-field inversion above once you know what you are steering. A near-total inversion carries plenty of magnitude on its own, so leave `cfg_scale` at 1.7; a strictly mirrored negative changing one clause needs it raised to compensate for the smaller vector.
3. If the result goes stiff or thin, drop the weight to 0.6-0.8 rather than lowering `cfg_scale`.
4. If one failure mode survives, cut the fields that are not fighting it. A shorter negative concentrates the vector instead of spreading it across five axes.

Implementation notes: the negative runs through the same `build_prompt(caption, "")` and `clean_caption()` path as the positive, so `<|x y|>` tags expand to `x is y` identically. The blend happens in embedding space and shares one `cfg_scale` with the positive, so it cannot push away from the negative harder than it pulls toward the caption. A three-branch variant with an independent weight would remove that ceiling.

## Corpus craft patterns

Recurring moves across the 1,000 official reference captions:

- Echo the arc across fields: emotional progression, production and groove each restate the same section-by-section development using the same section names. The redundancy is the control.
- State absences explicitly in any unused field, not just harmony ("No percussion or drum kit is present") - the model reads silence as licence to fill.
- BPM count and felt tempo are separate: the BPM line carries the number, the Groove field carries the feel (shuffle, 12/8, half-time). High-BPM captions still declare "half-time" in Groove.
- Numeric drum placement (snare on beats 2 and 4) beats adjectives - but a single numeric backbeat instruction overwrites paragraphs of odd-metre prose. One "snare plainly on 2 and 4" is enough to flatten a whole song to a square four.
- One metre for the whole song survives; four per-section metres average into mush. Pick one odd cycle, name its grouping (7 as 3+2+2, 9 as 2+2+2+3, 11 as 3+3+3+2), and restate it in more than one field.
- Odd metre stays approachable when one element ignores it: a ride or hat playing straight groups of four across a seven-beat cycle rotates against the riff and realigns every few bars, so the head still nods.
- Give the vocal a per-section delivery timeline (recited, clipped, whispered, spoken over the band, entering a beat late) rather than one global description. This is what stops a performance sounding prescribed.
- The field word ranges are typical lengths, not caps. Vocal Style and Groove & Foundation Progression reward deliberate overruns when they are carrying section-by-section control.
- For organic genres, keep deliberate imperfection audible: amp hum, string noise, breath.
- Lyric shape steers delivery. A short imperative alone on its line will be chanted; uneven line lengths and phrases that run past where a singer would breathe cannot be. A refrain that returns altered each time gets sung as development rather than as a hook.

Four of these patterns describe machinery the corpus does not contain. Odd metre appears in one caption of the 1,000, time signatures in two, and `imperfect` in four, so nothing in training supports them. They still work, because they spell out what the model should play rather than naming a style, and that is the only mode available for anything outside the corpus. Expect them to need restating across fields and to survive imperfectly.

Per-genre tempo/key conventions and field vocabulary: read [minimax-music-3-genres.md](minimax-music-3-genres.md). Which terms exist at all, what each tempo band contains, and what to write instead of an absent style name: read [minimax-music-3-corpus.md](minimax-music-3-corpus.md).

## Series and album consistency

For several tracks that should sound like one band, hold three fields byte-identical across every caption: `Vocal Gender & Timbre`, `Harmony/Backing Vocals` and `Vocal FX`. Those carry singer identity and recording chain, and any rewording drifts the voice between tracks. `Sonics & Production Profile` can share its first and last sentences (the room, the mix philosophy) while its middle varies per track.

Everything else is where the tracks differ: BPM, key, metre and grouping, genre third term, and all four Arrangement fields. `Vocal Style` varies per track because delivery should, but end each one with the same constraint clause so the performer's limits stay fixed.

An arrangement conceit per track keeps a set from blurring - density that rises monotonically and never drops, an arrangement that descends in register every section, gaps left open with room tone and hum named as the instruments filling them. State the conceit in `Global Emotional Progression` and again in `Groove & Foundation Progression`.

## Official template library

MiniMax publishes the 1,000 reference captions plus a caption-rewriting skill at https://github.com/MiniMax-AI/MiniMax-Music3 (`skills/music-caption-rewriter/`: genre router, 18 family indexes, `templates/`). Rules from it worth keeping:

- Draw on at most three reference captions, each with a distinct role: Foundation (overall identity and groove), Modifier (one requested dimension only - vocal character, cultural colour, production), Arrangement (section development and transitions). Never inherit a template's exact key, BPM, vocalist or section order, and never copy its sentences.
- Rank candidates in this order: genre and subgenre compatibility; explicit requirements and exclusions; groove and tempo compatibility, counting plausible half-time and double-time relationships as compatible; vocal configuration; instrumentation; mood and emotional arc; production character. A direct conflict on any of these outweighs shared mood vocabulary, so a close musical family beats a card that only matches the adjectives.
- One or two references is the right answer for a simple brief. Do not add a weak third to fill the role set.
- Its output contract targets 250-450 words - shorter than the 420-720 the template corpus itself uses. Prefer the corpus range for section-level control.
- It also forbids inventing an exact BPM, key or vocal gender the brief did not supply, where this guide asks for concrete values. Same trade as the word count: a vague caption is harder to contradict, a concrete one gives more section-level control. Choose concrete values unless the user explicitly wants the model to decide.

The reference Gradio app at https://huggingface.co/spaces/MiniMaxAI/MiniMax-Music3 (`app.py`) carries the shipped caption and lyric contracts in its system prompts. Constraints from it:

- Caption and lyrics are tokenised into one prompt under a single token ceiling, so a long caption and a long lyric sheet compete for the same budget.
- Generation caps at 9,000 latent frames, roughly 300 seconds, whatever duration is requested.
- State what enters, exits, changes or intensifies for every section in the Arrangement fields, aligned one-to-one with the lyric section tags.

## Resolving conflicts

Apply in this order when the user's brief, lyric tags and genre convention disagree:

1. Explicit user requirements and exclusions.
2. Section-local direction from a lyric tag, applied within that section only.
3. Strong implications of the user's own description.
4. Genre convention.

A section-local instruction changes that section, never the global genre. When two explicit user instructions conflict, prefer the more specific and later one. Never silently reverse an explicit vocal gender, instrumental request, tempo bound, required instrument, or prohibited element.

## ComfyUI specifics

- **Workflow**: Template Library > Audio > MiniMax Music 3 Text to Music. Two text nodes (caption, lyrics) feed the text encoder; the DiT synthesises the latent; the audio VAE decodes to 32kHz stereo, saved by `SaveAudioAdvanced` to `ComfyUI/output/audio/`.
- **max_duration**: seconds, template default 60, model ceiling ~300. It caps the output rather than setting it - see [Duration is a ceiling](#duration-is-a-ceiling). Longer costs time and VRAM.
- **seed**: fixed seed reproduces the take; change it for a different performance of the same caption.
- **negative_caption / negative_weight**: optional, where the workflow exposes them. Weight 1.0 is the normal setting and 0.0 disables it. Written as a caption, not a keyword list, and never with negation words - see [Negative prompting](#negative-prompting).
- **cfg_scale**: shared by the positive and negative captions, default 1.7. Raise it when a mirrored negative is too subtle to hear.
- **tiled_decode**: on cuts VAE VRAM for long songs at a small risk of seams at tile boundaries; off on a high-VRAM GPU for best quality.
- **Models**: `minimax_music3_dit_fp16.safetensors` (or the INT8 DiT for low VRAM) in `diffusion_models/`, `minimax_music3_text_encoder_pruned_int8_convrot.safetensors` in `text_encoders/`, `minimax_music3_dav.safetensors` in `vae/`.
- Iterating on one field at a fixed seed is the fastest way to hear what that field controls.

## Worked example

Caption:

```text
Global Metadata
Basic Attributes: bpm is 96. key is F, and scale is minor. Neo-Soul / Alternative R&B.
Global Emotional Progression: The song opens guarded and low-lit, a single electric piano chord carrying more space than movement. Warmth builds as the rhythm section settles underneath the first chorus, and the emotional weight climbs through the second verse on vocal intensity rather than added volume. The bridge breaks open into brief release before the outro withdraws to the opening sparseness, leaving the last line unresolved.
Application Scenarios & Imagery: A late-night drive through wet city streets, headlights smearing across the windscreen; equally suited to a slow-burn film scene set in an empty apartment before dawn.
Sonics & Production Profile: The soundstage is wide but uncrowded, with the voice held close and centred while keys and guitar sit further back. The low end is round and slightly loose, the upper mids softened, and tape-style saturation takes the edge off transients. Dynamics stay breathable, with light bus compression that lets the chorus lift without flattening the verses.
Vocal Details
Vocal Gender & Timbre: Singer A (Female). A smoky alto with a grainy edge at the top of the register and a soft, almost spoken bottom end that reads as intimate rather than fragile.
Vocal Style: Verses are conversational and behind the beat, with clipped phrase endings and audible breath. The chorus moves into a fuller chest projection with short melismatic turns at line ends, and the bridge sits at the top of the register where the grain becomes deliberate. The final chorus returns to a hushed delivery an octave down.
Harmony/Backing Vocals: Self-layered thirds enter beneath the second half of each chorus, widening to a four-part stack in the bridge. A single low unison double shadows the verse lines from the second verse onward, mixed well under the lead.
Vocal FX: A short plate reverb keeps the lead in a small room, with a quarter-note delay thrown only on the last word of each chorus. Light analogue saturation on the lead; harmonies are filtered and pushed wider without pitch correction artefacts.
Arrangement
Instrument Lifecycle Description (Primary/Secondary Layering):
Primary: A warm electric piano carries the harmony from the first bar to the last, played with loose voicings and a slight swing in the left hand. A clean electric guitar joins from the first chorus, answering vocal phrases with muted single-note figures rather than chords.
Secondary: A muted trumpet enters in the second verse with sparse long tones and drops out for the bridge. A low analogue pad supports the choruses only, thickening on the final one. Rhodes tremolo and a single sustained organ note fill the bridge, where the guitar steps back entirely before returning under the last chorus.
Groove & Foundation Progression: The intro carries no drums, only the electric piano and a soft kick pulse. A relaxed shuffled backbeat enters at the first verse with brushed snare and loose sixteenth hats. The bass is a round, fretless-style line that slides into root notes and leaves space on the downbeats. Hats open through the pre-chorus, the kick doubles under each chorus, and the whole kit drops to a rimshot pulse for the bridge before a two-bar tom fill returns the full groove for the final chorus.
Embellishments, Textures & Spatial FX: Vinyl crackle sits underneath the intro and outro. Reverse cymbal swells mark each chorus entry, and a filtered sweep opens the bridge. Finger noise on the guitar and pedal creak from the electric piano are left audible, and the outro fades on a long reverb tail from the last piano chord.
```

Lyrics:

```text
[Intro]

[Verse]
Streetlights blur across the windscreen
I keep the radio down low

[Pre-Chorus]
Every turn I take is one I know by heart

[Chorus]
So drive me somewhere new
Somewhere the morning waits for us

[Verse]
Your coat is folded on the back seat
Still smells like the room we left

[Chorus]
So drive me somewhere new
Somewhere the morning waits for us

[Bridge]
I stopped asking where the road goes

[Chorus]
So drive me somewhere new

[Outro]
```

## Think carefully about how your lyrics will match the music

We want the pacing, rhythm, and emotional tone of the lyrics to complement the music. Consider where the singer will take their breaths and how lyrics will flow, and resonate with the musical arrangement.

When referencing existing works created with minimax music 3 unless requested do not copy or reuse the exact same lines when asked to create completely new tracks - if the user asks you for more similar music they don't want want another version of the same song - they want another song the belongs on the same album.

## Review checklist

0. You have consulted the appropriate references and examples in order to form the highest quality output.
1. Three headings present, spelled exactly, in order, each on its own line.
2. Eleven field labels present and spelled exactly, including the bare `Instrument Lifecycle Description (Primary/Secondary Layering):` header above `Primary:` and `Secondary:`.
3. `Basic Attributes` follows the fixed phrasing with an exact BPM, key, scale and two or three genre terms. Each term names a style, not a modifier (`ballad`, `epic`, `dark`, `cinematic`, `modern`, `emotional`), and a fusion is ordered primary first.
4. No bracket tags, lyric lines or song title anywhere in the caption.
5. Singer IDs assigned once and reused; vocal gender and any instrumental request match the user's brief.
6. Every vocal field filled, including an explicit statement when harmonies or effects are absent.
7. Arrangement fields read as a timeline with entrances, exits and changes tied to named sections.
8. Groove field covers drums and bass development, not just a kit description.
9. Lyric tags are the only structural instruction in the lyrics input, and lyric volume suits `max_duration`. An instrumental track carries tag-only lines rather than an empty box, with enough sections to span the duration.
10. Field lengths land in the ranges above; the whole caption reaches 420-720 words.
11. When the brief rejects the mainstream rendering of a style, the genre terms and the section tags have been checked as sources of that default before any prose field is rewritten.
12. Every genre term and distinctive production phrase has been checked against the corpus, and the BPM has been checked for the neighbourhood it selects. Anything absent is described as machinery rather than named ([Pre-flight check](#pre-flight-check)).
13. Any negative caption is written in the caption format, names what to steer away from without negation words, and does not contradict the positive caption ([Negative prompting](#negative-prompting)).

## Delegating parallel songwriting to sub-agents

If the user asks you to delegate or parallelise songwriting tasks, you can create sub-agents to do the work in parallel. Ask the user if they want to use the fable or opus model for the sub-agents.

Task each of subagents in parallel with: 1) activating the llm prompting guide skill, 2) reading it's minimax music 3 prompting references, 3) reading this new document then finally 4) authoring a new artistic piece each faithful to the values and style outlined in the new document.
Get each of the agents to write their context, minimax music 3 prompts and lyrics to a new file each. Then when they're done review their work and give me thoughts on it or do as otherwise instructed.

## Iteratively improving or varying a song

If the user works with your to provide feedback and improve a song, default operating mode unless otherwise requested:
- For small tweaks and improvements update the caption / lyrics in place.
- For larger changes create a new version of the caption or lyrics in the same file, and add a note about the feedback / problems with the previous version. This allows you to keep track of the changes and the evolution of the song.
