# Colour & Emphasis Strategy

Colour is the single most powerful tool in data visualisation - and the most frequently misused. These guidelines ensure colour serves the story, not decoration.

---

## The Core Principle: Grey + One Accent Colour

The most impactful SWD technique:

1. **Default everything to grey** - all bars, lines, labels, and supporting elements
2. **Apply ONE accent colour** to the specific data point, series, or element that IS the story
3. The accent element instantly draws the eye because of contrast with the grey surroundings

This works because of **preattentive processing** - the brain detects colour differences before conscious thought. A single blue bar among grey bars is impossible to miss.

### When to use more than one accent colour

- Comparing exactly 2-3 things (e.g., "us vs competitor" - use brand colour vs grey)
- Showing positive vs negative (green vs red, or blue vs orange for accessibility)
- Categorical data where the categories ARE the story - but still limit to 3-4 colours max

---

## Colour Selection Rules

### Do

- **Use colour meaningfully** - each colour should encode information, not just look pretty
- **Be consistent** - same colour = same meaning throughout the entire piece
- **Use saturation for emphasis** - muted/desaturated for background, fully saturated for focus
- **Test in greyscale** - if the chart loses its message in greyscale, the colour strategy isn't strong enough
- **Use sequential palettes** for magnitude (light → dark of one hue)
- **Use diverging palettes** only when there's a meaningful midpoint (e.g., positive/negative, above/below target)

### Don't

- **Don't use rainbow palettes** - they have no natural order and create visual chaos
- **Don't use red + green** as the only differentiator - ~8% of men are red-green colour blind
- **Don't use bright colours for large areas** - saturated colours on big chart elements are overwhelming; reserve them for small accents
- **Don't use colour to differentiate 7+ categories** - if you need that many, restructure the visual (small multiples, filtering, or direct labels)
- **Don't use coloured backgrounds** unless there's a specific design reason - white or very light grey is almost always better for data readability

---

## Emphasis Hierarchy

Layer these preattentive attributes for progressive emphasis:

| Level         | Technique                         | Use for                                       |
| ------------- | --------------------------------- | --------------------------------------------- |
| **Strongest** | Accent colour + large size + bold | The single key number or data point           |
| **Strong**    | Accent colour + normal size       | The data series or category that is the story |
| **Medium**    | Dark grey + normal size           | Supporting data that provides context         |
| **Subtle**    | Light grey + smaller size         | Reference lines, gridlines, axis labels       |
| **Invisible** | Remove entirely                   | Anything that doesn't serve comprehension     |

---

## Colour for Specific Chart Types

### Bar Charts

- Grey all bars, accent the one(s) that tell the story
- Or: grey all bars, use a gradient of the accent colour to show magnitude
- Never use a different colour for every bar unless the categories ARE the point

### Line Charts

- Grey all lines, accent the one series the audience should track
- Use line weight (thickness) as secondary emphasis - thicker = more important
- Dashed lines for projections/forecasts to distinguish from actual data

### Tables & Heatmaps

- Use subtle alternating row shading (very light grey, not colour)
- Use a single-hue sequential palette for heatmap values
- Bold + accent colour for the specific cells you want to highlight

### Text-Heavy Content (Slides, Reports, Infographic Panels)

- Title hierarchy: dark colour for main title, medium grey for subtitles
- Use accent colour in text sparingly - highlight only the key phrase or number
- Never use more than 2 text colours in a single view or section (excluding grey for de-emphasis)

---

## Recommended Palettes

### Safe Defaults (accessible, professional)

- **Accent**: Steel blue (#4472C4) or Teal (#008080) - professional, colour-blind safe
- **De-emphasis**: Medium grey (#A6A6A6) for supporting data
- **Background elements**: Light grey (#D9D9D9) for gridlines and borders
- **Positive/Negative**: Blue (#4472C4) / Orange (#ED7D31) - avoids red/green issues

### For Dark Backgrounds

- If the user insists on dark backgrounds, invert: use lighter greys for de-emphasis and brighter accent colours
- Test carefully - dark backgrounds reduce readability and are rarely worth the aesthetic trade-off

---

## Applying Emphasis to Non-Chart Content

The same principles apply to text-heavy sections in any format (slide panels, dashboard cards, infographic sections, report pages):

- **Bold the key phrase**, not the entire sentence
- **Increase font size** for the single most important number or statement
- **Grey out supporting context** - it's there if they need it but doesn't compete for attention
- **Use colour in text minimally** - one accent colour for the critical insight
- **Progressive disclosure**: In presentations, use animation to reveal key insights progressively. In interactive formats (dashboards, web pages), use overview-then-detail patterns, expandable sections, or scroll-triggered reveals. In static formats (infographics, reports), control the reveal through reading order and visual hierarchy
