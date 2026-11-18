// Runs a demo and writes frames/, frames.ffconcat and scenes.json into outDir.
import { existsSync, mkdirSync, readFileSync, rmSync } from "node:fs";
import { homedir } from "node:os";
import { basename, join, resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { record } from "./lib/recorder.mjs";

const [, , demoArg, outArg] = process.argv;
const usage = `usage: node record.mjs <demo.mjs> [outDir]  (default outDir ~/Downloads/demo-recorder/<demo name>)
An <outDir>/pace.json (written by fit.mjs) scales each scene's h.wait pauses; delete it to record at the demo's own pace.`;
if (demoArg === "-h" || demoArg === "--help") {
  console.log(usage);
  process.exit(0);
}
if (!demoArg) {
  console.error(usage);
  process.exit(2);
}
const demoPath = resolve(demoArg);
const outDir = resolve(outArg || join(homedir(), "Downloads", "demo-recorder", basename(demoPath, ".mjs")));
rmSync(`${outDir}/frames`, { recursive: true, force: true }); // stale frames from a longer take would be re-used
mkdirSync(outDir, { recursive: true });

const paceFile = join(outDir, "pace.json");
const paces = existsSync(paceFile) ? JSON.parse(readFileSync(paceFile, "utf8")) : {};
if (Object.keys(paces).length) console.log(`pacing scenes from ${paceFile}`);

const demo = await import(pathToFileURL(demoPath).href);
const ctx = (await demo.setup?.()) ?? {};
try {
  const { scenes, frames, fps } = await record({ outDir, ...demo.options, paces, run: (h) => demo.run(h, ctx) });
  console.log(`${frames} frames, ${fps.toFixed(1)} fps average (only repaints are captured)`);
  console.log(scenes.map((s) => `${s.start.toFixed(1)}s ${s.name}`).join("\n"));
} finally {
  await demo.teardown?.(ctx);
}
