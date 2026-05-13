---
name: web-artifacts-builder
description: Suite of tools for creating elaborate, multi-component claude.ai HTML artefacts using modern frontend web technologies (React 19, Tailwind CSS v4, shadcn/ui). Use for complex artefacts requiring state management, routing, or shadcn/ui components - not for simple single-file HTML/JSX artefacts.
license: Complete terms in LICENSE.txt (Anthropic original, locally modified)
metadata:
  source: Rewritten from Anthropic's official `web-artefacts-builder` skill, with lots of updates
---

# Web Artefacts Builder

To build a frontend claude.ai artefact, follow these steps:
1. Initialise the frontend repo with `scripts/init-artifact.sh`
2. Pick a theme from `resources/themes.css` and apply it (see "Themes" below)
3. Develop your artefact by editing the generated code
4. Bundle to a single HTML file with `scripts/bundle-artifact.sh`
5. Share the bundled artefact with the user
6. (Optional) Test the artefact

**Stack**: React 19 + TypeScript + Vite 8 + Tailwind CSS v4 + shadcn/ui (new-york style) + lucide-react. Bundling via `vite-plugin-singlefile`. Requires Node 20.19+ or 22.12+.

## Design principles

These principles are adapted from the `html-design-examples` skill. Load that skill alongside this one when you need patterns for specific artefact intents (status report, code review, PR write-up, design system page, editor, etc.); its rendered catalogue at `resources/index.html` indexes 20 single-file references.

- **Calm, editorial aesthetic.** Restrained accent colour, generous whitespace, content does the talking. Avoid hero gradients, marketing sheen, and dashboard-style chrome unless the artefact is a dashboard.
- **Typography over chrome.** Establish hierarchy with weight, size, and leading before reaching for borders, backgrounds, or coloured bars. Serif headings paired with sans body is the recurring pattern in the references and a reliable choice when you have no other signal. Defaulting to Inter as the only typeface is an AI-output tell - pick a pairing from the chosen theme's font notes.
- **Earn your accent.** Most themes ship with a single accent colour. Treat it as scarce. Use it for the one thing on the page that demands attention (the primary action, the link, the focused state) and almost nowhere else.
- **Use the full width when it helps.** Don't centre a narrow column when the content is tabular, comparative, or spatial. A wide layout with structured columns reads better than a 720px text shaft for anything that isn't longform prose.
- **Export interactive state.** If the artefact is an editor, board, or any surface where the user is doing work, finish it with a "copy as JSON" or "copy as prompt" button so the result flows back into the agent loop. See the `18-editor-triage-board.html` example in `html-design-examples` for the pattern.

## Anti-slop rule

Use visual accents (coloured border stripes, tinted-background callout boxes, accent bars on cards) only when the colour or treatment encodes specific information - status, category, severity, or priority that I've explicitly defined. Don't apply visual accents decoratively, don't rotate through palette colours across sibling items for variety, and don't reach for the tinted-callout-with-coloured-bar pattern as a default way to mark asides. If you're about to add an accent, ask whether removing it would lose information; if not, remove it and rely on plain typographic hierarchy instead.

Other things to avoid because they read as AI-default output: excessive centred layouts, purple gradients, uniformly rounded corners on everything, glassmorphism, emoji bullets, and three-card-grid hero sections with identical icons.

## Themes

`resources/themes.css` ships five named themes. Pick one before you start writing components - retrofitting a palette is much more work than choosing one up front.

| Theme | Mood | Good for |
|-------|------|----------|
| Editorial paper | Warm paper, ink, ochre accent | Longform writeups, plans, reports, post-mortems |
| Technical mono | Near-monochrome, single green accent | Code reviews, system diagrams, status pages, debugging |
| Warm desaturated | Sand, clay-brown, muted terracotta | Brand-adjacent artefacts, design pages, anything that wants warmth without volume |
| Cool muted | Quiet slate, low-chroma teal | Dashboards, status reports, technical docs |
| Nordic dark | Polar-night greys, frost-blue | Incident write-ups, debug dumps, dark-mode-first developer tooling |

To apply a theme:
1. Read `resources/themes.css` and copy the `:root { ... }` and `.dark { ... }` blocks for the chosen theme.
2. Replace the existing `:root` and `.dark` blocks in your project's `src/index.css`. Leave the `@theme inline` and `@layer base` blocks alone - they wire the variables into Tailwind utilities.
3. Add the suggested font stack (the comment block above each theme lists one) - either via a `<link rel="stylesheet">` tag in `index.html` from Google Fonts, or by setting `body { font-family: ... }` in `src/index.css`.

If the user has an existing brand or design system, defer to it rather than picking from the gallery.

## Quick start

### Step 1: Initialise the project

```bash
bash scripts/init-artifact.sh <project-name>
cd <project-name>
```

This creates a configured project with:
- React 19 + TypeScript via Vite 8
- Tailwind CSS v4 (CSS-first config in `src/index.css`, no `tailwind.config.js`)
- 40+ shadcn/ui components in `src/components/ui/`
- `radix-ui` umbrella package and lucide-react
- Path alias `@/` configured in both `tsconfig.json` and `vite.config.ts`
- Minimal `App.tsx` placeholder ready for you to edit

### Step 2: Apply a theme

See "Themes" above.

### Step 3: Develop the artefact

Edit `src/App.tsx` and add components as needed. Components are imported from `@/components/ui/<name>`. The `cn()` helper lives at `@/lib/utils`.

To preview during development:

```bash
pnpm dev
```

### Step 4: Bundle to a single HTML file

```bash
bash scripts/bundle-artifact.sh
```

This produces `bundle.html` - a single self-contained file with all JS, CSS, and assets inlined. The script:

- Adds `vite-plugin-singlefile` as a dev dependency
- Writes a `vite.config.bundle.ts` that extends your config with the single-file plugin and inlining options
- Runs `vite build --config vite.config.bundle.ts`
- Renames `dist/index.html` to `bundle.html`

The artefact requires nothing at runtime - hand it to the user directly.

### Step 5: Share with the user

Pass `bundle.html` back to the user as the artefact.

### Step 6: Test (optional)

Only test before sharing if the user has asked, or if the artefact has interactive logic that you don't want to ship broken. Use Playwright or open the file locally. Otherwise prefer shipping fast and iterating on feedback.

## Reference

- shadcn/ui components: https://ui.shadcn.com/docs/components
- Tailwind CSS v4 docs: https://tailwindcss.com/docs
- Companion skill for design patterns: `html-design-examples`
