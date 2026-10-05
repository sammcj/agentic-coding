---
name: explain
description: Explain a concept, system or piece of code as a diagram-first terminal answer, or as an interactive HTML page.
disable-model-invocation: true
argument-hint: "[html] <topic>"
compatibility: claude-code
metadata:
  version: 2026-10-05
---

Arguments: `$ARGUMENTS`. If the first word is `html` use HTML mode, unless otherwise instructed use terminal mode. The rest is the topic. With no topic, explain what the conversation is currently about.

## Both modes

- Show the real mechanism: the actual components, data flow and state changes, with real names, shapes and numbers. A labelled box saying "processing" explains nothing.
- Picture first, prose second. Prose is short captions keyed to the picture.
- Captions follow Simplified Technical English: max 20 words per step, 25 per description, active voice, one idea per sentence, plain words with one meaning. Keep code and identifiers verbatim.
- For code in the current project, read it first and cite `path:line`.

## Terminal mode

1. Draw an ASCII diagram, at most 80 columns wide. Stack vertically rather than in one long row.
2. Follow it with numbered captions that use the diagram's labels.

## HTML mode

1. Create a task per step below, then work them to completion.
2. Load the `html-design-examples` skill for visual patterns, if available.
3. Write one self-contained page to `.explain/<kebab-slug>.html` in the working directory: inline CSS and JS, no build step. Reuse the slug when revising the same topic. In a git repo, append `.explain/` to `$(git rev-parse --git-path info/exclude)` if missing, so pages stay untracked without touching `.gitignore`.
4. Put the key picture in the first 1200x800 screen. Detail and depth go below it. Done when a reader gets the core idea without scrolling.
5. Draw diagrams as inline SVG so parts can highlight and animate. For a large flowchart or sequence, Mermaid from `https://cdn.jsdelivr.net/npm/mermaid@latest/dist/mermaid.esm.min.mjs` is fine.
6. For a process (pipeline, algorithm, protocol, request lifecycle), build a step-through: scenes driven by one step index, with prev/next buttons, arrow keys and play/pause. Each scene highlights what changed and shows a one-line caption. Load on the final, fully built scene so the first screen shows the whole picture. Done when buttons, arrow keys and play/pause all move the step index.
7. Add other controls (sliders, toggles, compare views) only where changing a value teaches something.
8. Support light and dark via `prefers-color-scheme`. Text meets WCAG AA contrast.
9. If a browser tool is available, screenshot the first 1200x800 screen in light and dark, and read the console. Fix clipped or overlapping text and any errors. With no browser tool, say the page was not visually checked.
10. Reply with the page path and a 2-3 line summary, leaving the HTML out of the reply.
