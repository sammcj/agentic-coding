// Records a scripted browser walkthrough as screencast frames, with a visible cursor and a scene timing log.
import { mkdirSync, writeFileSync } from "node:fs";
import { writeFile } from "node:fs/promises";
import { dirname, relative } from "node:path";
import { chromium } from "playwright";

// Headless capture has no mouse pointer; this draws one that follows real mouse events.
function cursorOverlay(hideSelectors) {
  const install = () => {
    const style = document.createElement("style");
    style.textContent = `
      ${hideSelectors.length ? `${hideSelectors.join(", ")} { visibility: hidden !important; }` : ""}
      #__cursor { position: fixed; left: -50px; top: -50px; width: 22px; height: 22px; border-radius: 50%;
        background: rgba(17, 24, 39, 0.25); border: 2px solid rgba(17, 24, 39, 0.8); pointer-events: none;
        z-index: 2147483647; transform: translate(-50%, -50%); transition: transform 120ms ease; }
      #__cursor.down { transform: translate(-50%, -50%) scale(0.6); }`;
    document.head.append(style);
    const c = document.createElement("div");
    c.id = "__cursor";
    document.body.append(c);
    const at = (e) => {
      c.style.left = `${e.clientX}px`;
      c.style.top = `${e.clientY}px`;
    };
    document.addEventListener("mousemove", at, true);
    document.addEventListener("mousedown", () => c.classList.add("down"), true);
    document.addEventListener("mouseup", () => c.classList.remove("down"), true);
  };
  if (document.body) install();
  else document.addEventListener("DOMContentLoaded", install);
}

// Playwright's own recordVideo encodes VP8 at ~1 Mbps, which smears small UI text. Chromium's screencast
// hands over each repainted frame as a JPEG instead, so the only lossy step left is the final encode.
async function startScreencast(page, dir, maxWidth, maxHeight) {
  mkdirSync(dir, { recursive: true });
  const cdp = await page.context().newCDPSession(page);
  const frames = [];
  const writes = [];
  cdp.on("Page.screencastFrame", ({ data, metadata, sessionId }) => {
    cdp.send("Page.screencastFrameAck", { sessionId }).catch(() => {});
    const file = `${dir}/${String(frames.length).padStart(6, "0")}.jpg`;
    frames.push({ file, ts: metadata.timestamp });
    writes.push(writeFile(file, Buffer.from(data, "base64")));
  });
  // q95: indistinguishable from PNG once x264 has had its turn, at a fraction of the capture cost.
  await cdp.send("Page.startScreencast", { format: "jpeg", quality: 95, maxWidth, maxHeight, everyNthFrame: 1 });
  return async () => {
    await cdp.send("Page.stopScreencast").catch(() => {});
    await Promise.all(writes);
    return frames;
  };
}

// Frames arrive only when the page repaints, so each one is held until the next.
// Paths are relative to the concat file (ffmpeg resolves them that way), so the out dir can be moved.
function writeConcat(path, frames, endTs) {
  const rel = (f) => relative(dirname(path), f.file);
  const lines = ["ffconcat version 1.0"];
  frames.forEach((f, i) => {
    const next = i + 1 < frames.length ? frames[i + 1].ts : endTs;
    lines.push(`file '${rel(f)}'`, `duration ${Math.max(0.001, next - f.ts).toFixed(4)}`);
  });
  // Without a repeat the demuxer drops the last duration; with one it plays it twice. encode.sh cuts at "end".
  lines.push(`file '${rel(frames.at(-1))}'`);
  writeFileSync(path, `${lines.join("\n")}\n`);
}

export async function record({ outDir, width = 1920, height = 1080, scale = 2, hide = [], permissions = [], run }) {
  // The screencast ignores Playwright's emulated deviceScaleFactor and sends CSS-pixel frames. A real device
  // scale from the launch flag, with the window as the viewport, gets full-density frames over the same layout.
  const browser = await chromium.launch({
    args: [`--force-device-scale-factor=${scale}`, `--window-size=${width},${height}`],
  });
  const context = await browser.newContext({ viewport: null, permissions });
  await context.addInitScript(cursorOverlay, hide);
  const page = await context.newPage();
  const stop = await startScreencast(page, `${outDir}/frames`, width * scale, height * scale);
  const marks = [];
  let pos = { x: width / 2, y: height / 2 };

  const wait = (ms) => page.waitForTimeout(ms);
  const loc = (target) => (typeof target === "string" ? page.locator(target).first() : target);
  const h = {
    page,
    wait,
    // Marks where a narrated section starts; encode.sh turns these into the timing table.
    scene: (name) => marks.push({ name, at: Date.now() / 1000 }),
    async moveTo(target, { steps = 30, dx = 0, dy = 0 } = {}) {
      let x, y;
      if (typeof target === "object" && "x" in target && "y" in target) ({ x, y } = target);
      else {
        const l = loc(target);
        await l.scrollIntoViewIfNeeded();
        const b = await l.boundingBox();
        x = b.x + b.width / 2 + dx;
        y = b.y + b.height / 2 + dy;
      }
      await page.mouse.move(x, y, { steps });
      pos = { x, y };
    },
    async click(target, opts) {
      await h.moveTo(target, opts);
      await wait(250); // a beat on the target so the viewer sees what is about to be clicked
      await page.mouse.down();
      await wait(90);
      await page.mouse.up();
    },
    async type(target, text, { delay = 120 } = {}) {
      await h.click(target);
      await page.keyboard.type(text, { delay });
    },
    // Wheel in small steps so the scroll reads as smooth on video.
    async scroll(dy, { step = 40, ms = 16 } = {}) {
      for (let done = 0; Math.abs(done) < Math.abs(dy); done += Math.sign(dy) * step) {
        await page.mouse.wheel(0, Math.sign(dy) * step);
        await wait(ms);
      }
    },
    get pos() {
      return pos;
    },
  };

  let frames = [];
  try {
    await run(h);
    h.scene("end");
  } finally {
    frames = await stop();
    await context.close();
    await browser.close();
  }
  if (!frames.length) throw new Error("screencast produced no frames");
  const t0 = frames[0].ts;
  const endTs = marks.at(-1)?.at ?? frames.at(-1).ts;
  writeConcat(`${outDir}/frames.ffconcat`, frames, endTs);
  const scenes = marks.map((m) => ({ name: m.name, start: Math.max(0, m.at - t0) }));
  const fps = frames.length / (endTs - t0);
  writeFileSync(
    `${outDir}/scenes.json`,
    JSON.stringify({ frames: "frames.ffconcat", width: width * scale, height: height * scale, scenes }, null, 2),
  );
  return { scenes, frames: frames.length, fps };
}
