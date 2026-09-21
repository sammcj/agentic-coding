---
name: bento-slides
description: Use when creating single file HTML slide decks, or when editing HTML presentations using Bento.
---

# Authoring Bento decks

A Bento deck is one self-contained `.bento.html` file. The document is plain JSON in a single block:

```html
<script type="application/bento+json" id="bento-doc"> { "format":"bento/slides", ... } </script>
```

Edit that block only, in place. Escape every `<` in the JSON as `\u003c` so it can never contain a literal `</script>`. This also makes the splice idempotent: a build script can rewrite the block by finding the first `</script>` after the opening tag. Leave the rest of the file (the compressed runtime) untouched.

Generate the document JSON from a throwaway Node script rather than hand-writing it. A deck runs to ~100 elements each needing a full field set, and a missing field renders wrong with no warning. Give the script helpers that fill the default fields (`rotation`, `opacity`, `stroke`, `strokeWidth`) and compute image dimensions so logos keep their aspect ratio.

In a chat context the user copies the JSON out (Save > Copy document JSON) and pastes your replacement back (Save > Replace from JSON). `window.bento.loadDoc(json)` does the same from the console.

## Starting from nothing

The user does not need Bento installed. The app ships inside every deck. When there is no `.bento.html` to edit, fetch the latest signed release and author into it:

```bash
# name the file after the deck's topic, e.g. Q4_Review.bento.html
curl -fsSL https://bento.page/releases/slides/Bento_Slides.bento.html -o "<Topic>.bento.html"
```

(Windows without curl: `iwr https://bento.page/releases/slides/Bento_Slides.bento.html -OutFile <Topic>.bento.html`.)

Verify the download contains `id="bento-doc"`, then write your document into that block. The block is empty on disk: a browser mints a demo deck on first open, so there is nothing to discard or copy from.

Rules for a fresh document:

- Start from the "Minimal valid document" skeleton in https://bento.page/agents.md. `size` and `theme` (including `theme.fontFamily`) are required or the app will not boot.
- Fully specify element fields as the skeleton shows. Shapes need `stroke`/`strokeWidth`, text needs `fontFamily`/`align`/`valign`. Missing fields render wrong or not at all.
- Omit `docId` and `collab`. The app mints a fresh identity and dormant collaboration credentials on first open.

## Workflow

Create a task per step below, each with its completion criterion, then work them to completion.

1. **Find the document.** Locate the `#bento-doc` block and parse its JSON. Note `doc.size` (canonical 1280x720), `doc.theme`, existing element `id`s, and whether `doc.template` or `doc.readonly` are set.
2. **Check `doc.collab` before reading further.** If it carries `ownerPriv`, `writerPriv` or `invite`, the deck's live-session keys are in the file, and anything that receives the file or its JSON can join and write to that session. Tell the user before continuing, since they may not know the deck is shared. Offer a read-only copy, or Share > Stop sharing on a duplicate. If the file has already gone somewhere, the remedy is Share > Rotate keys; removing the keys afterwards does not retract them.
3. **Classify the source material.** For each piece: a stat, a table, a process, a definition to expand, a photo?
4. **Map each piece to a feature.** This step makes it a Bento deck:
   - numbers to compare (trend, magnitude, share) -> a `chart` element
   - a comparison, spec, pricing or feature grid -> a `table` element (`columns` weights + `rows` of `cells` + a `style` object)
   - consecutive slides about the same thing changing -> morph: shared element `id`s on both slides + `transition:"morph"` on the later one (Bento's signature move, use it liberally)
   - a point to drill into -> a state slide (`stateOf` + element `link`)
   - a hero or full-slide image -> full-bleed image + scrim rect + text, with ken-burns drift
   - a sequence, flow or timeline -> a line/`path` with a `dash-march` loop, or morph a highlight through the steps
   - a headline number -> big text + `fx:{countUp:true}`
   - every cover or divider -> at least one ambient motion
   - repeated chrome or logo -> keep its `id` stable across slides so it morphs in place
   - a demo clip, recording or soundbite -> a `media` element (see gotchas)
5. **Author** using the schema. Fetch https://bento.page/agents.md and keep it open: element shapes, morph/chart/state/ken-burns snippets, gotchas. Respect one accent colour, at most two typefaces, 96px side margins (right-most x <= 1184). Write speaker notes on each slide. Size text with `window.bento.measure({html, w, fontSize, lineHeight})` rather than guessing heights: pass it to `render_check.mjs --eval` (below), or run it in the browser console when the user has the deck open.
6. **Write back** the edited `#bento-doc` block, or return the replacement JSON.
7. **Render check** (below): run `render_check.mjs`, fix every warning and error, read each PNG. Text overflow, crowded elements and a dropped chart key are invisible in the JSON and obvious on screen.
8. **Self-audit before finishing:**
   - [ ] any numbers rendered as text that should be a chart?
   - [ ] do consecutive slides on one subject share ids + `transition:"morph"`?
   - [ ] at least one motion moment (ken-burns / loop / count-up), especially the cover?
   - [ ] a drill-down that would work better as a state slide?
   - [ ] one accent colour, at most two typefaces, 96px margins?
   - [ ] speaker notes on every slide?
   - [ ] `render_check.mjs` clean and every PNG reviewed?

## Render check

```bash
node scripts/render_check.mjs "<Topic>.bento.html"
```

Boots the deck in headless Brave/Chrome, prints `window.bento.validate()` findings (unknown keys, text overflow, off-canvas elements, broken links, ignored chart options), enters present mode and saves one PNG per page. `--help` lists the options, including `--eval` for `measure()` calls.

## Critical gotchas

- **Charts:** bar/line series `data` must be plain numbers (`{value,...}` item objects coerce to 0; only pie takes `{name,value}`). Colour by series, not per bar. `option` is pure JSON with template formatters only (`{b}`/`{c}`/`{d}`), never functions.
- **Morph needs stable, deterministic ids** shared across the slides that animate together. Different ids = no morph, the elements just cut.
- **Images and fonts are embedded** as data URIs in `doc.assets` and referenced by `"asset:<key>"`, so the file stays self-contained.
- **Media:** `media` element (`kind: video|audio`). Embed short clips as a data URI in `src`; reference big files by URL to keep the deck small. `autoplay` runs only in present mode and needs `muted:true` for video.
- **`docId` is the document's identity.** Keep it unchanged when editing an existing deck.
- `template:true` -> every open mints a fresh deck. `readonly:true` -> the file boots straight into the show with no editor. A template cannot be edited through the app: change the JSON and rebuild.
- **Morphed elements need the same `fontFamily` on every slide** they appear on, or the tween swaps typeface mid-flight. Vary size and weight only.
- **`{{date}}` renders the viewer's today** in their machine's locale. Write a literal ISO date (YYYY-MM-DD) on the cover instead. The `:arg` suffix only pads `{{page}}` and `{{pages}}`.
- **`doc.layouts` insert semantics:** inserting deep-clones the layout, preserves element ids (so shared chrome keeps morphing) and clears `notes`. Leave `link` out of layouts, since its target slide id will not exist in the deck it is used in. Put teaching notes on demo slides, never on layouts.
- **Reading the runtime source:** agents.md does not cover everything. The two `bento/deflate-b64` script blocks near the end of the file are raw DEFLATE; `zlib.inflateRawSync(Buffer.from(b64, "base64"))` gives readable minified source to settle a question about app behaviour.

Working examples of every technique: open any template at https://bento.page and read its `#bento-doc` block.
