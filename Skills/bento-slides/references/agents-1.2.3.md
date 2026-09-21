# bento/slides agent guide (vendored)

Pruned copy of https://bento.page/agents.md, guide version 1.2.3, read 2026-09-22. Cut because the skill replaces them: intro, "Make a GREAT deck", measure/validate and Gotchas (SKILL.md, `format-reference.md`), the vertical title band (SKILL.md "Density rules"). Stale lines corrected against the 1.2.3 source are marked `[1.2.3]`.

## Minimal valid document

Start from this skeleton when creating a deck from scratch. `size` and `theme` are required. The full field set shown is what the on-disk block holds; write the compact form and let the runtime expand it (SKILL.md "Authoring form").

```json
{
  "format": "bento/slides", "version": 1, "title": "My deck",
  "size": { "width": 1280, "height": 720 },
  "theme": { "background": "#101418", "color": "#F2F0EA",
             "accent": "#FF9E8A", "fontFamily": "system-ui, sans-serif" },
  "slides": [
    { "id": "s1", "background": "#101418", "transition": "none",
      "notes": "speaker notes here",
      "elements": [
        { "id": "t1", "type": "text", "x": 96, "y": 260, "w": 1088, "h": 160,
          "rotation": 0, "opacity": 1,
          "html": "Hello from an agent.",
          "fontSize": 88, "fontFamily": "system-ui, sans-serif",
          "fontWeight": 800, "color": "#F2F0EA",
          "align": "left", "valign": "top", "lineHeight": 1.1 }
      ] }
  ]
}
```

## Element types (all share `id,x,y,w,h,rotation,opacity`)

- **text**: `html` (tags only, see `format-reference.md` "Text html rules" `[1.2.3]`), `fontSize`, `fontFamily`,
  `fontWeight`, `color`, `align` (`left|center|right`), `valign`,
  `lineHeight`, optional `letterSpacing`.
- **shape**: `shape` = `rect|ellipse|triangle|arrow|line|path`, `fill`, `stroke`,
  `strokeWidth`, `radius` (rect corner). Optional `fillGradient`
  `{angle, stops:[{at:0..1, color}]}` (CSS-convention angle). Lines take
  their color from `fill` and draw horizontally across the box (rotate for
  vertical); `strokeStyle: solid|dashed|dotted`; tips `lineStart`/`lineEnd`
  (11 kinds, `format-reference.md` `[1.2.3]`). A `path` is a free vector: `d` (SVG path data) +
  `pathBox` `[x,y,w,h]` authoring viewBox, stretched into the element box;
  for a **curved line** set `fill:"transparent"` + a `stroke` + `strokeWidth`.
  A **connector** is a `line` (or `path`) with `from`/`to: {el, side}` - its ends
  follow those elements and re-route when they move (side `"auto"` picks the
  nearest border). Make sure a shape's colour contrasts with its slide background.
- **image**: `src` = data URI or `"asset:<key>"` into `doc.assets`,
  `fit: cover|contain|fill`, `radius`. Embed images as data URIs in
  `doc.assets` and reference them - the file must stay self-contained.
- **chart**: `preset: bar|line|pie|scatter`, `option` = ECharts-SHAPED pure
  JSON. **Bar/line series data must be plain numbers** (`{value,itemStyle}`
  objects coerce to 0 - only pie takes `{name,value}`); per-item bar colors
  are unsupported, color by series; template formatters only (`{b}`, `{c}`,
  `{d}`), never functions. **Dual axis**: for two series on very different
  scales (e.g. volume + a %), make `yAxis` an ARRAY of two `{type:"value"}`
  axes (give the 2nd `axisLabel:{formatter:"{value}%"}`) and point the odd
  series at it with `"yAxisIndex":1` - render it as a `line` over the bars.
  **The engine is charts-lite, not ECharts** - it reads the option SHAPE and
  ignores every key it does not implement, silently. What it honours:
  - top level - `color`, `series`, `xAxis`, `yAxis`, `legend`, `grid`,
    `tooltip`, `textStyle`, `dataZoom`
  - any series - `type`, `name`, `data`, `yAxisIndex`, `itemStyle.color`
  - bar - `itemStyle.borderRadius`
  - line - `smooth`, `symbol`, `symbolSize`, `lineStyle.color`,
    `lineStyle.width`, `areaStyle.color`
  - pie - `radius`, `label.formatter` (or `label:false`),
    `itemStyle.borderColor`, `itemStyle.borderWidth`
  - axes - `type`, `data`, `min`, `max`, `axisLabel` (`fontSize`,
    `fontWeight`, `color`, `formatter`), `axisLine`, `splitLine`
  - legend - `show`, `top`, `bottom`, `textStyle.fontSize`,
    `textStyle.fontWeight`

  **`label` on a bar or line series does nothing** - value labels above bars
  are pie-only. If you need the numbers visible on a cartesian chart, put them
  in a table beside it, or use text elements.
- **table**: `columns` (array of `{w}` fractional weights), `rows` (array of
  `{cells:[{html, align?, color?, bg?, bold?}]}`), `header` (bool - row 0 is
  the header), and a `style` object (`headerBg`, `headerColor`, `zebra?`,
  `borderColor`, `borderWidth`, `cellPadX`, `cellPadY`, `fontSize`, `color`,
  `radius`). Renders as a real HTML table. Use for comparison/spec/pricing
  grids - NOT for numeric trends (use a chart).
- **svg**: `asset` or `markup` for static artwork. Prefer composing rects/
  texts/paths - those stay editable and can morph.
- **media**: `kind: video|audio`, `src` = data URI (embedded - travels in the
  file), an external URL / relative path (referenced - keeps the file small,
  needs the network at play time), or `"asset:<key>"`. Video also takes
  `poster`, `fit: cover|contain|fill`, `radius`. Playback flags: `controls`,
  `autoplay`, `loop`, `muted`. **Autoplay fires only in present mode**; `muted`
  defaults to true and `muted:false` blocks video autoplay `[1.2.3]`. **Embed only SHORT
  clips** - a big data URI bloats the file and makes it slow to open/save;
  host large media and reference its URL instead.

## The rules that make decks feel designed

- **Morph = shared ids.** Slides with `"transition": "morph"` tween any
  elements whose `id` matches the previous slide - position, size, color,
  gradients. This is THE signature move: carry 2-4 ids through the deck and
  rearrange them per slide. Generators must emit deterministic ids.
- **`morphId` decouples morph identity from `id`.** The real pairing key is
  `morphId || id`, so an element can keep whatever `id` it likes and set
  `"morphId": "running-head"` to morph against a differently-named element on
  the next slide. For a generator this beats threading one id by hand through
  every slide, and it lets two independently-created elements pair up. The key
  must be unique **within** a slide. Plain shared `id` still works and is still
  the simplest thing when you control both slides.
- **Entrances**: `fx: { enter: "fade-up", order: 0 }` - equal `order` =
  simultaneous. On a **morph arrival** the rule is per element, and it turns on
  whether that element has a morph partner on the previous slide:
  - **has a partner** → it morphs, and `fx.enter` and `fx.countUp` are both
    skipped. It is already in motion and already showing its number; an
    entrance would fight the tween and a count-up would restart from zero.
  - **no partner** → it is new to the slide, so both run normally. Without an
    `fx.enter` it gets an automatic fade-and-rise so nothing ever just pops in.

  So a headline number, or a panel that sweeps in from the right, is fine on a
  morph slide - just make sure it is new to that slide.
- **Ken-burns**: `fx: { ambient: "kenburns", ken: { dir: "drift|out|in",
  scale: 1.08, duration: 20 } }` - `drift` loops, `out`/`in` settle once on
  slide entry. For full-bleed photos: image at 0,0,1280,720 + a scrim rect
  + text on top. Never combine entrance tweens with motion-path loops.
- **Loops**: two shapes, both under `fx.loop`.
  - `{ type: "dash-march", distance: 18, duration: 1.4 }` - marches the stroke
    dashes along a shape. It animates `strokeDashoffset`, so it needs a
    `stroke` **and** a dash pattern: set `strokeStyle: "dashed"` or `"dotted"`.
    On a solid stroke the tween still runs and there is nothing to see.
  - `{ type: "motion-path", path: "M0,0 C60,-40 140,40 200,0", duration: 6,
    delay: 0, ease: "none", speeds: [1, 1] }` - drifts the element along a
    path given RELATIVE to its resting position (the first anchor is where it
    sits). `speeds` is optional, one multiplier per on-curve point, and lets
    the element dwell in places and rush others; omit it for constant pace.
    Never put an entrance tween on a motion-path element - they fight over the
    same transform.
- **Interactivity**: element `link: "<slide-id>"` jumps on click; a slide
  with `stateOf: "<parent-id>"` is a hidden variant reached only by links
  (arrow keys skip it, ← returns to parent). Give clickable things a padded
  transparent rect as the hit target, not the text itself.
- **Hidden slides**: `"hidden": true` keeps a slide in the deck and out of the
  show - arrow keys skip it, PDF export leaves it out, and it is never the
  file's thumbnail - but an element `link` still reaches it. That is what it is
  for: backup and appendix material you jump to only if asked. By default a
  hidden slide does not consume a page number either, so `{{page}}`/`{{pages}}`
  stay contiguous for the audience; set `present.numberHidden: true` for the
  office-suite behaviour where it keeps its number.

  Not the same as `stateOf`. A state is a variant OF another slide (← returns
  to its parent, and it morphs with it); hidden carries no such relationship.
  Use a state for "click to drill into this", hidden for "only if they ask".
- **Numbers count up** with `fx: { countUp: true }`.
- **Speaker notes** (`notes`) are part of the document - write them; they
  make a template teach itself.

## Layout guardrails

- Canonical canvas 1280×720 (`doc.size` can differ - read it first).
- Keep 96 px side margins (right-most content x ≤ 1184).
- **Column arithmetic, already done.** On 1280×720 inside 96 px margins the
  content band is 1088 px wide. Use these rather than computing your own:

  | Split | Width | `x` positions | Gutter |
  |---|---|---|---|
  | 2 columns | 528 | 96, 656 | 32 |
  | 3 columns | 340 | 96, 470, 844 | 34 |
  | 4 columns | 254 | 96, 374, 652, 930 | 24 |
  | 60 / 40 (text + image) | 624 / 432 | 96, 752 | 32 |

  Every row ends flush at x = 1184. Vertical bands: SKILL.md "Density rules".
- One accent colour; 2 typefaces max. `theme` sets deck defaults.
- A `fontFamily` naming a face the document does not carry falls back silently to the next entry in the stack, and it looks right to you because you have the face installed. `validate()` reports it as `font-not-embedded`. Always write a full stack (`"'Fraunces', Georgia, serif"`), never a bare family name. Embedding: `format-reference.md`, "Fonts".

## Layouts and `role`

`doc.layouts` is a supported top-level key: an array of Slide-shaped templates
the editor offers under *Apply layout*. Every deck also gets nine built-ins
(title, title-content, two-col, section, blank, three-cards, quote, image-left,
image-right `[1.2.3]`), which are scaled to the deck's `doc.size` when applied.

The part that matters when you are generating a deck is **`role`**. Any text
element can carry `"role": "title" | "subtitle" | "body" | "kicker" | "quote" | "attribution" | "card1".."card3"`, an image `"image"` `[1.2.3]`. Applying a
layout matches donor to target by `id` first and then by `role` + `type`, so
roles are what let someone restyle your deck later without re-typing it -
content rides across, the layout supplies frame and typography. Setting them
costs one key per element and makes a generated deck feel native to the editor.

Two smaller things: a layout's text elements use `placeholder` (a dimmed prompt
shown in the editor, hidden in present and print) rather than `html`, and
slides instantiated from the same layout keep their element ids - which is
exactly why their furniture morphs across a transition.

## Dynamic fields (tokens in text `html`)

Put these tokens in any text element's `html`; they resolve at render time (the
model keeps the raw token, so numbering/props update automatically):
`{{page}}`, `{{pages}}` (position among non-state slides; zero-pad with
`{{page:2}}`→"06"), `{{title}}`, `{{date}}`, `{{time}}` (pin a shape with `{{date:YYYY-MM-DD}}` `[1.2.3]`), and the document
properties `{{author}}`, `{{company}}`, `{{subject}}`, `{{event}}`. Set the
props in an optional top-level `"meta": {author, company, subject, event,
keywords}` object - great for title slides and footers that fill from one place.
