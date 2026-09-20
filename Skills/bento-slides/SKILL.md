---
name: bento-slides
description: Use when creating single file HTML slide decks, or when editing HTML presentations using Bento.
---

# Authoring Bento decks

A Bento deck is one self-contained `.bento.html` file. The document is plain JSON in a single block:

```html
<script type="application/bento+json" id="bento-doc"> { "format":"bento/slides", ... } </script>
```

Edit that block only, in place. Escape every `<` in the JSON as `<` so it can never contain a literal `</script>`. Leave the rest of the file (the compressed runtime) untouched.

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

When done, open the file (`open` / `xdg-open` / `start`) and look at every slide before reporting done. Text overflow, crowded elements, a heading wrapped to three lines and a dropped chart key are invisible in the JSON and obvious on screen. Author, render, check, fix.

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
5. **Author** using the schema. Fetch https://bento.page/agents.md and keep it open: element shapes, morph/chart/state/ken-burns snippets, gotchas. Respect one accent colour, at most two typefaces, 96px side margins (right-most x <= 1184). Write speaker notes on each slide.
6. **Self-audit before finishing:**
   - [ ] any numbers rendered as text that should be a chart?
   - [ ] do consecutive slides on one subject share ids + `transition:"morph"`?
   - [ ] at least one motion moment (ken-burns / loop / count-up), especially the cover?
   - [ ] a drill-down that would work better as a state slide?
   - [ ] one accent colour, at most two typefaces, 96px margins?
   - [ ] speaker notes on every slide?
7. **Write back** the edited `#bento-doc` block, or return the replacement JSON.

## Critical gotchas

- **Charts:** bar/line series `data` must be plain numbers (`{value,...}` item objects coerce to 0; only pie takes `{name,value}`). Colour by series, not per bar. `option` is pure JSON with template formatters only (`{b}`/`{c}`/`{d}`), never functions.
- **Morph needs stable, deterministic ids** shared across the slides that animate together. Different ids = no morph, the elements just cut.
- **Images and fonts are embedded** as data URIs in `doc.assets` and referenced by `"asset:<key>"`, so the file stays self-contained.
- **Media:** `media` element (`kind: video|audio`). Embed short clips as a data URI in `src`; reference big files by URL to keep the deck small. `autoplay` runs only in present mode and needs `muted:true` for video.
- **`docId` is the document's identity.** Keep it unchanged when editing an existing deck.
- `template:true` -> every open mints a fresh deck. `readonly:true` -> the file boots straight into the show with no editor.

Working examples of every technique: open any template at https://bento.page and read its `#bento-doc` block.
