---
name: guided-demo
description: >
  A pattern for adding self-narrating (typed out) guided walkthrough to any HTML/web application.
  Use this skill whenever the user wants to add a guided demo, auto-narration, typewriter walkthrough,
  self-presenting mode, automated tour, auto-play demo, self-running presentation, presentation mode,
  or step-by-step tour to an HTML page, web app, prototype, slide deck, dashboard, or data story.
---

# Guided Demo Pattern

Add a self-narrating walkthrough to any HTML/web application. A declarative step array drives a `setTimeout` loop that toggles CSS classes on DOM elements and writes text character-by-character into a fixed panel. The engine overlays the existing page without modifying its code. When the demo stops, all state resets.

About 100 lines of JS and 30 lines of CSS for the core. Interstitials, speed controls, keyboard shortcuts, and progress bar are optional layering.

## Before implementing

Ask the user these questions (skip any already answered in conversation):

1. **What are the sections?** Tabs, routes, scroll positions, slide indices? Determines how section switching works.
2. **Framework?** Vanilla HTML works directly. React/Vue/Svelte need the engine as a conditional overlay component, and `querySelector` must run after render.
3. **Presenter talking over it, or self-narrating?** Talking over: shorter text, longer pauses. Self-narrating: detailed text, moderate pauses.
4. **Interactive elements to trigger?** Map to step actions. Confirm CSS selectors are stable (not framework-generated hashes).
5. **Offline requirement?** Keep everything in one file if so. No CDN dependencies without fallbacks.
6. **How many steps?** Under 15 for a pitch, 20-30 for a detailed walkthrough. Over 40 loses attention.
7. **Touch device support needed?** Most guided demos target desktop/laptop presentation contexts. The narrator panel has on-screen prev/play/next buttons that work on touch, but swipe gestures or mobile-specific layout are rarely needed.

## Implementation

Read `references/implementation.md` for all code snippets (vanilla JS / static HTML). If the target application uses React with React Router, also read `references/react-integration.md` for React-specific patterns covering stale closures, route navigation timing, and component architecture. For other SPA frameworks (Vue, Svelte, etc.), the same concepts apply (poll for elements after route change, store timer-relevant state outside the reactivity system) but the implementation details differ.

The four required pieces are:

1. **Narrator panel** - fixed-position bar with text container and progress bar
2. **Highlight class** - `outline` (not `border`) with animated glow, no layout shift
3. **Typewriter function** - recursive `setTimeout`, narration text set via `textContent` (never set user-authored narration via `innerHTML`), blinking cursor via CSS. The `innerHTML = ''` clearing before each tick is intentional and safe (no user content involved)
4. **Playback loop** - `playStep(idx)` that switches sections, runs actions, highlights, types, and auto-advances

### Step array

The single source of truth. Each step is a plain object:

```javascript
const DEMO_SCRIPT = [
  { section: 0, target: '.card', text: "Narration text." },
  { section: 1, target: null, text: "Transition.", transition: true },
  { section: 1, target: '#el', text: "Detail.", action: 'open', actionTarget: 'panel-id' },
];
```

Properties: `section` (which view), `target` (CSS selector or null), `text` (narrator copy), `transition` (show interstitial), `action`/`actionTarget` (trigger UI change).

### Timing defaults

| Constant | Default | When to adjust |
| --- | --- | --- |
| TYPE_SPEED | 5ms/char | 3ms for long text, 15ms for dramatic short statements |
| PAUSE_MS | 3000ms | 4-5s if audience reads rather than listens |
| Speed range | 0.5x-2x | Both constants divided by multiplier |

### Writing narrator copy

The typewriter effect means each word lands individually, so writing style matters:

- Short declarative sentences. Each step should make exactly one point.
- Conversational tone, present tense. Address the audience directly.
- Describe what the element means, not what the UI shows: "This column quantifies the cost impact" not "The cost is shown in this column".
- No jargon the audience wouldn't know. Match terminology to the domain, not the implementation.
- Under 30 words per step for presenter-led demos, up to 50 for self-narrating.

### Keyboard controls

Gate all keyboard capture behind an `isActive` flag so it does not interfere with normal page interaction. Space = play/pause, arrows = step, Escape = exit and reset.

### Optional: transition interstitials

Full-screen overlay with cycling status messages between sections. Simulates processing time. Define messages per section in a 2D array. Fade each message, then dismiss overlay via callback.

### Optional: step actions

String-matched in `executeStep()`. Actions run before highlighting because elements inside collapsed panels can't be found by `querySelector` until the panel is open. Adding a new action is one `if` block. Keep it simple. Common patterns beyond expand/collapse: `expandOne` (open one panel, close all siblings - accordion style), `call` (trigger a named function like `requestBriefing()`), `addClass`/`removeClass` (toggle a CSS class on `document.body` for global state changes).

## Gotchas

These are the failure points that come up repeatedly:

- **Layout shift**: Use `outline` not `border` for highlighting. Outline does not affect box model.
- **Hidden elements**: If target is inside a collapsed container, the action must open it first. This is why actions execute before highlighting.
- **Dynamic selectors**: Framework-generated class names (`.css-1a2b3c`) break between builds. Use `data-*` attributes or IDs.
- **Scroll conflicts**: `scrollIntoView({ block: 'center' })` conflicts with fixed headers/panels. Set `scroll-padding-bottom` on the scroll container to account for the narrator panel height.
- **Z-index**: Narrator panel at 500+, interstitials at 490, highlighted elements at 2+. Check for conflicts with existing modals or dropdowns.
- **Cleanup on exit**: Reset every piece of state the demo touched: close opened panels, remove highlights, clear timers. Missing cleanup leaves confusing UI state.
- **Form inputs**: If the page has text inputs, textareas, or selects, the keyboard handler must skip them. Otherwise pressing Space in a text field triggers play/pause instead of typing. Check `e.target.tagName` and bail out for `INPUT`, `TEXTAREA`, `SELECT`.
- **ES modules**: If using `<script type="module">`, all demo functions called from `onclick` must be on `window.*`.
- **Print**: Hide demo panel and interstitial in `@media print`.
- **Accessibility**: Narrator panel should have `role="status"` and `aria-live="polite"`. Highlight outlines must meet contrast requirements.

## Applicability

Works for: prototypes, PoCs, HTML slide decks, data storytelling dashboards, product demos, workshop facilitation, investor pitches, onboarding walkthroughs.

Does not replace: user testing tools, screen recorders, production onboarding tours (use a tour library with persistence and analytics for those).

For framework apps, mount the demo engine as a conditional overlay component and pass the script array as a prop. For single-file demos, inline everything for offline/USB-stick distribution.
