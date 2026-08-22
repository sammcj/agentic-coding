# MiniMax Music 3 Corpus Coverage

The model responds to what its published training captions contain, not to genre names in general. A term that appears nowhere in the 1,000 reference captions carries no signal, and the encoder falls back on whatever neighbourhood the rest of the caption points at. `Progressive Rock` is the standing example: `Progressive` exists in the corpus almost entirely as `Progressive House`, so the term drags a rock brief toward 128 BPM electronic dance.

Checking a term takes seconds. Not checking it costs a generation.

## Contents

- [Contents](#contents)
- [Checking a term](#checking-a-term)
- [What the corpus contains](#what-the-corpus-contains)
- [Zero-coverage terms](#zero-coverage-terms)
- [BPM to family map](#bpm-to-family-map)
- [Absent territories and substitutes](#absent-territories-and-substitutes)
- [Corpus-wide defaults](#corpus-wide-defaults)

## Checking a term

Note that this skill allows you to clone the templates to it's references/minimax-music-3-templates folder (gitignored)

```sh
PATH="/PATH/TO/SKILL/references/minimax-music-3-templates"
cd "$PATH" && git pull || git clone --depth 1 https://github.com/MiniMax-AI/MiniMax-Music3.git "$PATH"
cd "$PATH/skills/music-caption-rewriter"

# label count: does it route? (appears as a genre term on a Basic Attributes line)
rg -icl '^Basic Attributes:.*psychedelic' templates | wc -l

# body count: has the model heard it described?
rg -icl 'psychedelic' templates | wc -l
```

Two counts, two meanings. The label count is what routes the caption to a style neighbourhood. The body count is descriptive vocabulary the model has seen attached to sound. A term with a body count and no label count is safe to describe with and useless to route with.

Watch for substring traps when reading counts: `emo` matches `emotional` in all 1,000, `glitch` matches `glitchy`, `drone` matches `drone double-stops`, `movement` and `motif` match ordinary prose. Use `rg -w` for short words.

Spelling and hyphenation are corpus-specific. The captions are American-spelled and use `side-chain`, not `sidechain`; `analog`, not `analogue`. A zero result on the wrong variant is a false alarm.

## What the corpus contains

1,000 captions across 18 style families. Minor share matters as much as the term list: it tells you what the family sounds like before you choose a key.

Note that these are known _examples_, they are limit the complete limitations of the model, you can also use different BPM ranges.

| Family | n | BPM range (median) | Minor | Dominant terms |
|-|-|-|-|-|
| metal-heavy-rock | 78 | 79-194 (98) | 88% | Alternative Metal 19, Metalcore 17, Hard Rock 16, Nu-Metal 11, Symphonic Metal 11 |
| pop-alternative-rock | 75 | 57-182 (100) | 33% | Pop Rock 37, Alternative Rock 35, Arena Rock 10, Power Ballad 8, Symphonic Rock 7 |
| east-asian-modern | 75 | 70-182 (128) | 40% | Mandopop 51, C-Pop 19, Pop Rock Ballad 8, EDM 7 |
| hip-hop-rap | 74 | 71-182 (92) | 85% | Hip-Hop 37, Lo-fi Hip Hop 11, Trap 8, Alternative Hip-Hop 7, Boom Bap 4 |
| east-asian-ballad-heritage | 72 | 62-146 (72) | 31% | C-Pop 34, Mandopop 32, Cinematic Ballad 13, Orchestral Ballad 9 |
| modern-rnb-neo-soul | 66 | 58-162 (92) | 57% | Contemporary R&B 44, Neo-Soul 16, Alternative R&B 9, Trap Soul 7 |
| jazz-swing-big-band | 65 | 56-214 (120) | 44% | Vocal Jazz 29, Big Band Jazz 16, Swing 12, Jazz Ballad 10 |
| contemporary-folk-acoustic | 64 | 56-182 (90) | 15% | Indie Folk 42, Acoustic Pop 18, Singer-Songwriter 13, Acoustic Ballad 12 |
| soul-blues-gospel | 59 | 56-176 (97) | 69% | Blues Rock 32, Soul 22, Blues 5, Hard Rock 4, Southern Rock 4 |
| electronic-synth-ambient-pop | 59 | 58-182 (109) | 59% | Electronic Pop 19, Synth-Pop 12, Ambient Pop 9, Dream Pop 5, New Age 4 |
| cinematic-pop-ballad | 54 | 62-207 (75) | 38% | Cinematic Pop 24, Cinematic Ballad 21, Orchestral Ballad 13 |
| country-americana | 50 | 74-194 (88) | 20% | Country 23, Americana 15, Country Rock 11, Country Pop 5 |
| traditional-vocal-stage | 43 | 58-194 (90) | 27% | Traditional Pop 18, Musical Theatre 16, Vocal Jazz Ballad 6 |
| cinematic-orchestral-epic | 42 | 62-143 (85) | 50% | Cinematic Orchestral 27, Epic Choral 6, Patriotic Anthem 3 |
| dance-pop-disco-funk | 37 | 109-140 (120) | 78% | Nu-Disco 19, Dance-Pop 12, Funk Pop 10, Synth-Pop 5 |
| roots-traditional-global | 29 | 61-158 (83) | 62% | Folk 8, Chinese Traditional 5, Americana 4, Chinese Folk 3 |
| general-pop-ballad | 29 | 66-194 (94) | 20% | Indie Pop 8, Pop 5, Contemporary Ballad 4, Children's Music 3 |
| club-edm-house-trance | 29 | 100-182 (136) | 44% | Progressive House 12, Vocal Trance 5, Trance 4 |

472 distinct genre terms appear across the 1,000 Basic Attributes lines, with a long tail used once or twice. A term outside the dominant handful for its family exists but carries thin signal, so support it with the machinery description rather than leaning on the name.

The corpus is weighted toward mainstream song forms. Guitar music in it means Pop Rock, Alternative Rock, Arena Rock and Blues Rock. Nothing in the 1,000 sits in the experimental, psychedelic or progressive tradition, which is why briefs from that world need the whole sound described by hand.

## Zero-coverage terms

Absent as both genre label and prose, across all 1,000 captions:

- Rock and adjacent: psychedelic, art rock, space rock, krautrock, post-rock, shoegaze, noise rock, math rock, sludge, doom metal, stoner, garage rock, new wave, hardcore punk, glam, yacht rock.
- Metal: progressive metal, black metal, thrash, grindcore, post-metal.
- Electronic: trip-hop, breakbeat, IDM, UK garage, chiptune, vaporwave. Drum and bass and jungle have no genre label and one or two passing prose mentions each, which amounts to the same thing.
- Other: free jazz, avant-garde, atonal, modal, afrobeat, flamenco, klezmer, psych folk, freak folk, sadcore, motorik.

Production and technique phrases with zero body count, despite being obvious things to write:

- Instruments and gear: mellotron, moog, theremin, sitar, 12-string, e-bow, talk box, leslie, ring modulator, condenser, valve, tube.
- Effects: tape echo, tape delay, phaser, fuzz, varispeed, vocoder, sequencer, arpeggiator. Related terms that do exist: `tape saturation` 12, `tape hiss` 27, `echo` 200, `delay` 882, `wah` 9, `reverse guitar` 9, `flanger` 1, `spring reverb` 1, `arpeggiated` 580, `sequenced` 297.
- Rhythm and form: polyrhythm, 7/8, 5/4, odd meter, pedal point, through-composed. Time signatures appear in two captions in total, and `12/8` in one.
- Key changes: `key change` appears once, and modulation to a new key twice. A modulation has to be described as an event, and it may still not arrive.

Near-zero terms worth knowing: `classic rock` 3, `slowcore` 1, `darkwave` 1, `post-punk` 1, `surf rock` 1, `bossa nova` 1, `celtic` 2, `reggae` 1, `experimental` 1, `progressive rock` 1 (a musical theatre card labelled `Progressive Rock Opera`).

## BPM to family map

Choosing a tempo silently chooses a neighbourhood. Bands with their actual occupants:

| BPM | n | Who lives there |
|-|-|-|
| 56-69 | 66 | East Asian heritage ballads, jazz ballads, soul, cinematic ballads, folk. 39% minor |
| 70-79 | 189 | East Asian heritage ballads 43, cinematic pop ballads 28, pop rock 19, country 15. 30% minor |
| 80-89 | 139 | Hip-hop 26, folk 14, R&B 12, country 11, metal 10, soul-blues 10. 51% minor |
| 90-99 | 124 | Metal 29, R&B 24, hip-hop 22. 68% minor, the darkest band in the corpus |
| 100-109 | 64 | Synth and ambient pop, jazz, soul-blues, orchestral. 50% minor |
| 110-119 | 59 | Nu-disco and funk 16, stage, jazz, East Asian modern. 57% minor |
| 120-129 | 98 | Nu-disco and funk 18, synth pop 15, jazz 12, East Asian modern 12. 57% minor |
| 130-139 | 61 | East Asian modern 21, club EDM 13, jazz 7. 54% minor |
| 140-149 | 57 | Pop and alternative rock 10, East Asian modern 9, club 6, hip-hop 6. 49% minor |
| 150-169 | 71 | Pop and alternative rock 12, folk 10, hip-hop 8, soul-blues 8, country 7. 49% minor |
| 170-199 | 64 | Metal 17, pop and alternative rock 10, country 7, jazz 7. 46% minor |
| 200+ | 6 | Jazz only, and always a double-time count over a slow swing |

Consequences worth planning around:

- Below 76 BPM the corpus is ballads. Of the 182 cards at or under 75 BPM, 52 are East Asian heritage ballads, 28 are cinematic pop ballads and 14 are jazz ballads. A slow brief inherits ballad production unless the arrangement fields fight it.
- Slow plus guitar lands in blues rock, southern rock or americana, because that is what the slow guitar neighbourhood contains. Of the 20 cards at or under 60 BPM, every rock-labelled one is Blues Rock, Slow Blues or Soul Ballad; the remaining guitars belong to acoustic folk ballads, jazz ballads and neo-soul.
- 90-99 is the corpus's heavy band, shared by metal, R&B and hip-hop at 68% minor. A mid-tempo minor-key brief lands here by default.
- 120-140 is electronic and dance territory whatever else the caption says. A rock brief at 128 BPM is swimming upstream.
- High BPM does not mean fast: the jazz cards at 200-214 are double-time counts over a slow swing, and the Groove field carries the felt tempo.

## Absent territories and substitutes

For each, the nearest represented neighbourhood and the machinery to spell out by hand. In every case the genre name is worthless and the description does all the work, so expect these captions to run long in the Arrangement fields.

**Progressive and art rock.** Nearest: `Symphonic Rock` (8 cards, all J-Rock, anime or C-Pop, 77-146 BPM), plus `Alternative Rock` for the guitar language. Never write `Progressive` in the genre line; it routes to house. Describe instead: sections that do not return, an instrumental passage longer than any vocal section, `ostinato` (25) figures that change length, Hammond organ (52) and Rhodes (25) carrying harmony, `counterpoint` (49) between guitar and keys, an ending that is `unresolved` (98) or `abrupt` (72). Odd metre has effectively no corpus support, so name the cycle and its grouping in more than one field and expect the model to round it off.

**Psychedelic and space rock.** Nearest: `Blues Rock` for the guitar tone, `Ambient Pop` or `Dream Pop` for the haze. Zero support for psychedelic, phaser, mellotron, sitar or backwards tape. Buildable from what exists: `hypnotic` (51), `drone` (31), `reverse guitar` (9), `wah` (9), `slide guitar` (36), `echo` (200) and long delay described by its interval, `swirling` textures (12), `tape saturation` (12), `vinyl crackle` (111), a long `instrumental break` (282), and stereo `panning` moves (211).

**Post-rock, shoegaze and krautrock.** Nearest: `Ambient Pop`, `Cinematic Orchestral` for the build. Describe: a `crescendo` (69) across the whole piece rather than per section, guitars as texture with `feedback` (57) and sustained `swells` (914), a groove that repeats without developing, and drums that enter once and never change pattern. Say what does not happen, since the corpus default is a chorus lift. `Tremolo picking` appears twice, so spell out the picking hand.

**Noise, math, sludge, doom and stoner.** Nearest: `Alternative Metal` and `Hard Rock` for weight, though both carry a polished vocal prior. Describe: down-tuned guitars (the corpus does use `down-tuned`), tempo held under 70 with the kit in half-time, `dissonant` (14) intervals, feedback held between sections, and one riff repeated past the point a chorus would arrive.

**Extreme metal.** `Death Metal` exists on three cards and `Melodic Death Metal` is the corpus's heavy ceiling. Black metal, thrash, grindcore and post-metal are absent. Describe blast beats, tremolo picking and harsh vocal type explicitly, and expect the clean-chorus reflex to need suppressing through the section tags.

**Breakbeat lineage.** Drum and bass, jungle, trip-hop, breakbeat, IDM, UK garage and glitch hop have no labels. Nearest: lo-fi hip-hop for the sampled feel, `Melodic Dubstep` and future bass for the sound design. Described from scratch: chopped and resequenced breakbeats with the BPM stated and the felt tempo declared separately in Groove, since half-time appears in only 106 cards and is the mechanism that makes a fast count feel slow.

**Free jazz and avant-garde.** Absent entirely, and `atonal` and `modal` return zero. The jazz family is vocal-led and arranged. Describe collective improvisation as an event with a start and end, name who plays over whom, and accept that `improvisation` (40) mostly means a written-sounding solo in this corpus.

**Global styles beyond the represented ones.** Afrobeat, flamenco, klezmer and most Latin styles are absent (`latin` appears as a word in three captions, `bossa nova` in one). Chinese traditional instruments are the exception and are well covered. For anything else, name the instrument, its playing technique and its rhythmic role, and do not rely on the regional label.

## Corpus-wide defaults

What arrives if the caption does not say otherwise. Counts are out of 1,000.

- `The piece opens` or `The track begins` 879. Openings are near-universally soft.
- `The performance begins with a [restrained/controlled] ...` 421, `evolves into` 381, some form of belt 558. The verse-restraint-to-chorus-belt arc is the single strongest prior in the corpus and it crosses every family including blues rock. Overriding it needs a stated counter-movement, not an adjective.
- `polished` 391 against `raw` 123. `imperfect` in any form appears in four captions, so audible imperfection has to be described as specific events (string noise, amp hum, a missed entry) rather than named.
- Snare on beats 2 and 4, 316. Reverse cymbal 465, risers 419, wall of sound 300.
- Plate reverb 564, pitch correction 169, multi-tracked self-harmony 352.
- `lingering` 512 and a fade or gradual decay ending is the default close. An abrupt ending (72) has to be asked for.
- Locking the bass tightly with the kick, 361. A bass that plays against the kick is unusual here and needs stating.
- Guitar solo 50, extended instrumental 11. Long instrumental stretches are rare, so section length has to be described rather than implied.

Recording-chain vocabulary sits outside the corpus almost entirely: `condenser`, `ribbon`, `valve` and `tube` return zero, `one take` and `live in the room` total five, `bleed` two, `room tone` 18, `hum` six. Describing the chain still works as an anti-polish lever precisely because those words carry no prior of their own, but the caption has to spell out what the microphone hears rather than naming gear.
