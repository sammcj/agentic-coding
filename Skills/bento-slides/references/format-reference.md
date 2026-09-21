# Bento slides format reference (1.0.19 to 1.2.3 additions and runtime rules)

Supplements `agents-1.2.3.md`, whose upstream text stops at 1.0.18. Authoritative key list: https://bento.page/schema/slides.json (`window.bento.schema()` in the app).

Contents: Compact form | Elements and fields | Slide, present, theme | Date and time patterns | Text html rules | Chart rules | window.bento signatures. Animation: `motion.md`.

## Compact form

`"compact": true` at the top level. Accepted only by `window.bento.loadDoc()`, Save > Replace from JSON, and `render_check.mjs --doc`. The on-disk `#bento-doc` block must hold the full document (boot does no expansion).

- Omit every field equal to the editor default (rotation 0, opacity 1, weight 400, centre/middle, lineHeight 1.25, transparent stroke, theme background, `transition:"fade"`). Always write the type's content key, and `x y w h` unless the element is role-placed.
- `id` may be omitted: minted as `<slideId>-<type>-<index>`, deterministic across re-runs.
- `elements` may contain nested arrays (a helper returning `[bg, title, body]` needs no spread).
- Text: omit `h` or write `"h":"auto"` to size the box to its text on the deck's real fonts. Write `md` instead of `html`: `**bold**`, `*italic*`, `` `code` ``, `~~strike~~`, `[caption](https://…)`. `md` bullets (`- item`) become "•" glyph lines with the bad wrap described in SKILL.md, so write bulleted elements as `html` with `<ul><li>`. When both present, `html` wins.
- Placement by role: give the slide `layout` and elements `role`, omit geometry and typography. An element with `x y w h` is placed as given. Extra `body` elements stack in the body slot. A role the layout lacks falls back to body and is noted in `dropped`.
- A role-placed element contributes only its content (`html`/`md`, or `src` for an image) to the layout's slot copy. Every other key on it (`fx`, `fontSize`, `color`, `link`, a typo) is discarded silently and never reaches `dropped`. For step reveals, fonts or effects, place the element with `x y w h` instead.
- Built-in layouts and roles: `title` (title, subtitle), `title-content`/`title-body` (title, body), `two-col`/`two-column` (title, body, left, right), `section` (title, kicker), `three-cards`/`cards` (title, card1-3), `quote` (quote, attribution), `image-left` and `image-right` (image, title, body). A deck's own `layouts` may be named the same way.
- Gate on load: an element missing its required keys is dropped (text `html`, shape `shape`+`fill`, image `src`, chart `option`, table `columns`+`rows`, media `kind`+`src`). Unknown keys are dropped and reported with their path. Colour strings max 64 chars; `url()` only as `url(#local-id)` on a shape `fill`.

## Elements and fields

- Every element may carry `shadow` (`{x,y,blur,color}` or an array to stack), `blur` (px), `blend` (mix-blend-mode), `backdropFilter` (px, screen only, pair with translucent `fill` for PDF), `link`, `group`, `showOnHover`, `themeRefs`.
- `link`: a slide id (jump, the state-slide idiom) or an http(s) URL (opens a new tab). Editor clicks never follow it. Text `html` may also carry `<a href="https://…">`.
- `themeRefs`: `{"fill":"accent1 -20%"}` re-derives the literal from `theme.palette` on every change, overwriting the literal. Slots: bg1, tx1, accent1 (from theme.background/color/accent), bg2, tx2, accent2-6, hlink.
- Text extras: `letterSpacing` (px), `textStroke` `{width,color,fill?}` (`fill:"none"` for hollow glyphs), `colorGradient` (wins over `color`). Empty `html` with `placeholder` is hidden in present mode. Text never autoshrinks.
- Shape: `lineStart`/`lineEnd` in none|arrow|dot|bar|arrow-open|triangle|triangle-open|diamond|diamond-open|square|circle-open; `heads:2` double arrow; `strokeStyle` solid|dashed|dotted. Line colour comes from `fill`, and lines draw horizontally across the box (vertical = rotation).
- Connectors (line/path): `from`/`to` `{el:"<id>", side?:"auto|top|right|bottom|left"}`. Endpoint geometry is derived and follows the target element. A dangling ref frees the endpoint (`dangling-connector` finding).
- Image: `crop` `{x:0..1, y:0..1, scale:1..8}`, `keepAspectRatio`. Photos the editor inserts are downscaled to 2560px JPEG; agent-embedded images are not, so downscale before embedding (About > Compress pictures fixes it later).
- `code` element: `content`, `grammarName` (a key of `kernel/src/tokenize.ts` LANGS such as js ts py rust go sh sql json yaml, plus `diff`/`md`; unknown falls back to js), `themeName`, plus `fontSize fontFamily align valign lineHeight color`. Needs a 1.2.0+ shell.
- `chart`: `source:{tableId}` binds the series to a table element on the same slide.
- `embed` element: `app`, `view`, `doc`, `url`, `live`. Low authoring value; leave to the editor.
- Fonts: `doc.fonts[]` entries `{family, asset, weight, style?}`. The two shell faces need no bytes: `{"family":"Fraunces","asset":"builtin:fraunces-900","weight":"900"}`, `{"family":"Instrument Sans","asset":"builtin:instrument-sans","weight":"400 700"}`. Any other non-system first family not in `doc.fonts` gets a `font-not-embedded` finding.

## Slide, present, theme

- Slide: `unnumbered:true` keeps the slide in the walk but repeats the previous page number (a build spread over several slides). `hidden` slides drop out of `{{pages}}` unless `present.numberHidden`. `hover:{type:"focus-group"|"reveal", dim?, default?}` with element `group`/`showOnHover`.
- `present`: `slideNumber` and `progress` default true, `controls` false. A deck with its own `{{page}}` footer double-numbers unless `present:{"slideNumber":false}`. `morphSeconds`: `motion.md`.
- Theme: `headingFamily`, `palette` (bg2, tx2, accent2-6, hlink), `table` defaults, `codePalette` (keys a c d f k n p s).

## Date and time patterns

`{{date:PATTERN}}` and `{{time:PATTERN}}` pin the shape (field list in `agents-1.2.3.md` "Dynamic fields"): tokens YYYY YY MMMM MMM MM M DD D HH H hh h mm ss A a; bracket literal words `[at]`. Examples `{{date:D MMMM YYYY}}`, `{{time:h:mm a}}`.

## Text html rules

Allowed tags: b i u br span div p strong em s code ul ol li h1 h2 a. Every attribute is stripped except `href` on http(s) links. No inline `style`, colour or size: split into separate text elements. `$…$` on one line renders LaTeX (`$typst: …$` for Typst); escape a literal dollar as `\$`.

## Chart rules

- Font defaults to `sans-serif`, not the theme font: set `option.textStyle.fontFamily`.
- `legend` must be an object (`{}`) to render at all. `label:false` hides pie labels. `axisLabel.formatter` supports `{value}`.
- Bar/line `data` plain numbers (numeric strings and `{value}` objects coerce to 0). Pie needs `{name,value}` and draws only its first series.
- No stacking, per-item colours, `title`, or `axisLabel.rotate`. `validate()` lists ignored keys as `chart-key-ignored`.

## window.bento signatures

- `loadDoc(json)` -> `false` | `{ok, compact, dropped:[{path,reason}], expanded, fitted, laidOut, findings, refit, stacks}`.
- `compact()` -> compact JSON string. `schema()` -> JSON Schema 2020-12.
- `validate(doc?, {measure?, margin?})` -> `{ok, measured, counts:{error,warning,info}, findings:[{code, severity, message, slide?, element?, path?}]}`. Margin check (`past-margin`, info severity) is 96px x 0.9 on text/table only; elements under 3% of canvas area exempt. `font-not-embedded` is info too; `render_check.mjs` surfaces both it and `collab-secrets-present`.
- `measure(idOrSpec, {doc?})` with spec `{html, w, h?, fontSize?, fontFamily?, fontWeight?, lineHeight?, letterSpacing?}` -> `{height, width, lines, fits?, overflow?}`. Without `fontFamily` it measures in the editor stack, so always pass the deck's font.
- `serialize()` returns the full file but stamps the session's collab keys into it. `render_check.mjs --write` splices `window.bento.doc` instead.
- Player (`readonly`) files expose only `{format, doc, readonly}`; validate/measure need an editor shell.
