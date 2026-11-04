import assert from "node:assert/strict";
import { test } from "node:test";
import { handle, tokenHash } from "../src/index.js";

const TOKEN = "A".repeat(43);
const ORIGIN = "https://example.test";

function limiter(limit) {
  const counts = new Map();
  return {
    limit: async ({ key }) => {
      counts.set(key, (counts.get(key) ?? 0) + 1);
      return { success: counts.get(key) <= limit };
    },
  };
}

async function makeEnv({ ipLimit = 20 } = {}) {
  const tokens = new Map([[await tokenHash(TOKEN), "tester"]]);
  const objects = new Map([
    ["latest.json", "{}"],
    ["download/App-1.tar.gz", "bytes"],
  ]);
  return {
    BETA_TOKENS: { get: async (key) => tokens.get(key) ?? null },
    IP_LIMITER: limiter(ipLimit),
    TOKEN_LIMITER: limiter(2),
    UPDATES: {
      get: async (key) => {
        if (!objects.has(key)) return null;
        const body = objects.get(key);
        return { body, size: body.length, httpEtag: '"e"', writeHttpMetadata() {} };
      },
    },
  };
}

const get = (env, path, token = TOKEN, method = "GET") =>
  handle(new Request(ORIGIN + path, { method, headers: token ? { Authorization: `Bearer ${token}` } : {} }), env);

test("a registered token gets the feed, uncached", async () => {
  const response = await get(await makeEnv(), "/latest.json");
  assert.equal(response.status, 200);
  assert.equal(await response.text(), "{}");
  assert.equal(response.headers.get("cache-control"), "private, no-store");
});

test("a missing, malformed or unregistered token gets 401", async () => {
  const env = await makeEnv();
  assert.equal((await get(env, "/latest.json", null)).status, 401);
  assert.equal((await get(env, "/latest.json", "short")).status, 401);
  assert.equal((await get(env, "/latest.json", "B".repeat(43))).status, 401);
});

test("unknown paths get 404 and other methods get 405", async () => {
  const env = await makeEnv();
  assert.equal((await get(env, "/secret")).status, 404);
  assert.equal((await get(env, "/download/nested/file.tar.gz")).status, 404);
  assert.equal((await get(env, "/download/App-0.tar.gz")).status, 404);
  assert.equal((await get(env, "/latest.json", TOKEN, "POST")).status, 405);
});

test("feed checks are limited per token and downloads are not", async () => {
  const env = await makeEnv();
  assert.equal((await get(env, "/latest.json")).status, 200);
  assert.equal((await get(env, "/latest.json")).status, 200);
  assert.equal((await get(env, "/latest.json")).status, 429);
  assert.equal((await get(env, "/download/App-1.tar.gz")).status, 200);
});

test("the IP limit applies before the token lookup", async () => {
  const env = await makeEnv({ ipLimit: 1 });
  let lookups = 0;
  const { get: lookup } = env.BETA_TOKENS;
  env.BETA_TOKENS.get = (key) => (lookups++, lookup(key));
  await get(env, "/latest.json");
  assert.equal((await get(env, "/latest.json")).status, 429);
  assert.equal(lookups, 1);
});
