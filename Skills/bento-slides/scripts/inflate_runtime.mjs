#!/usr/bin/env node
// Extract the compressed Bento runtime from a .bento.html file into readable (minified) JS and CSS.
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { basename, join, resolve } from "node:path";
import { inflateBlocks } from "./bento_file.mjs";

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

const blocks = inflateBlocks(readFileSync(deck, "utf8"));
if (blocks.length === 0) fail("No bento/deflate-b64 or bento/deflate-b86 script blocks found; is this a .bento.html file?");
mkdirSync(outDir, { recursive: true });
for (const { id, encoding, text } of blocks) {
  const file = join(outDir, `${id}.${/css/i.test(id) ? "css" : "js"}`);
  writeFileSync(file, text);
  console.log(`${file} (${encoding}, ${text.length} chars)`);
}
