# MiniMax H3 Prompt Guide

MiniMax H3 is an omni-modal video model: it generates video and 32kHz stereo audio (dialogue, SFX, music) in a single pass, 4-15s at 24fps, 768p locally and up to 2K through the platform API. It was trained on prompts written in a specific labelled structure, so the field names (`integrated_multimodal_description:`, `overall_soundscape:`, ...), the shot markers, and the tag syntax are part of the prompt text you paste into the workflow's text-encode node. Free-form paragraphs work far worse than the structure below.

A community format built on `[0s-2s]` timecode brackets with plain prose and no labelled fields circulates widely, and some people report good results from it, particularly for dialogue. It is not the grammar the model was trained on, and it discards the diegetic/non-diegetic split, speaker IDs and `<d>` tags. Treat it as a fallback to experiment with, not a starting point.

## Contents

[Pick the mode](#pick-the-mode)

Base modes (T2VA / I2VA / FL2VA / L2VA), whose grammar R2V also inherits:

- [Prompt skeleton](#base-modes-prompt-skeleton)
- [Alignment instruction line](#alignment-instruction-line) - includes how duration snapping sets `S.SS`
- [integrated_multimodal_description](#integrated_multimodal_description)
- [Shots and cuts](#shots-and-cuts)
- [Pacing](#pacing)
- [Camera motion](#camera-motion)
- [Speakers, dialogue, singing](#speakers-dialogue-singing)
- [On-screen text](#on-screen-text)
- [overall_soundscape](#overall_soundscape)
- [non_diegetic_music](#non_diegetic_music)
- [Keyframe handling per mode](#keyframe-handling-per-mode)

R2V only:

- [Reference mode](#reference-mode-r2v) - includes [choosing reference images](#choosing-reference-images)

Both:

- [Beyond 15 seconds](#beyond-15-seconds)
- [ComfyUI specifics](#comfyui-specifics)
- [Worked examples](#worked-examples)
- [Review checklist](#review-checklist)

## Pick the mode

Mode is decided by which inputs are connected, and it changes both the first line of the prompt and the set of fields.

| Mode | Inputs | ComfyUI node / weights | Prompt shape |
|-|-|-|-|
| T2VA | text only | T2V template, `minimax_h3_fl2va_*` | 3 fields, no instruction line |
| I2VA | `first_frame` | `MiniMaxH3ImageToVideo`, `minimax_h3_fl2va_*` | first-frame instruction + 3 fields |
| FL2VA | `first_frame` + `last_frame` | `MiniMaxH3ImageToVideo`, `minimax_h3_fl2va_*` | two-picture alignment + 3 fields |
| L2VA | `last_frame` only | `MiniMaxH3ImageToVideo`, `minimax_h3_fl2va_*` | last-picture alignment + 3 fields |
| R2V | reference images / videos / audio | `MiniMaxH3ReferenceToVideo`, `minimax_h3_ref2va_*` | 6 fields, reference labels |

ComfyUI's template library labels these T2V, I2V and R2V. R2V loads a different checkpoint from the other four, so R2V-style labelled sections do not belong in a T2VA/I2VA workflow.

## Base modes: prompt skeleton

Instruction line (I2VA / FL2VA / L2VA only), one blank line, then the three core fields separated by blank lines:

```text
<alignment instruction line>

integrated_multimodal_description: [Shot 1] ...

overall_soundscape: ...

non_diegetic_music: ...
```

- `integrated_multimodal_description` - visuals, actions, shots, speakers, dialogue, singing and diegetic audio along the timeline.
- `overall_soundscape` - ambience, physical action sounds, non-verbal human sounds across the whole video.
- `non_diegetic_music` - score the characters cannot hear.

## Alignment instruction line

Use these strings verbatim. `N` is the index of the real final shot; `S.SS` is the effective video duration to exactly two decimal places.

Derive `S.SS` from the duration the node actually uses, not the value typed in. Duration snaps to a `17k + 5` frame grid at 24fps, so effective seconds = frames / 24 and the result is usually not a round number: 175 frames is 7.29s, not 8. The same frame count bounds every cut time in the description.

I2VA:

```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.
```

FL2VA:

```text
How the reference pictures align with the target video - Picture 1 (from Shot 1) aligns with the 0.00-second mark of the target video; Picture 2 (from Shot N) aligns with the S.SS-second mark of the target video.
```

L2VA:

```text
How the reference pictures align with the target video - <Picture 1> (from [Shot N]) aligns with the S.SS-second mark of the target video.
```

T2VA has no instruction line and starts straight at `integrated_multimodal_description:`.

## integrated_multimodal_description

Every detail should be something the model can render or play: visual style, opening composition, subject appearance and position, scene and props, actions and reactions, cuts, spoken language, synchronised diegetic sound. Abstract mood statements and plot summary give the model nothing to key on.

Work outside in. Settle the overall scene first (location, who is present, what is happening), then decompose it into timed shots; shots drafted before the scene is fixed tend to drift apart.

Open `[Shot 1]` with the overall style and the initial composition. Usable style words include `Cinematic`, `live-action`, `2D-animated`, `3D CG`, `claymation`, `watercolor`, `vintage film`. For keyframe modes derive the style from the reference image; for T2VA take it from the user's text.

```text
[Shot 1] Live-action, cinematic, a medium-wide shot frames...
```

## Shots and cuts

`[Shot 1]` carries no timestamp. Every later shot opens with a strictly increasing cut time inside the video duration, formatted `MM:SS.mmm`:

```text
[Shot 2] At 00:03.500, the camera cuts to...
```

Cut times are bounded by the snapped duration, so a cut at `00:08.000` in a 175-frame (7.29s) clip is unreachable.

Cut verbs: `the camera cuts to`, `the shot cuts to`, `the shot transitions to`, `the shot changes to`, `the shot switches to`. Cross-dissolve, fade and wipe are available when the user asks for them. A cut should deliver new information (subject, space, state, viewpoint, time); if only the distance or angle shifts slightly, use camera motion instead of a cut.

## Pacing

Decide where the peaks and the rests fall before writing shots. A peak is a completed action, an entrance, a text reveal or a full reveal; a rest is a held detail, a readable text hold, or a final frame hold.

- ~5s: one peak, then a stable close.
- ~10s: one or two peaks, one or two braking moments.
- ~15s: two or three peaks, two quiet moments.

One main action per beat. Secondary elements enter slightly late rather than competing: the subject settles, then the text appears; the highlight sweeps, then the copy moves.

Drive transitions off something actually in frame - an edge, a highlight, a part that opens or rotates, a matched silhouette, matched camera direction. White flashes, floating particles and generic light effects give the model nothing to align to. Do not open on an empty frame; the first second should already carry an action or an angle worth watching.

## Camera motion

Write motion as natural English action inside the shot, never as labels appended to the sentence. Three dimensions: type, amplitude, speed. Omit amplitude and speed when they are medium/normal.

| Dimension | Expression | Meaning |
|-|-|-|
| Type | `Zoom In / Zoom Out` | Focal length changes, body stationary |
| Type | `Push In / Pull Out` | Camera moves forward / backward |
| Type | `Pan Left / Pan Right` | Lens pivots horizontally in place |
| Type | `Truck Left / Truck Right` | Camera translates horizontally |
| Type | `Tilt Up / Tilt Down` | Lens pivots vertically in place |
| Type | `Pedestal Up / Pedestal Down` | Whole camera rises / lowers |
| Type | `Arc Shot` | Camera arcs around the subject |
| Type | `Tracking Shot` | Camera follows a moving subject |
| Type | `Static Shot` | Position and lens both still |
| Type | `Shake Slightly / Shake Strongly` | Camera shake |
| Type | `POV` | Subject's point of view |
| Type | `Roll Clockwise / Roll Counterclockwise` | Roll around the lens axis |
| Amplitude | `with small amplitude` / `with large amplitude` | Range of compositional change |
| Speed | `at slow speed` / `at fast speed` | Pacing of that change |

```text
The camera pushes in with small amplitude at slow speed toward the folded letter in her hands.
The camera pans right with large amplitude at fast speed, revealing the open doorway.
The camera holds a static shot as the runner exits the frame.
```

## Speakers, dialogue, singing

Anyone who speaks, sings, or produces an off-screen human voice gets a stable ID: `(S1)`, `(S2)`, assigned once in the order of actual vocal events and reused at every later event. Simultaneous speech from already-numbered speakers uses a compound ID `(S1,S2)`. IDs persist across shots. Characters who never vocalise get no ID.

At a speaker's first appearance, establish identity from visual and audio context: character type, age, gender, on- or off-screen, pitch, timbre, rate, accent. Keep the identifying phrase, ID, action and delivery **outside** `<d>`; inside `<d>` put only the language tag and the exact spoken words. Preserve the user's words and punctuation verbatim, no translation, no rewriting.

```text
The young woman with a quiet, breathy voice (S1) says: <d>[English] I get off at the next station.</d>
The two children (S1,S2) shout together, <d>[English] Wait for us!</d>
```

Voiceover uses the exact phrase `says in an off-screen voiceover`, and every voiceover `<d>` block is immediately followed by a statement that the on-screen character's lips stay closed:

```text
The man (S1) says in an off-screen voiceover: <d>[English] I still remember that road.</d> while his lips remain completely closed.
```

Dialogue or lyrics crossing a cut: put `<scenetrans>` at the connecting point in both parts and say the audio continues - `continues seamlessly across the cut`, `continues uninterrupted into the next shot`, `carries over from the previous shot`, `remains audible across the transition`. Use `<cutoff>` when speech is truncated by the end of the video.

## On-screen text

Any banner, sign, label, subtitle or neon text actually visible goes in English double quotes, original text and punctuation preserved, untranslated. H3 renders spelled-out text and brand elements cleanly, so on-screen text is worth specifying rather than avoiding.

```text
A red neon sign reading "营业中" glows above the doorway.
```

Typography rules that survive the renderer:

- One line at a time. No wrapping, no stacked title plus subtitle, no two text blocks in frame at once.
- 3-5 words, under about 32 characters including spaces. Isolated one- or two-word labels read as feature tags, not design.
- At most two colours in a shot.
- Treat text as a composition element in the central visual zone, not a lower-third subtitle bar. It can sit against an edge, a surface or a highlight, and must never cover eyes, or the mouth during lip-sync.
- Spell every line out verbatim in the prompt with its time window, entry order and colours. `leave space for copy` or `text beat sync` produces nothing.
- Reveal a two-part line inside the same line: first half fades or slides in, second half follows, first half shifts about 10-15% of its width to make room.
- One main typography event per shot. If text comes back garbled, cut the number of text moments rather than shrinking them, and keep one stable line in the final shot.
- When a character is singing or speaking on screen, visible text must match the performed words exactly.

## overall_soundscape

1-4 English sentences, one paragraph: ambience, physical action sounds, non-verbal human sounds (wind, rain, traffic, footsteps, fabric, impacts, breathing, laughter, panting). Dialogue, singing and diegetic music live in the description field and are not repeated here. `N/A` only when the user asks for total silence.

```text
overall_soundscape: Steady rain taps against the café windows while low room ambience continues underneath. The entrance bell rings once, followed by wet footsteps and the soft scrape of a chair.
```

## non_diegetic_music

1-3 English sentences describing audience-only score: instrumentation, tempo, rhythm, dynamic change. Keep to what is audible; mood labels and explanations of emotional function are wasted tokens. Music a character can hear (singing, an instrument, radio, TV, phone) is diegetic and belongs in the description field. `N/A` when there is no score.

```text
non_diegetic_music: Sparse piano notes at a slow tempo, joined by sustained low strings that gradually increase in volume before fading out.
```

## Keyframe handling per mode

**I2VA** - `<Picture 1>` is the literal frame at 0.00s and belongs to `[Shot 1]`. Establish the image's style, subjects, composition and scene anchors first, then move forward. Hold identity, clothing, colours, key objects and spatial relationships constant.
Structure: first-frame anchor -> action onset -> continuous development -> result or reaction.

**FL2VA** - Picture 1 opens, Picture 2 closes. Describe the path, not two stills: how the subject moves, how poses change, how objects are handled, how composition evolves, how scene and lighting transition. Prefer a single shot unless the user asks for cuts, so the model can interpolate continuously. The last frame must be reached by the final `[Shot N]` at the end of the video.
Structure: first-frame state -> observable intermediate changes -> progressively narrowing differences -> last-frame state.

**L2VA** - `<Picture 1>` is the final frame and belongs to the last `[Shot N]`, not Shot 1. Infer a plausible earlier state from user intent plus the image, then converge characters, objects, camera and scene onto it.
Structure: plausible preceding state -> explicit action and transition path -> gradual convergence in the final shot -> last-frame landing.

## Reference mode (R2V)

Six sections in this order:

| Section | Purpose |
|-|-|
| `subject_definitions` | Defines referenced content and its labels |
| `summary` | Task type, target video, main reference relationships |
| `retention_analysis` | How each reference is preserved, transferred or reused |
| `detailed_description` | Visuals, actions, shots, sound, dialogue in playback order |
| `overall_soundscape` | Ambience and physical sounds |
| `non_diegetic_music` | Audience-only score |

All six are written in English; original language survives only inside `<d>` and in visible on-screen text.

### Labels

| Label | Meaning |
|-|-|
| `<Subject N>` | Visible content abstracted from references, reusable or modifiable in the target |
| `<Picture N>` | A reference image used as a concrete frame anchor or shot-planning anchor |
| `<Video N>` | A reference video giving an edit source, continuation point, or whole-video temporal structure |
| `<Audio N>` | An audio signal copied or referenced |

A label keeps one meaning across all six sections. In ComfyUI the numbering follows the exact order inputs were connected to the node.

`<Subject N>` covers people, animals, objects, scenes, environments, clothing, props, interfaces, effects, styles, actions, expressions and poses - the content unit used in the target, not the source file. One subject can draw on several assets, and one asset can supply several subjects.

```text
<Subject 1> is the young woman in <Picture 1>, with long dark hair, a blue cardigan, and a thin silver necklace.
<Subject 1> is the woman whose appearance comes from <Picture 1> and whose walking motion comes from <Video 1>.
```

Give `<Picture N>` its own line only when the image itself is a frame anchor (first frame, keyframe, last frame, edited keyframe, composition anchor) or a storyboard reference. An image that only defines a character, scene, costume or style is cited inside the relevant `<Subject N>` line instead.

```text
<Picture 2> is the first frame of [Shot 1], showing a woman seated beside a café window.
<Picture 3> is a storyboard reference for [Shot 1] and [Shot 2], defining their viewpoint, subject placement, and shot order.
```

A standalone `<Video N>` entry is for whole-video relationships: editing the source, continuing from its end, or referencing its camera movement, cuts, rhythm or temporal structure. A person or effect lifted out of a reference video is still a `<Subject N>`. A reference video does not produce an `<Audio N>` merely because the file has sound.

A `<Picture N>` or `<Video N>` that only identifies where another referenced item came from is cited inside that item's definition, gets no line of its own, and so gets no `retention_analysis` line either - as with `<Picture 1>` and `<Video 1>` in the worked example below.

`<Audio N>` covers a standalone clip or an enabled synchronised track: copying a signal, referencing a music style, a speaker's timbre and delivery, dialogue/lyrics/SFX from the original, or beat and continuity. When an audio maps to a target speaker, reuse that speaker's global ID rather than assigning a new one:

```text
<Audio 1> is the voice-timbre reference for <Subject 1> (S1).
```

`<Video N>` and `<Audio N>` number independently, so the same source file can be `<Video 1>` and `<Audio 2>`; name the shared source only when provenance would otherwise be ambiguous.

### summary

One short English paragraph, opening with a square-bracketed task-type prefix, using only labels already defined.

| Task type | When |
|-|-|
| `keyframe completion` | An image is a concrete frame anchor of the target |
| `reference generation` | An asset guides character, scene, style, action, camera or storyboard without being a concrete frame or an edited/continued source |
| `video editing` | An existing source video is directly modified. Editing an image, or generating between still keyframes, does not count |
| `video continuation` | New content continues, extends, resumes or transitions from a source video |
| `audio reuse` | The same audio signal is reused in whole or part |
| `audio reference` | Only style, timbre, dialogue content, texture, beat or continuity is referenced |

Combine multiple types with ` + `, no repeats: `[video continuation + keyframe completion]`, `[video editing + audio reuse]`. Presence of a video or audio input does not by itself create a type - a video supplying only camera movement or rhythm is `reference generation`. When editing a source video whose original audio stays audible, add `audio reuse`. When continuing a source video without copying its audio signal, add `audio reference` if the new audio only carries the original track's audible characteristics forward. For video-editing tasks, the sentence immediately after the task-type prefix is:

```text
The target video is an edited version of <Video 1>.
```

### retention_analysis

One line per separately defined label, meaning unchanged from `subject_definitions`. Labels cited only as provenance inside another definition get no line. Never write `(Sx)` here.

Visual markers: `fully_preserved`, `partially_preserved`, `attribute_transfer` (characteristics moved to a different identifiable subject), `weak_reference` (broad similarity of style, category, composition or atmosphere only).

Audio markers: `fully_copy` (whole source audio becomes the whole final track), `partially_copy` (part of the timeline or selected layers, or copied then altered), `reference` (timbre, rhythm, style, dialogue content or texture only), `weak_reference`.

```text
<Subject 1> (appears in [Shot 1], [Shot 3]): fully_preserved - ...
<Picture 2> ([Shot 1] first frame): fully_preserved - ...
<Video 1> (cut and pacing structure): weak_reference - ...
<Audio 1>: fully_copy - <Audio 1> is reused 1:1 as the target video's complete final audio track.
<Audio 2>: reference - the target speaker follows <Audio 2>'s voice timbre and measured delivery without copying the original signal.
```

Pick a marker within the role already defined for that label. New actions, backgrounds or plot events added to the target are not losses of fidelity.

### detailed_description

Same shot, camera, speaker, dialogue and sound formats as the base modes, with four differences:

| Dimension | Base modes | Reference mode |
|-|-|-|
| Main field | `integrated_multimodal_description` | `detailed_description` |
| Style opening | Inside `[Shot 1]` | One or two sentences **before** `[Shot 1]` |
| Reference info | No labels | Insert `<Subject N>` / `<Picture N>` / `<Video N>` / `<Audio N>` at first appearance and wherever their role applies |
| Audio | Describes the target's own sound | Also cites `<Audio N>` in the relevant shot and states copy vs reference |

```text
The target video is in a cinematic, literary music-video style with soft lighting and a slightly desaturated color palette.
[Shot 1] The scene opens in a crowded urban street...
[Shot 2] At 00:09.000, the shot cuts to an extreme close-up...
```

Target 350-500 English words for generation tasks; dialogue-dense content prioritises fitting the full spoken timeline over hitting a count, and editing tasks scale with the source video. A single-shot video does not license a short description - spread detail across shots by information load. For each shot, pin down composition, subject appearance and position, environment and lighting, actions and state changes, camera movement, current sound, and the exact points where referenced content takes effect. A plot summary or a bare list of reference relationships is the failure mode to avoid.

Frame anchors read naturally: `the shot begins from <Picture 1>`, `the shot's keyframe corresponds to <Picture 2>`, `the shot ends on <Picture 3>`.

### Speakers in reference mode

When a referenced subject speaks, carry both labels: `<Subject 2> (S1)`. Off-screen speech from the same subject keeps the form and is marked `off-screen`. A speaker with no defined subject gets a stable voice description plus `(Sx)`.

```text
<Subject 2> (S1) turns toward the woman and says, <d>[English] Last summer, I went to my grandfather's house. He talked about you.</d>
```

Verbal content that exists only inside a directly reused BGM or full soundtrack, with no person, character, narrator or other independent vocal source physically producing it, uses `<Audio N>` as the source and gets no `(Sx)`. Where a concrete vocal source does produce the voice - including an off-screen narrator - assign and reuse `(Sx)` as normal:

```text
When <Audio 1> reaches the phrase <d>[English] I'm lonely lonely lonely lonely lonely I'm lonely</d>, <Subject 1> performs the corresponding hand gesture without becoming a separate speaker source.
```

`(Sx)` is assigned once, in the order of actual vocal events in the target video, and reused everywhere. When dialogue, narration or lyrics are directly reused or reperformed, keep the exact source words and original language inside `<d>`, write `[unclear]` for unintelligible spans rather than guessing, and standardise punctuation to `,` `.` `?` `!` (stripping tildes, emoji, bullets and decorative repeats). When only timbre, rhythm, emotion or delivery is referenced, do not carry the original words across.

For reference audio, state the copy/reference relationship in the section matching the audible layer - ambience and SFX in `overall_soundscape`, audience-only score in `non_diegetic_music`:

```text
overall_soundscape: The copied ambience layer from <Audio 1> continues throughout the target video.
non_diegetic_music: <Audio 2> is directly reused as the complete audience-only score.
```

### Choosing reference images

- Give each reference one narrow job and state it: identity, scene and lighting, typography style, motion, camera, voice. A card carrying a person, a room and a text treatment at once bleeds all three into the output.
- Feed standalone full-frame images. Grids, four-panel sheets, split screens, contact sheets and storyboard boards get reproduced as layout inside the video, and the closing shot is where that surfaces worst.
- References anchor identity, not shot order. Three references are not three segments; the shot list decides order.
- Where clean anchor images have been generated from a source photo, pass the anchors alone. Passing both puts two versions of the same subject in play.

## Beyond 15 seconds

H3 generates about 15s per pass, so anything longer is stitched from several generations.

- Lock the full audio track first and treat it as the master. Per-segment native audio will not line up across a seam; align every clip to timestamps on that one track at assembly.
- Split into 2-5s shots mapped to named beats or lyric timestamps, not to equal slices.
- Continue a scene by feeding the previous segment's tail frame as the next segment's first frame (I2VA), or bracket a segment with FL2VA. For a hard cut, hold the same reference cards, wardrobe and lighting, and carry either camera direction or a match-cut element across.
- Repeat the same style header verbatim at the top of every segment prompt - grain, colour direction, light direction - then grade and grain the assembly to hide batch differences.
- Cut on the beat grid and on lyric pauses or breaths. Never cut mid-vowel unless the next shot is an extreme close-up holding the mouth shape.
- Carry typography momentum across the seam: text exits on an accent, the next text enters on the following one.

## ComfyUI specifics

- **Resolution**: native canvas is a 768px short edge, capped at 768x1344, rounded to a multiple of 32. The Resolution Selector node computes width/height from aspect ratio, megapixels and multiple; keep multiple at `32`, and use about `1.0` megapixels at 16:9 (~1344x768) for full quality.
- **Duration**: snaps to the 17-frames-per-block grid, `17k + 5` frames at 24fps, floor 4s and ceiling about 15s. See [Alignment instruction line](#alignment-instruction-line) for how the snapped frame count drives `S.SS` and every cut time.
- **Reference limits (R2V)**: up to 9 images; up to 3 videos (each 2-15s, 15s total, each may carry its own soundtrack); up to 3 standalone audio clips (each 2-15s, 15s total). No more than 12 reference files across all types, so the per-type maximums cannot all be used at once.
- **Tag order (R2V)**: `<Picture 1>`, `<Video 1>`, `<Audio 1>` follow connection order on the node - a prompt referring to `<Picture 2>` when only one image is connected has nothing to bind to.
- **ref_image_size**: `match` downscales references to generation resolution for speed; `max` keeps up to a 2048px short edge for stronger identity fidelity, slower.
- **Assign each reference a job.** Stating which reference drives identity, which drives style, which drives motion, camera or voice works substantially better than listing them.

## Worked examples

I2VA:

```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Live-action, cinematic, the young woman shown in <Picture 1> remains beside the rain-covered train window, preserving her appearance, clothing, seat position, and the carriage layout. The camera trucks right with small amplitude at slow speed as she lifts her gaze from the folded letter toward the passing city lights. Her reflection moves across the glass while the quiet, breathy young woman (S1) says: <d>[English] I get off at the next station.</d> She folds the letter along its existing crease.

overall_soundscape: The train wheels produce a steady metallic rhythm beneath a low ventilation hum. Rain ticks against the window while paper rustles softly in her hands.

non_diegetic_music: Sustained cello notes at a slow tempo with widely spaced piano tones, gradually decreasing in volume.
```

FL2VA, eight-second single shot - the body supplies the motion path rather than two static image descriptions:

```text
How the reference pictures align with the target video - Picture 1 (from Shot 1) aligns with the 0.00-second mark of the target video; Picture 2 (from Shot 1) aligns with the 8.00-second mark of the target video.

integrated_multimodal_description: [Shot 1] Live-action, cinematic, a rain-soaked cyclist begins in the position and framing established by Picture 1, holding a closed black umbrella beside a silver bicycle. The camera pulls out with small amplitude at slow speed as she releases the bicycle handle, raises the umbrella above her shoulder, and presses the runner upward until the canopy opens. Water rolls from the expanding fabric while she steps beneath it, rotates the handle into the final angle, and settles into the pose, spacing, and composition established by Picture 2 at the end of the shot.

overall_soundscape: Rain falls steadily on the pavement, followed by the metallic click of the umbrella runner and the soft snap of the canopy opening. Water drips from the bicycle frame as distant traffic passes.

non_diegetic_music: N/A
```

R2V, abridged - a real `detailed_description` runs 350-500 words across more shots than this:

```text
subject_definitions:
<Subject 1> is the coffee-shop environment in <Picture 1>, featuring an exposed brick wall, an orange tufted sofa with patterned pillows, a neon sign, and a wooden coffee table.
<Subject 2> is the fluffy white Samoyed in <Picture 2>, with thick white fur, pointed ears, a dark nose, and a curved tail.
<Subject 3> is the young blonde woman in <Video 1>, with long blonde hair and a light-pink button-down shirt with rolled-up sleeves.
<Audio 1> is the voice-timbre reference for <Subject 3> (S1), containing a spoken English vocal layer.

summary:
[reference generation + audio reference] The target video shows <Subject 3> eating a cookie in <Subject 1>, until <Subject 2> lunges toward it. The exchange uses <Audio 1> as the voice-timbre reference for <Subject 3>.

retention_analysis:
<Subject 1> (appears in [Shot 1], [Shot 2]): fully_preserved - the exposed brick wall, orange tufted sofa, patterned pillows, neon sign, and wooden coffee table are retained.
<Subject 2> (appears in [Shot 1]): fully_preserved - the Samoyed's thick white fur, pointed ears, dark nose, and curved tail are retained.
<Subject 3> (appears in [Shot 1], [Shot 2]): fully_preserved - the blonde woman's identity, long hair, and light-pink shirt are retained.
<Audio 1>: reference - its vocal timbre guides the dialogue delivery of <Subject 3> without copying the original signal.

detailed_description:
The target video uses a realistic multi-camera sitcom style with warm indoor lighting.
[Shot 1] A medium shot establishes <Subject 1>, the coffee shop with its exposed brick wall, orange tufted sofa, patterned pillows, neon sign, and wooden coffee table. <Subject 3> (S1), the young woman with long blonde hair and a light-pink button-down shirt, sits on the sofa holding a chocolate-chip cookie. From the left, <Subject 2>, the thick-furred white Samoyed with pointed ears and a curved tail, lunges toward the cookie with its front paws on the coffee table. <Subject 3> (S1) jerks her hand back and, using the clear youthful voice timbre referenced from <Audio 1>, exclaims with light annoyance, <d>[English] Hey! Watch your dog!</d> She closes her lips and guards the cookie.
[Shot 2] At 00:03.000, the camera cuts to a close-up of <Subject 3> (S1), the blonde woman in the light-pink shirt from Shot 1. Her annoyance softens as she looks toward the Samoyed and replies in the same voice with an amused cadence, <d>[English] Well, he has good taste at least.</d> A classic canned audience laugh begins immediately after the line and continues through the final frame.

overall_soundscape:
Soft indoor coffee-shop room tone continues throughout the scene.

non_diegetic_music:
N/A
```

## Review checklist

Run over a draft prompt in this order:

1. Mode matches the connected inputs, and the instruction line (if any) is the verbatim string with correct `N` and `S.SS`.
2. All required fields present, in order, blank-line separated, spelled exactly.
3. `[Shot 1]` has no timestamp; later shots have increasing `MM:SS.mmm` times, and `S.SS` plus every cut time derive from the snapped frame count rather than the nominal duration.
4. Style and initial composition stated in the right place for the mode.
5. Camera motion written as in-sentence action with a type, and amplitude/speed only where meaningful.
6. Speaker IDs in vocal-event order, stable across shots, identity established at first appearance; `<d>` holds only the language tag plus verbatim words.
7. Voiceovers use the exact phrase and the lips-closed clause; cross-cut lines carry `<scenetrans>` plus a continuity phrase; truncated speech carries `<cutoff>`.
8. On-screen text quoted verbatim in double quotes, one line in frame at a time, positioned as composition rather than subtitle, with its time window and colours stated.
9. Soundscape and score fields obey the diegetic/non-diegetic split, no duplication, `N/A` used correctly.
10. Peaks and rests match the duration, one main action per beat, transitions driven by in-frame elements.
11. Stitched pieces only: one master audio, cuts on the beat grid and clear of vowels, style header repeated verbatim per segment, tail frame carried into the next segment's first frame.
12. R2V only: six sections; every label defined before use; task-type prefix matches the actual roles; one `retention_analysis` line per separately defined label, with a valid marker and no `(Sx)`; description reaches the detail level rather than summarising the plot.
