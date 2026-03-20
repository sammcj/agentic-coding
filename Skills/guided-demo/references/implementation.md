# Implementation Reference

Copy-paste example code snippets for implementing the guided demo pattern. Adapt colours, selectors, timing etc. to suit the application.

## Narrator panel

```html
<div id="demoPanel" class="demo-panel">
  <div class="demo-progress"><div id="progressFill" class="demo-progress-fill"></div></div>
  <div style="padding:16px 24px;">
    <div id="narrator" class="demo-narrator"></div>
  </div>
  <div class="demo-controls">
    <button onclick="stepBack()">&laquo;</button>
    <button id="playBtn" onclick="togglePlayback()">&#9654;</button>
    <button onclick="stepForward()">&raquo;</button>
    <span style="margin-left:12px;font-size:12px;opacity:0.6;">
      <button onclick="setSpeed(0.5)" style="background:none;border:none;color:inherit;cursor:pointer;opacity:0.6;font-size:11px;">0.5x</button>
      <button onclick="setSpeed(1)" style="background:none;border:none;color:inherit;cursor:pointer;font-size:11px;">1x</button>
      <button onclick="setSpeed(2)" style="background:none;border:none;color:inherit;cursor:pointer;opacity:0.6;font-size:11px;">2x</button>
    </span>
    <span style="margin-left:auto;font-size:12px;opacity:0.6;" id="demoCounter">1 / 10</span>
  </div>
</div>
```

```css
.demo-panel {
  position: fixed; bottom: 0; left: 0; right: 0;
  z-index: 500;
  background: #1a1a2e; color: white;
  transform: translateY(100%);
  transition: transform .35s cubic-bezier(.4,0,.2,1);
  display: flex; flex-direction: column;
}
.demo-panel.open { transform: translateY(0); }
.demo-narrator {
  font-size: 18px; line-height: 1.65;
  color: rgba(255,255,255,0.9); min-height: 48px;
}
.demo-narrator .typing-cursor {
  display: inline;
  animation: blink .7s infinite;
  color: #4fc3f7;
}
@keyframes blink { 50% { opacity: 0; } }
.demo-progress { height: 3px; background: rgba(255,255,255,0.1); }
.demo-progress-fill { height: 100%; background: #4fc3f7; transition: width .3s ease; }
.demo-controls {
  display: flex; align-items: center; gap: 8px;
  padding: 6px 24px 14px;
  border-top: 1px solid rgba(255,255,255,0.1);
}
.demo-controls button {
  background: rgba(255,255,255,0.1); border: none;
  color: white; padding: 4px 12px; border-radius: 4px;
  cursor: pointer; font-size: 14px;
}
.demo-controls button:hover { background: rgba(255,255,255,0.2); }
```

Adapt: background colour to match the application's branding. The `#4fc3f7` accent works on dark backgrounds; swap for the app's accent colour.

---

## Highlight class

```css
.demo-highlight {
  outline: 2px solid #4fc3f7 !important;
  outline-offset: 4px;
  border-radius: 6px;
  animation: demoGlow 2s ease-in-out infinite;
  position: relative;
  z-index: 2;
}
@keyframes demoGlow {
  0%, 100% { box-shadow: 0 0 0 0 rgba(79,195,247,0); outline-color: #4fc3f7; }
  50% { box-shadow: 0 0 16px 4px rgba(79,195,247,0.15); outline-color: rgba(79,195,247,0.7); }
}
```

Why `outline` not `border`: outline does not affect the element's box model, so adding or removing the highlight does not cause layout shift.

---

## Typewriter function

```javascript
let typeTimer = null;
const TYPE_SPEED = 5;  // ms per character at 1x
const PAUSE_MS = 3000; // ms pause between steps at 1x
let playbackSpeed = 1;

function typeText(text, element, onComplete) {
  element.innerHTML = '';
  let i = 0;

  function tick() {
    if (i < text.length) {
      const span = document.createElement('span');
      span.textContent = text.substring(0, ++i);
      element.innerHTML = '';
      element.appendChild(span);
      const cursor = document.createElement('span');
      cursor.className = 'typing-cursor';
      cursor.textContent = '|';
      element.appendChild(cursor);
      typeTimer = setTimeout(tick, TYPE_SPEED / playbackSpeed);
    } else {
      element.textContent = text;
      if (onComplete) onComplete();
    }
  }

  tick();
}
```

Uses `textContent` (not `innerHTML`) for the narration text to prevent injection. The `innerHTML = ''` clearing is intentional and safe (no user content). The timer reference is stored so it can be cancelled on pause, step, or stop.

```javascript
function setSpeed(s) {
  playbackSpeed = s;
  document.querySelectorAll('.demo-controls span button').forEach(btn => {
    btn.style.opacity = parseFloat(btn.textContent) === s ? '1' : '0.6';
  });
}
```

---

## Playback loop

```javascript
let isActive = false;
let isPlaying = false;
let currentStep = 0;
let currentSection = 0;
let pauseTimer = null;
let currentHighlight = null;

function startDemo() {
  if (isActive) return;
  isActive = true;
  isPlaying = true;
  currentStep = 0;
  document.getElementById('demoPanel').classList.add('open');
  updatePlayButton();
  // Navigate to first section
  switchSection(0);
  playStep(0);
}

function playStep(idx) {
  currentStep = idx;
  const step = DEMO_SCRIPT[idx];
  updateProgress();

  // Section change
  if (step.section !== currentSection) {
    if (step.transition) {
      showInterstitial(step.section, () => {
        switchSection(step.section);
        executeStep(step);
      });
      return;
    }
    switchSection(step.section);
  }

  executeStep(step);
}

function executeStep(step) {
  // Run action before highlighting
  if (step.action) {
    executeAction(step.action, step.actionTarget);
  }

  // Highlight target
  clearHighlight();
  if (step.target) {
    const el = document.querySelector(step.target);
    if (el) {
      el.classList.add('demo-highlight');
      currentHighlight = el;
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }

  // Narrate
  const narrator = document.getElementById('narrator');
  const onDone = () => {
    if (isPlaying && currentStep < DEMO_SCRIPT.length - 1) {
      pauseTimer = setTimeout(() => {
        if (isPlaying) playStep(currentStep + 1);
      }, PAUSE_MS / playbackSpeed);
    }
  };

  if (isPlaying) {
    typeText(step.text, narrator, onDone);
  } else {
    narrator.textContent = step.text;
  }
}

function switchSection(idx) {
  currentSection = idx;
  // Replace this with your app's navigation logic:
  // e.g. show/hide tab panels, call router.push(), set slide index
  document.querySelectorAll('.section').forEach((s, i) => {
    s.style.display = i === idx ? 'block' : 'none';
  });
}
```

The `switchSection()` function is the main integration point. Replace its body with whatever navigation the application uses (tab switching, route changes, scroll-to-section, slide index).

---

## Transition interstitials

```html
<div class="demo-interstitial" id="demoInterstitial">
  <div class="demo-interstitial-text" id="interstitialText">Processing...</div>
</div>
```

```css
.demo-interstitial {
  position: fixed; inset: 0; z-index: 490;
  background: rgba(0,0,0,0.85);
  display: flex; align-items: center; justify-content: center;
  flex-direction: column; gap: 16px;
  opacity: 0; visibility: hidden;
  transition: opacity .3s, visibility .3s;
}
.demo-interstitial.visible { opacity: 1; visibility: visible; }
.demo-interstitial-text {
  font-size: 15px; color: rgba(255,255,255,0.7);
  font-weight: 500; letter-spacing: .01em;
}
```

```javascript
function showInterstitial(sectionIdx, onComplete) {
  const overlay = document.getElementById('demoInterstitial');
  const textEl = document.getElementById('interstitialText');

  // Define messages per section
  const messages = [
    [],
    ['Analysing data...', 'Running calculations...'],
    ['Generating recommendations...', 'Scoring confidence...'],
    ['Preparing summary...', 'Compiling results...']
  ];
  const msgs = messages[sectionIdx] || ['Processing...'];

  overlay.classList.add('visible');
  let i = 0;

  function next() {
    if (i < msgs.length) {
      textEl.textContent = msgs[i++];
      setTimeout(next, 1200);
    } else {
      overlay.classList.remove('visible');
      onComplete();
    }
  }
  next();
}
```

Adapt: interstitial messages should reflect what the application is "doing" between sections. Brand the overlay with a logo or icon if appropriate.

---

## Step actions

```javascript
function executeAction(action, target) {
  if (action === 'expand') {
    document.getElementById(target).classList.add('open');
  }
  if (action === 'collapse') {
    document.getElementById(target).classList.remove('open');
  }
  if (action === 'collapseAll') {
    document.querySelectorAll('.' + target + '.open').forEach(el => el.classList.remove('open'));
  }
  if (action === 'click') {
    document.getElementById(target).click();
  }
  if (action === 'expandOne') {
    // Accordion: close all siblings, open target
    document.querySelectorAll('.' + target.split(':')[0] + '.open').forEach(el => el.classList.remove('open'));
    document.getElementById(target.split(':')[1]).classList.add('open');
  }
  if (action === 'call') {
    // Trigger a named function, e.g. actionTarget: 'requestBriefing'
    if (typeof window[target] === 'function') window[target]();
  }
  if (action === 'addClass') {
    document.body.classList.add(target);
  }
  if (action === 'removeClass') {
    document.body.classList.remove(target);
  }
  // Add more as needed - one if block per action type
}
```

Actions run before highlighting because the target element might be inside a collapsed panel. The panel must be open before `querySelector` can find and scroll to the element.

---

## Keyboard controls

```javascript
document.addEventListener('keydown', (e) => {
  if (!isActive) return;

  if (e.code === 'Space') {
    e.preventDefault();
    togglePlayback();
  } else if (e.code === 'ArrowRight') {
    stepForward();
  } else if (e.code === 'ArrowLeft') {
    stepBack();
  } else if (e.code === 'Escape') {
    stopDemo();
  }
});

function togglePlayback() {
  if (isPlaying) {
    isPlaying = false;
    clearTimeout(typeTimer);
    clearTimeout(pauseTimer);
  } else {
    isPlaying = true;
    playStep(currentStep);
  }
  updatePlayButton();
}

function stepForward() {
  clearTimeout(typeTimer);
  clearTimeout(pauseTimer);
  isPlaying = false;
  updatePlayButton();
  if (currentStep < DEMO_SCRIPT.length - 1) playStep(currentStep + 1);
}

function stepBack() {
  clearTimeout(typeTimer);
  clearTimeout(pauseTimer);
  isPlaying = false;
  updatePlayButton();
  if (currentStep > 0) playStep(currentStep - 1);
}

function updatePlayButton() {
  document.getElementById('playBtn').innerHTML = isPlaying ? '&#9646;&#9646;' : '&#9654;';
}
```

The `isActive` gate prevents keyboard capture when the demo is not running.

---

## Progress bar

```javascript
function updateProgress() {
  const pct = ((currentStep + 1) / DEMO_SCRIPT.length * 100);
  document.getElementById('progressFill').style.width = pct + '%';
  document.getElementById('demoCounter').textContent =
    (currentStep + 1) + ' / ' + DEMO_SCRIPT.length;
}
```

---

## Cleanup

```javascript
function stopDemo() {
  isActive = false;
  isPlaying = false;
  clearTimeout(typeTimer);
  clearTimeout(pauseTimer);
  document.getElementById('demoPanel').classList.remove('open');
  clearHighlight();
  document.getElementById('narrator').textContent = '';
  // Reset any UI state modified by actions during the demo
  document.querySelectorAll('.open').forEach(el => {
    // Only close elements that the demo opened - scope this selector
    // to your app's collapsible class names
  });
}

function clearHighlight() {
  if (currentHighlight) {
    currentHighlight.classList.remove('demo-highlight');
    currentHighlight = null;
  }
  document.querySelectorAll('.demo-highlight').forEach(el =>
    el.classList.remove('demo-highlight')
  );
}
```

Cleanup must reset every piece of state the demo touched. Scope the `.open` cleanup to the application's specific collapsible classes to avoid accidentally closing unrelated UI.

---

## Flow diagram

```mermaid
flowchart TD
    Start([User clicks Play]) --> Init[Open narrator panel\nReset to step 0]
    Init --> PlayStep

    PlayStep[playStep idx] --> SectionCheck{Section changed?}

    SectionCheck -- No --> Execute
    SectionCheck -- Yes --> TransCheck{Has transition?}

    TransCheck -- Yes --> Interstitial[Show overlay\nCycle status messages]
    TransCheck -- No --> SwitchSection[Switch visible content]

    Interstitial --> SwitchSection
    SwitchSection --> Execute

    Execute[executeStep] --> RunAction{Has action?}
    RunAction -- Yes --> DoAction[Run UI mutation]
    RunAction -- No --> Highlight
    DoAction --> Highlight

    Highlight[Add highlight class to target\nscrollIntoView] --> TypeCheck{Auto-playing?}

    TypeCheck -- Yes --> Typewriter[Type text char by char]
    TypeCheck -- No --> Instant[Show full text]

    Typewriter --> Pause[Wait pause duration / speed]
    Instant --> WaitInput([Wait for input])

    Pause --> LastCheck{Last step?}
    LastCheck -- No --> PlayStep
    LastCheck -- Yes --> Complete([Done])

    WaitInput -- Space --> PlayStep
    WaitInput -- Arrow keys --> PlayStep
    WaitInput -- Escape --> Cleanup([Reset all state])
```

---

## Print styles

```css
@media print {
  .demo-panel, .demo-interstitial { display: none !important; }
}
```

## Accessibility

```html
<div id="narrator" class="demo-narrator" role="status" aria-live="polite"></div>
```

Add `role="status"` and `aria-live="polite"` to the narrator element so screen readers announce the narration text as it changes.
