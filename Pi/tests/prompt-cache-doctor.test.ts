/**
 * Tests for the prompt-cache-doctor extension's pure functions, driven by synthetic
 * payloads shaped like the real ones.
 *
 * Lives outside extensions/ deliberately: pi loads every extensions/*.ts as an extension,
 * so a test file in there would be executed as one at startup.
 *
 * Run: bun test tests/prompt-cache-doctor.test.ts
 */

import { describe, expect, test } from "bun:test"
import { buildReport, diverge, fingerprint } from "../extensions/prompt-cache-doctor.ts"

const tool = (name: string) => ({ type: "function", function: { name, description: `the ${name} tool` } })
const KW = { enable_thinking: true, thinking: true, reasoning_effort: "medium" }

function payload({
  tools = ["read", "bash"],
  system = "SYSTEM",
  agent,
  msgs = ["hello"],
  kwargs = KW,
}: {
  tools?: string[]
  system?: string
  agent?: string
  msgs?: string[]
  kwargs?: Record<string, unknown>
} = {}) {
  const sys = agent ? `PARENT\n\n<active_agent name="${agent}"/>\n\n${system}` : system
  return {
    model: "qwen3-8-27b",
    chat_template_kwargs: kwargs,
    tools: tools.map(tool),
    messages: [{ role: "system", content: sys }, ...msgs.map((m) => ({ role: "user", content: m }))],
  }
}

const fpOf = (opts: Parameters<typeof payload>[0], seq: number) => fingerprint(payload(opts), seq)!

describe("fingerprint", () => {
  test("a payload with no <active_agent> tag is the main session", () => {
    const fp = fpOf({}, 1)
    expect(fp.agent).toBe("(main session)")
    expect(fp.toolNames).toEqual(["read", "bash"])
    expect(fp.roles[0]).toBe("system")
  })

  test("reads the agent name out of the system prompt", () => {
    expect(fpOf({ agent: "general-purpose" }, 2).agent).toBe("general-purpose")
  })

  test("a payload with no messages yields nothing", () => {
    expect(fingerprint({}, 3)).toBeUndefined()
  })

  test("content-part arrays fingerprint like strings rather than crashing", () => {
    const fp = fingerprint(
      { model: "m", messages: [{ role: "system", content: [{ type: "text", text: "SYSTEM" }] }] },
      4,
    )!
    expect(fp.systemLen).toBe("SYSTEM".length)
  })
})

/**
 * diverge() compares in template render order and returns the FIRST differing stage, because
 * everything behind that point is lost regardless of whether it also matches.
 */
describe("diverge", () => {
  const base = fpOf({ agent: "gp" }, 1)

  test("identical payloads do not diverge", () => {
    expect(diverge(base, fpOf({ agent: "gp" }, 2)).stage).toBe("none")
  })

  test("a reordered tool is reported at its index", () => {
    const d = diverge(base, fpOf({ agent: "gp", tools: ["bash", "read"] }, 3))
    expect(d.stage).toBe("tools")
    expect(d.detail).toMatch(/tool 0 differs/)
  })

  test("an extra tool at the end is reported as an extra", () => {
    const d = diverge(base, fpOf({ agent: "gp", tools: ["read", "bash", "zzz"] }, 4))
    expect(d.stage).toBe("tools")
    expect(d.detail).toMatch(/extra tool/)
  })

  test("a differing system prompt behind matching tools is reported", () => {
    expect(diverge(base, fpOf({ agent: "gp", system: "OTHER" }, 5)).stage).toBe("system")
  })

  test("kwargs render first, so they outrank a tool difference", () => {
    const d = diverge(
      base,
      fpOf({ agent: "gp", tools: ["bash", "read"], kwargs: { ...KW, reasoning_effort: "xhigh" } }, 6),
    )
    expect(d.stage).toBe("kwargs")
  })

  test("kwargs are compared order-insensitively", () => {
    const reordered = fpOf(
      { agent: "gp", kwargs: { reasoning_effort: "medium", thinking: true, enable_thinking: true } },
      9,
    )
    expect(diverge(base, reordered).stage).toBe("none")
  })

  test("differing only in the task is the good case", () => {
    const d = diverge(base, fpOf({ agent: "gp", msgs: ["different task"] }, 7))
    expect(d.stage).toBe("messages")
    expect(d.detail).toMatch(/message 1/)
  })

  test("a continued conversation is not a divergence", () => {
    expect(diverge(base, fpOf({ agent: "gp", msgs: ["hello", "next"] }, 8)).stage).toBe("none")
  })
})

describe("buildReport", () => {
  test("says so when nothing has been recorded", () => {
    expect(buildReport([], [])).toMatch(/Nothing recorded yet/)
  })

  test("a constant set in varying orders recommends sorting", () => {
    const r = buildReport([fpOf({ agent: "gp" }, 1), fpOf({ agent: "gp", tools: ["bash", "read"] }, 2)], [])
    expect(r).toMatch(/TOOL ORDER VARIES/)
    expect(r).not.toMatch(/TOOL SET VARIES/)
  })

  /** Sorting an unstable set can be worse than doing nothing, so the report must say so. */
  test("a varying set warns against sorting and names the unstable tool", () => {
    const r = buildReport(
      [fpOf({ agent: "gp" }, 1), fpOf({ agent: "gp", tools: ["read", "bash", "advisor"] }, 2)],
      [],
    )
    expect(r).toMatch(/TOOL SET VARIES/)
    expect(r).toMatch(/advisor/)
    expect(r).toMatch(/will NOT fix this/)
  })

  test("two agent types with different tools are not reported as a fault", () => {
    const r = buildReport(
      [fpOf({ agent: "gp", tools: ["read", "bash"] }, 1), fpOf({ agent: "Explore", tools: ["read"] }, 2)],
      [],
    )
    expect(r).not.toMatch(/VARIES/)
  })

  test("the healthy case reports the prefix working", () => {
    const r = buildReport(
      [fpOf({ agent: "gp", msgs: ["task one"] }, 1), fpOf({ agent: "gp", msgs: ["task two"] }, 2)],
      [{ input: 500, cacheRead: 30000, output: 100 }],
    )
    expect(r).toMatch(/prefix is doing its job/)
    expect(r).toMatch(/served from cache/)
  })
})
