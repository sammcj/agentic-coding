/**
 * Local Models Extension
 *
 * Manage self-hosted LLM endpoints entirely from the TUI.
 * Commands:
 *   /local-models  - Open the local models manager
 *
 * Config is persisted across sessions. Models show up in /model selector
 * automatically when their endpoint is reachable.
 *
 * Provides:
 *   - Endpoint manager TUI: add, refresh, delete; endpoints probed in parallel
 *   - Context window detection across server dialects (vLLM, oMLX, LM Studio,
 *     llama-swap, llama.cpp/router), with maxTokens derived from it
 *   - Filters aliases, embeddings, rerankers, TTS and ASR out of the picker
 *   - Vision input detection
 *   - Thinking control: one chat_template_kwargs bundle for every model, plus the
 *     effort levels Qwen and DeepSeek templates actually accept
 *   - Pins supportsDeveloperRole off, which pi-ai otherwise infers from the baseUrl
 *   - Fuzzy type-to-filter model picker
 *   - Per-model overrides in local-models.json
 *   - Picking a model persists it as the startup default in settings.json
 */

import { DynamicBorder, type ExtensionAPI, getAgentDir, type ProviderModelConfig } from "@earendil-works/pi-coding-agent"
import {
  Container,
  fuzzyFilter,
  type SelectItem,
  SelectList,
  Text,
  Spacer,
} from "@earendil-works/pi-tui"

// ─── Types ───────────────────────────────────────────────────────────────────

/** Hand-written per-model tweaks, persisted in local-models.json and keyed by model id. */
export interface ModelOverride {
  reasoning?: boolean
  thinkingFormat?: ThinkingFormat
  contextWindow?: number
  maxTokens?: number
  hidden?: boolean
}

export interface LocalEndpoint {
  id: string
  name: string
  baseUrl: string
  apiKey?: string
  status: "checking" | "up" | "down"
  models?: Record<string, ModelOverride>
}

/** One /v1/models entry, normalised across the dialects the various servers speak. */
export interface DiscoveredModel {
  id: string
  contextWindow?: number
  input: ("text" | "image")[]
  /** False for embeddings, rerankers, TTS and ASR - none of them can back a chat session. */
  chat: boolean
  /** llama-swap lists aliases beside the real models; registering both duplicates the picker. */
  alias: boolean
}

/**
 * ProviderModelConfig["compat"] is a union across every API flavour pi supports. We always
 * register as "openai-completions", so narrow to that arm rather than fighting the union.
 */
type OpenAICompat = Extract<NonNullable<ProviderModelConfig["compat"]>, { thinkingFormat?: unknown }>
type ThinkingFormat = NonNullable<OpenAICompat["thinkingFormat"]>
type ThinkingLevelMap = NonNullable<ProviderModelConfig["thinkingLevelMap"]>

// ─── Helpers ─────────────────────────────────────────────────────────────────

function normalizeBaseUrl(url: string): string {
  return url.trim().replace(/\/+$/, "")
}

function generateEndpointId(baseUrl: string): string {
  return crypto.createHash("sha256").update(normalizeBaseUrl(baseUrl)).digest("hex").slice(0, 10)
}

function generateUniqueEndpointId(baseUrl: string): string {
  const baseId = generateEndpointId(baseUrl)
  let id = baseId
  let suffix = 2
  while (endpoints.some((ep) => ep.id === id && normalizeBaseUrl(ep.baseUrl) !== normalizeBaseUrl(baseUrl))) {
    id = `${baseId}-${suffix++}`
  }
  return id
}

async function fetchJson(url: string, apiKey: string | undefined, timeoutMs: number): Promise<any | null> {
  try {
    const headers: Record<string, string> = { "Accept": "application/json" }
    if (apiKey) headers["Authorization"] = `Bearer ${apiKey}`
    const res = await fetch(url, { headers, signal: AbortSignal.timeout(timeoutMs) })
    return res.ok ? await res.json() : null
  } catch {
    return null
  }
}

/**
 * Provider registration has to finish inside the extension factory (pi resolves the
 * startup model and `--list-models` before any session event), so every probe made
 * during load blocks the TUI. An endpoint that accepts SYNs but never answers is
 * capped here rather than at the 8s discovery budget.
 */
const STARTUP_PROBE_TIMEOUT_MS = 2000

/** Budget for the follow-up /api/v0/models and /props calls, once /models has answered. */
const SECONDARY_PROBE_TIMEOUT_MS = 5000

/** Interactive probe budget: nothing is blocking on startup, so allow the full discovery time. */
const INTERACTIVE_PROBE_TIMEOUT_MS = 8000

// ─── Model discovery ─────────────────────────────────────────────────────────

/** Used when a server tells us nothing at all about capacity. */
const DEFAULT_CONTEXT_WINDOW = 65536
const MAX_OUTPUT_CAP = 32768

/**
 * Names that identify a model as something other than a chat model. The \w* tails matter:
 * "embeddinggemma-300m" runs the two words together, so a trailing boundary never fires.
 */
const NON_CHAT_ID =
  /(^|[-_/.])(bge|gte|e5|tts|asr|stella\w*|nomic\w*|embed\w*|rerank\w*|whisper\w*|kokoro\w*|clip|colbert|siglip)([-_/.:]|$)/i
const NON_CHAT_TYPE = /embed|rerank|tts|asr|audio/i

/** Vision variants that servers with no modality reporting only signal through the name. */
const VISION_ID = /(^|[-_/.])(vision|vlm|vl)([-_/.:]|$)/i

export function positive(value: unknown): number | undefined {
  return typeof value === "number" && Number.isFinite(value) && value > 0 ? value : undefined
}

/** llama.cpp router mode hides the served context in the spawn args it reports per model. */
export function ctxFromLlamaRouter(status: any): number | undefined {
  const args = status?.args
  if (Array.isArray(args)) {
    for (let i = 0; i < args.length; i++) {
      const arg = String(args[i])
      // Both spellings appear in the wild: "--ctx-size 8192", "--ctx-size=8192", and "-c 8192".
      const inline = arg.match(/^(?:--ctx-size|-c)=(\d+)$/)
      if (inline) return Number.parseInt(inline[1], 10)
      if (arg === "--ctx-size" || arg === "-c") {
        const n = Number.parseInt(String(args[i + 1]), 10)
        if (Number.isFinite(n) && n > 0) return n
      }
    }
  }
  if (typeof status?.preset === "string") {
    const m = status.preset.match(/^\s*ctx-size\s*=\s*(\d+)/m)
    if (m) return Number.parseInt(m[1], 10)
  }
  return undefined
}

/**
 * llama-swap reports no capacity at all, but its model ids carry a -NNk marker. It is not
 * always the last segment ("...-192k-vision"), so scan for the final match rather than anchoring.
 */
export function ctxFromIdSuffix(id: string): number | undefined {
  const matches = [...id.matchAll(/-(\d+)k(?=[-:._]|$)/gi)]
  const last = matches[matches.length - 1]
  return last ? Number.parseInt(last[1], 10) * 1024 : undefined
}

export function parseModelEntry(raw: any): DiscoveredModel | null {
  if (typeof raw?.id !== "string") return null
  const id: string = raw.id

  // Ordered by how closely each field tracks what the server will actually serve. Over-claiming
  // is the dangerous direction: too large truncates or errors mid-session, too small only wastes.
  const contextWindow =
    positive(raw.loaded_context_length) ?? // LM Studio, loaded models: what it was loaded with
    positive(raw.max_model_len) ?? // vLLM, oMLX
    positive(raw.max_context_length) ?? // LM Studio /api/v0; model maximum, not the loaded size
    positive(raw.context_length) ?? // llama-swap, OpenRouter
    positive(raw.context_window) ??
    ctxFromLlamaRouter(raw.status) ?? // llama.cpp router mode
    ctxFromIdSuffix(id) // llama-swap naming convention, when nothing above is served

  const modalities = raw.architecture?.input_modalities
  const input: ("text" | "image")[] = Array.isArray(modalities)
    ? (modalities.filter((m: unknown) => m === "text" || m === "image") as ("text" | "image")[])
    : VISION_ID.test(id) || raw.type === "vlm"
      ? ["text", "image"]
      : ["text"]

  return {
    id,
    contextWindow,
    input: input.length > 0 ? input : ["text"],
    chat: !NON_CHAT_ID.test(id) && !NON_CHAT_TYPE.test(String(raw.type ?? "")),
    alias: raw.meta?.llamaswap?.type === "alias",
  }
}

export type EndpointProbe = {
  /** The server answered /models with JSON. Distinguishes "serving nothing" from "down". */
  reachable: boolean
  models: DiscoveredModel[]
}

/**
 * One /models request answers both reachability and discovery. Asking twice doubled the
 * wait on an endpoint that never answers, which is exactly the case the timeout exists for.
 */
export async function probeEndpoint(
  url: string,
  apiKey?: string,
  timeoutMs = 8000,
): Promise<EndpointProbe> {
  const payload = await fetchJson(`${url}/models`, apiKey, timeoutMs)
  if (payload === null) return { reachable: false, models: [] }

  // Independent of the primary budget: at the 2s startup cap a derived timeout collapsed
  // to 2s and made llama.cpp's /props probe time out, falling back to n_ctx_train.
  const secondaryTimeoutMs = SECONDARY_PROBE_TIMEOUT_MS
  const raw: unknown[] = Array.isArray(payload?.data) ? payload.data : []
  const models: DiscoveredModel[] = raw
    .map(parseModelEntry)
    .filter((m): m is DiscoveredModel => m !== null)
  if (models.length === 0) return { reachable: true, models }

  // LM Studio's OpenAI surface omits capacity entirely; its native API carries it.
  if (url.endsWith("/v1") && models.some((m) => m.contextWindow === undefined)) {
    const native = await fetchJson(`${url.slice(0, -3)}/api/v0/models`, apiKey, secondaryTimeoutMs)
    const byId = new Map<string, DiscoveredModel>()
    for (const entry of Array.isArray(native?.data) ? native.data : []) {
      const parsed = parseModelEntry(entry)
      if (parsed) byId.set(parsed.id, parsed)
    }
    for (const m of models) {
      const extra = byId.get(m.id)
      if (!extra) continue
      m.contextWindow ??= extra.contextWindow
      if (!extra.chat) m.chat = false
    }
  }

  // meta.n_ctx_train identifies a plain llama-server, and only that: llama-swap and router
  // mode both omit it. That matters, because /props on llama-swap would force a model load.
  // n_ctx_train is the *training* context, so read the served size off /props instead and
  // keep the training value only as the ceiling.
  if (url.endsWith("/v1") && raw.some((e: any) => positive(e?.meta?.n_ctx_train))) {
    const props = await fetchJson(`${url.slice(0, -3)}/props`, apiKey, secondaryTimeoutMs)
    const served = positive(props?.default_generation_settings?.n_ctx)
    for (const m of models) {
      if (m.contextWindow !== undefined) continue
      const trained = positive((raw as any[]).find((e) => e?.id === m.id)?.meta?.n_ctx_train)
      m.contextWindow = served && trained ? Math.min(served, trained) : (served ?? trained)
    }
  }
  return { reachable: true, models }
}

export async function fetchModelsFromEndpoint(
  url: string,
  apiKey?: string,
  timeoutMs?: number,
): Promise<DiscoveredModel[]> {
  return (await probeEndpoint(url, apiKey, timeoutMs)).models
}

// ─── Reasoning capability ────────────────────────────────────────────────────

/**
 * Templates driven by a boolean switch: thinking is either on or off, no gradations. The one
 * level left standing has to be "medium", for two reasons that both bite otherwise:
 * clampThinkingLevel scans *upward* from pi's "medium" default, so leaving only "high" starts
 * every unmatched model a level higher than asked; and the level name is what gets sent as
 * reasoning_effort, where stock Qwen3.8 raise_exception()s on "high" but accepts "medium".
 */
const BOOLEAN_LEVELS: ThinkingLevelMap = { minimal: null, low: null, high: null, xhigh: null }

/**
 * Every local chat template takes its thinking switch from chat_template_kwargs, and Jinja
 * silently drops names the template never defines - llama.cpp and vLLM both forward the whole
 * object untouched. So one bundle covers every family and the key names stop being a per-model
 * concern. Which key each template actually reads:
 *
 *   enable_thinking   Qwen, GLM, Gemma, DeepSeek (fallback)
 *   thinking          DeepSeek V3.1+ / V4 (primary)
 *   reasoning_effort  Qwen, DeepSeek V4
 *   preserve_thinking Qwen, Gemma - keep earlier think blocks when rendering history
 *   clear_thinking    GLM's inverted spelling of the same thing
 *
 * Only the reasoning_effort *value* is family-specific, which is what EFFORT_LEVELS handles.
 */
const THINKING_KWARGS: NonNullable<OpenAICompat["chatTemplateKwargs"]> = {
  enable_thinking: { $var: "thinking.enabled" },
  thinking: { $var: "thinking.enabled" },
  reasoning_effort: { $var: "thinking.effort", omitWhenOff: true },
  preserve_thinking: true,
  clear_thinking: false,
}

/**
 * The two families where the effort string is not free-form. Everything else is on/off, and
 * an unread reasoning_effort costs nothing. Order matters: R1 is matched before the general
 * DeepSeek pattern.
 */
const EFFORT_LEVELS: { re: RegExp; levels: ThinkingLevelMap }[] = [
  // R1 and its distills think unconditionally and read no effort, so "off" is not on offer.
  { re: /deepseek[-_]?r1|(^|[-_])r1([-_.]|$)/i, levels: { ...BOOLEAN_LEVELS, off: null } },
  // DeepSeek V4 branches on reasoning_effort 'high' and 'max' only; every other value renders
  // plain thinking mode. That plain mode is the model's own default and has to stay reachable,
  // so keep "medium" - dropping it left pi's default clamping up into the heavier 'high' branch
  // with no way back down short of switching thinking off entirely.
  { re: /deepseek(?!.*(coder|math|[-_]vl|llm|[-_]v2))/i, levels: { minimal: null, low: null, xhigh: "max" } },
  // Qwen3+ raise_exception()s on any reasoning_effort outside low/medium/xhigh, so offer exactly
  // those three. Community templates bucket rather than raise - froggeric's collapses
  // high/max/extreme onto xhigh - but the safe set is the same either way, and the stricter
  // templates are the ones that decide it.
  //
  // Hiding a level does not stop it being requested, it only decides what it becomes: pi's
  // clampThinkingLevel scans *upward* through off/minimal/low/medium/high/xhigh/max, so a caller
  // asking for "high" lands on xhigh and "minimal" lands on low. That matters because the subagent
  // tool advertises the full range as a spawn parameter, so the model picks it per spawn.
  //
  // Cache cost, on any template that renders the effort into the system block: "medium" emits
  // nothing and is byte-identical to sending no effort at all, so off<->medium is nearly free,
  // while low<->medium<->xhigh rewrites token ~5 and reprefills the whole prompt both ways.
  { re: /qwen-?3(?![0-9])|thinkingcap|hunyuan/i, levels: { minimal: null, high: null, xhigh: "xhigh" } },
  // Thinks unconditionally: enable_thinking:false is read by nothing in its template.
  { re: /minimax/i, levels: { ...BOOLEAN_LEVELS, off: null } },
]

/**
 * No local server reports whether a model thinks, and an id allow-list goes stale with every
 * release. Since the kwargs above are inert on a template that ignores them, default every chat
 * model to thinking-capable and let `"reasoning": false` in local-models.json opt one out.
 */
export function resolveLevels(id: string, override?: ModelOverride): ThinkingLevelMap | undefined {
  if (override?.reasoning === false) return undefined
  return EFFORT_LEVELS.find(({ re }) => re.test(id))?.levels ?? BOOLEAN_LEVELS
}

export function buildModelConfig(model: DiscoveredModel, override?: ModelOverride): ProviderModelConfig {
  const contextWindow = override?.contextWindow ?? model.contextWindow ?? DEFAULT_CONTEXT_WINDOW
  const levels = resolveLevels(model.id, override)
  const config: ProviderModelConfig = {
    id: model.id,
    name: model.id,
    reasoning: levels !== undefined,
    input: model.input,
    cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
    contextWindow,
    // Nothing in the OpenAI surface reports a max output size, and local servers just generate
    // until the context fills, so reserve most of the window for the prompt. The outer min
    // matters on small windows: a 4096 floor against a 4096 window leaves no room to prompt.
    maxTokens:
      override?.maxTokens ??
      Math.min(contextWindow >> 1, Math.max(4096, Math.min(MAX_OUTPUT_CAP, contextWindow >> 2))),
    // pi-ai auto-detects supportsDeveloperRole from the baseUrl, and every host on its
    // non-standard list is a named cloud provider - a local URL matches none of them, so it
    // resolves true and the system prompt goes out as role:"developer" for any reasoning model.
    // llama.cpp passes the role straight to the template: GLM 4.7 and 5.2 have no branch for it
    // and drop the prompt, stock Qwen3.8 raise_exception()s. No local template gains anything
    // from the role, so pin it off.
    compat: { supportsDeveloperRole: false },
  }
  if (levels) {
    config.thinkingLevelMap = levels
    config.compat = {
      ...config.compat,
      thinkingFormat: override?.thinkingFormat ?? "chat-template",
      chatTemplateKwargs: THINKING_KWARGS,
    }
  }
  return config
}

function getProviderName(endpoint: LocalEndpoint): string {
  return `local-${endpoint.id}`
}

/** Aliases duplicate real entries, and non-chat models only clutter the picker. */
export function selectableModels(endpoint: LocalEndpoint, models: DiscoveredModel[]): DiscoveredModel[] {
  return models.filter((m) => m.chat && !m.alias && endpoint.models?.[m.id]?.hidden !== true)
}

function registerLocalProvider(pi: ExtensionAPI, endpoint: LocalEndpoint, models: DiscoveredModel[]) {
  const usable = selectableModels(endpoint, models)
  if (usable.length === 0) return

  const configs = usable.map((m) => buildModelConfig(m, endpoint.models?.[m.id]))
  const providerName = getProviderName(endpoint)

  pi.registerProvider(providerName, {
    name: endpoint.name,
    baseUrl: endpoint.baseUrl,
    apiKey: endpoint.apiKey || "sk-no-key",
    api: "openai-completions",
    models: configs,
  })
}

function unregisterLocalProvider(pi: ExtensionAPI, endpoint: LocalEndpoint) {
  pi.unregisterProvider(getProviderName(endpoint))
}

// ─── State ───────────────────────────────────────────────────────────────────

import * as crypto from "node:crypto"
import * as fs from "node:fs"
import * as path from "node:path"

/** Resolved per call, not at import: a cached path would pin whatever HOME was at load time. */
function configFile(): string {
  return (
    process.env.PI_LOCAL_MODELS_CONFIG || path.join(process.env.HOME || "/tmp", ".pi/agent/local-models.json")
  )
}

// In-memory state, loaded from JSON file once
let endpoints: LocalEndpoint[] = []
/** Set when the config existed but could not be parsed; suppresses writes so it isn't clobbered. */
let loadFailed = false

function loadEndpoints(): LocalEndpoint[] {
  try {
    const raw = fs.readFileSync(configFile(), "utf-8")
    const parsed = JSON.parse(raw) as Partial<LocalEndpoint>[]
    let changed = false
    endpoints = parsed
      .filter((ep) => ep.name && ep.baseUrl)
      .map((ep) => {
        const normalized: LocalEndpoint = {
          id: ep.id || generateEndpointId(ep.baseUrl!),
          name: ep.name!,
          baseUrl: normalizeBaseUrl(ep.baseUrl!),
          apiKey: ep.apiKey || undefined,
          status: ep.status === "up" || ep.status === "down" ? ep.status : "checking",
          models: ep.models,
        }
        if (!ep.id || ep.baseUrl !== normalized.baseUrl || ep.status !== normalized.status) changed = true
        return normalized
      })
    loadFailed = false
    if (changed) saveEndpoints()
  } catch (e) {
    // Only an absent file is a clean empty start. A malformed one must not be overwritten:
    // saveEndpoints runs on every startup, so persisting [] here would destroy the config.
    loadFailed = (e as { code?: string })?.code !== "ENOENT"
    endpoints = []
    if (loadFailed) console.error(`local-models: refusing to overwrite unreadable ${configFile()}:`, e)
  }
  return endpoints
}

/** Set while the endpoints TUI is open, so a probe still in flight can repaint it. */
let onEndpointStatusChange: (() => void) | undefined

/**
 * Probed concurrently: this runs during extension load, so a serial sweep would add
 * every unreachable endpoint's full timeout to Pi's startup before the TUI appears.
 * Each endpoint repaints as it settles rather than at the end of the sweep, so a slow
 * or unreachable one never holds up the others.
 */
async function registerKnownEndpoints(pi: ExtensionAPI, timeoutMs: number): Promise<void> {
  await Promise.all(
    endpoints.map(async (ep) => {
      const { reachable, models } = await probeEndpoint(ep.baseUrl, ep.apiKey, timeoutMs)
      ep.status = reachable ? "up" : "down"
      // Drop the provider when an endpoint goes away, or /model keeps offering models
      // that nothing is serving. Unregistering an unknown provider is a no-op.
      if (models.length > 0) registerLocalProvider(pi, ep, models)
      else unregisterLocalProvider(pi, ep)
      onEndpointStatusChange?.()
    }),
  )
  saveEndpoints()
}

function saveEndpoints() {
  if (loadFailed) return
  try {
    const dir = path.dirname(configFile())
    fs.mkdirSync(dir, { recursive: true })
    fs.writeFileSync(configFile(), JSON.stringify(endpoints, null, 2))
  } catch (e) {
    console.error("Failed to save local models config:", e)
  }
}

/**
 * pi's ExtensionAPI setModel never persists ({persist: true} is only reachable from the
 * built-in /model selector's ctrl+s), so a model picked here lasted one session while
 * settings.json kept naming whatever was saved last - if that endpoint was gone, every
 * startup asked for a model again. Write the default straight into settings.json.
 *
 * pi's SettingsManager writes under a proper-lockfile lock (an mkdir'd settings.json.lock
 * directory, stale after 10s) and merges only the fields it modified onto the file's
 * current content, so a cooperative locked read-modify-write of just these two keys
 * survives pi's own saves and vice versa.
 */
export async function persistDefaultModel(provider: string, modelId: string): Promise<boolean> {
  const file = path.join(getAgentDir(), "settings.json")
  const lockDir = `${file}.lock`
  const deadline = Date.now() + 2000
  for (;;) {
    try {
      fs.mkdirSync(lockDir, { recursive: false })
      break
    } catch {
      try {
        if (Date.now() - fs.statSync(lockDir).mtimeMs > 10_000) {
          fs.rmSync(lockDir, { recursive: true, force: true })
          continue
        }
      } catch {}
      if (Date.now() > deadline) return false
      await new Promise((r) => setTimeout(r, 50))
    }
  }
  try {
    let settings: Record<string, unknown> = {}
    try {
      settings = JSON.parse(fs.readFileSync(file, "utf-8"))
    } catch (e) {
      // A missing file starts empty; a malformed one must not be flattened to two keys.
      if ((e as { code?: string })?.code !== "ENOENT") throw e
    }
    settings.defaultProvider = provider
    settings.defaultModel = modelId
    fs.writeFileSync(file, JSON.stringify(settings, null, 2))
    return true
  } catch (e) {
    console.error("local-models: failed to persist default model:", e)
    return false
  } finally {
    fs.rmSync(lockDir, { recursive: true, force: true })
  }
}

// ─── Extension ───────────────────────────────────────────────────────────────

export default async function (pi: ExtensionAPI) {
  // Register saved local providers during extension load, before Pi restores the
  // default/scoped model list. Registering in session_start is too late for
  // startup model resolution and `pi --list-models`.
  loadEndpoints()
  await registerKnownEndpoints(pi, STARTUP_PROBE_TIMEOUT_MS)

  // ─── /local-models command ──────────────────────────────────────────────

  pi.registerCommand("local-models", {
    description: "Manage local LLM endpoints",
    handler: async (_args, ctx) => {
      // Not awaited: the list is drawn from the saved config straight away and each row
      // flips from 🟡 to its real status as the probe lands. Awaiting here meant the
      // command blocked on the slowest endpoint before anything appeared.
      for (const ep of endpoints) ep.status = "checking"
      registerKnownEndpoints(pi, INTERACTIVE_PROBE_TIMEOUT_MS).catch((e) =>
        console.error("local-models: endpoint probe failed:", e),
      )

      await showEndpointsList(pi, ctx)
    },
  })
}

// ─── TUI: Endpoints list ─────────────────────────────────────────────────────

/** Both pickers in this file dress a SelectList the same way. */
function listTheme(theme: any) {
  return {
    selectedPrefix: (t: string) => theme.fg("accent", t),
    selectedText: (t: string) => theme.fg("accent", t),
    description: (t: string) => theme.fg("muted", t),
    scrollInfo: (t: string) => theme.fg("dim", t),
    noMatch: (t: string) => theme.fg("warning", t),
  }
}

async function showEndpointsList(pi: ExtensionAPI, ctx: any): Promise<void> {
  const items = buildEndpointItems()

  await ctx.ui.custom((tui: any, theme: any, _kb: any, done: (v: void | null) => void) => {
    const container = new Container()

    // Top border
    container.addChild(new DynamicBorder((s: string) => theme.fg("accent", s)))

    // Title
    container.addChild(new Text(theme.fg("accent", theme.bold(" Local Models - Providers ")), 1, 0))

    if (items.length === 0) {
      container.addChild(new Text(theme.fg("dim", "  No endpoints configured yet."), 1, 0))
      container.addChild(new Text(theme.fg("dim", "  Press 'a' to add one."), 1, 0))
    }

    const selectList = new SelectList(items, Math.min(items.length, 12), listTheme(theme))

    // Endpoints settle one at a time; repaint each row as its probe lands rather than
    // holding the whole list until the slowest one answers.
    const repaint = () => {
      for (const item of items) {
        const ep = endpoints.find((e) => e.id === item.value)
        if (ep) Object.assign(item, endpointItem(ep))
      }
      selectList.invalidate()
      container.invalidate()
      tui.requestRender()
    }
    onEndpointStatusChange = repaint
    const close = () => {
      onEndpointStatusChange = undefined
      done(null)
    }

    selectList.onSelect = async (item: SelectItem) => {
      const value = item.value
      if (value === "__add__") {
        close()
        await showAddEndpoint(pi, ctx)
        return
      }
      if (value === "__refresh__") {
        await refreshAllEndpoints(pi, repaint)
        return
      }
      // Select an endpoint → pick a model
      close()
      await selectModelForEndpoint(pi, ctx, value)
    }

    selectList.onCancel = () => close()

    container.addChild(selectList)

    // Help text
    container.addChild(new Spacer(1))
    container.addChild(
      new Text(theme.fg("dim", "  ↑↓ navigate • enter select • esc back • 'a' add • 'r' refresh • 'd' delete"), 1, 0),
    )

    // Bottom border
    container.addChild(new DynamicBorder((s: string) => theme.fg("accent", s)))

    return {
      render: (w: number) => container.render(w),
      invalidate: () => container.invalidate(),
      handleInput: (data: string) => {
        if (data === "a") {
          close()
          showAddEndpoint(pi, ctx)
          return
        }
        if (data === "r") {
          refreshAllEndpoints(pi, repaint)
          return
        }
        if (data === "d") {
          const selected = selectList.getSelectedItem()
          // The action rows share the list with real endpoints; only the latter can be removed.
          if (selected && selected.value !== "__add__" && selected.value !== "__refresh__") {
            close()
            confirmRemoveEndpoint(pi, ctx, selected.value)
            return
          }
        }
        selectList.handleInput?.(data)
        tui.requestRender()
      },
    }
  })
}

export function endpointItem(ep: LocalEndpoint): SelectItem {
  const statusIcon = ep.status === "up" ? "🟢" : ep.status === "down" ? "🔴" : "🟡"
  return {
    value: ep.id,
    label: `${statusIcon} ${ep.name}`,
    description: ep.status === "up" ? ep.baseUrl : `${ep.baseUrl} (${ep.status})`,
  }
}

function buildEndpointItems(): SelectItem[] {
  const items: SelectItem[] = endpoints.map(endpointItem)

  if (items.length > 0) {
    items.push({ value: "__refresh__", label: "🔄  Refresh all", description: "Check status of all endpoints" })
  }

  items.push({ value: "__add__", label: "➕  Add endpoint", description: "Configure a new local LLM endpoint" })

  return items
}

// ─── TUI: Add endpoint ───────────────────────────────────────────────────────

async function showAddEndpoint(pi: ExtensionAPI, ctx: any): Promise<void> {
  const name = await ctx.ui.input("Endpoint name", "e.g., llama.cpp, oMLX, LM Studio")
  if (!name) { await showEndpointsList(pi, ctx); return }

  const baseUrlInput = await ctx.ui.input("Base URL (with /v1)", "e.g., http://localhost:8000/v1")
  if (!baseUrlInput) { await showEndpointsList(pi, ctx); return }
  const baseUrl = normalizeBaseUrl(baseUrlInput)

  const existing = endpoints.find((ep) => normalizeBaseUrl(ep.baseUrl) === baseUrl)
  if (existing) {
    ctx.ui.notify(`${existing.name} is already onboarded as ${getProviderName(existing)}`, "info")
    await showEndpointsList(pi, ctx)
    return
  }

  const useKey = await ctx.ui.confirm("API Key", "Does this endpoint require an API key?")
  let apiKey: string | undefined
  if (useKey) {
    apiKey = await ctx.ui.input("API Key (leave empty if none)")
    if (apiKey === undefined) apiKey = ""
  }

  ctx.ui.notify(`Connecting to ${baseUrl}...`, "info")

  // Check endpoint and discover models
  const { reachable: isUp, models } = await probeEndpoint(baseUrl, apiKey)
  if (!isUp) {
    const retry = await ctx.ui.confirm("Connection failed", `Could not reach ${baseUrl}. Add anyway?`)
    if (!retry) return
  }

  const endpoint: LocalEndpoint = {
    id: generateUniqueEndpointId(baseUrl),
    name,
    baseUrl,
    apiKey: apiKey || undefined,
    status: isUp ? "up" : "down",
  }

  endpoints.push(endpoint)
  saveEndpoints()

  const usable = selectableModels(endpoint, models)
  if (isUp && usable.length > 0) {
    registerLocalProvider(pi, endpoint, models)
    const skipped = models.length - usable.length
    const skippedNote = skipped > 0 ? ` (${skipped} alias/non-chat skipped)` : ""
    ctx.ui.notify(`Registered ${endpoint.name} with ${usable.length} model(s)${skippedNote}`, "success")

    // Refresh model list in /model
    ctx.ui.notify("Check /model to select a local model", "info")
  } else if (isUp && usable.length === 0) {
    ctx.ui.notify(`${endpoint.name} is up but no models found`, "warning")
  } else {
    ctx.ui.notify(`${endpoint.name} added (offline)`, "warning")
  }

  await showEndpointsList(pi, ctx)
}

// ─── TUI: Filterable picker ──────────────────────────────────────────────────

/**
 * ctx.ui.select renders a plain scrolling list with no filtering, which does not survive an
 * endpoint serving 40+ models. SelectList.setFilter only does a prefix match on value, so drive
 * fuzzyFilter directly - that matches "27b" or "vision" mid-id, the way pi's own /model does.
 */
async function selectFromFilterableList(ctx: any, title: string, items: SelectItem[]): Promise<string | null> {
  return (await ctx.ui.custom((tui: any, theme: any, _kb: any, done: (v: string | null) => void) => {
    let query = ""
    let list = build()

    function build(): SelectList {
      const visible = query ? fuzzyFilter(items, query, (i) => `${i.label} ${i.description ?? ""}`) : items
      const selectList = new SelectList(visible, Math.min(Math.max(visible.length, 1), 12), listTheme(theme))
      selectList.onSelect = (item: SelectItem) => done(item.value)
      selectList.onCancel = () => done(null)
      return selectList
    }

    function matchCount(): number {
      return query ? fuzzyFilter(items, query, (i) => `${i.label} ${i.description ?? ""}`).length : items.length
    }

    return {
      render: (w: number) => [
        theme.fg("accent", theme.bold(` ${title} `)),
        theme.fg("dim", `  filter: ${query || "(type to filter)"}   ${matchCount()}/${items.length}`),
        ...list.render(w),
        theme.fg("dim", "  ↑↓ navigate • enter select • esc cancel • backspace edit filter"),
      ],
      invalidate: () => list.invalidate(),
      handleInput: (data: string) => {
        if (data === "\x7f" || data === "\b") {
          query = query.slice(0, -1)
          list = build()
        } else if (data.length === 1 && data >= " " && data <= "~") {
          query += data
          list = build()
        } else {
          list.handleInput(data)
        }
        tui.requestRender()
      },
    }
  })) as string | null
}

// ─── TUI: Select model for endpoint ──────────────────────────────────────────

async function selectModelForEndpoint(pi: ExtensionAPI, ctx: any, endpointId: string): Promise<void> {
  const ep = endpoints.find((e) => e.id === endpointId)
  if (!ep) return

  if (ep.status !== "up") {
    ctx.ui.notify(`${ep.name} is offline`, "error")
    return
  }

  const models = await fetchModelsFromEndpoint(ep.baseUrl, ep.apiKey)
  const usable = selectableModels(ep, models)
  if (usable.length === 0) {
    ctx.ui.notify("No chat models found on this endpoint", "error")
    return
  }

  // Surface what was detected, so a wrong context window is visible before it bites.
  const items: SelectItem[] = usable.map((m) => {
    const cfg = buildModelConfig(m, ep.models?.[m.id])
    const detected = m.contextWindow !== undefined
    return {
      value: m.id,
      label: m.id,
      description: `${Math.round(cfg.contextWindow / 1024)}k${detected ? "" : "?"}${cfg.reasoning ? " · thinking" : ""}`,
    }
  })

  const chosen = await selectFromFilterableList(ctx, `Models on ${ep.name}`, items)
  if (!chosen) return

  // Ensure provider is registered, then switch the active Pi model.
  registerLocalProvider(pi, ep, models)
  const model = ctx.modelRegistry.find(getProviderName(ep), chosen)
  if (!model) {
    ctx.ui.notify(`Model not found after registration: ${getProviderName(ep)}/${chosen}`, "error")
    return
  }
  const success = await pi.setModel(model)
  if (!success) {
    ctx.ui.notify(`No API key available for ${getProviderName(ep)}/${chosen}`, "error")
    return
  }
  const persisted = await persistDefaultModel(getProviderName(ep), chosen)
  ctx.ui.notify(
    persisted
      ? `Selected ${getProviderName(ep)}/${chosen} (saved as default)`
      : `Selected ${getProviderName(ep)}/${chosen} - could not save as default, settings.json is locked`,
    persisted ? "success" : "warning",
  )
}

// ─── TUI: Refresh all endpoints ──────────────────────────────────────────────

/** Re-probes in place: the list stays on screen and each row updates as its probe lands. */
async function refreshAllEndpoints(pi: ExtensionAPI, repaint: () => void): Promise<void> {
  for (const ep of endpoints) {
    ep.status = "checking"
  }
  repaint()
  await registerKnownEndpoints(pi, INTERACTIVE_PROBE_TIMEOUT_MS)
}

// ─── TUI: Remove endpoint ────────────────────────────────────────────────────

async function confirmRemoveEndpoint(pi: ExtensionAPI, ctx: any, endpointId: string): Promise<void> {
  const ep = endpoints.find((e) => e.id === endpointId)
  if (!ep) return

  const ok = await ctx.ui.confirm("Remove endpoint", `Delete "${ep.name}" (${ep.baseUrl})?`)
  if (!ok) {
    await showEndpointsList(pi, ctx)
    return
  }

  unregisterLocalProvider(pi, ep)
  endpoints = endpoints.filter((e) => e.id !== endpointId)
  saveEndpoints()
  ctx.ui.notify(`Removed ${ep.name}`, "info")
  await showEndpointsList(pi, ctx)
}
