/**
 * Replay captured payloads through prompt-cache-doctor's report, so the extension's
 * verdict can be checked against a run whose answer is already known.
 *
 *   bun replay.mjs <captures-dir>
 */
import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";

// diagnostics/ and extensions/ are siblings under the pi agent dir, so resolve across
// rather than hardcoding a home path - these scripts get copied between machines.
const { fingerprint, buildReport } = await import(
  new URL("../extensions/prompt-cache-doctor.ts", import.meta.url).href
);

const dir = process.argv[2] ?? "captures";
const files = readdirSync(dir).filter((f) => f.endsWith(".json")).sort();
const reqs = [];
for (const [i, f] of files.entries()) {
  const fp = fingerprint(JSON.parse(readFileSync(join(dir, f), "utf-8")), i + 1);
  if (fp) reqs.push(fp);
}
console.log(buildReport(reqs, []));
