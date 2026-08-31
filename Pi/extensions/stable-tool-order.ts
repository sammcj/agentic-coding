/**
 * Stable Tool Order
 *
 * Sorts the tool array by name on every outgoing provider request.
 *
 * Why: llama.cpp keeps one KV cache per slot and reuses the longest common prefix of the
 * incoming tokens. Qwen-style chat templates render the tool definitions at the *front* of
 * the system block and append the system prompt after them, so the tool JSON is the first
 * few thousand tokens of every request. One reordered tool discards the prefix from that
 * point on, including a system prompt behind it that may be byte-identical.
 *
 * Measured, 21 captured requests from one session: every `general-purpose` spawn carried the
 * same 44 tools and the same 29,169-byte system prompt, but the tool array arrived in one of
 * two orders, alternating per spawn. Whole extension blocks moved as units - pi loads
 * extensions serially and concatenates their tools, so order is load order, and something
 * upstream of that is not deterministic. The system prompt behind the divergence was lost
 * every time the order flipped.
 *
 * Scope: this fixes ORDER, not set membership. Sorting only helps when every request carries
 * the same tools. If one request has a tool another lacks, that tool displaces everything
 * behind it wherever it sorts to, and sorting can be worse than leaving well alone - measured
 * at 5,288 shared characters before sorting and 0 after, on a pair differing by one tool that
 * happened to sort first. Confirm the set is constant (`/prompt-cache` reporting one tool set
 * per agent, with no TOOL SET VARIES) before trusting this to help.
 *
 * Agents with genuinely different tools - the main session has Agent/steer_subagent and lacks
 * grep/find/ls - cannot share a prefix on this template regardless, since the tool block
 * precedes the system prompt. That is by design, not a fault.
 */

import type { ExtensionAPI } from "@earendil-works/pi-coding-agent"

/**
 * Provider-name prefix owned by local-models.ts, whose getProviderName() returns
 * `local-${endpoint.id}`. Kept as a constant rather than importing across extensions: a
 * cross-import would evaluate that module's provider registration from here, which is a
 * lot of coupling to carry for one string. If the prefix ever changes there, change it here.
 */
const LOCAL_PROVIDER_PREFIX = "local-"

/**
 * Sorting only pays off where the server reuses a *prefix* and the template renders tools
 * first - a local llama.cpp-style endpoint. Hosted providers cache by explicit breakpoint
 * (Anthropic) or by a server-managed key (OpenAI), so reordering their tools buys nothing
 * and still changes what the model is shown. Restrict to local providers.
 *
 * Resolves the payload's model id through the registry rather than trusting the session's
 * active model, because a subagent can run on a different model than its parent and several
 * requests can be in flight at once. Falls back to the active model only when the registry
 * has nothing to say.
 */
export function isLocalRequest(
  modelId: unknown,
  registered: { id: string; provider: string }[],
  activeProvider: string | undefined,
): boolean {
  if (typeof modelId === "string") {
    const matches = registered.filter((m) => m.id === modelId)
    // An id served by both a local and a hosted provider is ambiguous, so leave it alone.
    if (matches.length > 0) return matches.every((m) => m.provider.startsWith(LOCAL_PROVIDER_PREFIX))
  }
  return typeof activeProvider === "string" && activeProvider.startsWith(LOCAL_PROVIDER_PREFIX)
}

/** OpenAI tool entries are `{function:{name}}`; pi also emits `{custom:{name}}` for grammar tools. */
function toolName(tool: unknown): string {
  const t = tool as { function?: { name?: unknown }; custom?: { name?: unknown } }
  const name = t?.function?.name ?? t?.custom?.name
  return typeof name === "string" ? name : ""
}

/**
 * Sorting is only safe if the names are unique - two tools sharing a name would otherwise be
 * ordered by whatever the sort does with equal keys, which is the non-determinism this is
 * meant to remove. Duplicate or unnameable entries leave the array untouched.
 */
export function sortToolsByName(tools: unknown[]): unknown[] {
  const names = tools.map(toolName)
  if (names.some((n) => n === "")) return tools
  if (new Set(names).size !== names.length) return tools
  return [...tools].sort((a, b) => (toolName(a) < toolName(b) ? -1 : toolName(a) > toolName(b) ? 1 : 0))
}

export default function (pi: ExtensionAPI) {
  pi.on("before_provider_request", (event, ctx) => {
    const payload = event.payload as { tools?: unknown[]; model?: unknown } | undefined
    if (!payload || !Array.isArray(payload.tools) || payload.tools.length < 2) return

    let registered: { id: string; provider: string }[] = []
    try {
      registered = ctx.modelRegistry?.getAll?.() ?? []
    } catch {
      // A registry mid-refresh is not a reason to fail the request; fall through to ctx.model.
    }
    if (!isLocalRequest(payload.model, registered, ctx.model?.provider)) return

    const sorted = sortToolsByName(payload.tools)
    if (sorted === payload.tools) return
    // Returning a new payload replaces it for the rest of the chain; mutating in place would
    // work too, but a copy keeps this handler free of side effects on pi's state.
    return { ...payload, tools: sorted }
  })
}
