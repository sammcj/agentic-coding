# React + React Router Integration Reference

Guidance for implementing the guided demo pattern in React applications with React Router. The vanilla JS patterns from `implementation.md` need adaptation for React's rendering model.

## Architecture decision: Context + Components

Use a React Context provider for the demo engine, not a vanilla JS overlay mounted outside the React tree. The primary reason is that `useNavigate()` (React Router) is only available inside the router's component tree. A vanilla overlay would need hacks to trigger route changes.

The engine is a hybrid: React manages state and lifecycle, but highlighting and scroll use direct DOM manipulation (classList, scrollIntoView) because the highlight target is any arbitrary element on any page.

### File structure

```
src/demo/
  DemoContext.tsx      # Engine: state, playback loop, typewriter, navigation
  DemoPanel.tsx        # Fixed bottom narrator bar with controls
  DemoInterstitial.tsx # Full-screen transition overlay
  DemoTrigger.tsx      # Start/stop button
  DemoHighlight.css    # Highlight + panel + interstitial styles
  demoScript.ts        # Step definitions and interstitial messages
```

### Provider placement

The DemoProvider must be inside the router (needs `useNavigate`) and wrapping the app:

```tsx
<BrowserRouter>
  <AppProvider>
    <DemoProvider>
      <App />
    </DemoProvider>
  </AppProvider>
</BrowserRouter>
```

The panel, interstitial, and trigger button render inside the app shell layout alongside the main content.

---

## Step definitions use routes, not section indices

In vanilla JS, steps reference `section: 0` (an integer index for show/hide). In React Router apps, steps reference `route: '/sites/SITE-001'` (the path to navigate to).

```typescript
interface DemoStep {
  route: string           // React Router path
  target: string | null   // CSS selector for element to highlight
  text: string            // Narrator text
  transition?: boolean    // Show interstitial overlay before navigating
  action?: string         // Optional UI mutation before highlighting
  actionTarget?: string   // Selector or ID for the action target
  delay?: number          // Override pause duration for this step (ms)
}
```

For demos with hardcoded mock data, use literal route strings. For demos against live data where IDs aren't known at script-authoring time, use a resolver function:

```typescript
interface DemoStep {
  route: string | (() => string)  // function for dynamic routes
  // ...
}
// e.g. { route: () => `/sites/${getFirstSite().id}`, ... }
```

When `route` is a function, call it at playback time to resolve the path. This keeps the step array declarative while supporting runtime data.

The `switchSection()` function from the vanilla pattern becomes a `navigate()` call followed by a render wait.

---

## Stale closures: the core React challenge

This is the single trickiest issue. The vanilla JS engine uses mutable variables (`let isPlaying = false`) that `setTimeout` callbacks close over. The value is always current because there is only one binding.

In React, `useState` creates a new value on each render. A `setTimeout` scheduled during render N captures render N's value. By the time it fires, the component may be on render N+5, but the callback still sees the old value.

### Solution: mirror every timer-relevant state value in a ref

```typescript
const [isPlaying, setIsPlaying] = useState(false)
const isPlayingRef = useRef(false)

// Keep ref in sync
useEffect(() => { isPlayingRef.current = isPlaying }, [isPlaying])
```

All timer callbacks (`setTimeout` in typewriter ticks, pause timers, interstitial cycling) must read from refs, not state:

```typescript
// WRONG: captures stale isPlaying from the render when setTimeout was scheduled
pauseTimerRef.current = setTimeout(() => {
  if (isPlaying) playStep(nextIdx)  // isPlaying is stale
}, PAUSE_MS)

// RIGHT: reads the current value at execution time
pauseTimerRef.current = setTimeout(() => {
  if (isPlayingRef.current) playStepRef.current(nextIdx)
}, PAUSE_MS / playbackSpeedRef.current)
```

Values that need refs: `isPlaying`, `isActive`, `currentStep`, `playbackSpeed`, `location.pathname`, `navigate` function.

### The playStep/executeStep circular dependency

In vanilla JS, `playStep` calls `executeStep`, and `executeStep`'s `onDone` callback calls `playStep`. This is fine with plain functions.

In React with `useCallback`, this creates a circular dependency that breaks memoisation (each depends on the other). Solution: store `playStep` in a ref that is updated every render.

```typescript
const playStepRef = useRef<(idx: number) => Promise<void>>(async () => {})

// Plain function (not useCallback) - recreated every render, which is intentional
async function playStepImpl(idx: number) {
  // ... engine logic using refs for all state reads
}

// Update ref every render so callbacks always call the latest version
playStepRef.current = playStepImpl

// In executeStep's onDone callback:
const onDone = () => {
  if (isPlayingRef.current) {
    pauseTimerRef.current = setTimeout(() => {
      playStepRef.current(stepIdx + 1)  // always calls latest playStep
    }, PAUSE_MS / playbackSpeedRef.current)
  }
}
```

The stable `useCallback` functions (`startDemo`, `stopDemo`, `togglePlayback`, `stepForward`, `stepBack`) call `playStepRef.current(...)` instead of `playStep(...)` directly.

---

## querySelector timing after route navigation

When `navigate('/new-route')` is called, React unmounts the old page and mounts the new one asynchronously. `querySelector` returns null until the new DOM is painted.

### Solution: poll with a short timeout after navigation

```typescript
async function playStep(idx: number) {
  const step = DEMO_SCRIPT[idx]

  if (locationRef.current !== step.route) {
    if (step.transition) await showInterstitial(step.route)
    navigateRef.current(step.route)

    // Wait for React to render the new page
    await new Promise<void>(resolve => {
      setTimeout(resolve, 200)  // 200ms covers most page renders
    })
  }

  await executeStep(idx)
}
```

For highlighting, use an additional polling loop to find the target element:

```typescript
function waitForElement(selector: string, maxAttempts = 10): Promise<Element | null> {
  return new Promise(resolve => {
    let attempts = 0
    function poll() {
      const el = document.querySelector(selector)
      if (el) { resolve(el); return }
      if (++attempts >= maxAttempts) { resolve(null); return }
      pollTimerRef.current = setTimeout(poll, 50)
    }
    poll()
  })
}
```

50ms interval, 10 attempts = 500ms maximum wait. This is invisible to the user since the typewriter hasn't started yet.

### Update locationRef after navigation

The React effect that syncs `locationRef` from `location.pathname` hasn't fired yet when `playStep` continues after navigation. Manually update the ref:

```typescript
navigateRef.current(step.route)
await new Promise<void>(resolve => {
  setTimeout(() => {
    locationRef.current = step.route  // manual sync
    resolve()
  }, 200)
})
```

---

## Interstitial promise cancellation

The interstitial overlay uses a Promise that resolves when the message cycling timer completes. If the user steps forward or backward during an interstitial, `clearAllTimers()` kills the cycling timer but the Promise never resolves. The overlay stays visible and `playStep` hangs on the await.

### Solution: dismiss interstitial at the start of every playStep call

```typescript
async function playStep(idx: number) {
  clearAllTimers()
  // Force-dismiss any stuck interstitial from a cancelled previous step
  setInterstitialVisible(false)
  setInterstitialText('')
  // ... proceed with step
}
```

This is a no-op when there is no active interstitial, and fixes the stuck overlay when there is.

---

## Step actions: the .click() bridge

The vanilla skill's `executeAction()` uses direct DOM manipulation (`classList.add`, `.click()`). In React, calling `.click()` on a React-rendered element triggers its synthetic event handler, which updates state through React's normal flow. This is the simplest and most reliable way to bridge from the demo engine's DOM world into React state.

For example, clicking a tab button fires its `onClick` handler which calls `setActiveTab()` through React's state management. No conflicts with re-rendering occur because the click triggers a state change, which triggers a re-render, which is exactly what you want.

Preferred approaches for triggering React state from the demo engine, in order:

1. **`.click()` on the trigger element** - simplest, works when there's a clickable element in the DOM. Reach for this first.
2. **Custom events** - dispatch a `CustomEvent` on `document` and have the component listen for it. Keeps the component in control of its own state. Use when there's no clickable trigger element.
3. **`useImperativeHandle` with ref** - exposes `open()`/`close()` methods. Cleanest React pattern but requires modifying the target component, which you want to avoid in a demo overlay.

---

## Highlight survival across re-renders

`classList.add('demo-highlight')` mutates the actual DOM node. React only overwrites DOM attributes it manages. During reconciliation, React uses `setAttribute('class', ...)` which will overwrite the class list and strip `demo-highlight` - but only if the component actually re-renders while highlighted.

In practice this rarely happens because highlight durations are short (a few seconds per step) and steps that highlight an element don't typically trigger state changes on that element's component. Navigation to a new route unmounts the old page entirely.

If a highlighted component does re-render frequently (e.g. from a timer or websocket), use a data attribute instead of a class:

```typescript
// Defensive alternative: survives React re-renders
el.setAttribute('data-demo-highlight', 'true')
// ...
el.removeAttribute('data-demo-highlight')
```

```css
[data-demo-highlight] {
  outline: 2px solid #4fc3f7 !important;
  outline-offset: 4px;
  /* ... same styles as .demo-highlight */
}
```

React doesn't manage arbitrary data attributes set via `setAttribute`, so they survive reconciliation.

---

## Data attributes on React components

The skill recommends `data-*` attributes for stable selectors. In React, custom components silently swallow unknown props unless they spread `...rest` onto a DOM element.

```tsx
// BROKEN: FilterBar doesn't forward data-demo to the DOM
<FilterBar data-demo="filter-bar" searchValue={search} ... />

// WORKS: wrapper div receives the attribute directly
<div data-demo="filter-bar">
  <FilterBar searchValue={search} ... />
</div>
```

Check whether each component forwards arbitrary props before adding `data-demo` directly. When in doubt, use a wrapper div. The wrapper adds no visual impact and guarantees the attribute reaches the DOM.

Tailwind utility classes (e.g. `.grid.grid-cols-3`) are stable across builds (unlike CSS Modules hashes), but complex selectors with escaped characters (`.sm\\:grid-cols-2`) are fragile and hard to read. Prefer `data-demo` attributes for any element the demo targets.

---

## Keyboard handler: skip form inputs

The vanilla skill's keyboard section doesn't mention this. React apps commonly have form inputs on demo-targeted pages. Without this guard, pressing Space while focused on a text input triggers play/pause instead of typing a space character.

```typescript
function handleKeyDown(e: KeyboardEvent) {
  if (!isActiveRef.current) return

  // Don't capture keys when user is interacting with form elements
  const tag = (e.target as HTMLElement).tagName
  if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return

  if (e.code === 'Space') { e.preventDefault(); togglePlayback() }
  else if (e.code === 'ArrowRight') { stepForward() }
  else if (e.code === 'ArrowLeft') { stepBack() }
  else if (e.code === 'KeyM') { toggleTTS() }
  else if (e.code === 'Escape') { stopDemo() }
}
```

---

## Typewriter in React: state vs DOM

The vanilla typewriter sets `element.textContent` directly. In React, use state for the displayed text and a ref for the timer:

```tsx
// In DemoContext
function typeText(text: string, onComplete?: () => void) {
  setCurrentText('')
  setShowCursor(true)
  let i = 0

  function tick() {
    if (i < text.length) {
      setCurrentText(text.substring(0, ++i))
      typeTimerRef.current = setTimeout(tick, TYPE_SPEED / playbackSpeedRef.current)
    } else {
      setCurrentText(text)
      setShowCursor(false)
      if (onComplete) onComplete()
    }
  }
  tick()
}

// In DemoPanel component
<div className="demo-narrator" role="status" aria-live="polite">
  {currentText}
  {showCursor && <span className="typing-cursor">|</span>}
</div>
```

This avoids innerHTML entirely. The cursor is a conditional React element, not an injected DOM node.

---

## Cleanup: local vs global state

Add an effect that cleans up if the provider unmounts while the demo is active (e.g. hot module reload during development, or a parent route change):

```typescript
useEffect(() => {
  return () => {
    clearAllTimers()
    clearHighlight()
    document.body.classList.remove('demo-active')
  }
}, [clearAllTimers, clearHighlight])
```

Without this, orphaned timers fire against stale state setters, causing React warnings in the console.

### What stopDemo needs to restore

`stopDemo()` resets demo engine state (timers, highlights, `demo-active` class) and typically navigates to `/`. Local component state (open panels, selected filters) resets naturally when the component unmounts on navigation.

The exception is global state held in React Context (e.g. an active role, selected theme, or user preference). If any demo action mutated global context state, `stopDemo` must explicitly restore it. If the demo doesn't navigate away on exit, local component state cleanup becomes the caller's responsibility too.

---

## Text-to-speech narration in React

The vanilla TTS pattern from `implementation.md` needs React-specific handling for state synchronisation and cleanup.

### Dual state + ref for isMuted

`isMuted` needs both a React state (for UI re-renders of the toggle icon) and a ref (for access inside timer callbacks without stale closures). Keep them in sync:

```typescript
const [isMuted, setIsMuted] = useState(true)  // off by default
const isMutedRef = useRef(true)

useEffect(() => { isMutedRef.current = isMuted }, [isMuted])
```

The `speakText` function reads from `isMutedRef` (not `isMuted` state) because it runs inside `setTimeout` callbacks:

```typescript
function speakText(text: string) {
  if (!('speechSynthesis' in window)) return
  speechSynthesis.cancel()
  if (isMutedRef.current) return

  const utterance = new SpeechSynthesisUtterance(text)
  utterance.rate = playbackSpeedRef.current
  if (selectedVoiceRef.current) utterance.voice = selectedVoiceRef.current
  speechSynthesis.speak(utterance)
}
```

### Voice initialisation in useEffect

```typescript
const selectedVoiceRef = useRef<SpeechSynthesisVoice | null>(null)

useEffect(() => {
  if (!('speechSynthesis' in window)) return

  function pickVoice() {
    const voices = speechSynthesis.getVoices()
    if (!voices.length) return

    // Adapt cascade to project locale
    const cascades: Array<(v: SpeechSynthesisVoice) => boolean> = [
      v => v.name.includes('Daniel') && v.lang === 'en-GB',
      v => v.name.includes('Google') && v.lang.startsWith('en-GB'),
      v => v.lang.startsWith('en-GB') && !/Grandma|Grandpa|Novelty/i.test(v.name),
      v => v.lang.startsWith('en-AU'),
      v => v.lang.startsWith('en'),
    ]

    for (const predicate of cascades) {
      const match = voices.find(predicate)
      if (match) { selectedVoiceRef.current = match; return }
    }
  }

  speechSynthesis.addEventListener('voiceschanged', pickVoice)
  pickVoice()
  return () => speechSynthesis.removeEventListener('voiceschanged', pickVoice)
}, [])
```

### Toggle with atomic state + ref update

Use the `setState(prev => ...)` pattern and update the ref inside the same callback:

```typescript
const toggleTTS = useCallback(() => {
  setIsMuted(prev => {
    const next = !prev
    isMutedRef.current = next
    if (next && 'speechSynthesis' in window) speechSynthesis.cancel()
    return next
  })
}, [])
```

### Cancellation in cleanup

Add `speechSynthesis.cancel()` to `clearAllTimers` and the provider's unmount effect:

```typescript
function clearAllTimers() {
  if (typeTimerRef.current) clearTimeout(typeTimerRef.current)
  if (pauseTimerRef.current) clearTimeout(pauseTimerRef.current)
  if (pollTimerRef.current) clearTimeout(pollTimerRef.current)
  if ('speechSynthesis' in window) speechSynthesis.cancel()
}

// In the cleanup useEffect:
useEffect(() => {
  return () => {
    clearAllTimers()
    clearHighlight()
    document.body.classList.remove('demo-active')
  }
}, [clearAllTimers, clearHighlight])
```

`clearAllTimers()` already cancels speech, so the unmount effect doesn't need a separate `speechSynthesis.cancel()` call.

### Preserving play state on manual step

`stepForward()` and `stepBack()` must NOT set `isPlaying` to false. They should only clear timers then play the target step. The existing `isPlayingRef` value determines whether the new step auto-types or shows instantly. Forcing pause on every manual step is a common bug that makes the play button show the wrong state.

```typescript
const stepForward = useCallback(() => {
  clearAllTimers()
  // Do NOT call setIsPlaying(false) here
  if (currentStepRef.current < DEMO_SCRIPT.length - 1) {
    playStepRef.current(currentStepRef.current + 1)
  }
}, [clearAllTimers])
```

### DemoPanel toggle button

```tsx
<button
  onClick={toggleTTS}
  title="Toggle narration (M)"
  style={{ opacity: isMuted ? 0.4 : 1, background: 'none', border: 'none', color: 'inherit', cursor: 'pointer', fontSize: '16px' }}
>
  {isMuted ? '\u{1F507}' : '\u{1F50A}'}
</button>
```

Place between the step navigation buttons and speed controls.

---

## Step countdown indicator in React

The vanilla countdown uses DOM node cloning to reset the CSS animation. In React, the cleaner approach is conditional rendering: mounting a fresh element restarts the animation automatically.

### State in DemoContext

```typescript
const [countdownActive, setCountdownActive] = useState(false)
const [countdownDuration, setCountdownDuration] = useState(0)
```

No refs needed for these - they drive UI rendering only and are never read inside timer callbacks.

### Starting the countdown

In the `onDone` callback (fired when typewriter text finishes), before setting the pause timer:

```typescript
const onDone = () => {
  if (isPlayingRef.current && stepIdx < DEMO_SCRIPT.length - 1) {
    const adjustedPause = (step.delay ?? PAUSE_MS) / playbackSpeedRef.current
    setCountdownActive(true)
    setCountdownDuration(adjustedPause)
    pauseTimerRef.current = setTimeout(() => {
      playStepRef.current(stepIdx + 1)
    }, adjustedPause)
  }
}
```

### Clearing the countdown

Add `setCountdownActive(false)` to `clearAllTimers()` (alongside the existing timer clears and `speechSynthesis.cancel()` from the TTS section). This single site handles all reset scenarios (stepping, pausing, stopping, exiting):

```typescript
// Add this line inside the existing clearAllTimers:
setCountdownActive(false)
```

### DemoPanel markup

Place directly below the step progress bar, above the narrator text:

```tsx
<div className="demo-step-countdown">
  {countdownActive && (
    <div
      className="demo-step-countdown-fill"
      style={{ animationDuration: `${countdownDuration}ms` }}
    />
  )}
</div>
```

The container is always rendered (prevents layout shift). The fill element is conditionally mounted. When `countdownActive` goes from `false` to `true`, React mounts a fresh DOM element, which starts the CSS animation from 0%. When it goes back to `false`, the element unmounts. This mount/unmount cycle resets the animation cleanly between steps - no need for key props, `requestAnimationFrame` two-phase tricks, or CSS transition hacks.

### CSS (same as vanilla)

```css
.demo-step-countdown {
  height: 2px;
  background: rgba(255, 255, 255, 0.06);
}

.demo-step-countdown-fill {
  height: 100%;
  background: rgba(79, 195, 247, 0.7);  /* use the app's accent colour */
  animation: demoCountdown linear forwards;
}

@keyframes demoCountdown {
  from { width: 0%; }
  to { width: 100%; }
}
```

### Edge cases handled by clearAllTimers

- **Pausing mid-countdown**: timers cleared, bar disappears. Resuming replays the step which restarts the countdown after text finishes.
- **Stepping while paused**: `clearAllTimers` resets the bar. The paused code path doesn't call `onDone`, so no new countdown starts.
- **Last step**: `onDone` only sets the countdown when `stepIdx < script.length - 1`, so no bar on the final step.
- **Speed change mid-countdown**: the current bar keeps its original duration. The new speed applies to the next step's countdown.

---

## Scroll padding target

The main SKILL.md gotchas mention `scroll-padding-bottom`. In React app layouts, the scroll container is typically `body` or `html`, not the `<main>` element. Set `scroll-padding-bottom` on the actual scroll container, and `padding-bottom` on `main` to push content above the narrator panel.

---

## React StrictMode

In development, React StrictMode double-invokes effects. The keyboard handler effect returns a cleanup function (removes the listener), so double-invocation is handled. The `startDemo` function should guard against double-start with `if (isActiveRef.current) return`.
