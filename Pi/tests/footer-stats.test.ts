/**
 * Tests the cache-rate maths that prompt-cache-doctor publishes to the footer, plus the
 * custom-footer rule that decides which statuses get highlighted.
 *
 * Both are reimplemented here rather than imported: the extension computes the rate inside
 * an event handler with no exported seam, and the footer rule lives inside a render closure.
 * Keep these in step with the originals.
 *
 * Run: bun test tests/footer-stats.test.ts
 */

import { describe, expect, test } from "bun:test"

type Sample = { input: number; cacheRead: number; output: number }

/** Mirrors prompt-cache-doctor's message_end handler. */
function statusFor(samples: Sample[]): string | undefined {
  const prompt = samples.reduce((n, s) => n + s.input + s.cacheRead, 0)
  const reused = samples.reduce((n, s) => n + s.cacheRead, 0)
  if (prompt <= 0) return undefined
  const rate = Math.round((100 * reused) / prompt)
  const last = samples[samples.length - 1]
  const missed = last.cacheRead === 0 && last.input > 1024
  return `cache ${rate}%${missed ? " miss" : ""}`
}

/** Mirrors custom-footer's highlight rule. */
const isWarning = (s: string) => /\b(miss(ed|es)?|warn(ing)?s?|stale|errors?)\b/i.test(s)

const s = (input: number, cacheRead: number): Sample => ({ input, cacheRead, output: 0 })

describe("cache rate", () => {
  test("is cumulative over the session, not just the last request", () => {
    expect(statusFor([s(1000, 0)])).toBe("cache 0%")
    expect(statusFor([s(0, 1000)])).toBe("cache 100%")
    expect(statusFor([s(500, 500)])).toBe("cache 50%")
  })

  test("a later hit lifts the rate even though the first request missed", () => {
    expect(statusFor([s(1000, 0), s(0, 3000)])).toBe("cache 75%")
  })

  test("no usage at all yields no status rather than a divide-by-zero", () => {
    expect(statusFor([])).toBeUndefined()
    expect(statusFor([s(0, 0)])).toBeUndefined()
  })

  test("rounding stays in bounds and never renders a decimal", () => {
    expect(statusFor([s(1, 99999)])).toBe("cache 100%")
    expect(statusFor([s(99999, 1)])).toMatch(/^cache \d+%$/)
  })
})

describe("miss flag", () => {
  test("reflects the last request only, and only when the prompt was big enough to matter", () => {
    expect(statusFor([s(0, 3000), s(30000, 0)])).toMatch(/miss$/)
    expect(statusFor([s(0, 3000), s(100, 0)])).not.toMatch(/miss/)
    expect(statusFor([s(30000, 0), s(0, 3000)])).not.toMatch(/miss/)
  })

  test("fires above the threshold, not at it", () => {
    expect(statusFor([s(1024, 0)])).not.toMatch(/miss/)
    expect(statusFor([s(1025, 0)])).toMatch(/miss/)
  })
})

describe("footer highlighting", () => {
  test("highlights a miss and leaves an ordinary rate alone", () => {
    expect(isWarning("cache 12% miss")).toBe(true)
    expect(isWarning("cache 87%")).toBe(false)
  })

  test("plurals and -ed forms count", () => {
    expect(isWarning("2 errors")).toBe(true)
    expect(isWarning("1 warning")).toBe(true)
    expect(isWarning("3 missed")).toBe(true)
    expect(isWarning("stale")).toBe(true)
  })

  test("word boundaries stop substrings triggering it", () => {
    expect(isWarning("mission control")).toBe(false)
    expect(isWarning("terrorist")).toBe(false)
    expect(isWarning("dismissal")).toBe(false)
  })
})
