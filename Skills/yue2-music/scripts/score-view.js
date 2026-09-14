"use strict";
// Engrave each case's ABC with abcjs and highlight the notes the audio is currently playing.
// The recording owns time; the score only follows it (same approach as the YuE2 demo page).

function prepare(abc) {
  // abcjs counts a compressed multi-bar rest as one visual bar when wrapping voices, so expand
  // Z<n> into n bars; 5/16 notes need two tied glyphs. Engraving only; the audio is untouched.
  const tune = ABCJS.parseOnly(abc)[0];
  const replacements = [];
  for (const line of tune?.lines || []) {
    for (const staff of line.staff || []) {
      for (const voice of staff.voices) {
        for (const note of voice) {
          const source = abc.slice(note.startChar, note.endChar);
          if (note.pitches?.length === 1 && note.duration === 5 / 16) {
            const token = /^([A-Ga-g][,']*)10$/.exec(source);
            if (token) replacements.push([note.startChar, source.length, `${token[1]}8-${token[1]}2`]);
          }
          const count = note.rest?.text;
          if (note.rest?.type !== "multimeasure" || !Number.isSafeInteger(count) || count <= 1) continue;
          const token = /Z\d+(?=\s*$)/.exec(source);
          if (token && Number(token[0].slice(1)) === count) {
            replacements.push([note.startChar + token.index, token[0].length, Array(count).fill("Z").join("|")]);
          }
        }
      }
    }
  }
  for (const [start, length, replacement] of replacements.sort((a, b) => b[0] - a[0])) {
    abc = abc.slice(0, start) + replacement + abc.slice(start + length);
  }
  return abc;
}

function attach(frame) {
  const article = frame.closest("article");
  const source = article.querySelector(".abc-source");
  const audio = article.querySelector("audio");
  if (!source || typeof ABCJS === "undefined") return;
  let abc;
  try { abc = prepare(source.textContent); } catch (error) { abc = source.textContent; }
  const visual = ABCJS.renderAbc(frame, abc, { responsive: "resize", add_classes: true })[0];
  if (!visual || !audio) return;
  const timings = visual.setTiming(visual.getBpm(visual.metaText?.tempo), 0);
  let highlighted = [];
  let lastEvent = null;
  const paint = () => {
    const ms = audio.currentTime * 1000;
    let low = 0, high = timings.length;
    while (low < high) {
      const mid = (low + high) >>> 1;
      if (timings[mid].milliseconds <= ms) low = mid + 1; else high = mid;
    }
    const candidate = timings[low - 1];
    const event = ms > 0 && candidate?.type === "event" ? candidate : null;
    if (event === lastEvent) return;
    lastEvent = event;
    highlighted.forEach(node => node.classList.remove("playing-note"));
    highlighted = (event?.elements || []).flat().filter(Boolean);
    highlighted.forEach(node => node.classList.add("playing-note"));
    const target = highlighted[0];
    if (!target) return;
    const box = target.getBoundingClientRect(), view = frame.getBoundingClientRect();
    if (box.top < view.top + 20 || box.bottom > view.bottom - 20) {
      frame.scrollTop += box.top - view.top - 40;
    }
  };
  let raf = null;
  const tick = () => { paint(); raf = audio.paused ? null : requestAnimationFrame(tick); };
  audio.addEventListener("play", () => { if (raf === null) raf = requestAnimationFrame(tick); });
  audio.addEventListener("seeked", paint);
  audio.addEventListener("pause", paint);
}

document.querySelectorAll(".score").forEach(attach);
