// What the skill's scripts share about a .bento.html file and the release channel.
import { inflateRawSync } from "node:zlib";

export const DOC_BLOCK = /(<script type="application\/bento\+json" id="bento-doc">)([\s\S]*?)(<\/script>)/;
// Older saves parked the preview in <noscript>; current ones use a <div> plus a remover <script>.
// The div holds nested divs, so the match ends on the remover, never on a </div>.
export const PREVIEW_BLOCK = /<div data-bento-preview[^>]*>[\s\S]*?<script data-bento-preview[^>]*>[\s\S]*?<\/script>|<noscript data-bento-preview[^>]*>[\s\S]*?<\/noscript>/;
export const ENCRYPTED_DOC = /"format"\s*:\s*"bento\/enc"/;
export const LANG_BLOCKS = /<script\b[^>]*type="application\/bento\+lang"[^>]*>[\s\S]*?<\/script>/g;

// The manifest the app's own self-update reads. Its signature is not checked here: this answers "what is latest",
// and the sha256 it pins is compared against the download by upgrade_deck.mjs.
const MANIFEST = "https://bento.page/releases/slides/manifest.json";

export async function latestRelease() {
  // Short, because render_check.mjs waits on this and only prints the answer.
  const res = await fetch(MANIFEST, { signal: AbortSignal.timeout(5000) });
  if (!res.ok) throw new Error(`${MANIFEST} returned ${res.status}`);
  const release = JSON.parse((await res.json()).payload);
  if (release.app !== "bento-slides" || ![release.version, release.sha256, release.url].every((v) => typeof v === "string")) {
    throw new Error(`${MANIFEST} is malformed`);
  }
  return release;
}

export function compareVersions(a, b) {
  const [x, y] = [a, b].map((v) => v.split(".").map(Number));
  for (let i = 0; i < Math.max(x.length, y.length); i++) {
    const d = (x[i] ?? 0) - (y[i] ?? 0);
    if (d) return Math.sign(d);
  }
  return 0;
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

export function inflateBlocks(html) {
  const re = /<script\b([^>]*)type="bento\/deflate-(b64|b86)"([^>]*)>([\s\S]*?)<\/script>/g;
  return [...html.matchAll(re)].map((m, i) => {
    const payload = m[4].replace(/\s+/g, "");
    const bytes = m[2] === "b64" ? Buffer.from(payload, "base64") : Buffer.from(b86decode(payload));
    return {
      id: /id="([^"]+)"/.exec(m[1] + m[3])?.[1] || `block-${i + 1}`,
      encoding: m[2],
      text: inflateRawSync(bytes).toString("utf8"),
    };
  });
}

// Read from the file so no browser is needed; null for a shell that does not carry the marker.
export function runtimeVersion(html) {
  for (const { text } of inflateBlocks(html)) {
    const m = /__bentoRuntime",\{value:"([0-9.]+)"/.exec(text);
    if (m) return m[1];
  }
  return null;
}
