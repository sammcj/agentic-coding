# Chart Selection Guide

Based on the Storytelling with Data methodology. Choose the simplest chart that communicates your message effectively.

## Decision Matrix

Ask: **"What relationship am I showing?"** Then pick from below.

---

### Comparison Across Categories

**Default: Horizontal Bar Chart**
- The workhorse of data visualisation - familiar, easy to read, works for almost everything
- Labels read naturally left-to-right; bars extend right for easy length comparison
- Use when: comparing discrete items (products, regions, departments, survey responses)
- Order bars meaningfully: by value (largest to smallest) or by natural order (e.g., survey scale)
- Always start the value axis at zero (truncated axes distort bar comparisons)

**Alternative: Vertical Bar Chart (Column Chart)**
- Use when categories have a natural sequential order (months, quarters, years)
- Also works for small numbers of categories (< 8) with short labels
- Still must start at zero

**Alternative: Dot Plot**
- Use when you want to show values without the visual weight of bars
- Good for showing range between two values (e.g., before/after, min/max)

---

### Change Over Time (Trends)

**Default: Line Chart**
- Best for continuous time series - the slope communicates rate of change intuitively
- Audiences naturally read left-to-right as time progression
- Limit to 3-4 lines maximum; beyond that, use small multiples or filter
- OK to not start at zero (unlike bar charts) if the focus is rate of change

**Alternative: Vertical Bar Chart**
- Use for discrete time periods (Q1, Q2, Q3, Q4) where continuity isn't implied
- Use when absolute magnitude matters more than the trend shape

**Alternative: Slopegraph**
- Use when comparing exactly two time periods (before/after, Year 1 vs Year 2)
- Excellent for showing which items increased vs decreased simultaneously
- The slope direction and steepness tells the story at a glance

**Avoid: Area Chart (usually)**
- Stacked area charts are hard to read - only the bottom series has a clear baseline
- Single area charts can work to emphasise volume/magnitude over time

---

### Part-to-Whole (Composition)

**Default: Stacked Bar Chart (Horizontal)**
- Shows composition AND allows comparison across categories
- Use 100% stacked bars when proportions matter more than absolute values
- Order segments consistently across bars

**Alternative: Waterfall Chart**
- Shows how individual components add up to a total (or how a starting value changes)
- Great for financial walk-throughs (revenue → costs → profit)

**Avoid: Pie Charts and Doughnut Charts**
- Human eyes are poor at comparing angles and areas accurately
- Any data that could go in a pie chart is better served by a horizontal bar chart
- If you must show parts of a whole and your audience insists on pies, limit to 2-3 slices maximum

---

### Relationship Between Two Variables

**Default: Scatterplot**
- Shows correlation, clusters, and outliers between two continuous variables
- Add a trend line only if it genuinely helps interpretation
- Label notable outliers directly on the chart

---

### Single Key Number

**Default: Simple Text**
- If your key message is one number, make it BIG
- Show it as a large formatted number with brief context: "Revenue grew **23%** year-over-year, reaching $4.2M"
- No chart needed - a chart with one data point is wasteful

---

### Detailed Lookup / Reference Data

**Default: Table**
- When the audience needs to look up specific values, a well-formatted table beats any chart
- Use light formatting: remove heavy borders, alternate subtle row shading, align numbers right
- Bold or colour-highlight the row/column you want to draw attention to

**Alternative: Heatmap**
- A table with colour-encoded cell values to show magnitude patterns
- Good for spotting patterns in matrix data (time × category, feature × product)
- Use a single colour gradient (light → dark) rather than a diverging palette unless there's a meaningful midpoint

---

## When to Combine Visuals

- **Chart + Simple Text callout**: Lead with the headline number in large text, support with the chart below
- **Small multiples**: When you have too many series for one chart, repeat the same chart type for each category - same scale, same format, arranged in a grid
- **Annotation layers**: Add text callouts, reference lines, and shaded regions directly on charts to guide interpretation

---

## Universal Rules

1. **Every chart needs a declarative action title** - not "Q3 Sales by Region" but "Southeast region drove 60% of Q3 growth"
2. **Label data directly** when possible - eliminate legends by placing labels next to the data they describe
3. **Use consistent scales** when comparing multiple charts - don't change axis ranges between views
4. **Round numbers** - 23% not 23.47% unless precision genuinely matters
5. **Bar charts must start at zero** - line charts don't have to
6. **Horizontal bars > vertical bars** in most cases (labels are easier to read)
