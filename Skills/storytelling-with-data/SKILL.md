---
name: storytelling-with-data
description: "Apply storytelling principles to create, review, and improve data visualisations and data-driven communications. Combines Cole Nussbaumer Knaflic's SWD framework (chart selection, decluttering, emphasis) with narrative frameworks from Brent Dykes (Data Storytelling Arc), Nancy Duarte (Sparkline), Donald Miller (StoryBrand SB7), Matthew Dicks (Five-Second Moment), and Heath Brothers (SUCCESs). Use when creating charts, dashboards, infographics, presentations, pitch decks, or reports that communicate data, or when structuring narrative arcs, hooks, aha moments, or persuasive stories. Trigger on: 'SWD', 'storytelling with data', 'data story', 'narrative arc', 'hook', 'aha moment', 'StoryBrand', 'Sparkline', 'declutter', 'chart makeover', 'pitch deck narrative'."
---

# Storytelling with Data (SWD) Skill

Apply the 6-lesson SWD framework from Cole Nussbaumer Knaflic for visual and design decisions, combined with narrative storytelling frameworks (Dykes, Duarte, Miller, Dicks, Cron, Heath) for structuring compelling stories that drive action.

## When to Use This Skill

- **Creating**: Building new visualisations, dashboards, infographics, presentations, pitch decks, or data-driven pages
- **Reviewing**: Critiquing existing data communications for clarity and impact
- **Improving**: Performing "makeovers" on charts, dashboards, or layouts to make them more effective
- **Advising**: Helping choose the right chart type, structure a narrative, declutter, craft a hook, or position a message
- **Storytelling**: Structuring any narrative: data stories, pitches, brand positioning, conference talks, stakeholder briefings

> **Format-agnostic by design**: This skill covers _what_ to communicate and _how_ to design it. Pair it with format-specific skills that handle output mechanics (e.g. pptx skill for slide decks, a web framework for dashboards).

---

## The SWD 6-Lesson Framework

Every data communication task should be evaluated against these 6 lessons, applied in order:

### Lesson 1: Understand the Context

Before touching any tool, answer three questions:

1. **WHO** is your audience? What do they care about? What's their relationship to you? What will motivate them?
2. **WHAT** do you need them to know or do? Define the single action or takeaway.
3. **HOW** will you communicate? Live presentation? Email? Dashboard? This changes everything about design.

**Key techniques:**

- **The 3-Minute Story**: Can you explain your entire message in 3 minutes? If not, you haven't distilled it enough.
- **The Big Idea**: One sentence that articulates your unique point of view, what's at stake, and what you want the audience to do. Format: [situation] + [complication] → [recommended action].
- **Storyboard first**: Sketch your flow on sticky notes or paper before opening any tool. Rearrange freely.
- **Exploratory ≠ Explanatory**: The audience sees only the _explanatory_ output - the curated insight, not the full analysis journey. Never dump exploratory analysis on your audience.

**When reviewing existing work, ask:**

- Is there a clear "so what?" on every chart, panel, or section?
- Could the audience state the key message after a 3-second glance?
- Is there a specific call to action?

### Lesson 2: Choose an Appropriate Visual Display

Match the visual to the message. You can handle the vast majority of business communications with just a few chart types.

**Read `references/chart-selection.md` for the detailed chart selection guide.**

Quick decision framework:

- **Comparison across categories** → Horizontal bar chart (default workhorse)
- **Trend over time** → Line chart (continuous) or vertical bar chart (discrete periods)
- **Part-to-whole** → Stacked bar or waterfall (NOT pie charts)
- **Two data points comparison** → Slopegraph
- **Single important number** → Simple text (the number itself, large, with context)
- **Detailed lookup** → Table or heatmap

**Charts to AVOID:**

- Pie and doughnut charts (hard to compare areas/angles accurately)
- 3D anything (adds clutter, distorts data, makes reading values harder)
- Dual y-axes (confuse the audience about scale relationships)
- Spaghetti graphs (too many overlapping lines - filter or use small multiples instead)

### Lesson 3: Eliminate Clutter

Clutter is any visual element that takes up space without adding understanding. Every element increases **cognitive load** - the mental effort to process information.

**Identify and remove:**

- Chart borders and unnecessary outlines
- Gridlines (reduce to light or remove entirely)
- Data markers on every point (only mark what matters)
- Redundant labels (if the axis says it, the data label doesn't need to)
- Bold/italic/colour on everything (when everything is emphasised, nothing is)
- Legends (can you label directly instead?)
- Rotated text (hard to read - restructure the chart instead)
- Decorative elements that don't encode data

**Apply Gestalt Principles to structure what remains:**

- **Proximity**: Group related items close together; separate unrelated ones
- **Similarity**: Use consistent colours/shapes for items in the same category
- **Enclosure**: Subtle backgrounds can group related content
- **Closure**: Remove unnecessary borders - the eye fills in gaps
- **Continuity**: Align elements so the eye flows naturally
- **Connection**: Lines connecting points imply sequence or relationship

**Decluttering process (step by step):**

1. Remove chart borders
2. Remove or lighten gridlines
3. Remove data markers (unless specific points need emphasis)
4. Clean up axis labels (round numbers, remove unnecessary precision)
5. Label data directly (eliminate legends where possible)
6. Use consistent, strategic colour

### Lesson 4: Focus Your Audience's Attention

Use **preattentive attributes** - visual properties the brain processes before conscious thought - to guide the eye to what matters:

- **Colour**: The most powerful tool. Use a single accent colour to highlight the key data; push everything else to grey. Never use colour decoratively.
- **Size**: Larger elements draw attention first. Make the key number or data point bigger.
- **Position**: Items at the top-left get seen first (in left-to-right reading cultures). Place the most important information there.
- **Bold/weight**: Use sparingly on text to create hierarchy. Bold the key phrase, not the whole paragraph.

**The Grey + One Colour rule**: Default everything to grey, then use ONE strategic accent colour to highlight the story. This is the single most impactful SWD technique.

**Memory matters:**

- **Iconic memory** (~0.5 seconds): Preattentive attributes are processed here - that's why colour and size pop instantly
- **Short-term memory** (~4 items): Don't overload a single view with too many competing elements
- **Long-term memory**: Connect to what the audience already knows - use familiar chart types and conventions

### Lesson 5: Think Like a Designer

Design serves the message. Apply these principles:

- **Form follows function**: Every element earns its place by serving comprehension
- **Affordances**: Make interactive elements look clickable; make important text look important
- **Accessibility**: Would this work in greyscale? For colour-blind audiences? Without a narrator explaining it?
- **Aesthetics build trust**: Clean, well-aligned visuals signal competence and credibility

**Practical design rules:**

- Use consistent alignment (create an invisible grid)
- Left-align text (easier to read than centred for body content)
- Use white space generously - it's not wasted space, it's breathing room
- Limit fonts to 1-2 families; use size and weight for hierarchy
- Action titles > descriptive titles: "Revenue grew 23% in Q3" beats "Q3 Revenue"
- Every chart, section, or panel should have a clear, declarative title that states the "so what"
- Add context with text annotations directly on the visualisation

### Lesson 6: Tell a Story

Without narrative, data visualisations are just pretty pictures. Multiple frameworks exist for structuring compelling stories. Choose based on your scenario.

**Read `references/narrative-frameworks.md` for detailed framework guidance** and **`references/hooks-and-moments.md` for hook and aha moment techniques**.

#### Framework Selection

| Scenario | Primary Framework | Supporting |
|---|---|---|
| Data insight presentation | Dykes Data Storytelling Arc | Heath SUCCESs |
| Persuasive keynote or pitch | Duarte Sparkline | Miller SB7, Dicks |
| Product/brand positioning | Miller StoryBrand SB7 | Duarte, Heath |
| Conference talk / personal story | Dicks Five-Second Moment | Duarte, Cron |
| Message stickiness review | Heath SUCCESs checklist | |

#### The Data Storytelling Arc (Brent Dykes) - Default for Data Presentations

1. **Setting & Hook**: Provide "just enough" context, then present a notable observation that reveals a problem or opportunity. The Hook creates an open question.
2. **Rising Points**: Focused supporting details that build understanding and tension. Not a data dump.
3. **Aha Moment**: The central insight: an unexpected shift in understanding + explicit "so what." This is the climax. Do NOT put it upfront.
4. **Solution & Next Steps**: Provide options and make a recommendation.

**Key principle**: Data storytelling = Data + Narrative + Visuals (all three required). An insight must surprise, shift understanding, AND inspire action. Reporting is not storytelling.

#### The Sparkline (Nancy Duarte) - For Persuasive Presentations

Alternate between **"what is"** (current state) and **"what could be"** (desired future) throughout. Contrast creates energy. End with **"new bliss"**: the world with your idea adopted. The audience is the hero; the presenter is the mentor.

#### The StoryBrand SB7 (Donald Miller) - For Product/Brand Positioning

7 elements: Character (customer = hero) > Problem (external, internal, philosophical) > Guide (your brand: empathy + authority) > Plan (clear steps) > Call to Action > Failure (stakes if they don't act) > Success (transformation). Key insight: *Companies sell solutions to external problems, but customers buy solutions to internal problems.*

#### The Five-Second Moment (Matthew Dicks) - For Personal Stories

Every great story is about a single moment of transformation taking no more than five seconds. Start at the end (know your moment), begin as close to it as possible. Use the **Dinner Test**: if you wouldn't tell it this way to a friend, don't tell it that way at all.

#### Brain Science (Lisa Cron) + Sticky Messages (Heath Brothers)

Hooks work because they create **knowledge gaps** that trigger dopamine. Use the **SUCCESs** checklist: Simple, Unexpected, Concrete, Credible, Emotional, Stories. Combat the **Curse of Knowledge**: once you know something, you can't imagine not knowing it.

#### Storytelling techniques (applicable across all frameworks):

- **Horizontal logic**: Read just the section/slide titles in sequence. They should tell a complete story on their own.
- **Vertical logic**: Each individual section, panel, or slide should make sense on its own with title + content.
- **Repetition**: Repeat your key message at least 3 times in different ways.
- **Progressive reveal**: Don't show everything at once. Build up piece by piece.
- **Match the medium**: Live presentations = sparse visuals (you are the narrator). Read-alone formats need more text and annotation.
- **Hooks within 60 seconds**: Use anomaly, stakes, contrast, question, vulnerability, or in-medias-res hooks (see `references/hooks-and-moments.md`).
- Use **"but" and "therefore"** to connect story elements: "and" kills momentum (Dicks).

---

## Applying SWD: Task-Specific Workflows

### Creating New Data Communications

This workflow applies regardless of output format (slide deck, dashboard, infographic, static site, report).

1. **Context interview** - Ask the user: Who's the audience? What's the one thing they should take away? How will this be delivered?
2. **Choose narrative framework** - Data insight: Dykes Arc. Persuasive pitch: Duarte Sparkline. Product positioning: Miller SB7. (See `references/narrative-frameworks.md`)
3. **Storyboard** - Draft section/panel titles as a narrative arc. For Dykes: Setting > Hook > Rising Points > Aha Moment > Solution. For Duarte: What Is > What Could Be (alternating) > New Bliss.
4. **Craft the Hook** - Must land within 60 seconds. Choose from: anomaly, stakes, contrast, question, vulnerability, or in-medias-res. (See `references/hooks-and-moments.md`)
5. **Chart selection** - For each data point, pick the simplest effective chart (see `references/chart-selection.md`)
6. **Build** - Apply Lessons 3-5 while creating each section or view
7. **Verify the Aha Moment** - Does it surprise? Shift understanding? Have an explicit "so what"? Is it at the climax, not the beginning?
8. **Review** - Check horizontal logic (titles alone tell the story), vertical logic (each unit stands alone), and run the SUCCESs checklist

### Format-Specific Considerations

| Format                       | Key adaptations                                                                                                                               |
| ---------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| **Slide deck**               | Sparse visuals (presenter narrates), one idea per slide, progressive build/reveal                                                             |
| **Dashboard**                | Self-explanatory (no presenter), overview panels first with drill-down detail, interactive filters to reduce clutter                          |
| **Infographic**              | Single linear flow top-to-bottom, strong visual hierarchy to guide the eye, must stand alone without explanation                              |
| **Static site / playground** | Progressive disclosure (summary up top, detail below or on click), responsive layout considerations, can use animation/interaction for reveal |
| **Written report**           | More annotation and explanation than visual formats, charts support the narrative text rather than replace it                                 |

### Creating a Persuasive Pitch or Keynote

1. **Define The Big Idea** (Duarte): One sentence = situation + complication leading to recommended action
2. **Map the audience as hero** (Miller SB7): What do they want? What problem do they face (external, internal, philosophical)? How are you the guide?
3. **Structure with Sparkline contrast**: Alternate "what is" vs "what could be" throughout
4. **Plant a S.T.A.R. Moment** (Duarte): Something They'll Always Remember: a dramatic, tangible demonstration of the idea
5. **Craft sound bites**: Small, repeatable phrases for headlines and sharing
6. **End with New Bliss**: Paint the picture of the world with the idea adopted + clear call to action
7. **Apply SWD Lessons 2-5** for any data slides within the pitch

### Structuring a Personal or Conference Story

1. **Find the five-second moment** (Dicks): What single moment of transformation is this story about?
2. **Start at the end**: Know where you're going, then build backward
3. **Begin in the opposite**: Open in the emotional/situational opposite of where the story ends
4. **Apply the Dinner Test**: Would you tell it this way to a friend over dinner?
5. **Load engagement devices**: Stakes (hopes/fears before moving forward), Surprise (build it, don't spoil it), Suspense (make them wonder what's next)
6. **Slow down at the moment**: Use the Hourglass (Dicks): add detail and a beat right before the climax

### Positioning a Product or Brand

1. **Complete the SB7 BrandScript** (Miller): Character > Problem > Guide > Plan > CTA > Failure > Success
2. **Define the villain**: Must be a root source (not a feeling), relatable, singular, and real
3. **Articulate three problem levels**: External (tangible), Internal (emotional), Philosophical (why it's wrong)
4. **Establish Guide credentials**: Empathy ("I understand") + Authority ("I've solved this before")
5. **Show the transformation**: Clear before/after: who does the customer become?
6. **Run SUCCESs check** (Heath): Is the message Simple, Unexpected, Concrete, Credible, Emotional, Story-driven?

### Reviewing / Critiquing Existing Work

Run through the **SWD Review Checklist** in `references/review-checklist.md`. For each chart, panel, section, or slide, evaluate against all 6 lessons and provide specific, actionable feedback. Additionally evaluate the narrative structure:

- Does the presentation have a clear Hook within the first 60 seconds?
- Is there a genuine Aha Moment (surprise + shift + "so what")?
- Is the insight at the climax, not the beginning?
- Does the narrative follow a coherent arc (not just a collection of charts)?
- Would it pass the Dinner Test: is it told the way a human would tell it?
- Does the closing provide clear, actionable next steps?

### Chart / Visualisation Makeover

1. Identify the core message (what should the audience think/do?)
2. Choose a better chart type if needed (Lesson 2)
3. Strip all clutter (Lesson 3)
4. Apply grey + accent colour strategy (Lesson 4)
5. Add a declarative action title (Lesson 5)
6. Add text annotations to guide interpretation (Lesson 5)
7. Show before/after to demonstrate the improvement

---

## Reference Files

| File | When to read |
|------|-------------|
| `references/narrative-frameworks.md` | When structuring any narrative: data stories, pitches, keynotes, brand positioning. Contains Dykes (Data Storytelling Arc), Duarte (Sparkline), Miller (SB7), Dicks (Five-Second Moment), Cron (Brain Science), Heath (SUCCESs), plus framework selection guide. |
| `references/hooks-and-moments.md` | When crafting a hook or aha moment. Contains 6 hook types, the Insight Test, placement principles, and engagement devices. |
| `references/chart-selection.md` | When choosing a chart type or advising on visual selection |
| `references/review-checklist.md` | When reviewing or critiquing existing data communications |
| `references/colour-and-emphasis.md` | When making colour choices or applying emphasis strategies |
