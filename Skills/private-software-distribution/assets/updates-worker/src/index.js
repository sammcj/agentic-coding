// Serves the update feed and archives from R2 to registered beta testers only.
// Integrity comes from the signatures in the feed. This Worker only gates access.

const ROUTE = /^\/(latest\.json|appcast\.xml|download\/[A-Za-z0-9._-]+)$/;
// 32 random bytes, base64url without padding (scripts/beta-token.sh).
const BEARER = /^Bearer ([A-Za-z0-9_-]{43})$/;

export async function tokenHash(token) {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(token));
  return Array.from(new Uint8Array(digest), (b) => b.toString(16).padStart(2, "0")).join("");
}

// The registered token's hash, or null.
async function registeredHash(request, env) {
  const token = BEARER.exec(request.headers.get("Authorization") ?? "")?.[1];
  if (token === undefined) return null;
  const hash = await tokenHash(token);
  // KV holds only token hashes, so a KV leak yields no usable tokens.
  return (await env.BETA_TOKENS.get(hash)) === null ? null : hash;
}

async function allowed(limiter, key) {
  return (await limiter.limit({ key })).success;
}

function tooMany() {
  return new Response(null, { status: 429, headers: { "retry-after": "60" } });
}

export async function handle(request, env) {
  if (request.method !== "GET") return new Response(null, { status: 405 });
  const key = ROUTE.exec(new URL(request.url).pathname)?.[1];
  if (key === undefined) return new Response(null, { status: 404 });
  // Before the KV lookup, so a flood of made-up tokens is turned away without spending KV reads.
  if (!(await allowed(env.IP_LIMITER, request.headers.get("CF-Connecting-IP") ?? "unknown"))) return tooMany();
  const hash = await registeredHash(request, env);
  if (hash === null) return new Response(null, { status: 401 });
  // Only feed checks are limited per token: one update needs a single feed fetch, and downloads are rare.
  if (!key.startsWith("download/") && !(await allowed(env.TOKEN_LIMITER, hash))) return tooMany();

  const object = await env.UPDATES.get(key);
  if (object === null) return new Response(null, { status: 404 });
  const headers = new Headers();
  object.writeHttpMetadata(headers);
  headers.set("etag", object.httpEtag);
  headers.set("content-length", String(object.size));
  // Gated content must never land in a shared cache.
  headers.set("cache-control", "private, no-store");
  return new Response(object.body, { headers });
}

export default { fetch: handle };
