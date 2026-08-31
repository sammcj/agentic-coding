/**
 * Tests for the stable-tool-order extension.
 *
 * Lives outside extensions/ deliberately: pi loads every extensions/*.ts as an extension,
 * so a test file in there would be executed as one at startup.
 *
 * Run: bun test tests/stable-tool-order.test.ts
 */

import { describe, expect, test } from "bun:test"
import { isLocalRequest, sortToolsByName } from "../extensions/stable-tool-order.ts"

const fn = (name: string) => ({ type: "function", function: { name } })
const custom = (name: string) => ({ type: "custom", custom: { name } })
const nm = (t: any) => t.function?.name ?? t.custom?.name

describe("sortToolsByName", () => {
  test("reorders into name order", () => {
    expect(sortToolsByName([fn("read"), fn("bash"), fn("advisor")]).map(nm)).toEqual([
      "advisor",
      "bash",
      "read",
    ])
  })

  test("the same set converges on the same order regardless of input order", () => {
    const set = ["ctx_execute", "preview_export", "advisor", "read"]
    const one = sortToolsByName(set.map(fn)).map(nm)
    const two = sortToolsByName([...set].reverse().map(fn)).map(nm)
    expect(one).toEqual(two)
  })

  test("an extra tool sorting last does not disturb the shared prefix", () => {
    const a = sortToolsByName(["bash", "read", "write"].map(fn)).map(nm)
    const b = sortToolsByName(["bash", "read", "write", "zzz_last"].map(fn)).map(nm)
    expect(b.slice(0, 3)).toEqual(a)
  })

  test("grammar-style {custom:{name}} entries sort too", () => {
    expect(sortToolsByName([custom("zeta"), fn("alpha")]).map(nm)).toEqual(["alpha", "zeta"])
  })

  test("duplicate names are left alone rather than ordered arbitrarily", () => {
    const dupes = [fn("read"), fn("bash"), fn("read")]
    expect(sortToolsByName(dupes)).toBe(dupes)
  })

  test("an unnameable entry is left alone rather than sorted to an arbitrary spot", () => {
    const weird = [fn("read"), { type: "function" }]
    expect(sortToolsByName(weird)).toBe(weird)
  })

  test("does not mutate its input", () => {
    const orig = [fn("read"), fn("bash")]
    const copy = [...orig]
    sortToolsByName(orig)
    expect(orig).toEqual(copy)
  })
})

/**
 * The sort must not touch hosted providers: they cache by explicit breakpoint or by a
 * server-managed key, so reordering buys nothing and still changes what the model is shown.
 */
describe("isLocalRequest", () => {
  const REG = [
    { id: "qwen3-8-27b-ud-q6kl-192k", provider: "local-9503ec274c" },
    { id: "claude-opus-5", provider: "anthropic" },
    { id: "shared-id", provider: "local-9503ec274c" },
    { id: "shared-id", provider: "openrouter" },
  ]

  test("the registry wins over the session's active model", () => {
    expect(isLocalRequest("qwen3-8-27b-ud-q6kl-192k", REG, "anthropic")).toBe(true)
  })

  test("a hosted model is not sorted even while a local model is active", () => {
    expect(isLocalRequest("claude-opus-5", REG, "local-9503ec274c")).toBe(false)
  })

  test("an id served by both local and hosted providers is ambiguous, so left alone", () => {
    expect(isLocalRequest("shared-id", REG, undefined)).toBe(false)
  })

  test("a registry miss falls back to the active provider", () => {
    expect(isLocalRequest("unknown-model", REG, "local-abc")).toBe(true)
    expect(isLocalRequest("unknown-model", REG, "anthropic")).toBe(false)
    expect(isLocalRequest("unknown-model", REG, undefined)).toBe(false)
    expect(isLocalRequest(undefined, [], "local-abc")).toBe(true)
  })

  test("no signal at all means do nothing", () => {
    expect(isLocalRequest(undefined, [], undefined)).toBe(false)
  })

  test("an empty registry is not read as 'everything is local'", () => {
    expect(isLocalRequest("qwen3-8-27b-ud-q6kl-192k", [], "anthropic")).toBe(false)
  })
})
