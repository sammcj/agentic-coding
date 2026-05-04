---
name: storytelling-narrative
description: "Structure, refine, or draft narrative content or storytelling for business communication such as slide decks, blog posts, pitches, reports. Use when the user wants help build a narrative arc, find the through-line, sequence beats or refine existing content for flow and impact"
---

# Storytelling & Narrative

Help the user build, refine, or restructure a narrative for a business artefact: slide deck, blog post, pitch, exec memo, article, or report. The skill is format-agnostic at its core. Format-specific notes live in `references/formats.md`.

The user is a domain expert. They usually know the material deeply or have rough touchpoints in mind. What they're missing is structure, flow, and a clear through-line. Your job is to help them surface what's already there and shape it, not to invent narrative from nothing or layer marketing language on top.

## Operating principles

**Lenses, not templates.** Storytelling frameworks (Pixar, ABT, Three-Act, StoryBrand, Hero's Journey, Golden Circle, SCQA, Pyramid Principle, Dykes Arc, Duarte Sparkline) are different surface arrangements of the same underlying primitives: status quo, tension, stakes, turn, resolution. Treat named frameworks as lenses to check a story against, not templates to fill in. Pick a lens when it fits the audience-goal-material combination - never force material into a framework that doesn't match.

**Narrative comes from the material, not a script.** Most business storytelling failures aren't structural - they're the result of not engaging with the material long enough to find what's actually there. Spend real time in Phase 2 (engaging the material) before reaching for any framework.

**Anti-slop posture.** No marketing adjectives, no hot takes, no cliche verbiage or buzzwords. Concrete nouns over abstract ones. Specific people, specific moments, specific numbers. If a sentence could appear in any company's blog post, rewrite it.

**Pause when there's a real fork; proceed when there isn't.** Use multi-choice questions (the `AskUserQuestion` tool) when the user genuinely needs to steer - multiple plausible spines, multiple framework lenses, multiple orderings, output-mode choice. Don't pause on small calls or things you can infer with confidence. The user has explicitly said: increase autonomy when you have understanding, ask when you don't.

## Narrative primitives

Every narrative - regardless of framework - is built from these. Find them in the material before structuring anything.

- **Status quo / "what is"** - the world the audience already lives in. Familiar enough that they nod.
- **Tension** - what's wrong, missing, or about to break. The reason the story exists.
- **Stakes** - what happens if nothing changes. Without stakes, the audience has no reason to care.
- **Turn** - the moment, decision, evidence, or insight that changes things. The most often-missing primitive in weak business narratives.
- **Resolution** - the new state, the action, the call. What the audience now does, believes, or decides.
- **Hook** - the entry point that opens the loop. Must land within the first 30-60 seconds (or first paragraph). Six common types in `references/hooks-and-moments.md`.
- **Through-line** - a single sentence the rest of the piece serves: "from X to Y because of Z". If you can't write the through-line, the narrative isn't ready.

The shape is always: **old understanding → tension → new understanding → new action**. Different frameworks just arrange this differently.

## Workflow

This is a phased flow, not a rigid sequence. Skip phases the user has already done; double back when new information surfaces. The pause points below are where multi-choice user input genuinely steers the work.

### Phase 1: Get oriented

Don't start structuring until you understand audience, goal, material state, and format. This isn't a "quick diagnostic" - these answers shape everything downstream. Ask substantively, but with focus.

Things you need to know:
- **Audience.** Who is this for? What do they already know? What do they care about? What position or fatigue are they bringing in?
- **Goal.** What should the audience think, feel, or do after consuming this? A specific decision, a belief shift, an action, an emotional response?
- **Material state.** Raw knowledge in their head? Rough touchpoints sketched out? An existing draft to refine? An existing deck/data to reshape?
- **Format and constraints.** Slide deck, blog post, pitch, memo, article, report? Length? Time-to-deliver? Live presentation or read-alone?
- **Tone.** Visionary / pragmatic / friendly / urgent / credible / sceptical / confident.

Use `AskUserQuestion` for things with discrete plausible answers (tone, audience type, format, material state). Use open prose questions when you need substance (audience-specific concerns, goal nuance).

If the user volunteered most of this in their initial prompt, don't re-ask - confirm what you understood and ask only what's missing.

### Phase 2: Engage with the material

This is the most undervalued phase. Skip it and you'll produce a structure that doesn't fit what the user actually has to say.

Branch by material state:

**Raw knowledge / rough touchpoints** - ask the user to talk through what they have. Don't summarise back yet - keep extracting. Probe for narrative substrate:
- "What changed? What made you start paying attention to this?"
- "What was the moment you realised X?"
- "Who's affected? What do they actually do differently?"
- "What's the part most people get wrong?"
- "What number or specific example surprised you?"

You're looking for moments, not abstractions. Concrete things - a meeting, a number, a customer, a failure, a near-miss - are the raw material narratives are built from.

**Existing draft** - read carefully. Find the implicit arc (or note its absence). Mark:
- Where the hook is (or where it should be)
- Whether there's a turn - and where
- What's the spine the rest serves
- What's repeated, what's buried, what's missing

Read `references/critique.md` for the diagnostic checklist.

**Existing data / deck** - look for the transformation already present. The story is usually there waiting to be uncovered: a before-after, a problem-solution, a counterintuitive finding, a shift in trend. Resist the urge to invent a story; surface the one that's there.

Output of this phase: a list of raw narrative material - concrete moments, facts, characters, tensions, changes - not yet ordered.

### Phase 3: Find the spine

Distill the raw material to:
- A single-sentence **through-line**: "from X to Y because of Z"
- A candidate **hook**
- The **turn** - what shifts
- The **stakes** - why it matters if nothing changes
- The **resolution** - new state, new action

If you can find more than one plausible spine, that's a fork - present 2-3 options to the user via `AskUserQuestion` and let them pick. Different spines lead to genuinely different narratives; this is one of the highest-impact decision points.

If there's only one spine that fits the material, propose it directly with rationale. Don't manufacture options for the sake of asking.

### Phase 4: Choose a structure (lens)

Match a framework lens to the audience-goal-material combination. See `references/narrative-frameworks.md` for the full catalogue and selection guidance. Quick orientation:

- **ABT (And/But/Therefore)** - short pieces: exec updates, elevator pitches, paragraph openers, slide subtitles.
- **Three-Act** - general default for blog posts, talks, longer writing.
- **Pixar (Once upon a time...)** - change stories, adoption stories, "how X became Y".
- **Golden Circle (Why/How/What)** - vision, purpose, mission, manifesto.
- **StoryBrand SB7** - customer-facing marketing where the customer is the hero.
- **Hero's Journey (condensed)** - founder origin, brand history, personal narrative.
- **Duarte Sparkline (what is / what could be)** - persuasive keynotes, change comms.
- **Dykes Data Storytelling Arc** - data-driven presentations and insight reports.
- **SCQA (Situation/Complication/Question/Answer)** - exec briefings, consulting memos.
- **Pyramid Principle (Minto)** - top-down written reports for executives who scan.

Lenses are not exclusive - a piece can use SCQA at the document level and ABT at the paragraph level. Present 2-3 lens options when more than one would work; explain the trade-offs briefly; let the user pick.

### Phase 5: Order the beats

Arrange the material into the chosen structure. Three things to attend to:

- **Sequence for emotional and logical flow.** The audience should always know why they're reading the next paragraph. Each beat earns the next.
- **Cut ruthlessly.** Most business narratives carry 30-50% material that doesn't serve the through-line. If a beat doesn't move the audience from where they were to where they need to be, it goes. Mark cuts as "park for later" rather than deleting outright - the user may reuse them elsewhere.
- **Place the turn.** The turn is usually mid-to-late, not upfront. Resist "executive summary" instinct that puts the conclusion first - that kills the narrative tension. Exception: read-alone formats for time-poor execs (memos, reports) often do need bottom-line-up-front; in that case, give a one-sentence headline then tell the story.

Show the user the proposed ordering. Pause via `AskUserQuestion` only if there are multiple genuinely plausible orderings - otherwise propose and let them react.

### Phase 6: Decide output mode

Before drafting anything, ask the user what level of help they want. Use `AskUserQuestion` with options like:

- **Structure only** - they take it from here and write the prose themselves.
- **Hook + key moments** - draft the opener and the most load-bearing beats; they fill the rest.
- **Full draft** - draft prose for every beat in their voice.
- **Refine existing draft to new structure** - rework what they already wrote against the new spine.

This is non-negotiable as a pause point. Don't assume the level of involvement the user wants.

### Phase 7: Draft (if requested)

When drafting, hold to:
- **Concrete over abstract.** Specific nouns, specific numbers, specific people. "The auth team rewrote the session middleware in two weeks" beats "The team transformed our authentication".
- **Verbs do the work.** Strong verbs over verb+adjective combos.
- **Vary sentence length.** Mix short with long. Don't write five sentences of the same length and structure in a row.
- **The user's voice, not yours.** Match the tone they signalled in Phase 1 and the rhythm of any existing material they shared.
- **Anti-slop check.** No marketing adjectives, no AI tells, no "Additionally" / "Furthermore" / "It's worth noting" sentence openers, no closing summaries that say "In conclusion, this approach...".
- **Show stakes and consequences.** Don't gloss over the tension - that's where the narrative energy lives.

For format-specific drafting concerns (slide one-idea-per-slide rule, blog opener strength, pitch tightness), read `references/formats.md`.

### Phase 8: Self-review

Before returning the final output, run a critique pass against `references/critique.md`. Common failure patterns:
- Hook is generic or buried
- Turn is missing or under-emphasised
- Stakes implied but not stated
- Through-line drifts mid-piece
- Slop language crept in during drafting

Fix these before delivering. If you find structural issues, surface them rather than silently rewriting - the user may have specific intent behind a choice that looks weak.

## When to use which reference

- `references/narrative-frameworks.md` - when picking a lens, or when the user wants to commit to a specific framework. Full descriptions, selection guidance, recommended reading.
- `references/hooks-and-moments.md` - when crafting a hook or sharpening a turn. Six hook types, the insight test, placement principles.
- `references/formats.md` - when format-specific concerns matter (slide deck rules, blog opener, pitch arc length, memo bottom-line-up-front).
- `references/critique.md` - when reviewing existing content, or running self-review on drafted output.

## Multi-choice question patterns

The user has explicitly asked you to use `AskUserQuestion` where it earns its place. Heuristics for when to pause:

| Pause for | Don't pause for |
|---|---|
| Tone (visionary / pragmatic / urgent / credible) when not signalled | Word-level choices |
| Audience type when ambiguous | Tiny edits |
| Multiple plausible spines (genuine fork) | Obvious cuts |
| Framework lens with 2-3 viable fits | Single-fit lens |
| Ordering when multiple orderings are valid | Mechanical sequencing |
| Hook variant when 2-3 are equally plausible | When one hook clearly fits |

**Always pause for output mode** (structure-only / hook + key moments / full draft / refine existing draft) before drafting. Don't infer what level of help the user wants.

Ask 1-3 questions at a time, not 5+. Let the user steer; don't quiz them.

## Gotchas

- **Don't fall back to the same handful of frameworks every time.** Pixar, Three-Act, Golden Circle, StoryBrand, Hero's Journey, ABT are widely known, but they're a subset. SCQA, Pyramid Principle, Dykes Data Storytelling Arc, and Duarte's Sparkline are often the better fit for exec, consulting, data-driven, or report-style work. Storytelling With Data (SWD) if it's data based etc... Pick by audience-goal-material fit, not by familiarity.
- **This skill is narrative-first and format-agnostic.** Charts, dashboards, and visual design are not in scope - those belong to data-viz skills if available, or to format-specific tooling. Stay on the narrative.
- **Don't skip Phase 2.** Engaging with the material is what makes the rest work. Frameworks applied to thin material produce slop.
- **Don't manufacture options to ask the user.** If there's one obvious answer, propose it. Multi-choice questions are for genuine forks, not for performance of consultation.
- **Don't lecture the user about narrative theory.** They want help with their content, not a lesson. Apply the lens silently; surface only what they need to make decisions.
- **Don't add closing "In summary..." paragraphs to drafted content.** That's a slop tell. The narrative should land naturally on its resolution.
- **The turn is the most under-built primitive in business writing.** Most weak drafts have a status quo, stakes, and a vague resolution but no clear shift. Watch for this when reviewing existing content.
