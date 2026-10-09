// openspeccer walkthrough against a throwaway copy of an OpenSpec repo (the live-reload scene edits a file).
// Env: DEMO_SRC (repo to copy, default ~/git/sammcj/cotyper), OPENSPECCER (serve.py path).
import { execFileSync, spawn } from "node:child_process";
import { mkdtempSync, readFileSync, writeFileSync, existsSync } from "node:fs";
import { homedir, tmpdir } from "node:os";
import { basename, join } from "node:path";

const SRC = process.env.DEMO_SRC || join(homedir(), "git/sammcj/cotyper");
const SERVE = process.env.OPENSPECCER || join(homedir(), ".claude/skills/openspeccer/scripts/serve.py");
const LIVE_CHANGE = "mvp-a";
const LIVE_TASK = "13.6 "; // an unticked task in LIVE_CHANGE's tasks.md, ticked on camera

export const options = {
  permissions: ["clipboard-read", "clipboard-write"],
  hide: [".repo-path"], // the copy's temp path would show in the status bar
};

export async function setup() {
  // Named after the source, since the dashboard shows the folder name as the repo name.
  const repo = join(mkdtempSync(join(tmpdir(), "openspeccer-demo-")), basename(SRC));
  // A clone keeps git history (created dates, spec diffs); rsync brings over uncommitted openspec state.
  execFileSync("git", ["clone", "-q", SRC, repo]);
  execFileSync("rsync", ["-a", "--delete", `${SRC}/openspec/`, `${repo}/openspec/`]);
  for (const d of [".claude", ".omp", ".pi"]) {
    if (existsSync(join(SRC, d))) execFileSync("rsync", ["-a", "--exclude", "worktrees", `${SRC}/${d}/`, `${repo}/${d}/`]);
  }
  const proc = spawn(SERVE, [repo, "--no-open", "--port", "4391"], { stdio: ["ignore", "pipe", "inherit"] });
  const base = await new Promise((ok, fail) => {
    proc.stdout.on("data", (b) => {
      const m = String(b).match(/(http:\/\/\S+?)\/?\s/);
      if (m) ok(m[1]);
    });
    proc.on("exit", (code) => fail(new Error(`serve.py exited ${code}`)));
  });
  console.error(`demo repo ${repo}, serving ${base}`);
  return { repo, base, proc };
}

export async function teardown({ proc }) {
  proc?.kill();
}

const nav = (h, hash) => h.click(`.nav a[href="${hash}"]`);

export async function run(h, { base, repo }) {
  const { page, wait, scene, moveTo, click, scroll, type } = h;
  await page.goto(`${base}/#/`);
  await page.waitForSelector(".card-title");
  await page.mouse.move(h.pos.x, h.pos.y);
  await wait(800);

  scene("dashboard");
  await wait(1500);
  for (const i of [0, 2, 4, 5]) {
    await moveTo(page.locator(".stat").nth(i), { steps: 25 });
    await wait(500);
  }
  await moveTo(page.locator(".card-title", { hasText: LIVE_CHANGE }), { steps: 35 });
  await wait(1200);
  await moveTo(page.locator(".card-title", { hasText: "suggestion-quality" }), { steps: 30 });
  await wait(1200);
  await moveTo({ x: 1100, y: 800 });
  await scroll(500);
  await wait(1500);
  await scroll(-500);

  scene("change");
  await click(page.locator(".card-title", { hasText: "suggestion-quality" }));
  await page.waitForSelector(".tabs");
  const tab = (name) => page.locator(".tabs button").filter({ hasText: name });
  await wait(1000);
  // The default sort opens the most recently modified artifact, so pick Tasks explicitly.
  await click(tab("Tasks"));
  await wait(800);
  await moveTo({ x: 1100, y: 600 });
  await scroll(700, { ms: 22 });
  await wait(1200);
  await scroll(-700, { step: 70 });
  await click(tab("Specs"));
  await wait(2500);
  await click(tab("Proposal"));
  await wait(2500);

  scene("specs");
  await nav(h, "#/specs");
  await wait(1200);
  await type('input[placeholder="Filter specs"]', "app");
  await wait(600);
  await click(page.locator(".tree-name", { hasText: "app-shell" }));
  await wait(1500);
  await moveTo({ x: 1100, y: 650 });
  await scroll(600, { ms: 22 });
  await wait(1000);
  await scroll(-600, { step: 80 });
  await click(page.locator(".chips button").filter({ hasText: "History" }));
  await wait(2500);

  scene("timeline");
  await nav(h, "#/timeline");
  await page.waitForSelector(".bd-chart");
  await wait(1500);
  const chart = await page.locator(".bd-chart").first().boundingBox();
  await moveTo({ x: chart.x + chart.width * 0.3, y: chart.y + chart.height * 0.5 });
  await moveTo({ x: chart.x + chart.width * 0.97, y: chart.y + chart.height * 0.5 }, { steps: 90 });
  await wait(1200);
  await moveTo(page.locator(".tl-label", { hasText: "suggestion-quality" }), { steps: 40 });
  await wait(1000);
  await click(".export-menu .btn");
  await wait(2200);
  await page.keyboard.press("Escape");
  await wait(400);

  scene("schemas");
  await nav(h, "#/schemas");
  await wait(1000);
  await click(page.locator(".schema-card .card-title", { hasText: "spec-driven" }));
  await page.waitForSelector(".dag-node");
  await wait(1200);
  await click(page.locator(".dag-node", { hasText: "design" }));
  await wait(2500);

  scene("agents");
  await nav(h, "#/agents");
  await wait(800);
  for (const card of await page.locator(".agent-card").all()) {
    await moveTo(card, { steps: 25 });
    await wait(700);
  }
  await wait(800);

  scene("commands");
  await nav(h, "#/commands");
  await page.waitForSelector(".cmd");
  await wait(1200);
  await moveTo({ x: 1100, y: 650 });
  await scroll(900, { ms: 18 });
  await wait(800);
  await scroll(-900, { step: 120 });
  await type('input[placeholder="Filter commands and options"]', "archive");
  await wait(1000);
  // "archive" also matches `list --archived`, so name the command to copy.
  await click(page.locator(".cmd-head .copyable").filter({ hasText: "openspec archive" }).first());
  await wait(2500);

  scene("live");
  await page.goto(`${base}/#/changes/${LIVE_CHANGE}`);
  await page.waitForSelector(".tabs");
  await wait(1000);
  const row = page.locator("li", { hasText: LIVE_TASK }).last();
  await row.scrollIntoViewIfNeeded();
  const box = await row.boundingBox();
  // Rest on the checkbox at the row's left edge, so the eye is already there when it ticks.
  await moveTo({ x: box.x + 9, y: box.y + 11 }, { steps: 35 });
  await wait(2500);
  const file = join(repo, "openspec/changes", LIVE_CHANGE, "tasks.md");
  writeFileSync(file, readFileSync(file, "utf8").replace(`- [ ] ${LIVE_TASK}`, `- [x] ${LIVE_TASK}`));
  await wait(4000);
  await nav(h, "#/");
  await wait(1000);
  await moveTo(page.locator(".card-title", { hasText: LIVE_CHANGE }), { steps: 35 });
  await wait(3000);
}
