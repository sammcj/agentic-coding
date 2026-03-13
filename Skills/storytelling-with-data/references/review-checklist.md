# SWD Review Checklist

Use this checklist when reviewing or critiquing any data communication: charts, dashboards, infographics, slide decks, static sites, or reports. Evaluate each item and provide specific, actionable feedback.

---

## 1. Context & Message

- [ ] **Clear audience**: Is it obvious who this is for? Is the complexity/detail level appropriate for them?
- [ ] **Single key message**: Can you identify the ONE thing the audience should take away from each chart, panel, or section?
- [ ] **Action title**: Does each title state the "so what" - not just describe the data? (e.g., "Churn increased 15% after price change" vs "Monthly Churn Rate")
- [ ] **Call to action**: Does the communication end with a clear recommendation or next step?
- [ ] **Explanatory not exploratory**: Is this showing curated insights, or dumping raw analysis?

**Common problems:**

- Generic titles like "Overview", "Results", "Data"
- No clear recommendation - ends with data and no interpretation
- Too much data shown "for completeness" rather than for the story

---

## 2. Chart Type Selection

- [ ] **Right chart for the message**: Does the visual type match what you're trying to show? (comparison → bars, trend → lines, composition → stacked bars)
- [ ] **Simple over complex**: Could a simpler chart type work? (e.g., bar chart instead of radar chart)
- [ ] **No pies or donuts**: If present, recommend replacing with horizontal bars
- [ ] **No 3D effects**: If present, remove immediately - they distort data
- [ ] **No dual y-axes**: If present, split into two separate charts or use indexing
- [ ] **No spaghetti**: If >4 overlapping lines, recommend small multiples, filtering, or highlighting one series

**Common problems:**

- Pie chart with 8+ slices where a bar chart would be much clearer
- Line chart for categorical data that has no natural order
- Overly complex or exotic chart types when simple bars/lines would work

---

## 3. Clutter Audit

- [ ] **Chart borders removed**: No unnecessary boxes around charts
- [ ] **Gridlines minimal**: Light grey or removed entirely
- [ ] **No redundant labels**: If axis labels exist, individual data labels are usually unnecessary (and vice versa)
- [ ] **No rotated text**: If axis labels are rotated, the chart should be restructured (usually flip to horizontal bars)
- [ ] **Legend placement**: Can the legend be replaced by direct labelling on the data?
- [ ] **Data-ink ratio**: Is most of the "ink" (pixels) used to represent actual data, not decoration?
- [ ] **White space**: Is there enough breathing room, or is everything crammed together?
- [ ] **Decimal precision appropriate**: Are numbers rounded to the level of precision that matters?

**Common problems:**

- Every data point labelled AND axis ticks AND gridlines - pick one approach
- Bright coloured backgrounds or borders that compete with data
- Logos, clip art, or decorative images that add no informational value

---

## 4. Attention & Emphasis

- [ ] **Strategic use of colour**: Is colour used to highlight the key message, or is it decorative/random?
- [ ] **Grey + accent pattern**: Are non-essential elements pushed to grey with one strategic accent colour?
- [ ] **Visual hierarchy**: Can you tell what's most important within 3 seconds?
- [ ] **Preattentive attributes used**: Is size, colour, or position guiding the eye to the key insight?
- [ ] **Not everything is bold**: Bold/colour/size emphasis is reserved for the key elements only

**Common problems:**

- Rainbow colour palettes where every category gets a bright colour - nothing stands out
- Everything is the same visual weight - no hierarchy
- Red/green colour coding that's inaccessible to colour-blind viewers

---

## 5. Design Quality

- [ ] **Consistent alignment**: Are elements aligned to an invisible grid? Check left edges, spacing, chart sizes
- [ ] **Text is left-aligned**: Body text and labels should be left-aligned (not centred) for readability
- [ ] **Font consistency**: Maximum 2 font families; hierarchy through size and weight only
- [ ] **Annotations present**: Are there text annotations on charts explaining key data points or changes?
- [ ] **Accessible in greyscale**: Would the key message still come through without colour?
- [ ] **Standalone clarity**: If someone sees this without a presenter, would they understand it?

**Common problems:**

- Centred text blocks that are hard to scan
- Inconsistent spacing between sections or chart elements
- Charts that are meaningless without someone talking over them

---

## 6. Narrative Structure

- [ ] **Sequential logic**: Reading just the section/panel/slide titles in order tells a coherent story
- [ ] **Self-contained units**: Each individual section, panel, or slide makes sense with just its title + content
- [ ] **Narrative arc**: The communication follows Beginning (setup) → Middle (tension/insight) → End (recommendation)
- [ ] **Repetition of key message**: The core takeaway appears at least 3 times (intro, body, conclusion)
- [ ] **Progressive disclosure**: Is information built up logically, or is the audience hit with everything at once? (In interactive formats: is there an overview with drill-down?)

**Common problems:**

- Titles that are just category labels ("Finance", "Operations") rather than insights
- No clear narrative thread - feels like a collection of charts, not a story
- The conclusion introduces new data instead of synthesising and recommending

---

## Review Output Format

When providing a review, structure feedback as:

1. **Overall assessment** - 2-3 sentence summary of the biggest opportunities for improvement
2. **Top 3 priority changes** - The changes that would have the most impact, ranked
3. **Section-by-section / chart-by-chart feedback** - Specific, actionable items with clear recommendations
4. **What's working well** - Reinforce the things that are already effective

Always suggest _what to do instead_, not just what's wrong. Where possible, describe or sketch the improved version.
