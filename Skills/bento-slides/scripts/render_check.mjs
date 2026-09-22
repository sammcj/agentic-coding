#!/usr/bin/env node
// Open a .bento.html deck in a headless Chromium browser, run window.bento.validate(), screenshot every slide in present mode.
import { spawn } from "node:child_process";
import { copyFileSync, existsSync, mkdirSync, mkdtempSync, readdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { basename, join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const HELP = `Usage: node render_check.mjs <deck.bento.html> [options]

Renders a Bento deck headlessly, prints validate() findings (info severity omitted, except collab-secrets-present,
font-not-embedded and past-margin), runs the skill's own checks (type floor, coverage, typefaces, speaker notes,
double page numbers, motion, runtime version), and saves one PNG per page.
Exit code 1 when validate() reports an error-severity finding, --doc drops a key, present mode does not open, or the deck fails to boot.

Options:
  --out <dir>        Screenshot directory (default: $TMPDIR/bento-render/<deck-name>)
  --browser <path>   Chromium-based browser binary (default: first of Brave, Chrome, Chromium found)
  --boot-timeout <s> Seconds to wait for window.bento (default: 40; the splash animation delays boot ~13s)
  --settle <ms>      Pause after each slide change before capture, lets entrance animations finish (default: 1500)
  --doc <json>       Load this document (full or compact JSON) into the booted deck via window.bento.loadDoc()
                     before validating; prints the load report (dropped keys, fields expanded, boxes fitted)
  --write <path>     Write the loaded, fully expanded document back into the deck's #bento-doc block at <path>
                     (may equal the deck path). Only meaningful with --doc. Strips collab/docId when the input had none,
                     always drops collab.sync (a stale CRDT stamp resurrects deleted elements on the next open), and
                     keeps the previous file as <path>.bak.
  --eval <js>        Evaluate an expression against the booted deck and print the JSON result,
                     e.g. --eval 'window.bento.measure({html:"Long heading", w:880, fontSize:82, fontFamily:"Fraunces"})'
  --no-shots         Run validate() (and --eval) only, skip present mode and screenshots
  --min-font <px>    Warn on text, code or table fontSize below this (default: 14; decks are shown downscaled over video calls)
  --min-cover <0-1>  Warn when a slide's content box covers less of the canvas height than this (default: 0.55).
                     Full-bleed backdrops and edge chrome (footers, page numbers, logos) are not content; slides with
                     two or fewer content elements are treated as covers/dividers and skipped
  --margin <px>      Side margin for validate()'s past-margin check (default: the runtime's 96)
  --motion           The user asked for animation: skip the motion-in-static-deck warning (fx, loops, transitions
                     other than none/fade)
  --online           Let the browser reach the network. Off by default: a shared deck (collab.on) would otherwise join
                     its live room on boot and validate() would report the owner's open tab, not the file
  -h, --help         Show this help

Compact JSON (see the skill) is accepted only by loadDoc, never by the on-disk block: author compact, then
--doc doc.json --write deck.bento.html expands it through the real runtime and writes the full document.

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
const VALUE_OPTS = new Set(["--out", "--browser", "--boot-timeout", "--settle", "--eval", "--doc", "--write", "--min-font", "--min-cover", "--margin"]);
const FLAG_OPTS = new Set(["--no-shots", "--online", "--motion"]);
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
const minFont = num("--min-font", 14);
const minCover = num("--min-cover", 0.55);
const margin = opts["--margin"] === undefined ? undefined : num("--margin", 96);
if (minCover > 1) fail("--min-cover is a fraction of canvas height, 0 to 1");
const docPath = opts["--doc"] && resolve(opts["--doc"]);
if (docPath && !existsSync(docPath)) fail(`Document not found: ${docPath}`);
if (opts["--write"] && !docPath) fail("--write needs --doc. See --help.");
const writePath = opts["--write"] && resolve(opts["--write"]);
if (docPath) {
  // Refuse a "bento/enc" envelope, since plain JSON written over it destroys the ciphertext.
  const raw = readFileSync(docPath, "utf8");
  let head;
  try { head = JSON.parse(raw); } catch (e) { fail(`--doc is not valid JSON: ${e.message}`); }
  if (head?.format === "bento/enc") fail("--doc is an encrypted envelope; open it with its password in the app instead");
}
const DOC_BLOCK = /(<script type="application\/bento\+json" id="bento-doc">)([\s\S]*?)(<\/script>)/;
const deckBlock = readFileSync(deck, "utf8").match(DOC_BLOCK);
if (!deckBlock) fail("No #bento-doc block in the deck; is this a .bento.html file?");
if (/"format"\s*:\s*"bento\/enc"/.test(deckBlock[2])) fail("This deck is password-encrypted; the app must open it with its password before any edit");
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
    // No DNS means no relay, no update check and no cross-tab state: the render reflects the file alone.
    ...(opts["--online"] ? [] : ["--host-resolver-rules=MAP * ~NOTFOUND"]),
    pathToFileURL(deck).href,
  ],
  { stdio: "ignore" },
);
process.on("exit", () => {
  proc.kill();
  // The browser may still be flushing the profile as it dies; a leftover temp dir is not a failed run.
  try { rmSync(profile, { recursive: true, force: true, maxRetries: 3 }); } catch {}
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
// --window-size is not honoured reliably by headless=new (captures came out 800x541); pin the viewport to the canvas size.
await cdp("Emulation.setDeviceMetricsOverride", { width: 1280, height: 720, deviceScaleFactor: 1, mobile: false });

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

// The skill's references are pinned to one Bento version (references/agents-<version>.md); a newer shell may carry
// keys and behaviour they do not describe, an older one may lack features they assume.
const runtimeVersion = api.includes("schema") ? await evaluate("window.bento.schema()['x-bento-version'] || null") : null;
const refVersion = (() => {
  try {
    const f = readdirSync(new URL("../references/", import.meta.url)).find((n) => /^agents-.+\.md$/.test(n));
    return f && f.slice("agents-".length, -".md".length);
  } catch { return undefined; }
})();
console.log(`Runtime: Bento ${runtimeVersion ?? "unknown (no schema())"}${refVersion ? ` | skill references: ${refVersion}` : ""}`);
if (runtimeVersion && refVersion && runtimeVersion !== refVersion) {
  // Informational, not a [warning]: nothing in the deck can fix it, and a fix-every-warning loop would never end.
  console.log(`  note: the deck runs Bento ${runtimeVersion} but the skill describes ${refVersion}; treat https://bento.page/schema/slides.json as authoritative where they differ`);
}

// Load a document through the runtime: compact JSON expands here, and the report names what the gate dropped.
let droppedKeys = false;
if (docPath) {
  if (!api.includes("loadDoc")) fail(`loadDoc not in this runtime (window.bento has: ${api.join(", ")}); download a fresh Bento_Slides.bento.html`);
  const input = readFileSync(docPath, "utf8");
  const report = await evaluate(`(() => {
    const r = window.bento.loadDoc(${JSON.stringify(input)});
    if (r === false) return false;
    return r === true ? { legacy: true } : JSON.parse(JSON.stringify(r));
  })()`);
  if (report === false) fail("loadDoc rejected the document (not a bento/slides document, or missing format/slides)");
  if (report.legacy) {
    console.log("loadDoc: ok (this runtime predates the load report; no dropped-key detail available)");
  } else {
    console.log(`loadDoc: ok compact=${Boolean(report.compact)} expanded=${report.expanded ?? 0} fitted=${report.fitted ?? 0} laidOut=${report.laidOut ?? 0} dropped=${(report.dropped || []).length}`);
    for (const d of report.dropped || []) console.log(`  [dropped] ${d.path}: ${d.reason}`);
    // A dropped key is content that silently vanished from the deck; treat it like a validate error.
    if ((report.dropped || []).length) droppedKeys = true;
  }
  // Fonts named by the loaded doc may still be settling; auto heights are refitted on fonts.ready.
  await evaluate("document.fonts.ready.then(() => true)");
  await sleep(500);
}

const info = await evaluate(`(() => {
  const d = window.bento.doc;
  // The arrow-key walk covers slides that are neither states nor hidden (model.ts inLinearFlow).
  const walk = d.slides.filter(s => !s.stateOf && !s.hidden);
  // Each fx.step on a page consumes one arrow press before the next page arrives.
  return { title: d.title, slides: d.slides.length, pages: walk.length,
    steps: walk.map(s => Math.max(0, ...(s.elements || []).map(e => (e.fx && e.fx.step) || 0))),
    states: d.slides.filter(s => s.stateOf).map(s => s.id), hidden: d.slides.filter(s => s.hidden && !s.stateOf).map(s => s.id),
    size: d.size };
})()`);
console.log(`Deck: ${info.title} | ${info.slides} slides (${info.pages} pages, ${info.states.length} state slides, ${info.hidden.length} hidden)`);
// Non-canonical canvases would otherwise letterbox inside the 1280x720 viewport.
if (info.size.width !== 1280 || info.size.height !== 720) {
  await cdp("Emulation.setDeviceMetricsOverride", { width: info.size.width, height: info.size.height, deviceScaleFactor: 1, mobile: false });
}

// Validate
let hasError = droppedKeys;
if (api.includes("validate")) {
  const v = await evaluate(`JSON.parse(JSON.stringify(window.bento.validate(undefined, ${JSON.stringify(margin === undefined ? {} : { margin })})))`);
  // Info findings are design choices except these: keys in the file are a leak the agent must surface, a
  // font that is not embedded looks right only on the machine that has it installed, and the skill holds 96px margins.
  const SURFACED_INFO = new Set(["collab-secrets-present", "font-not-embedded", "past-margin"]);
  // With --doc the keys were minted in this browser session, never in a file; --write strips them again.
  if (docPath && !("collab" in JSON.parse(readFileSync(docPath, "utf8")))) SURFACED_INFO.delete("collab-secrets-present");
  const findings = (v.findings || []).filter((f) => f.severity !== "info" || SURFACED_INFO.has(f.code));
  console.log(`validate(): ok=${v.ok} ${JSON.stringify(v.counts || {})}`);
  for (const f of findings) {
    console.log(`  [${f.severity}] ${f.code} ${f.slide ? `slide=${f.slide} ` : ""}${f.element ? `el=${f.element} ` : ""}${f.message}`);
  }
  hasError ||= findings.some((f) => f.severity === "error");
} else {
  console.log(`validate(): not in this runtime (window.bento has: ${api.join(", ")}). Download a fresh Bento_Slides.bento.html from https://bento.page/releases/slides/ and splice the document JSON into its #bento-doc block.`);
}

// Checks validate() does not make: the skill's readability and house rules. Runs on the loaded doc in the browser
// so assets never cross the wire.
const readability = await evaluate(`((minFont, minCover, motion) => {
  const d = window.bento.doc, W = d.size.width, H = d.size.height, out = [];
  const hasText = (e) => e.type === "text" && /[^\\s]/.test(String(e.html || "").replace(/<[^>]*>/g, ""));
  const all = d.slides.flatMap((s) => (s.elements || []).map((e) => [s, e]));

  // A monospace stack is the code face and does not count against the two-typeface limit; the system aliases are one face.
  const SYSTEM = /^(system-ui|-apple-system|blinkmacsystemfont|segoe ui|sans-serif)$/;
  const face = (stack) => {
    const s = typeof stack === "string" ? stack : "";
    if (!s.trim() || /\\bmonospace\\b/i.test(s)) return null;
    const f = s.split(",")[0].trim().replace(/^['"]|['"]$/g, "").toLowerCase();
    return SYSTEM.test(f) ? "system-ui" : f;
  };
  const faces = new Set();
  for (const [, e] of all) {
    const f = face(hasText(e) && e.fontFamily) || face(e.type === "chart" && e.option && e.option.textStyle && e.option.textStyle.fontFamily);
    if (f) faces.add(f);
  }
  if (faces.size > 2) out.push({ code: "too-many-typefaces", message: faces.size + " typefaces (" + [...faces].join(", ") + "); keep to two" });

  const noNotes = d.slides.filter((s) => !String(s.notes || "").trim()).map((s) => s.id);
  if (noNotes.length) out.push({ code: "missing-notes", message: "no speaker notes on " + noNotes.join(", ") });

  if (!(d.present && d.present.slideNumber === false) && all.some(([, e]) => /\\{\\{page(:\\d+)?\\}\\}/.test(String(e.html || "")))) {
    out.push({ code: "double-page-number", message: "a {{page}} footer plus the default slide number shows two numbers; set present:{\\"slideNumber\\":false}" });
  }

  if (!motion) {
    const moving = [];
    for (const s of d.slides) {
      const t = s.transition || "fade";
      const fx = (s.elements || []).filter((e) => e.fx && Object.keys(e.fx).length).length;
      const why = [t !== "none" && t !== "fade" ? "transition " + t : "", fx ? fx + " fx" : ""].filter(Boolean);
      if (why.length) moving.push(s.id + " (" + why.join(", ") + ")");
    }
    const shown = moving.slice(0, 8).join("; ") + (moving.length > 8 ? "; +" + (moving.length - 8) + " more slides" : "");
    if (moving.length) out.push({ code: "motion-in-static-deck", message: shown + "; remove, or pass --motion if the user asked for animation" });
  }

  for (const s of d.slides) {
    const els = (s.elements || []).filter((e) => e.opacity !== 0);
    for (const e of els) {
      // Tables carry their size in style.fontSize; code and text on the element.
      const size = e.type === "table" ? e.style && e.style.fontSize : (e.type === "code" || hasText(e)) ? e.fontSize : undefined;
      if (typeof size === "number" && size < minFont) out.push({ code: "text-too-small", slide: s.id, element: e.id, message: "fontSize " + size + " is below the " + minFont + "px floor" });
    }
    // Full-bleed shapes and images are backdrops, and footers, page numbers and logos are chrome: neither is content.
    // Without the chrome exclusion a {{page}} footer at y=680 makes every slide "cover" the canvas.
    const backdrop = (e) => (e.type === "shape" || e.type === "image") && e.w * e.h >= 0.6 * W * H;
    const chrome = (e) => (e.h < 0.05 * H || e.w * e.h < 0.015 * W * H) && (e.y + e.h > 0.88 * H || e.y < 0.06 * H);
    // An invisible shape (a transparent click target over a link) would stretch the box without showing anything.
    const invisible = (e) => e.type === "shape" && /^(transparent|none|rgba\\([^)]*,\\s*0\\))$/i.test(String(e.fill || "")) && !(e.strokeWidth > 0 && e.stroke && !/^(transparent|none)$/i.test(e.stroke));
    const content = els.filter((e) => !backdrop(e) && !chrome(e) && !invisible(e));
    // Decorative shapes (accent bars, card backgrounds) extend the box but do not make a slide dense: a cover is
    // title + subtitle + accent bar, and counting the bar would flag every cover.
    const dense = content.filter((e) => e.type !== "shape" && (e.type !== "text" || hasText(e)));
    if (dense.length <= 2) continue;
    const x0 = Math.min(...content.map((e) => e.x)), y0 = Math.min(...content.map((e) => e.y));
    const x1 = Math.max(...content.map((e) => e.x + e.w)), y1 = Math.max(...content.map((e) => e.y + e.h));
    const ch = (y1 - y0) / H, cw = (x1 - x0) / W;
    if (ch < minCover) out.push({ code: "low-coverage", slide: s.id, message: "content spans " + Math.round(ch * 100) + "% of the height and " + Math.round(cw * 100) + "% of the width (y " + Math.round(y0) + ".." + Math.round(y1) + "); tighten the band or grow the type" });
  }
  return out;
})(${minFont}, ${minCover}, ${Boolean(opts["--motion"])})`);
for (const f of readability) {
  console.log(`  [warning] ${f.code} ${f.slide ? `slide=${f.slide} ` : ""}${f.element ? `el=${f.element} ` : ""}${f.message}`);
}
if (readability.length) console.log(`checks: ${readability.length} warning(s); --min-font, --min-cover and --motion adjust them`);

if (opts["--eval"]) {
  try {
    console.log(`eval: ${JSON.stringify(await evaluate(opts["--eval"]))}`);
  } catch (e) {
    fail(`--eval failed: ${e.message}`);
  }
}

// Write the expanded document into the shell. Bypasses window.bento.serialize(), which would stamp the
// session's freshly minted collab keys into the file.
if (writePath) {
  const input = JSON.parse(readFileSync(docPath, "utf8"));
  const full = await evaluate("JSON.parse(JSON.stringify(window.bento.doc))");
  // The runtime re-mints collab it finds incomplete, which would sever the owner's room: the file keeps what the
  // input had, minus `sync` (the CRDT state at the last save; reopening with it merges that state back over this edit).
  if (!("collab" in input)) delete full.collab;
  else if (input.collab && typeof input.collab === "object") {
    full.collab = { ...input.collab };
    delete full.collab.sync;
  }
  if (!("docId" in input)) delete full.docId;
  // parseDoc treats a template as a fresh instantiation and deletes the flag; the file on disk must keep it.
  if (input.template) full.template = true;
  if (input.layouts && !full.layouts) full.layouts = input.layouts;
  const ordered = { $schema: "https://bento.page/schema/slides.json", ...full };
  const json = JSON.stringify(ordered).replace(/</g, "\\u003c");
  let shell = readFileSync(deck, "utf8");
  // A stale first-page preview from an earlier save would show the old slide 1 in file managers; the next app save rewrites it anyway.
  // Older saves parked the preview in <noscript>; current ones use a <div> plus a remover <script>.
  shell = shell.replace(/<(div|noscript) data-bento-preview[^>]*>[\s\S]*?<\/\1>(\s*<script data-bento-preview[^>]*>[\s\S]*?<\/script>)?/, "");
  shell = shell.replace(DOC_BLOCK, (_, open, __, close) => `${open}${json}${close}`);
  // Decks often live outside git; the previous file is the only undo.
  if (existsSync(writePath)) copyFileSync(writePath, `${writePath}.bak`);
  writeFileSync(writePath, shell);
  console.log(`Wrote expanded document (${json.length} bytes) to ${writePath}`);
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
  // The fullscreen request is swallowed when headless denies it, so the overlay element is the marker that the click landed.
  if (!(await evaluate("Boolean(document.querySelector('.bento-present-overlay') || document.fullscreenElement)"))) fail("Present mode did not open after clicking Slideshow; the editor chrome may have changed");

  const press = async () => {
    for (const type of ["keyDown", "keyUp"]) {
      await cdp("Input.dispatchKeyEvent", { type, key: "ArrowRight", code: "ArrowRight", windowsVirtualKeyCode: 39 });
    }
    await sleep(settle);
  };
  const shoot = async (name) => {
    const { data } = await cdp("Page.captureScreenshot", { format: "png" });
    writeFileSync(join(outDir, `${name}.png`), Buffer.from(data, "base64"));
  };
  // Arrow keys skip state slides, so this walks the page count only. A page with fx.step reveals needs one press
  // per step before the next page arrives; its fully revealed state is captured as a second PNG.
  for (let i = 1; i <= info.pages; i++) {
    const page = String(i).padStart(2, "0");
    await shoot(`slide-${page}`);
    const steps = info.steps[i - 1];
    if (steps > 0) {
      for (let k = 0; k < steps; k++) await press();
      await shoot(`slide-${page}-revealed`);
    }
    if (i < info.pages) await press();
  }
  console.log(`Screenshots: ${outDir}/slide-01.png .. slide-${String(info.pages).padStart(2, "0")}.png (pages with step reveals also get slide-NN-revealed.png)`);
  if (info.states.length) {
    console.log(`State slides not captured (arrow keys skip them): ${info.states.join(", ")}. Check each by clicking its link element in the editor.`);
  }
  if (info.hidden.length) console.log(`Hidden slides not captured (arrow keys skip them): ${info.hidden.join(", ")}.`);
}

ws.onclose = null;
ws.close();
process.exit(hasError ? 1 : 0);
