/**
 * Recording reverse proxy for an OpenAI-compatible endpoint.
 *
 * Sits between pi and llama-swap, writes every /chat/completions request body to
 * disk, and forwards the request untouched. Streaming responses are piped straight
 * through so pi behaves exactly as it would against the real server.
 *
 * The upstream is required, as an argument or as UPSTREAM. There is no default: a wrong
 * one would silently record against the wrong server, and a right one would be somebody's
 * private hostname sitting in a file that gets copied between machines and committed.
 *
 *   node capture-proxy.mjs http://192.0.2.10:8080/v1
 *   UPSTREAM=http://192.0.2.10:8080/v1 PORT=8899 OUTDIR=./captures node capture-proxy.mjs
 *
 * Typed with JSDoc rather than converted to TypeScript: it runs under bare `node` with no
 * build step, and the repo's tsconfig only covers extensions/ and tests/.
 */
import http from "node:http";
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const PORT = Number(process.env.PORT || 8899);
const OUTDIR = process.env.OUTDIR || join(import.meta.dirname, "captures");

const upstreamArg = process.argv[2] ?? process.env.UPSTREAM;
if (!upstreamArg) {
  console.error("usage: node capture-proxy.mjs <upstream-url>   (or set UPSTREAM)");
  console.error("  e.g. node capture-proxy.mjs http://127.0.0.1:8080/v1");
  process.exit(2);
}

/**
 * Resolved once at startup so a typo fails here rather than on the first proxied request,
 * where the error would look like a server fault.
 * @returns {string}
 */
function resolveUpstream(/** @type {string} */ raw) {
  try {
    return new URL(raw).toString().replace(/\/+$/, "");
  } catch {
    console.error(`not a valid URL: ${raw}`);
    process.exit(2);
  }
}
const UPSTREAM = resolveUpstream(upstreamArg);

mkdirSync(OUTDIR, { recursive: true });
let seq = 0;

/**
 * @param {import("node:http").IncomingMessage} req
 * @returns {Promise<Buffer>}
 */
function readBody(req) {
  return new Promise((resolve, reject) => {
    /** @type {Buffer[]} */
    const chunks = [];
    req.on("data", (/** @type {Buffer} */ c) => chunks.push(c));
    req.on("end", () => resolve(Buffer.concat(chunks)));
    req.on("error", reject);
  });
}

/**
 * Hop-by-hop headers and the original host must not be forwarded. Node models a header as
 * string | string[] (only set-cookie arrives as an array); fetch wants plain strings, so
 * multi-value headers are rejoined the way they arrived on the wire.
 * @param {import("node:http").IncomingHttpHeaders} incoming
 * @returns {Record<string, string>}
 */
function forwardableHeaders(incoming) {
  const drop = new Set(["host", "connection", "content-length", "transfer-encoding"]);
  /** @type {Record<string, string>} */
  const out = {};
  for (const [k, v] of Object.entries(incoming)) {
    if (drop.has(k) || v === undefined) continue;
    out[k] = Array.isArray(v) ? v.join(", ") : v;
  }
  return out;
}

const message = (/** @type {unknown} */ e) => (e instanceof Error ? e.message : String(e));

/** @param {any} parsed @param {string} n @returns {string} */
function recordPayload(parsed, n) {
  // Order matters for a prefix diff, so keep the payload exactly as sent.
  const name = `${n}-${parsed.model ?? "unknown"}.json`.replace(/[^\w.-]/g, "_");
  writeFileSync(join(OUTDIR, name), JSON.stringify(parsed, null, 2));
  const toolNames = (parsed.tools ?? []).map(
    (/** @type {any} */ t) => t.function?.name ?? t.custom?.name,
  );
  console.log(
    `[${n}] ${parsed.model} msgs=${parsed.messages?.length} tools=${toolNames.length} ` +
      `sys=${(parsed.messages?.[0]?.content ?? "").length}ch -> ${name}`,
  );
  return name;
}

const server = http.createServer(async (req, res) => {
  const url = req.url ?? "/";
  const body = req.method === "POST" || req.method === "PUT" ? await readBody(req) : undefined;

  if (body && url.includes("/chat/completions")) {
    const n = String(++seq).padStart(3, "0");
    try {
      recordPayload(JSON.parse(body.toString("utf-8")), n);
    } catch {
      writeFileSync(join(OUTDIR, `${n}-unparsed.txt`), body);
      console.log(`[${n}] unparsed body -> ${n}-unparsed.txt`);
    }
  }

  let upstream;
  try {
    upstream = await fetch(UPSTREAM + url.replace(/^\/v1/, ""), {
      method: req.method,
      headers: forwardableHeaders(req.headers),
      body,
      redirect: "follow",
    });
  } catch (e) {
    res.writeHead(502, { "content-type": "application/json" });
    res.end(JSON.stringify({ error: { message: `proxy upstream failed: ${message(e)}` } }));
    return;
  }

  /** @type {Record<string, string>} */
  const outHeaders = {};
  upstream.headers.forEach((v, k) => {
    // The body is re-framed by this server, so the upstream's framing headers would lie.
    if (["content-encoding", "content-length", "transfer-encoding", "connection"].includes(k)) return;
    outHeaders[k] = v;
  });
  res.writeHead(upstream.status, outHeaders);

  if (!upstream.body) {
    res.end();
    return;
  }
  const reader = upstream.body.getReader();
  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      if (value) res.write(Buffer.from(value));
    }
  } catch (e) {
    console.error("stream error:", message(e));
  }
  res.end();
});

server.listen(PORT, "127.0.0.1", () => {
  console.log(`capture proxy on http://127.0.0.1:${PORT}/v1 -> ${UPSTREAM}`);
  console.log(`writing captures to ${OUTDIR}`);
});
