#!/usr/bin/env node
// Move a deck's document into the latest Bento release, as the app's own self-update does.
import { createHash } from "node:crypto";
import { constants, copyFileSync, existsSync, readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { compareVersions, DOC_BLOCK, ENCRYPTED_DOC, LANG_BLOCKS, latestRelease, runtimeVersion } from "./bento_file.mjs";

const HELP = `Usage: node upgrade_deck.mjs <deck.bento.html> [--check]

Compares the deck's runtime with the latest release. When it is behind, rewrites the deck as the same document in the
new shell. The #bento-doc block moves unchanged (encrypted bodies, collab keys and docId included), along with language
packs and, for unencrypted decks, <title>. The first-page preview is dropped; the next save from the app writes it again.
Slides files only.

The previous file stays beside the deck as <name>.v<version>-backup.bento.html.

  --check   Report only. Exit 0 when current, 2 when behind.

Close the deck's browser tab first. Needs network access to bento.page.`;

function fail(msg) {
  console.error(msg);
  process.exit(1);
}

const args = process.argv.slice(2);
if (args.length === 0 || args.includes("-h") || args.includes("--help")) {
  console.log(HELP);
  process.exit(args.length === 0 ? 1 : 0);
}
const unknown = args.find((a) => a.startsWith("--") && a !== "--check");
if (unknown) fail(`Unknown option ${unknown}. See --help.`);
const positional = args.filter((a) => !a.startsWith("--"));
if (positional.length !== 1) fail("Pass exactly one deck path. See --help.");
const deck = resolve(positional[0]);
if (!existsSync(deck)) fail(`Deck not found: ${deck}`);

const html = readFileSync(deck, "utf8");
const doc = html.match(DOC_BLOCK);
if (!doc) fail(`No #bento-doc block in ${deck}; is this a .bento.html file?`);
const encrypted = ENCRYPTED_DOC.test(doc[2]);
// Spaces, Dash and Type share the .bento.html suffix; a slides shell would not open their documents.
const generator = html.match(/<meta name="generator" content="([^"]*)"/)?.[1];
const isSlides = generator ? generator === "bento-slides" : encrypted || /"format"\s*:\s*"bento\/slides"/.test(doc[2]);
if (!isSlides) fail(`${deck} is not a Bento slides file (generator: ${generator ?? "none"}); left unchanged.`);
const current = runtimeVersion(html);

const release = await latestRelease().catch((e) => fail(`Could not read the release manifest (a sandbox blocking bento.page? run outside it): ${e.message}`));
if (current && compareVersions(current, release.version) >= 0) {
  console.log(`Deck runs Bento ${current}, the latest release.`);
  process.exit(0);
}
const from = current ?? "unknown";
if (args.includes("--check")) {
  console.log(`Deck runs Bento ${from}; latest is ${release.version}.`);
  process.exit(2);
}

// The shell is about 700KB; a minute allows for a slow link without hanging the agent.
const bytes = await fetch(release.url, { signal: AbortSignal.timeout(60000) })
  .then(async (res) => {
    if (!res.ok) throw new Error(`returned ${res.status}`);
    return Buffer.from(await res.arrayBuffer());
  })
  .catch((e) => fail(`Downloading ${release.url} failed: ${e.message}`));
const digest = createHash("sha256").update(bytes).digest("hex");
if (digest !== release.sha256.toLowerCase()) fail("The download does not match the manifest's sha256; deck left unchanged.");

const fresh = bytes.toString("utf8");
if (!DOC_BLOCK.test(fresh)) fail("The download has no #bento-doc block; deck left unchanged.");

// The document goes in last, so these edits cannot match text inside it. Function replacers: it may contain $ sequences.
let shell = fresh;
// Builds before 1.2.9 wrote an encrypted deck's real title in clear; the shell's neutral title stays.
const title = encrypted ? null : html.match(/<title>[\s\S]*?<\/title>/)?.[0];
if (title) shell = shell.replace(/<title>[\s\S]*?<\/title>/, () => title);
const packs = html.match(LANG_BLOCKS) ?? [];
if (packs.length) shell = shell.replace("</head>", () => `${packs.join("\n")}\n</head>`);
shell = shell.replace(DOC_BLOCK, () => doc[0]);

const scriptCloses = (s) => s.split("</script>").length - 1;
if (shell.match(DOC_BLOCK)?.[0] !== doc[0] || scriptCloses(shell) !== scriptCloses(fresh) + packs.length) {
  fail("The rebuilt file failed its read-back check; deck left unchanged.");
}

const backup = `${deck.replace(/\.bento\.html$/, "")}.v${from}-backup.bento.html`;
try {
  copyFileSync(deck, backup, constants.COPYFILE_EXCL);
} catch (e) {
  fail(e.code === "EEXIST" ? `${backup} already exists; move it aside and re-run.` : e.message);
}
writeFileSync(deck, shell);
console.log(`Upgraded ${deck}: Bento ${from} -> ${release.version}\nBackup: ${backup}`);
if (encrypted) console.log("Encrypted deck: ask the user to open it, enter the password and save once.");
