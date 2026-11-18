#!/usr/bin/env node
// Fits each scene's h.wait pauses to its narration clip by writing <outDir>/pace.json for the next record.
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const usage = `usage: fit.mjs <outDir> <audioDir>

Reads the last recording's scenes.json and the narration clips, then writes <outDir>/pace.json:
a multiplier per scene that record.mjs applies to that scene's h.wait pauses, so the scene ends
TAIL seconds after its clip. Moves, clicks, typing and page loads keep their speed.
Record again afterwards. One pass usually lands within half a second; run it again to tighten.

Environment:
  TAIL      seconds of quiet between a clip's end and the next scene (default 1.0)
  MIN_PACE  floor for a multiplier (default 0.4: shorter pauses stop reading as pauses)
  MAX_PACE  ceiling for a multiplier (default 3: longer ones leave the screen idle)`;

const [, , outDir, audioDir] = process.argv;
if (outDir === "-h" || outDir === "--help") {
  console.log(usage);
  process.exit(0);
}
if (!outDir || !audioDir) {
  console.error(usage);
  process.exit(2);
}
const tail = Number(process.env.TAIL ?? 1);
const min = Number(process.env.MIN_PACE ?? 0.4);
const max = Number(process.env.MAX_PACE ?? 3);

const scenesFile = join(outDir, "scenes.json");
if (!existsSync(scenesFile)) {
  console.error(`fit: no ${scenesFile}; record the demo first`);
  process.exit(1);
}
const { scenes } = JSON.parse(readFileSync(scenesFile, "utf8"));
if (scenes.some((s) => s.waits === undefined)) {
  console.error("fit: scenes.json has no pause totals; record the demo again with this version of the skill");
  process.exit(1);
}

const seconds = (f) =>
  Number(execFileSync("ffprobe", ["-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f], { encoding: "utf8" }));
const hash = (f) => createHash("sha256").update(readFileSync(f)).digest("hex").slice(0, 16);

// narrate.sh may have sped N.wav up to fit the old scene; its untouched render is in .narrate/. A hand-recorded
// N.wav (one narrate.sh did not write) is used as it is.
function clip(n) {
  const cache = join(audioDir, ".narrate");
  const wav = join(audioDir, `${n}.wav`);
  const ours = existsSync(wav) && existsSync(join(cache, `${n}.out`)) && readFileSync(join(cache, `${n}.out`), "utf8").trim() === hash(wav);
  if (ours && existsSync(join(cache, `${n}.wav`))) return join(cache, `${n}.wav`);
  return ["wav", "mp3", "m4a", "aiff"].map((ext) => join(audioDir, `${n}.${ext}`)).find(existsSync);
}

const paceFile = join(outDir, "pace.json");
const paces = existsSync(paceFile) ? JSON.parse(readFileSync(paceFile, "utf8")) : {};
const rows = [["scene", "clip", "was", "pace", "expect", "note"]];
let stuck = false;
scenes.slice(0, -1).forEach((s, i) => {
  const was = scenes[i + 1].start - s.start;
  const file = clip(i + 1);
  if (!file) return rows.push([s.name, "-", was.toFixed(1), (paces[s.name] ?? 1).toFixed(2), was.toFixed(1), "silent: left as recorded"]);
  const len = seconds(file);
  // Scene length = fixed time (moves, clicks, loads) + pace x pauses, so one recording gives the fixed part.
  const fixed = was - s.pace * s.waits;
  const want = len + tail;
  let pace = s.waits > 0 ? (want - fixed) / s.waits : s.pace;
  let note = "";
  if (s.waits === 0) note = "no h.wait in this scene to scale";
  else if (pace < min) note = `needs ${pace.toFixed(2)}: remove actions or lengthen the text`;
  else if (pace > max) note = `needs ${pace.toFixed(2)}: add actions or trim the text`;
  if (note) stuck = true;
  pace = Math.min(max, Math.max(min, pace));
  paces[s.name] = Number(pace.toFixed(3));
  rows.push([s.name, len.toFixed(1), was.toFixed(1), pace.toFixed(2), (fixed + pace * s.waits).toFixed(1), note]);
});
writeFileSync(paceFile, `${JSON.stringify(paces, null, 2)}\n`);
const widths = rows[0].map((_, c) => Math.max(...rows.map((r) => r[c].length)));
for (const r of rows) console.log(r.map((v, c) => v.padEnd(widths[c])).join("  ").trimEnd());
console.log(`wrote ${paceFile}; record again to apply it`);
// A scene that cannot be fitted still records, with silence or an overrun; the exit code makes that visible to make.
process.exit(stuck ? 1 : 0);
