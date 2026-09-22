---
name: bento-slides
description: Use when creating or editing Bento (`.bento.html`) slide decks, including any request for a single-file HTML slide deck.
---

# Authoring Bento decks

A Bento deck is one self-contained `.bento.html` file: a compressed app runtime plus the document as plain JSON in one block:

```html
<script type="application/bento+json" id="bento-doc"> { "format":"bento/slides", ... } </script>
```

- Edit that block only, in place. Leave the runtime untouched.
- `render_check.mjs --write` writes the block for you. A hand-written splice must escape every `<` in the JSON as its unicode escape (a backslash followed by `u003c`), so the block never contains a literal `</script>` and a build script can find the block's end at the first `</script>` after the opening tag.
- Chat context (no filesystem): the user copies the JSON out (Save > Copy compact JSON) and pastes your replacement back (Save > Replace from JSON). `window.bento.loadDoc(json)` does the same from the console.

## Before touching an existing deck

- **Ask the user to close the deck in their browser.** A save from the open tab overwrites your edit. Autosave keeps a recovery snapshot in IndexedDB keyed by `docId`, so a stale tab offers to "restore" the old version on the next open; tell the user to pick Discard.
- If the `#bento-doc` block contains `"format":"bento/enc"`, the deck is password-encrypted. Stop and tell the user; plain JSON written over it destroys the ciphertext.
- **Leave `collab` as found.** Keys mint at creation and every save writes them, so nearly every saved deck carries `ownerPriv`: anyone with the file can join its live session.
  - Deleting `collab` severs the owner from their own room while sent copies keep the old one.
  - Tell the user once that the file contains session keys. Hand-outs: Share > View-only copy. Leaked file: Share > Reset access.
  - Every save also stamps CRDT state into `collab.sync`; the next open merges it with the room, so elements a script deleted come back. `render_check.mjs --write` drops `collab.sync`. If edits still reappear, the owner's other tabs are in the room: set `collab:{"on":false}` and have the user Share > Reset access.
  - Author `collab:{"on":false}` otherwise only when the user asks for a deck that cannot be shared.

## Starting from nothing

The user does not need Bento installed; the app ships inside every deck. Fetch the latest release and author into it:

```bash
# name the file after the deck's topic, e.g. Q4_Review.bento.html
curl -fsSL https://bento.page/releases/slides/Bento_Slides.bento.html -o "<Topic>.bento.html"
```

Verify the download contains `id="bento-doc"`. The block is empty on disk (a browser mints a demo deck on first open), so there is nothing to discard. Omit `docId` and `collab`; the app mints both on open and writes them when the user saves.

## Workflow

Create a task per step below, each with its completion criterion, then work them to completion.

1. **Read the references.** `references/agents-1.2.3.md` (element shapes, chart/state/hidden-slide rules, column arithmetic) and `references/format-reference.md` (compact form, fields since 1.0.18, runtime rules). Every key, generated from the runtime: https://bento.page/schema/slides.json.
2. **Find the document** (existing deck). Parse the `#bento-doc` JSON. Note `doc.size`, `doc.theme`, element `id`s, `docId`, and whether `template` or `readonly` is set. Keep `docId` unchanged.
3. **Classify the source material.** For each piece: a stat, a table, a process, a definition to expand, a photo, code?
4. **Map each piece to a feature.** This step makes it a Bento deck:
   - numbers to compare (trend, magnitude, share) -> a `chart` element
   - a comparison, spec, pricing or feature grid -> a `table` element (`columns` weights + `rows` of `cells` + a `style` object)
   - a point to drill into -> a state slide (`stateOf` + element `link`)
   - a hero or full-slide image -> full-bleed image + scrim rect + text
   - a sequence, flow or timeline -> connectors (`from`/`to`) or a `path`
   - a headline number -> big text, one plain number per box
   - source code -> a `code` element
   - a build across slides -> one slide per step with `unnumbered:true` on the continuations
   - repeated chrome or logo -> keep its `id` stable across slides
   - a demo clip, recording or soundbite -> a `media` element
5. **Author `doc.json` in compact form** (`"compact": true`), per format-reference "Compact form". Its typography and role-placement rules fail silently: read both before writing text. Compact fills `size` (1280x720) and `theme` when omitted.
   - Keep one accent colour, at most two typefaces, and 96px side margins (right-most x <= 1184).
   - Write speaker notes on each slide.
   - Size text with compact `h:"auto"`; otherwise `window.bento.measure({html, w, fontSize, fontFamily})` via `render_check.mjs --eval`, always passing `fontFamily`.
   - When fanning slides out to several agents, the shared spec lists the type scale (title/body/caption px) and the band tier per slide, as well as colours and columns.
6. **Render and write back:** `render_check.mjs "<Topic>.bento.html" --doc doc.json --write "<Topic>.bento.html"` (add `--motion` if the user asked for animation). In a chat context, return the replacement JSON instead.
7. **Fix and re-run** until there are no `dropped` entries or errors, and no warnings on content you authored, then read every PNG. On an existing deck, report warnings about the user's own content (motion, notes, fonts) instead of rewriting it. Overflow, crowding and a dropped chart key are invisible in the JSON and obvious on screen.
8. **Self-audit before finishing:**
   - [ ] any numbers rendered as text that should be a chart?
   - [ ] a drill-down that would work better as a state slide?
   - [ ] one accent colour?
   - [ ] captions baked into raster images flagged to the user?
   - [ ] on content slides, does the content reach the bottom of the band, with slack spread between blocks rather than pooled underneath?

## Motion default

Static decks: `transition:"none"` or `"fade"`, no `fx`, no loops, no ken-burns. Most decks are shown over a video call, where frame drops smear motion and loops pull attention from the speaker. Bento's templates lean on animation; ignore that. Only when the user asks for animation, read `references/motion.md` (morph, entrances, step reveals, count-up, ken-burns, loops).

## Density rules

Bento's examples use a display band (`y:72 h:84`, content from `y:208`, 96px bottom margin) that leaves 416px of 720 for content. Pick a tier per slide:

- **Display tier** (cover, section divider, one-idea slide): that band, 88px headline, 40px+ body.
- **Content tier** (bullets, tables, charts, comparisons): title ~40px at `y:64`, rule at `y:132`, content from `y:156` to `y:656` (500px), 96px side margins kept.
- **Type floor:** body 16px or larger, nothing below 14px, 20px+ body on content slides. Video calls downscale the canvas, so 13px on 1280 reaches the audience at about 7px. Text baked into a raster image cannot be fixed; flag it during classification (step 3).
- **Fill the band, then choose the gaps.** On a content slide, content reaches the band's bottom and right edges, with leftover height distributed between blocks. For a column: measure every block (or use compact `h:"auto"`), sum, then split the remainder across the gaps.

## Scripts

- `node scripts/render_check.mjs <deck> [--doc doc.json [--write <deck>]]` boots the deck in headless Brave/Chrome with DNS off, prints the load report, `validate()` findings and the skill's own checks, and saves one PNG per page. `--help` lists the options.
- `node scripts/inflate_runtime.mjs <deck>` extracts the compressed runtime as searchable minified JS; `rg` it to settle a question about app behaviour.
- The browser needs its profile directory under `$TMPDIR`; a sandbox that blocks it kills the run, so run outside it. Outside the sandbox `$TMPDIR` differs: keep `doc.json` and the deck on project paths.

## Critical gotchas

- **Bullets are `<ul><li>` in `html`** (nested `<ul>` for sub-bullets, `<ol>` for numbered). A typed "•" or "-" is inline, so a wrapped line returns under the bullet instead of hanging under the text. Compact `md` bullets produce those glyph lines, so a bulleted element uses `html`. Lists cost height and `<ul>` already breaks (no `<br>` beside it): re-measure after converting. Centre or right aligned lists lose the hanging indent.
- **Text `html` keeps tags only** (b i u br p div span ul ol li h1 h2 a code strong em s). Every attribute except http(s) `href` is stripped, so inline colour or size needs a separate text element. `$…$` on one line renders as maths (`$typst: …$` for Typst); write `\$` for a literal dollar.
- **Charts implement a subset of ECharts:** unimplemented keys are ignored silently, and `validate()` misses ignored sub-keys. Write charts only from agents "chart" and format-reference "Chart rules".
- **`fit:"contain"` draws smaller than its box.** Margin and coverage checks read the box, so a portrait image in a landscape box passes while leaving dead space. Give the box the asset's aspect ratio.
- **Tables:** the header row is always bold and `borderWidth` applies to every edge. For horizontal rules only, set `borderWidth:0` and draw `rect` shapes of `h:1` at the row pitch.
- **Hairlines:** a `line` shape draws at 2px minimum. A 1px rule is a `rect` with `h:1`.
- **`{{date}}` renders the viewer's today.** `{{date:YYYY-MM-DD}}` pins the format only. Write a literal date for a fixed event.
- `template:true` -> every open mints a fresh deck, so the runtime strips the flag on load; `render_check.mjs --write` restores `template` and `layouts` from the input JSON. `readonly:true` -> the file boots straight into the show with no editor (validate/measure absent).
- **`doc.layouts` insert semantics:** deep-clones, preserves element ids, clears `notes`, `name` and `stateOf`. Leave `link` out of layouts.

Working examples of every technique: open any template at https://bento.page and read its `#bento-doc` block.
