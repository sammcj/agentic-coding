#!/usr/bin/env node
// Open a .bento.html deck in a headless Chromium browser, run window.bento.validate(), screenshot every slide in present mode.
import { spawn } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { basename, join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const HELP = `Usage: node render_check.mjs <deck.bento.html> [options]

Renders a Bento deck headlessly, prints validate() findings (info severity omitted), and saves one PNG per page.
Exit code 1 when validate() reports an error-severity finding, present mode does not open, or the deck fails to boot.

Options:
  --out <dir>        Screenshot directory (default: $TMPDIR/bento-render/<deck-name>)
  --browser <path>   Chromium-based browser binary (default: first of Brave, Chrome, Chromium found)
  --boot-timeout <s> Seconds to wait for window.bento (default: 40; the splash animation delays boot ~13s)
  --settle <ms>      Pause after each slide change before capture, lets entrance animations finish (default: 1500)
  --eval <js>        Evaluate an expression against the booted deck and print the JSON result,
                     e.g. --eval 'window.bento.measure({html:"Long heading", w:880, fontSize:82, lineHeight:1.06})'
  --no-shots         Run validate() (and --eval) only, skip present mode and screenshots
  -h, --help         Show this help

Needs Node 22+ (global fetch and WebSocket). No npm dependencies.`;

function fail(msg) {
  console.error(msg);
  process.exit(1);
}
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// Argument parsing
const args = process.argv.slice(2);
if (args.length === 0 || args.includes("-h") || args.includes("--help")) {
  console.log(HELP);
  process.exit(args.length === 0 ? 1 : 0);
}
const VALUE_OPTS = new Set(["--out", "--browser", "--boot-timeout", "--settle", "--eval"]);
const FLAG_OPTS = new Set(["--no-shots"]);
const opts = {};
const positional = [];
for (let i = 0; i < args.length; i++) {
  const a = args[i];
  if (VALUE_OPTS.has(a)) {
    const v = args[i + 1];
    if (v === undefined || v.startsWith("--")) fail(`${a} needs a value. See --help.`);
    opts[a] = v;
    i++;
  } else if (FLAG_OPTS.has(a)) {
    opts[a] = true;
  } else if (a.startsWith("--")) {
    fail(`Unknown option ${a}. See --help.`);
  } else {
    positional.push(a);
  }
}
if (positional.length !== 1) fail("Pass exactly one deck path. See --help.");
const deck = resolve(positional[0]);
if (!existsSync(deck)) fail(`Deck not found: ${deck}`);
const num = (name, fallback) => {
  const v = opts[name] === undefined ? fallback : Number(opts[name]);
  if (!Number.isFinite(v) || v < 0) fail(`${name} must be a non-negative number, got "${opts[name]}"`);
  return v;
};
const bootTimeout = num("--boot-timeout", 40) * 1000;
const settle = num("--settle", 1500);
const shots = !opts["--no-shots"];
const outDir = opts["--out"] || join(tmpdir(), "bento-render", basename(deck).replace(/\.bento\.html$/, ""));

const CANDIDATES = [
  "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  "/Applications/Chromium.app/Contents/MacOS/Chromium",
  "/usr/bin/brave-browser",
  "/usr/bin/google-chrome",
  "/usr/bin/chromium",
];
const browser = opts["--browser"] || CANDIDATES.find(existsSync);
if (!browser || !existsSync(browser)) fail(`Browser not found${browser ? `: ${browser}` : ""}; pass --browser <path>`);

// Launch. CDP rather than --screenshot: decks with ambient motion (ken-burns, dash-march) animate forever,
// so --virtual-time-budget never settles and the one-shot screenshot mode hangs.
// A throwaway profile per run: a shared one would carry state between decks and lock if two runs overlap.
const profile = mkdtempSync(join(tmpdir(), "bento-profile-"));
const proc = spawn(
  browser,
  [
    "--headless=new", "--disable-gpu", "--no-first-run",
    "--disable-crashpad", // the crash handler is a separate helper process that would outlive this run
    `--user-data-dir=${profile}`,
    "--remote-debugging-port=0", // let the OS pick a free port; read it back from DevToolsActivePort
    "--window-size=1280,720",
    pathToFileURL(deck).href,
  ],
  { stdio: "ignore" },
);
process.on("exit", () => {
  proc.kill();
  rmSync(profile, { recursive: true, force: true });
});
const onSpawnError = (e) => fail(`Could not launch browser ${browser}: ${e.message}`);
const onEarlyExit = (code) => fail(`Browser exited with code ${code} before connecting (a sandbox blocking the profile directory? run outside it)`);
proc.on("error", onSpawnError);
proc.on("exit", onEarlyExit);

// Connect
async function findTarget() {
  const portFile = join(profile, "DevToolsActivePort");
  const deadline = Date.now() + bootTimeout;
  while (Date.now() < deadline) {
    try {
      const port = readFileSync(portFile, "utf8").split("\n")[0].trim();
      const list = await (await fetch(`http://127.0.0.1:${port}/json`)).json();
      const page = list.find((t) => t.type === "page" && t.url.startsWith("file:"));
      if (page) return page.webSocketDebuggerUrl;
    } catch {}
    await sleep(250);
  }
  fail(`Browser did not expose the deck page within ${bootTimeout / 1000}s`);
}

const ws = new WebSocket(await findTarget());
await new Promise((r) => (ws.onopen = r));
proc.off("error", onSpawnError);
proc.off("exit", onEarlyExit);
ws.onclose = ws.onerror = () => fail("Browser connection closed mid-run");
let seq = 0;
const pending = new Map();
ws.onmessage = (ev) => {
  const msg = JSON.parse(ev.data);
  if (msg.id && pending.has(msg.id)) {
    pending.get(msg.id)(msg);
    pending.delete(msg.id);
  }
};
const cdp = (method, params = {}) =>
  new Promise((res, rej) => {
    const id = ++seq;
    pending.set(id, (m) => (m.error ? rej(new Error(`${method}: ${m.error.message}`)) : res(m.result)));
    ws.send(JSON.stringify({ id, method, params }));
  });
const evaluate = async (expression) => {
  const r = await cdp("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
  if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || "evaluate failed");
  return r.result.value;
};
await cdp("Page.enable");
await cdp("Runtime.enable");

// Boot: window.bento appears only after the splash animation.
const bootDeadline = Date.now() + bootTimeout;
while (!(await evaluate("Boolean(window.bento && window.bento.doc)"))) {
  if (Date.now() > bootDeadline) {
    const state = await evaluate("JSON.stringify({ready: document.readyState, bento: window.bento ? Object.keys(window.bento) : null, title: document.title, body: document.body.innerText.slice(0, 200)})");
    fail(`window.bento not ready after ${bootTimeout / 1000}s; is this a .bento.html file?\n${state}`);
  }
  await sleep(500);
}
await evaluate("document.fonts.ready.then(() => true)");
const api = await evaluate("Object.keys(window.bento)");

const info = await evaluate(`(() => {
  const d = window.bento.doc;
  return { title: d.title, slides: d.slides.length, pages: d.slides.filter(s => !s.stateOf).length,
    states: d.slides.filter(s => s.stateOf).map(s => s.id) };
})()`);
console.log(`Deck: ${info.title} | ${info.slides} slides (${info.pages} pages, ${info.states.length} state slides)`);

// Validate
let hasError = false;
if (api.includes("validate")) {
  const v = await evaluate("JSON.parse(JSON.stringify(window.bento.validate()))");
  const findings = (v.findings || []).filter((f) => f.severity !== "info");
  console.log(`validate(): ok=${v.ok} ${JSON.stringify(v.counts || {})}`);
  for (const f of findings) {
    console.log(`  [${f.severity}] ${f.code} ${f.slide ? `slide=${f.slide} ` : ""}${f.element ? `el=${f.element} ` : ""}${f.message}`);
  }
  hasError = findings.some((f) => f.severity === "error");
} else {
  console.log(`validate(): not in this runtime (window.bento has: ${api.join(", ")}). Download a fresh Bento_Slides.bento.html from https://bento.page/releases/slides/ and splice the document JSON into its #bento-doc block.`);
}

if (opts["--eval"]) {
  try {
    console.log(`eval: ${JSON.stringify(await evaluate(opts["--eval"]))}`);
  } catch (e) {
    fail(`--eval failed: ${e.message}`);
  }
}

// Present mode and screenshots
if (shots) {
  mkdirSync(outDir, { recursive: true });
  // The keyboard shortcut for present mode does not fire through CDP; click the Slideshow button instead.
  const findButton = `(() => {
    const el = [...document.querySelectorAll("button, [role=button]")].find(b => /slideshow|present/i.test(b.textContent + " " + (b.getAttribute("title") || "") + " " + (b.getAttribute("aria-label") || "")));
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0 ? { x: r.x + r.width / 2, y: r.y + r.height / 2 } : null;
  })()`;
  const btn = await evaluate(findButton);
  if (!btn) fail("Could not find a visible Slideshow button in the editor chrome");
  for (const type of ["mousePressed", "mouseReleased"]) {
    await cdp("Input.dispatchMouseEvent", { type, x: btn.x, y: btn.y, button: "left", clickCount: 1 });
  }
  await sleep(settle);
  // Present mode requests fullscreen on the stage, which is the one reliable marker that the click landed.
  if (!(await evaluate("Boolean(document.fullscreenElement)"))) fail("Present mode did not open after clicking Slideshow; the editor chrome may have changed");

  // Arrow keys skip state slides, so this walks the page count only.
  for (let i = 1; i <= info.pages; i++) {
    const { data } = await cdp("Page.captureScreenshot", { format: "png" });
    writeFileSync(join(outDir, `slide-${String(i).padStart(2, "0")}.png`), Buffer.from(data, "base64"));
    if (i < info.pages) {
      for (const type of ["keyDown", "keyUp"]) {
        await cdp("Input.dispatchKeyEvent", { type, key: "ArrowRight", code: "ArrowRight", windowsVirtualKeyCode: 39 });
      }
      await sleep(settle);
    }
  }
  console.log(`Screenshots: ${outDir}/slide-01.png .. slide-${String(info.pages).padStart(2, "0")}.png`);
  if (info.states.length) {
    console.log(`State slides not captured (arrow keys skip them): ${info.states.join(", ")}. Check each by clicking its link element in the editor.`);
  }
}

ws.onclose = null;
ws.close();
process.exit(hasError ? 1 : 0);
