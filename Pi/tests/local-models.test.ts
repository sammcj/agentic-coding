/**
 * Tests for the local-models extension.
 *
 * Lives outside extensions/ deliberately: pi loads every extensions/*.ts as an extension,
 * so a test file in there would be executed as one at startup.
 *
 * Run: bun test tests/local-models.test.ts
 */

import { describe, expect, test } from "bun:test"
import * as fs from "node:fs"
import * as os from "node:os"
import * as path from "node:path"
import { clampThinkingLevel, getSupportedThinkingLevels, type OpenAICompletionsCompat } from "@earendil-works/pi-ai"
import {
  buildModelConfig,
  ctxFromIdSuffix,
  ctxFromLlamaRouter,
  type DiscoveredModel,
  fetchModelsFromEndpoint,
  type LocalEndpoint,
  parseModelEntry,
  persistDefaultModel,
  resolveLevels,
  selectableModels,
} from "../extensions/local-models.ts"

const entry = (raw: any): DiscoveredModel => {
  const parsed = parseModelEntry(raw)
  if (!parsed) throw new Error(`unparseable: ${JSON.stringify(raw)}`)
  return parsed
}
const ctxOf = (raw: any) => entry(raw).contextWindow
const configFor = (id: string, extra: any = {}) => buildModelConfig(entry({ id, ...extra }))

/** compat is a union across provider APIs; everything here is the openai-completions arm. */
const compatOf = (id: string) => configFor(id).compat as OpenAICompletionsCompat | undefined
const kwargsOf = (id: string) => compatOf(id)?.chatTemplateKwargs as Record<string, any>

describe("context window detection", () => {
  test("reads each server dialect's own field", () => {
    expect(ctxOf({ id: "m", max_model_len: 128000 })).toBe(128000) // vLLM, oMLX
    expect(ctxOf({ id: "m", max_context_length: 262144 })).toBe(262144) // LM Studio native
    expect(ctxOf({ id: "m", context_length: 196608 })).toBe(196608) // llama-swap
    expect(ctxOf({ id: "m", context_window: 65536 })).toBe(65536)
  })

  test("prefers the loaded size over the model maximum", () => {
    // LM Studio reports both; the model can be loaded far below its ceiling, and
    // over-claiming truncates mid-session whereas under-claiming only wastes.
    expect(ctxOf({ id: "m", max_context_length: 262144, loaded_context_length: 8192 })).toBe(8192)
  })

  test("treats null and zero as absent, not as a value", () => {
    // LM Studio emits max_context_length: null for models it has no metadata for.
    expect(ctxOf({ id: "m", max_context_length: null })).toBeUndefined()
    expect(ctxOf({ id: "m", max_model_len: 0 })).toBeUndefined()
  })

  test("falls back to the -NNk id suffix when the server reports nothing", () => {
    expect(ctxOf({ id: "deepreinforce-35b-q5kl-192k" })).toBe(196608)
    expect(ctxOf({ id: "bge-reranker-v2-m3-q6_k-64k" })).toBe(65536)
  })

  test("finds the suffix when it is not the last segment", () => {
    // Regression: anchoring to end-of-string missed every -vision variant.
    expect(ctxFromIdSuffix("gemma-4-26b-a4b-ud-q4kxl-192k-vision")).toBe(196608)
    expect(ctxFromIdSuffix("gemma-4-31b-ud-q4kxl-128k-vision")).toBe(131072)
    expect(ctxFromIdSuffix("model-192k:instruct")).toBe(196608)
  })

  test("ignores quantisation tags that merely contain a k", () => {
    expect(ctxFromIdSuffix("gemma-3-270m-q8kxl-32k")).toBe(32768)
    expect(ctxFromIdSuffix("ninfer-qwen3-8-27b")).toBeUndefined()
  })

  test("parses llama.cpp router spawn args in every spelling", () => {
    expect(ctxFromLlamaRouter({ args: ["--ctx-size", "4096", "--model", "x.gguf"] })).toBe(4096)
    expect(ctxFromLlamaRouter({ args: ["--ctx-size=8192"] })).toBe(8192)
    expect(ctxFromLlamaRouter({ args: ["-c", "16384"] })).toBe(16384)
    expect(ctxFromLlamaRouter({ preset: "  ctx-size = 2048\nfit-target = 1024\n" })).toBe(2048)
    expect(ctxFromLlamaRouter({ args: ["--model", "x.gguf"] })).toBeUndefined()
    expect(ctxFromLlamaRouter(undefined)).toBeUndefined()
  })
})

describe("maxTokens derivation", () => {
  test("reserves most of the window for the prompt", () => {
    expect(configFor("m", { context_length: 262144 }).maxTokens).toBe(32768)
    expect(configFor("m", { context_length: 128000 }).maxTokens).toBe(32000)
  })

  test("never claims the whole window on a small context", () => {
    // Regression: a flat 4096 floor against a 4096 window left no room to prompt.
    const cfg = configFor("m", { context_length: 4096 })
    expect(cfg.maxTokens).toBe(2048)
    expect(cfg.maxTokens).toBeLessThan(cfg.contextWindow)
  })

  test("output never exceeds the context window at any size", () => {
    for (const ctx of [512, 1024, 4096, 8192, 32768, 131072, 1048576]) {
      const cfg = configFor("m", { context_length: ctx })
      expect(cfg.maxTokens).toBeLessThanOrEqual(cfg.contextWindow)
    }
  })
})

describe("non-chat and alias filtering", () => {
  const ep: LocalEndpoint = { id: "e", name: "e", baseUrl: "http://x/v1", status: "up" }
  const keeps = (id: string, extra: any = {}) => selectableModels(ep, [entry({ id, ...extra })]).length === 1

  test("drops embeddings, rerankers, TTS and ASR", () => {
    expect(keeps("bge-reranker-v2-m3-q6_k-64k")).toBe(false)
    expect(keeps("stella_en_1.5B_v5")).toBe(false)
    expect(keeps("kokoro-tts")).toBe(false)
    expect(keeps("unslothai/Qwen3-ASR-1.7B-GGUF:Q8_0")).toBe(false)
    expect(keeps("unsloth/bge-small-en-v1.5-GGUF:F16")).toBe(false)
    expect(keeps("text-embedding-nomic-embed-v2")).toBe(false)
  })

  test("drops run-together names with no separator", () => {
    // Regression: "embeddinggemma" needs a \w* tail, a trailing boundary never fires.
    expect(keeps("embeddinggemma-300m-q8_0-2k")).toBe(false)
  })

  test("honours a server-declared type", () => {
    expect(keeps("mystery-model", { type: "embeddings" })).toBe(false)
  })

  test("keeps ordinary chat models", () => {
    for (const id of [
      "qwen3.8-27b",
      "deepreinforce-35b-q5kl-192k",
      "muse-glimmer-30b",
      "poolside/laguna-s-2.1@bf16",
      "unsloth/gemma-4-E4B-it-qat-GGUF:Q4_K_XL",
      "llama-3.3-70b",
    ]) {
      expect(keeps(id)).toBe(true)
    }
  })

  test("drops llama-swap aliases so the picker has no duplicates", () => {
    expect(keeps("model-192k:instruct", { meta: { llamaswap: { type: "alias" } } })).toBe(false)
    expect(keeps("model-192k", { meta: { llamaswap: { type: "model" } } })).toBe(true)
  })

  test("honours a hidden override", () => {
    const hidden: LocalEndpoint = { ...ep, models: { "qwen3.8-27b": { hidden: true } } }
    expect(selectableModels(hidden, [entry({ id: "qwen3.8-27b" })])).toHaveLength(0)
  })
})

describe("vision input detection", () => {
  test("uses reported modalities when the server sends them", () => {
    expect(entry({ id: "m", architecture: { input_modalities: ["text", "image"] } }).input).toEqual(["text", "image"])
    expect(entry({ id: "m", architecture: { input_modalities: ["text"] } }).input).toEqual(["text"])
  })

  test("drops modalities pi cannot represent", () => {
    expect(entry({ id: "m", architecture: { input_modalities: ["text", "audio"] } }).input).toEqual(["text"])
  })

  test("falls back to the id and LM Studio's type", () => {
    expect(entry({ id: "qwen3-8-27b-ud-q5kxl-192k-vision" }).input).toEqual(["text", "image"])
    expect(entry({ id: "paddleocr-vl-1.5" }).input).toEqual(["text", "image"])
    expect(entry({ id: "m", type: "vlm" }).input).toEqual(["text", "image"])
    expect(entry({ id: "muse-glimmer-30b" }).input).toEqual(["text"])
  })
})

describe("reasoning defaults", () => {
  test("every chat model is thinking-capable, known family or not", () => {
    // The kwargs bundle is inert on a template that never reads it, so an id allow-list
    // would only go stale - a model missing from it silently loses its thinking toggle.
    for (const id of ["qwen3.8-27b", "deepseek-v4-flash-0731-oq2e-mtp", "glm-5.2-air", "gemma-4-31b", "muse-glimmer-30b"]) {
      expect(resolveLevels(id)).toBeDefined()
    }
  })

  test("an override is the only way to opt a model out", () => {
    expect(resolveLevels("qwen3.8-27b", { reasoning: false })).toBeUndefined()
  })

  test("families with a constrained effort string get their own map", () => {
    expect(resolveLevels("qwen3.8-27b")).not.toEqual(resolveLevels("muse-glimmer-30b"))
    expect(resolveLevels("deepseek-v4-flash-mtp")).not.toEqual(resolveLevels("muse-glimmer-30b"))
  })

  test("ids the family regexes must not claim fall through to the boolean map", () => {
    // Without these, loosening either lookahead would hand a non-thinking model an effort
    // string its template never validates, and nothing in the suite would notice.
    const boolean = resolveLevels("muse-glimmer-30b")
    for (const id of ["qwen-32b-instruct", "qwen-30b", "deepseek-coder-v2-16b", "deepseek-math-7b", "deepseek-v2.5"]) {
      expect(resolveLevels(id)).toEqual(boolean)
    }
  })
})

describe("developer role", () => {
  // pi-ai infers supportsDeveloperRole from the baseUrl and every host on its non-standard
  // list is a named cloud provider, so a local URL resolves it true and the system prompt
  // ships as role:"developer". llama.cpp hands the role straight to the template: GLM 4.7
  // and 5.2 drop the message, stock Qwen3.8 raise_exception()s on it.
  test("is pinned off for every local model", () => {
    for (const id of ["qwen3.8-27b", "glm-5.2-air", "muse-glimmer-30b"]) {
      expect(compatOf(id)?.supportsDeveloperRole).toBe(false)
    }
  })

  test("stays pinned off even when reasoning is overridden away", () => {
    const cfg = buildModelConfig(entry({ id: "qwen3.8-27b" }), { reasoning: false })
    expect((cfg.compat as OpenAICompletionsCompat).supportsDeveloperRole).toBe(false)
  })
})

describe("thinking levels", () => {
  const levelsFor = (id: string) => getSupportedThinkingLevels(configFor(id) as any)

  test("Qwen offers only levels its chat template accepts", () => {
    // Qwen's template raise_exception()s on anything outside low/medium/xhigh,
    // so an offered level that maps to "high" or "minimal" would hard-fail the request.
    expect(levelsFor("qwen3.8-27b")).toEqual(["off", "low", "medium", "xhigh"])
  })

  test("every Qwen level sends a value the template accepts", () => {
    const accepted = new Set(["low", "medium", "xhigh"])
    const cfg = configFor("qwen3.8-27b")
    for (const level of getSupportedThinkingLevels(cfg as any)) {
      if (level === "off") continue
      const sent = cfg.thinkingLevelMap?.[level] ?? level
      expect(accepted.has(sent as string)).toBe(true)
    }
  })

  test("R1 offers no off switch, because it cannot stop thinking", () => {
    expect(levelsFor("deepseek-r1-distill-32b")).not.toContain("off")
  })

  test("families that can be switched off offer off", () => {
    for (const id of ["qwen3.8-27b", "deepseek-v4-flash-mtp", "glm-4.7-air", "gemma-4-31b"]) {
      expect(levelsFor(id)).toContain("off")
    }
  })

  test("MiniMax offers no off switch, because it cannot stop thinking", () => {
    expect(levelsFor("minimax-m2-230b")).not.toContain("off")
  })

  test("DeepSeek offers plain thinking plus the two strings V4 acts on", () => {
    // V4 branches on reasoning_effort 'high' and 'max'; every other value is plain thinking
    // mode, which is the model's own default and has to stay selectable.
    const cfg = configFor("deepseek-v4-flash-mtp")
    expect(getSupportedThinkingLevels(cfg as any)).toEqual(["off", "medium", "high", "xhigh"])
    expect(cfg.thinkingLevelMap?.xhigh).toBe("max")
    expect(clampThinkingLevel(cfg as any, "medium")).toBe("medium")
  })

  test("a model outside the known families is a plain on/off toggle", () => {
    expect(levelsFor("muse-glimmer-30b")).toEqual(["off", "medium"])
    expect(configFor("muse-glimmer-30b").reasoning).toBe(true)
  })

  test("pi's medium default is not clamped upward on a boolean model", () => {
    // clampThinkingLevel scans upward, so a map whose only on-level is "high" silently
    // starts every unmatched model one level above what settings asked for.
    for (const id of ["muse-glimmer-30b", "gemma-4-31b", "glm-5.2-air", "deepseek-r1-distill-32b"]) {
      expect(clampThinkingLevel(configFor(id) as any, "medium")).toBe("medium")
    }
  })

  test("a boolean model sends an effort string stock Qwen3.8 would accept", () => {
    // The fallback also catches a Qwen served under a name the regex misses, and that
    // template raise_exception()s on anything outside low/medium/xhigh.
    const accepted = new Set(["low", "medium", "xhigh"])
    const cfg = configFor("muse-glimmer-30b")
    for (const level of getSupportedThinkingLevels(cfg as any)) {
      if (level === "off") continue
      expect(accepted.has((cfg.thinkingLevelMap?.[level] ?? level) as string)).toBe(true)
    }
  })
})

describe("request shape", () => {
  test("every model goes through chat_template_kwargs", () => {
    // pi-ai's built-in deepseek/zai formats emit the vendors' cloud parameters, which a
    // locally served model ignores - so "off" would not actually disable thinking.
    for (const id of ["qwen3.8-27b", "deepseek-v4-flash-mtp", "glm-4.7-air", "muse-glimmer-30b"]) {
      expect(compatOf(id)?.thinkingFormat).toBe("chat-template")
      expect(compatOf(id)?.chatTemplateKwargs).toBeDefined()
    }
  })

  test("both spellings of the switch ship on every request", () => {
    // Templates disagree on the key - Qwen and GLM read enable_thinking, DeepSeek reads
    // thinking - and Jinja drops whichever one its template never defines.
    for (const id of ["qwen3.8-27b", "deepseek-v4-flash-mtp", "glm-4.7-air"]) {
      const kwargs = kwargsOf(id)
      expect(kwargs.enable_thinking).toEqual({ $var: "thinking.enabled" })
      expect(kwargs.thinking).toEqual({ $var: "thinking.enabled" })
    }
  })

  test("effort is sent when thinking is on and omitted when it is off", () => {
    expect(kwargsOf("qwen3.8-27b").reasoning_effort).toEqual({ $var: "thinking.effort", omitWhenOff: true })
  })

  test("earlier think blocks are preserved in both spellings", () => {
    // Qwen and Gemma read preserve_thinking; GLM spells the same thing clear_thinking,
    // inverted. Sending both costs nothing on a template that reads neither.
    const kwargs = kwargsOf("qwen3.8-27b")
    expect(kwargs.preserve_thinking).toBe(true)
    expect(kwargs.clear_thinking).toBe(false)
  })

  test("a per-model thinkingFormat override still carries the kwargs", () => {
    // buildChatTemplateValues does Object.entries(kwargs), so a chat-template format with
    // no kwargs threw on every request.
    const cfg = buildModelConfig(entry({ id: "muse-glimmer-30b" }), { thinkingFormat: "chat-template" })
    expect((cfg.compat as OpenAICompletionsCompat).chatTemplateKwargs).toBeDefined()
  })
})

describe("per-model overrides", () => {
  const model = () => entry({ id: "qwen3.8-27b", context_length: 262144 })

  test("override wins over anything detected", () => {
    expect(buildModelConfig(model(), { contextWindow: 8192 }).contextWindow).toBe(8192)
    expect(buildModelConfig(model(), { maxTokens: 1234 }).maxTokens).toBe(1234)
  })

  test("reasoning can be forced off, which drops the thinking compat but not the rest", () => {
    const cfg = buildModelConfig(model(), { reasoning: false })
    expect(cfg.reasoning).toBe(false)
    expect(cfg.thinkingLevelMap).toBeUndefined()
    expect((cfg.compat as OpenAICompletionsCompat).chatTemplateKwargs).toBeUndefined()
  })

  test("a model with no detected context still gets a usable default", () => {
    const cfg = buildModelConfig(entry({ id: "mystery" }))
    expect(cfg.contextWindow).toBeGreaterThan(0)
    expect(cfg.maxTokens).toBeGreaterThan(0)
  })
})

describe("fetchModelsFromEndpoint", () => {
  /** Serve a fixed /v1/models payload, plus optional native/props routes. */
  function serve(routes: Record<string, unknown>) {
    return Bun.serve({
      port: 0,
      fetch(req) {
        const path = new URL(req.url).pathname
        if (!(path in routes)) return new Response("not found", { status: 404 })
        return Response.json(routes[path])
      },
    })
  }

  test("parses a plain OpenAI listing", async () => {
    const s = serve({ "/v1/models": { data: [{ id: "a", context_length: 4096 }, { id: "b" }] } })
    try {
      const models = await fetchModelsFromEndpoint(`http://127.0.0.1:${s.port}/v1`)
      expect(models.map((m) => m.id)).toEqual(["a", "b"])
      expect(models[0].contextWindow).toBe(4096)
    } finally {
      s.stop(true)
    }
  })

  test("falls back to LM Studio's native API when capacity is missing", async () => {
    const s = serve({
      "/v1/models": { data: [{ id: "qwen3.8-27b" }] },
      "/api/v0/models": { data: [{ id: "qwen3.8-27b", max_context_length: 262144, type: "vlm" }] },
    })
    try {
      const models = await fetchModelsFromEndpoint(`http://127.0.0.1:${s.port}/v1`)
      expect(models[0].contextWindow).toBe(262144)
    } finally {
      s.stop(true)
    }
  })

  test("reads the served context off /props rather than trusting n_ctx_train", async () => {
    // n_ctx_train is the training context; llama-server is usually run well below it.
    const s = serve({
      "/v1/models": { data: [{ id: "m", meta: { n_ctx_train: 262144 } }] },
      "/props": { default_generation_settings: { n_ctx: 16384 } },
    })
    try {
      const models = await fetchModelsFromEndpoint(`http://127.0.0.1:${s.port}/v1`)
      expect(models[0].contextWindow).toBe(16384)
    } finally {
      s.stop(true)
    }
  })

  test("returns empty rather than throwing when the endpoint is unreachable", async () => {
    expect(await fetchModelsFromEndpoint("http://127.0.0.1:1/v1")).toEqual([])
  })

  test("survives a malformed payload", async () => {
    const s = serve({ "/v1/models": { data: [{ no_id: true }, { id: "ok" }] } })
    try {
      expect((await fetchModelsFromEndpoint(`http://127.0.0.1:${s.port}/v1`)).map((m) => m.id)).toEqual(["ok"])
    } finally {
      s.stop(true)
    }
  })
})

describe("persistDefaultModel", () => {
  // getAgentDir reads PI_CODING_AGENT_DIR per call, so each test points it at a fresh dir.
  const withAgentDir = async (fn: (dir: string, settingsFile: string) => Promise<void>) => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), "local-models-settings-"))
    const prev = process.env.PI_CODING_AGENT_DIR
    process.env.PI_CODING_AGENT_DIR = dir
    try {
      await fn(dir, path.join(dir, "settings.json"))
    } finally {
      if (prev === undefined) delete process.env.PI_CODING_AGENT_DIR
      else process.env.PI_CODING_AGENT_DIR = prev
      fs.rmSync(dir, { recursive: true, force: true })
    }
  }

  test("merges the default into existing settings without touching other fields", async () => {
    await withAgentDir(async (_dir, file) => {
      fs.writeFileSync(file, JSON.stringify({ theme: "nebula-pulse", defaultProvider: "old", defaultModel: "gone" }))
      expect(await persistDefaultModel("local-abc123", "qwen3-8-27b")).toBe(true)
      const settings = JSON.parse(fs.readFileSync(file, "utf-8"))
      expect(settings).toEqual({ theme: "nebula-pulse", defaultProvider: "local-abc123", defaultModel: "qwen3-8-27b" })
    })
  })

  test("creates settings.json when absent", async () => {
    await withAgentDir(async (_dir, file) => {
      expect(await persistDefaultModel("local-abc123", "m")).toBe(true)
      expect(JSON.parse(fs.readFileSync(file, "utf-8"))).toEqual({ defaultProvider: "local-abc123", defaultModel: "m" })
    })
  })

  test("refuses to flatten a malformed settings.json", async () => {
    await withAgentDir(async (_dir, file) => {
      fs.writeFileSync(file, "{ not json")
      expect(await persistDefaultModel("local-abc123", "m")).toBe(false)
      expect(fs.readFileSync(file, "utf-8")).toBe("{ not json")
    })
  })

  test("gives up rather than writing while pi holds a fresh lock", async () => {
    await withAgentDir(async (_dir, file) => {
      fs.writeFileSync(file, JSON.stringify({ defaultProvider: "old" }))
      fs.mkdirSync(`${file}.lock`)
      expect(await persistDefaultModel("local-abc123", "m")).toBe(false)
      expect(JSON.parse(fs.readFileSync(file, "utf-8"))).toEqual({ defaultProvider: "old" })
      fs.rmSync(`${file}.lock`, { recursive: true, force: true })
    })
  })

  test("takes over a stale lock", async () => {
    await withAgentDir(async (_dir, file) => {
      fs.mkdirSync(`${file}.lock`)
      // proper-lockfile treats a lock as stale once its mtime is 10s old.
      const stale = new Date(Date.now() - 60_000)
      fs.utimesSync(`${file}.lock`, stale, stale)
      expect(await persistDefaultModel("local-abc123", "m")).toBe(true)
      expect(JSON.parse(fs.readFileSync(file, "utf-8"))).toEqual({ defaultProvider: "local-abc123", defaultModel: "m" })
      expect(fs.existsSync(`${file}.lock`)).toBe(false)
    })
  })
})
