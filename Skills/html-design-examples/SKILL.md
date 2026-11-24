---
name: html-design-examples
description: Reference gallery of polished single-file HTML artifacts demonstrating effective ways to communicate ideas through HTML. Use when the user wants to explain, showcase, demo, plan, review, or present an idea within an HTML file.
---

# HTML Design Examples

A library of self-contained `.html` files showing how a static HTML artifact can carry more signal than the same content as markdown. Use them as visual and structural references when building an HTML deliverable for a similar task.

## Why HTML, not markdown

The bottleneck is human attention, not what the agent can produce. A 500-line markdown plan goes unread; the same content as one HTML page with diagrams, tables and inline controls gets engaged with. HTML carries tables, SVG, CSS layout, scripts and spatial composition in a single file, opens in any browser, and shares as a URL rather than an attachment. The token and latency cost is real, and worth it for any artifact that needs to be read by a human.

Prefer HTML for human-facing, ephemeral artifacts (specs, plans, reports, writeups, prototypes, throwaway editors). Stay with markdown or source for things that need durable, line-by-line review in a repo (RFCs, ADRs, runbooks) - HTML diffs are noisy.

## How to use this skill

1. Pick the example that most closely matches the user's intent (catalogue below).
2. Read that file in full before writing your own. The reference's style, density, and structure are the point.
3. Match the shared conventions (see "Conventions").
4. Adapt to the user's real content. The examples use a fictional "Birchline" brand and fixture data - do not carry that across.
5. If the artifact is an editor or any interactive surface, end it with a "copy as JSON" or "copy as prompt" button so the user's work flows back into the agent loop.

## Resource catalogue

Files live in `resources/`. Open `resources/index.html` for the rendered gallery with thumbnails.

### Exploration & Planning
- `01-exploration-code-approaches.html` - side-by-side comparison of three implementation approaches with trade-offs called out inline.
- `02-exploration-visual-designs.html` - layout and palette options rendered live for visual comparison.
- `16-implementation-plan.html` - milestones on a timeline, data-flow diagram, inline mockups, risky code, risk table.

### Code Review & Understanding
- `03-code-review-pr.html` - annotated diff with margin notes, severity tags, jump links.
- `17-pr-writeup.html` - author-side PR description with motivation, before/after, file-by-file tour.
- `04-code-understanding.html` - unfamiliar package drawn as boxes and arrows with the hot path highlighted.

### Design
- `05-design-system.html` - colours, type scale, and spacing tokens rendered as copyable swatches.
- `06-component-variants.html` - every size, state, and intent of one component on a single contact sheet.

### Prototyping
- `07-prototype-animation.html` - a transition in isolation with sliders for duration and easing.
- `08-prototype-interaction.html` - four linked screens, enough fidelity to feel the interaction.

### Illustrations & Diagrams
- `10-svg-illustrations.html` - inline SVG figure sheet suitable for a blog post.
- `13-flowchart-diagram.html` - annotated flowchart with click-to-reveal step detail.
- For an animated diagram, see `21-scroll-walkthrough.html` (scroll-driven) or `22-looping-diagram.html` (always moving) under Research & Learning.

### Decks
- `09-slide-deck.html` - arrow-key navigable slides as one HTML file, no build step.

### Research & Learning
- `14-research-feature-explainer.html` - TL;DR, collapsible request-path steps, tabbed config snippets, FAQ.
- `15-research-concept-explainer.html` - interactive demo, comparison table, hover-linked glossary.
- `21-scroll-walkthrough.html` - monospaced technical explainer, light by default with a dark toggle, built around a pinned diagram that scroll drives (camera, dimming, step rail, live read-out). Also has a looping comparison with a phase scrubber, a prose-linked strip, draw-in charts and a canvas dropcap. Use it when a system has an order to walk through. About 16k tokens, so skip step 2 and read the `<style>` block, the HTML body and the `helpers` script block, then only the `/* ---------- name` blocks you need.
- `22-looping-diagram.html` - same style and themes, always animated with no scrolling. A simulated job queue plays on a loop with no visible restart (phase rail, pause, speed, draggable timeline, live counts), plus three small loops (cycle, fan-out, hit or miss). Use it when a system runs continuously or has many things in flight.

### Reports
- `11-status-report.html` - weekly status: what shipped, what slipped, small chart.
- `12-incident-report.html` - post-mortem with minute-by-minute timeline, log excerpts, follow-up checklist.

### Custom Editing Interfaces
- `18-editor-triage-board.html` - drag tickets across Now / Next / Later / Cut, then export the ordering as markdown.
- `19-editor-feature-flags.html` - grouped toggles with dependency warnings and a copy-diff button for changed keys.
- `20-editor-prompt-tuner.html` - editable template with highlighted variable slots; three sample inputs re-render live as you type.

## Conventions across all examples

- One `.html` file, opens directly in a browser. No build, no npm, no CDN scripts, no external stylesheets.
- CSS custom properties at `:root` for the colour palette and font stacks.
- Serif display headings paired with a sans-serif body is the recurring typographic pattern.
- Any interactivity is vanilla JS in a single `<script>` tag.
- Calm, editorial aesthetic: paper tones, restrained accent colour, generous whitespace (But not a narrow column of information. Use the available screen real estate wisely).
- `21-scroll-walkthrough.html` and `22-looping-diagram.html` are the deliberate exceptions to the type, palette and stylesheet rules above: mono throughout, light and dark themes from one set of tokens, one Google Fonts link each with a `ui-monospace` fallback. Take their style whole rather than mixing it with the paper look.
- Interactive surfaces export their state - a "copy as JSON" or "copy as prompt" button is the closing affordance.

## Aesthetic consistency

When the user has an existing project with its own design language, generate or reference a single design-system HTML file (see `05-design-system.html` for the shape) and use it as the style anchor for subsequent artifacts. Defer to the project's own brand and tokens rather than copying the gallery's editorial palette wholesale.

## Gotchas

- HTML diffs are noisy. If the artifact will live in a repo and be reviewed line-by-line over time, write markdown instead.
- An editor without an export button is half a tool. Always finish interactive artifacts with a way to get the result back into text.
- If the user wants an arrow-key slide deck specifically, the `html-slides` skill is purpose-built. If they want a configurable explorer with a copy-as-prompt button, the `playground` skill is purpose-built. This skill is for the broader case of any single-file HTML deliverable.
