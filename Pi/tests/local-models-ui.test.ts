/**
 * Endpoint-list TUI tests for the local-models extension.
 *
 * Drives the real extension against throwaway HTTP servers. PI_LOCAL_MODELS_CONFIG points it
 * at a temp config so a test run can never probe or overwrite the developer's own endpoints -
 * bun shares one module registry across test files, so redirecting HOME is not enough.
 *
 * Run: bun test tests/local-models-ui.test.ts
 */

import { afterAll, beforeAll, describe, expect, test } from "bun:test"
import * as fs from "node:fs"
import * as os from "node:os"
import * as path from "node:path"

const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "local-models-ui-"))
const configPath = path.join(tmp, "local-models.json")
process.env.PI_LOCAL_MODELS_CONFIG = configPath

/** Answers /v1/models after `delayMs`, so a probe in flight is observable. */
function serveModels(delayMs: number) {
  return Bun.serve({
    port: 0,
    async fetch(req) {
      if (delayMs) await new Promise((r) => setTimeout(r, delayMs))
      if (new URL(req.url).pathname !== "/v1/models") return new Response("no", { status: 404 })
      return Response.json({ data: [{ id: "test-model", context_length: 8192 }] })
    },
  })
}

const fast = serveModels(0)
const slow = serveModels(400)
/** Reachable but erroring, so "down" is reached deterministically instead of via a socket timeout. */
const dead = Bun.serve({ port: 0, fetch: () => new Response("nope", { status: 500 }) })

fs.writeFileSync(
  configPath,
  JSON.stringify([
    { id: "fast", name: "Fast", baseUrl: `http://127.0.0.1:${fast.port}/v1`, status: "up" },
    { id: "slow", name: "Slow", baseUrl: `http://127.0.0.1:${slow.port}/v1`, status: "up" },
    { id: "dead", name: "Dead", baseUrl: `http://127.0.0.1:${dead.port}/v1`, status: "up" },
  ]),
)

const theme = {
  fg: (_name: string, text: string) => text,
  bold: (text: string) => text,
}

interface Harness {
  /** What the list showed the instant the TUI was constructed, before any probe could land. */
  firstFrame: string
  /** Every frame the extension asked to be repainted, in order. */
  frames: string[]
  close: () => void
}

let harness: Harness

beforeAll(async () => {
  const ext = (await import("../extensions/local-models.ts")).default

  let handler: ((args: string, ctx: any) => Promise<void>) | undefined
  const pi: any = {
    registerProvider: () => {},
    unregisterProvider: () => {},
    on: () => {},
    registerCommand: (_name: string, spec: any) => {
      handler = spec.handler
    },
  }

  await ext(pi)
  if (!handler) throw new Error("extension registered no /local-models command")

  let component: any
  let done!: (v: unknown) => void
  let firstFrame = ""
  const frames: string[] = []
  const draw = () => frames.push(component.render(100).join("\n"))

  const ctx = {
    ui: {
      notify: () => {},
      custom: (factory: any) =>
        new Promise((resolve) => {
          done = resolve
          component = factory({ requestRender: draw }, theme, {}, resolve)
          // Rendered synchronously here: no probe can have resolved yet, so this is
          // the frame the user sees the moment the command is invoked.
          firstFrame = component.render(100).join("\n")
        }),
    },
  }

  const opened = handler("", ctx)
  // Let every endpoint settle.
  await new Promise((r) => setTimeout(r, 1200))

  harness = {
    firstFrame,
    frames,
    close: () => {
      done(null)
      return opened
    },
  }
})

afterAll(() => {
  harness?.close()
  fast.stop(true)
  slow.stop(true)
  dead.stop(true)
  fs.rmSync(tmp, { recursive: true, force: true })
})

describe("endpoint list", () => {
  test("appears before any endpoint has been probed", () => {
    // Regression: the command awaited the whole probe sweep, so nothing was drawn until
    // the slowest endpoint answered - up to the full timeout on an unreachable one.
    expect(harness.firstFrame).toContain("🟡 Fast")
    expect(harness.firstFrame).toContain("🟡 Slow")
    expect(harness.firstFrame).toContain("🟡 Dead")
  })

  test("lists every configured provider straight from the saved config", () => {
    expect(harness.firstFrame).toContain("Local Models - Providers")
    expect(harness.firstFrame).toContain("Add endpoint")
    expect(harness.firstFrame).toContain("Refresh all")
  })

  test("repaints per endpoint rather than once at the end of the sweep", () => {
    expect(harness.frames.length).toBeGreaterThanOrEqual(3)
  })

  test("a fast endpoint shows up while a slow one is still checking", () => {
    // The point of the change: no endpoint waits behind another to be drawn.
    expect(harness.frames.some((f) => f.includes("🟢 Fast") && f.includes("🟡 Slow"))).toBe(true)
  })

  test("every endpoint ends on its real status", () => {
    const last = harness.frames[harness.frames.length - 1]
    expect(last).toContain("🟢 Fast")
    expect(last).toContain("🟢 Slow")
    expect(last).toContain("🔴 Dead")
  })
})
