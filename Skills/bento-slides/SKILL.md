---
name: bento-slides
description: Use when creating single file HTML slide decks, or when editing HTML presentations using Bento.
---

# Authoring Bento decks

A Bento deck is one self-contained `.bento.html` file. The document is plain JSON in a single block:

```html
<script type="application/bento+json" id="bento-doc"> { "format":"bento/slides", ... } </script>
```

Edit that block only, in place. Never regenerate the rest of the file (the compressed runtime). Escape every `<` in the JSON as `<` so it can never contain a literal `</script>`; a build script can then rewrite the block by finding the first `</script>` after the opening tag.

In a chat context the user copies the JSON out (Save > Copy compact JSON) and pastes your replacement back (Save > Replace from JSON). `window.bento.loadDoc(json)` does the same from the console.

## Before touching an existing deck

- **Ask the user to close the deck in their browser first.** A save from the open tab overwrites your edit. Autosave also keeps a recovery snapshot in IndexedDB keyed by `docId`, so a stale tab makes the next open offer to "restore" the old version over yours.
- If the `#bento-doc` block holds `"format":"bento/enc"`, the deck is password-encrypted. Stop and tell the user; writing plain JSON over it destroys the ciphertext.

## Starting from nothing

The user does not need Bento installed. The app ships inside every deck. When there is no `.bento.html` to edit, fetch the latest signed release and author into it:

```bash
# name the file after the deck's topic, e.g. Q4_Review.bento.html
curl -fsSL https://bento.page/releases/slides/Bento_Slides.bento.html -o "<Topic>.bento.html"
```

Verify the download contains `id="bento-doc"`. The block is empty on disk: a browser mints a demo deck on first open, so there is nothing to discard or copy from. Omit `docId` and `collab`; the app mints both in memory on open and writes them only when the user saves.

## Authoring form

Write the **compact** form and let the runtime expand it. The on-disk block must hold the full document, so the loop is:

1. Write `doc.json` with `"compact": true` (see `references/format-reference.md`, "Compact form"): defaults omitted, ids optional, text `md` instead of `html`, `h` omitted for auto height, `layout` + `role` placement with no coordinates. A role-placed element keeps only its content; give any element carrying `fx`, fonts or colours explicit `x y w h`.
2. Run the render check (below) with `--doc doc.json --write "<Topic>.bento.html"`: the real runtime expands the document, reports `dropped` keys and findings, screenshots every page, and writes the full document into the block.
3. Fix the JSON, re-run.

Schema sources, in order of completeness: https://bento.page/schema/slides.json (every key, generated from the runtime), `references/format-reference.md` (1.0.19 to 1.2.3 additions and runtime rules), https://bento.page/agents.md (element shapes, morph/chart/state/ken-burns recipes; stops at 1.0.18). Start from agents.md's "Minimal valid document": `size` (1280x720) and `theme` are required. Unknown keys are dropped silently by the on-disk path and reported only by `loadDoc`.

## Workflow

Create a task per step below, each with its completion criterion, then work them to completion.

1. **Find the document.** Locate the `#bento-doc` block and parse its JSON. Note `doc.size`, `doc.theme`, existing element `id`s, `docId`, and whether `doc.template` or `doc.readonly` are set. Keep `docId` unchanged.
2. **Leave `collab` alone.** Keys mint at creation and every ordinary save writes them, so nearly every saved deck carries `ownerPriv`. Anyone holding the file can join that live session. Say so once. Deleting `collab` severs the owner from their own room (sent copies keep the old one), so keep it and point at Save > Save read-only copy for hand-outs or Share > Rotate keys if the file has leaked. Author `collab:{"on":false}` only when the user asks for a deck that cannot be shared.
3. **Classify the source material.** For each piece: a stat, a table, a process, a definition to expand, a photo, code?
4. **Map each piece to a feature.** This step makes it a Bento deck:
   - numbers to compare (trend, magnitude, share) -> a `chart` element
   - a comparison, spec, pricing or feature grid -> a `table` element (`columns` weights + `rows` of `cells` + a `style` object)
   - consecutive slides about the same thing changing -> morph: shared element `id`s on both slides + `transition:"morph"` on the later one (Bento's signature move, use it liberally)
   - a list revealed point by point -> `fx:{step:n}` on each element, one slide
   - a build across slides -> morph slides with `unnumbered:true` on the continuations
   - a point to drill into -> a state slide (`stateOf` + element `link`)
   - a hero or full-slide image -> full-bleed image + scrim rect + text, with ken-burns drift
   - a sequence, flow or timeline -> connectors (`from`/`to`) or a `path` with a `dash-march` loop, or morph a highlight through the steps
   - a headline number -> big text + `fx:{countUp:true}`, one plain number per box
   - source code -> a `code` element; same `id` across slides morphs token by token
   - every cover or divider -> at least one ambient motion
   - repeated chrome or logo -> keep its `id` stable across slides so it morphs in place
   - a demo clip, recording or soundbite -> a `media` element
5. **Author.** Respect one accent colour, at most two typefaces, 96px side margins (right-most x <= 1184). Write speaker notes on each slide. Prefer compact `h:"auto"` for text height; otherwise `window.bento.measure({html, w, fontSize, fontFamily})` via `render_check.mjs --eval`, always passing `fontFamily`.
6. **Write back** via `render_check.mjs --doc --write`, or return the replacement JSON in a chat context.
7. **Render check** (below): fix every `dropped` entry, warning and error, then read each PNG. Text overflow, crowded elements and a dropped chart key are invisible in the JSON and obvious on screen.
8. **Self-audit before finishing:**
   - [ ] any numbers rendered as text that should be a chart?
   - [ ] do consecutive slides on one subject share ids + `transition:"morph"`?
   - [ ] at least one motion moment (ken-burns / loop / count-up / step reveal), especially the cover?
   - [ ] a drill-down that would work better as a state slide?
   - [ ] one accent colour, at most two typefaces, 96px margins?
   - [ ] `present:{"slideNumber":false}` if the deck has its own `{{page}}` footer?
   - [ ] speaker notes on every slide?
   - [ ] `render_check.mjs` clean and every PNG reviewed?

## Render check

```bash
node scripts/render_check.mjs "<Topic>.bento.html" [--doc doc.json [--write <Topic>.bento.html]]
```

Boots the deck in headless Brave/Chrome, optionally loads a document through `loadDoc()` and prints its report, prints `window.bento.validate()` findings (unknown keys, text overflow, off-canvas elements, broken links, ignored chart options), enters present mode and saves one PNG per page. `--help` lists the options, including `--eval` for `measure()` calls. It refuses to run inside a sandbox that blocks the browser profile directory.

## Critical gotchas

Full rules in `references/format-reference.md`. The ones that bite most:

- **Text `html` keeps tags only** (b i u br p div span ul ol li h1 h2 a code strong em s). Every attribute except http(s) `href` is stripped, so inline colour or size needs a separate text element. `$…$` on one line renders as maths; write `\$` for a literal dollar.
- **Charts:** bar/line `data` plain numbers; pie takes `{name,value}`. `legend` must be an object to render. Chart text defaults to `sans-serif`: set `option.textStyle.fontFamily` to the deck font. `option` is pure JSON with template formatters only.
- **Morph needs stable ids** shared across the slides that animate together, and the same `fontFamily` on every slide (content swaps at frame one; only geometry, opacity and colour tween). Keep the box aspect ratio or the text stretches.
- **`fx.countUp` strips markup** and animates every number in the box.
- **`present.slideNumber` defaults on**, so a deck with its own `{{page}}` footer shows two numbers.
- **Fonts:** the shell faces need no bytes (`"asset":"builtin:fraunces-900"`, `"builtin:instrument-sans"`); any other face goes in `doc.assets` as a data URI. Images likewise, downscaled to 2560px before embedding.
- **Media:** `muted` defaults to true; `muted:false` blocks video autoplay. Embed short clips, host large files by URL.
- **`{{date}}` renders the viewer's today.** `{{date:YYYY-MM-DD}}` pins the shape only. Write a literal date for a fixed event.
- `template:true` -> every open mints a fresh deck. `readonly:true` -> the file boots straight into the show with no editor (validate/measure absent).
- **`doc.layouts` insert semantics:** deep-clones, preserves element ids (shared chrome keeps morphing), clears `notes`, `name` and `stateOf`. Leave `link` out of layouts.
- **Reading the runtime source:** `node scripts/inflate_runtime.mjs "<deck>.bento.html"` extracts the compressed runtime as searchable minified JS; `rg` it to settle a question about app behaviour.

Working examples of every technique: open any template at https://bento.page and read its `#bento-doc` block.
