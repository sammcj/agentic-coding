---
name: prototyping-logos-icons
description: Use when the user asks to mock up or prototype app icon, logo, favicon or menu bar / tray icon designs.
metadata:
  version: 2026-11-27
---

Present every concept in every place the mark will live, side by side, on one HTML sheet. Users judge an icon in context (16 px in a tab, a dark Dock, an About window), so a single large render hides the failures that decide the choice.

## Workflow

1. Create a task per step below, phrased with its completion criterion, then work them to completion.
2. Survey the product: what it does, the current icon and where the code sets it, theme or accent colours, and every surface the mark appears on.
3. When the mark depicts a real object (hardware, a device), look up its proportions and shape. Tell the user which details you could not verify.
4. Draw 3-4 concepts that differ in idea, not colour: literal (the object), function (what the product does), metaphor or scene, monogram or wordplay. Each is one SVG `<symbol>` on a 1024 grid.
5. Draw small-surface glyphs (menu bar, tray, favicon) as separate monochrome `currentColor` symbols on their native grid, 3-5 options.
6. Copy `assets/icon-sheet.html` to a git-ignored build directory and fill it in, keeping its section order (table below). Put the current icon in the first glyph row; for a macOS SF Symbol run `swift scripts/sf-symbol.swift <name> <out.png>`.
7. Run `scripts/render.sh` and Read the PNG; raise `--height` until the last section is fully in it. Re-render with `--scale 2 --crop` on the small-size rows and glyph rows. Done when you have inspected every section and fixed what broke.
8. Give the user the command to open the sheet, then a ranked pick: one line per concept naming the surface or size where it fails, and which to drop.
9. Iterate on the chosen concept with a variant sheet in the same layout: one concept, 4-8 variants along one axis (background, finish, glyph weight).
10. Once chosen, ship it: a standalone source SVG in the repo, a build target that rasterises each required size straight from the SVG (`resvg`, `rsvg-convert`; downscaling one 1024 render blurs 16 and 32 px) into the platform asset, and the generated rasters committed. Done when you have Read the icon from the built artefact at 16, 32 and 512 and it matches the sheet.

## Sheet sections

- **Concept cards** (always): large tile, then 128/64/32/16 on light and on dark.
- **Dock strip** (desktop apps): all concepts at 72 px on a wallpaper gradient.
- **Menu bar rows** (menu bar or tray apps): each glyph at real size in a light and a dark bar, current icon first, plus a zoomed copy.
- **States** (glyphs that reflect state): the chosen glyph idle, active and unavailable, light and dark.
- **About panel** (desktop apps): each concept in a light and a dark About window.

- Web products: swap the Dock and menu bar sections for a browser tab strip (favicon at 16/32), a site header (logo light and dark) and a social card.
- Label each card with the concept name only. When a card needs a sentence to be understood, redraw the concept.

## Variant sets

- Offer and iterate upon suitable variants, e.g. saturated, pastel and neutral/material sets (silver, aluminium, titanium, graphite).
- Show every variant at large and 64/32/16 on light and dark, in light and dark Docks, and in light and dark About panels.
- Ensure variants maintain a professional and coherent look.
- Avoid toyish or immature appearances.

## Gotchas

- Keep the shared `<defs>` `<svg>` at `width="0" height="0" style="position:absolute"`. Gradients and filters referenced from `<symbol>`s stop rendering when it is `display:none`.
- Scenes and people lose their detail below 32 px. Rank by the 16 px render.
- Dark tiles vanish on a dark Dock or dark About window. Pale tiles blend into light windows; a light rim plus a faint dark outline restores the edge.
- Check what a 16-20 px silhouette resembles: a rectangle on a stand reads as a monitor, a pill with a dot reads as a toggle switch.
- Headless Chromium needs an unsandboxed run on macOS.
- macOS 26+ puts a legacy icon that does not fill the standard squircle grid (824 px tile at 100 px inset, about 185 px corner radius) on a grey plate.
