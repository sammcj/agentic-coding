#!/usr/bin/env node
// Extract the compressed Bento runtime from a .bento.html file into readable (minified) JS and CSS.
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { basename, join, resolve } from "node:path";
import { inflateRawSync } from "node:zlib";

const HELP = `Usage: node inflate_runtime.mjs <deck.bento.html> [--out <dir>]

Inflates every "bento/deflate-b64" or "bento/deflate-b86" script block and writes one file per block
(<id>.js or <id>.css) so the runtime can be searched when agents.md does not answer a question.
Default --out: $TMPDIR/bento-runtime/<deck-name>`;

const args = process.argv.slice(2);
if (args.length === 0 || args.includes("-h") || args.includes("--help")) {
  console.log(HELP);
  process.exit(args.length === 0 ? 1 : 0);
}
const outIdx = args.indexOf("--out");
const outArg = outIdx === -1 ? null : args[outIdx + 1];
if (outIdx !== -1 && (!outArg || outArg.startsWith("--"))) fail("--out needs a value");
const positional = args.filter((a, i) => !a.startsWith("--") && args[i - 1] !== "--out");
if (positional.length !== 1) fail("Pass exactly one deck path. See --help.");
const deck = resolve(positional[0]);
if (!existsSync(deck)) fail(`Deck not found: ${deck}`);
const outDir = outArg || join(tmpdir(), "bento-runtime", basename(deck).replace(/\.bento\.html$/, ""));

function fail(msg) {
  console.error(msg);
  process.exit(1);
}

// Base86 as defined by the loader script inside every deck: 5 chars encode 4 bytes, a short tail pads with 85.
const B86 = "!#$%()*+,./0123456789:;=?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[]^_`abcdefghijklmnopqrstuvwxyz|}~";
const b86v = new Int16Array(128).fill(-1);
for (let q = 0; q < 86; q++) b86v[B86.charCodeAt(q)] = q;
function b86decode(t) {
  const n = t.length, full = (n / 5) | 0, rest = n - full * 5;
  const out = new Uint8Array(full * 4 + (rest ? rest - 1 : 0));
  let o = 0, i = 0, v;
  const c = (j) => {
    const x = t.charCodeAt(j), y = x < 128 ? b86v[x] : -1;
    if (y < 0) throw new Error(`base86: bad character code ${x} at index ${j}`);
    return y;
  };
  for (; i + 5 <= n; i += 5) {
    v = (((c(i) * 86 + c(i + 1)) * 86 + c(i + 2)) * 86 + c(i + 3)) * 86 + c(i + 4);
    out[o++] = (v / 16777216) & 255; out[o++] = (v >>> 16) & 255; out[o++] = (v >>> 8) & 255; out[o++] = v & 255;
  }
  if (rest) {
    v = 0;
    for (let k = 0; k < 5; k++) v = v * 86 + (k < rest ? c(i + k) : 85);
    const tail = [(v / 16777216) & 255, (v >>> 16) & 255, (v >>> 8) & 255, v & 255];
    for (let k = 0; k < rest - 1; k++) out[o++] = tail[k];
  }
  return out;
}

const html = readFileSync(deck, "utf8");
const re = /<script\b([^>]*)type="bento\/deflate-(b64|b86)"([^>]*)>([\s\S]*?)<\/script>/g;
mkdirSync(outDir, { recursive: true });
let count = 0;
for (const m of html.matchAll(re)) {
  const attrs = m[1] + m[3];
  const id = /id="([^"]+)"/.exec(attrs)?.[1] || `block-${count + 1}`;
  const payload = m[4].replace(/\s+/g, "");
  const bytes = m[2] === "b64" ? Buffer.from(payload, "base64") : Buffer.from(b86decode(payload));
  const text = inflateRawSync(bytes).toString("utf8");
  const file = join(outDir, `${id}.${/css/i.test(id) ? "css" : "js"}`);
  writeFileSync(file, text);
  console.log(`${file} (${m[2]}, ${text.length} chars)`);
  count++;
}
if (count === 0) fail("No bento/deflate-b64 or bento/deflate-b86 script blocks found; is this a .bento.html file?");
