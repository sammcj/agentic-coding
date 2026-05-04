# Format-Specific Narrative Notes

The narrative principles in `SKILL.md` are format-agnostic. This reference captures the narrative-specific differences between common business formats. It does not cover visual design, charting, or layout - those belong to format-specific skills (slide tooling, web frameworks, the data-viz skill).

For each format below: the dominant rhythm, the load-bearing rules, the common failure modes.

---

## Slide deck

**Dominant rhythm**: one idea per slide. The slide is the smallest narrative unit. The deck is read at the speed of the slowest reader, which is roughly the rate the speaker advances.

**Two modes**:
- **Live presentation** - the speaker narrates. Slides should be sparse: a phrase, an image, a number. Speaker carries the story; slides anchor it.
- **Read-alone deck** - distributed without a speaker (board pre-reads, follow-ups). Slides need to stand alone with more text, annotation, and a clear titles-only narrative.

**Load-bearing rules**:
- **Action titles, not descriptive titles.** "Revenue grew 23% in Q3" beats "Q3 Revenue". The title carries the story; the body supports it.
- **Horizontal logic.** Read just the slide titles in order. They should tell a coherent story by themselves. If they don't, the narrative is broken regardless of how good individual slides are.
- **Vertical logic.** Each slide makes sense on its own with title + content. No slide should require the previous one to be intelligible.
- **Progressive build.** Don't show everything at once. Reveal as the narrative requires.
- **One idea per slide.** If a slide has two ideas, it's two slides.

**Common failure modes**:
- Title is a topic, not a claim. ("Customer Feedback" instead of "Three of our top accounts asked for the same feature".)
- Bullet salad. Five sub-bullets that fight each other for attention.
- Densest slide hides the turn. The most important slide should be the cleanest.
- Slides written as speaker notes. The audience reads while the speaker talks; both lose.

**Narrative arc choice**: Sparkline (Duarte) for persuasive decks. Three-Act for general decks. SCQA opening slide for board / exec audiences who want the answer up front.

---

## Blog post / article

**Dominant rhythm**: linear top-to-bottom read. The reader chooses to keep going at every paragraph. The cost of losing them is high; once they leave, they don't come back.

**Load-bearing rules**:
- **Opening sentence does the most work.** It either earns the next sentence or loses the reader. Most blog posts squander the opening on summary.
- **The hook is non-negotiable.** First paragraph must open a loop the reader needs closed. Six hook types in `references/hooks-and-moments.md`.
- **Sub-headers are mini-titles.** A reader who scans should get the gist from headers alone. Action sub-heads, not topic sub-heads.
- **Paragraphs are beats.** Each paragraph earns the next. If a paragraph doesn't move the through-line forward, cut it.
- **End on the resolution, not a summary.** Avoid "In conclusion..." / "To summarise..." / "We've explored..." - slop tells. Land on the new state, the action, the call.

**Common failure modes**:
- Opening with throat-clearing ("In today's fast-paced world...").
- Listicle with no through-line - five disconnected points dressed as a story.
- Buried lede - the actual interesting thing is in paragraph six.
- "Hot take" framing - performance of insight without insight.
- Closing summary that adds nothing.

**Narrative arc choice**: Three-Act as default. ABT for very short pieces. Pixar for change/journey stories. Hero's Journey for founder/personal pieces.

---

## Pitch (investor / customer / internal)

**Dominant rhythm**: the audience is evaluating you and your idea simultaneously. Time is constrained - often 5-15 minutes. Every beat is auditioning.

**Load-bearing rules**:
- **The Big Idea opens.** One sentence: situation + complication + your unique recommendation. If you can't articulate this in one sentence, the pitch isn't ready.
- **Stakes early, not late.** The audience needs to know what's at risk before they care about the solution.
- **The customer is the hero, not you.** (StoryBrand instinct.) Your product is the guide. Resist the temptation to lead with your features.
- **Specifics over abstractions.** A real customer name, a real number, a real outcome beats any adjective.
- **Plant a STAR moment.** Something They'll Always Remember (Duarte). A specific, vivid, demonstrable beat that anchors the whole pitch.
- **End with the call.** What do you want from this audience, exactly? Investment? Pilot? Approval? Make it explicit.

**Common failure modes**:
- Product-first ordering. Features before problem.
- Generic problem statement. "Companies struggle with X" - which companies? what does struggling look like?
- No villain. Without a clear antagonist (status quo, competitor, broken process), the conflict is fuzzy.
- Closing slide that says "Questions?" instead of an explicit ask.

**Narrative arc choice**: Sparkline (Duarte) + StoryBrand SB7 for outward-facing pitches. Golden Circle for vision-heavy pitches. SCQA for short internal/exec pitches.

---

## Exec memo / status update / 1-pager

**Dominant rhythm**: scanned, not read. The reader's question is "what do I need to do or know about this?" - and they want the answer in the first 30 seconds.

**Load-bearing rules**:
- **Bottom line up front (BLUF).** Lead with the recommendation, decision, or finding. Then justify it.
- **SCQA at the top.** Situation → Complication → Question → Answer is the natural shape.
- **One screen rule.** A status update or memo that scrolls past one screen has lost the executive.
- **Numbered or bulleted scaffolding.** Exec readers parse structure faster than prose. Use it deliberately.
- **No throat-clearing.** No "I wanted to share..." / "As discussed..." / "Just following up..." openers. Get to the substance.
- **Ask is explicit and isolated.** If you want a decision, isolate the ask in a single sentence near the top: "Decision needed: approve $X for Y by Friday."

**Common failure modes**:
- Reverse-chronological structure (telling the story of how you got here before the headline).
- Hedged ask. "We might want to consider whether..." - make the recommendation, attach the uncertainty separately.
- Buried numbers. The most decision-relevant figure should be visible without scrolling.
- Memo that's actually a draft of a longer document. If it doesn't serve the scanning reader, it's the wrong format.

**Narrative arc choice**: SCQA always. ABT inside individual sections.

---

## Long report / strategy document / board paper

**Dominant rhythm**: scanned at multiple levels. Some readers will only read the executive summary. Some will scan headings and stop where their interest fires. Few will read linearly.

**Load-bearing rules**:
- **Pyramid Principle.** Lead with the answer; group supporting arguments below; each group has its own evidence underneath. Reader can stop at any level and have the gist.
- **Executive summary stands alone.** Often re-read separately. Must contain the through-line, the recommendation, and the rationale in one page.
- **Section openers are mini-SCQAs.** Each section starts with situation/complication/question/answer for that section's topic.
- **Headings are claims, not topics.** "Our cloud spend is growing faster than revenue" beats "Cloud Spend Analysis".
- **Appendix what would otherwise interrupt.** Detailed methodology, raw data, supporting evidence - appendix it. Don't let it slow the main narrative.

**Common failure modes**:
- Bottom-up writing. Building to a conclusion the time-poor reader will never reach.
- Buried recommendation in section 4 of 7.
- Methodology before findings. Readers don't care how you got there until they care that you got there.
- Throat-clearing introduction ("This document aims to...").

**Narrative arc choice**: Pyramid Principle as the structural backbone. SCQA at section level. Inside paragraphs, ABT.

---

## Conference talk / keynote

**Dominant rhythm**: live audience, time-bounded, often recorded. Memory is selective - audiences remember moments, not arguments.

**Load-bearing rules**:
- **Open with a moment, not an agenda.** No "Today I'll cover three things". Drop straight into the hook.
- **One single Big Idea.** A talk about three things is a talk about nothing. Pick one and serve it.
- **At least one S.T.A.R. moment.** A specific, tangible, dramatic beat that crystallises the idea (Duarte).
- **Personal beats earn trust.** A vulnerability hook or Five-Second Moment near the start changes the audience's relationship to the speaker.
- **Land the resolution.** The last sentence is what they'll quote. Write it first; everything else serves it.
- **Soundbites travel.** Build 1-2 short, repeatable phrases the audience can carry out the door.

**Common failure modes**:
- The "comprehensive overview" instinct. Tries to cover everything; the audience remembers nothing.
- Reading slides aloud.
- No personal stake. Generic talks read as generic.
- Anticlimactic ending. The ending is the part the audience remembers - don't waste it on "thanks for listening".

**Narrative arc choice**: Sparkline + Five-Second Moment. Golden Circle for vision-heavy keynotes.

---

## When the format isn't decided yet

If the user hasn't picked a format, the format choice itself is a narrative decision. Ask:

- Who is reading or watching, and how much of their attention do they have?
- Live or async?
- One reader or many?
- How long is the journey: a 30-second decision or a 30-minute talk?
- Does the audience need to act, decide, or simply understand?

These answers shape format. A persuasive case to a single decision-maker may be better as a 1-page memo than a 20-slide deck. A change story that needs to spread may be better as a blog post than a board paper. The format is downstream of the audience and the goal.
