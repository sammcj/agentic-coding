---
name: storytelling-with-data
description: "Apply Storytelling with Data (SWD) principles by Cole Nussbaumer Knaflic to create, review, and improve data visualisations and data-driven communications. Use when the user asks to create, review, or improve charts, graphs, dashboards, infographics, data-driven sites or playgrounds, slide decks, or written reports that communicate data."
---

# Storytelling with Data (SWD) Skill

Apply the 6-lesson framework from Cole Nussbaumer Knaflic's _Storytelling with Data_ methodology when creating, reviewing, or improving any data communication: charts, dashboards, infographics, slide decks, static sites, or written reports.

## When to Use This Skill

- **Creating**: Building new visualisations, dashboards, infographics, presentations, or data-driven pages
- **Reviewing**: Critiquing existing data communications for clarity and impact
- **Improving**: Performing "makeovers" on charts, dashboards, or layouts to make them more effective
- **Advising**: Helping the user choose the right chart type, structure a narrative, or declutter

> **Format-agnostic by design**: This skill covers _what_ to communicate and _how_ to design it. Pair it with format-specific skills or tools that handle the output mechanics (e.g. a pptx skill for slide decks, a web framework for interactive dashboards, an SVG/image tool for infographics).

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

Structure your communication as a **narrative arc**:

- **Beginning (Setup/Plot)**: Establish the situation - what does the audience need to know as background? Build common ground.
- **Middle (Conflict/Tension)**: This is the complication - the problem, the change, the unexpected finding. This is where data creates tension between "what we expected" and "what is actually happening."
- **End (Resolution/Call to Action)**: The recommendation. What should the audience DO with this information?

**Storytelling techniques:**

- **Repetition**: Repeat your key message at least 3 times in different ways
- **Sequential logic**: Read just the section or chart titles in order - they should tell a complete story on their own. In a slide deck this is "horizontal logic" (reading slide titles across). In a dashboard or infographic, it's the reading order of panels or sections top-to-bottom.
- **Self-contained units**: Each individual section, panel, or slide should make sense on its own with its title + content ("vertical logic" in presentation terms).
- **Match the medium**: If presenting live, visuals should be sparse (you are the narrator). If the output will be consumed without a presenter (dashboards, emailed reports, embedded infographics), it needs more text, annotation, and self-explanatory context.
- **Build/reveal progressively**: Don't show everything at once. In presentations, build up the visual piece by piece. In interactive formats (dashboards, web pages), use progressive disclosure - overview first, detail on demand.

---

## Applying SWD: Task-Specific Workflows

### Creating New Data Communications

This workflow applies regardless of output format (slide deck, dashboard, infographic, static site, report).

1. **Context interview** - Ask the user: Who's the audience? What's the one thing they should take away? What format/medium will this be consumed in?
2. **Storyboard** - Draught section or panel titles as a narrative arc (beginning, tension, resolution). For presentations, these become slide titles. For dashboards, these become panel headings. For infographics, these become section headers.
3. **Chart selection** - For each data point, pick the simplest effective chart (see `references/chart-selection.md`)
4. **Build** - Apply Lessons 3-5 while creating each section or view
5. **Review** - Check sequential logic (titles in order tell the story) and that each unit is self-contained

### Format-Specific Considerations

| Format                       | Key adaptations                                                                                                                               |
| ---------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| **Slide deck**               | Sparse visuals (presenter narrates), one idea per slide, progressive build/reveal                                                             |
| **Dashboard**                | Self-explanatory (no presenter), overview panels first with drill-down detail, interactive filters to reduce clutter                          |
| **Infographic**              | Single linear flow top-to-bottom, strong visual hierarchy to guide the eye, must stand alone without explanation                              |
| **Static site / playground** | Progressive disclosure (summary up top, detail below or on click), responsive layout considerations, can use animation/interaction for reveal |
| **Written report**           | More annotation and explanation than visual formats, charts support the narrative text rather than replace it                                 |

### Reviewing / Critiquing Existing Work

Run through the **SWD Review Checklist** in `references/review-checklist.md`. For each chart, panel, section, or slide, evaluate against all 6 lessons and provide specific, actionable feedback.

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

| File                                | When to read                                               |
| ----------------------------------- | ---------------------------------------------------------- |
| `references/chart-selection.md`     | When choosing a chart type or advising on visual selection |
| `references/review-checklist.md`    | When reviewing or critiquing existing data communications  |
| `references/colour-and-emphasis.md` | When making colour choices or applying emphasis strategies |
