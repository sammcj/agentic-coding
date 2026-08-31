# Prompt cache diagnostics

Tools for working out why a local llama.cpp-style server is reprefilling prompts it should be reusing.

## The failure they were built for

llama.cpp keeps one KV cache per slot and reuses the longest common _prefix_ of the incoming tokens. Qwen-style chat templates render the tool definitions at the **front** of the system block and append the system prompt after them, so the tool JSON is the first few thousand tokens of every request. One reordered or added tool discards the prefix from that point on, including a byte-identical system prompt sitting behind it.

Measured on one session: every `general-purpose` spawn carried the same 44 tools and the same 29,169-byte system prompt, but the tool array arrived in one of two orders, alternating per spawn. Whole extension blocks moved as units. Nothing after the first divergent tool was ever reused.

Two independent faults, and they must be fixed in this order:

1. **Set membership.** A tool present in some requests and absent from others displaces everything behind it. No ordering change can fix this.
2. **Order.** The same set in different arrangements. `extensions/stable-tool-order.ts` sorts by name on `before_provider_request`, scoped to local providers.

**Sorting an unstable set is worse than doing nothing.** Measured at 5,288 shared characters before sorting and 0 after, on a pair differing by one tool that happened to sort first. Confirm the set is constant before trusting the sort to help.

## Capturing

`extensions/prompt-cache-doctor.ts` is the normal way in. It hooks `before_provider_request`, so there is no proxy and no endpoint reconfiguration:

- `/prompt-cache` - report: per-agent tool set/order counts, system prompt hashes, first divergent stage
- `/prompt-cache record` - toggle full payload dumps into `captures/`
- `/prompt-cache reset` - clear accumulated state

It also publishes a `cache NN%` segment to the footer via `ctx.ui.setStatus`. A footer that calls `ctx.ui.setFooter` must render `footerData.getExtensionStatuses()` itself or the segment is silently swallowed.

`capture-proxy.mjs` is the fallback: a recording reverse proxy that writes each `/chat/completions` body and streams responses through untouched. Only worth it when you need the exact wire bytes rather than pi's pre-serialisation payload, or when capturing from a client that is not pi.

```
node capture-proxy.mjs http://127.0.0.1:8080/v1
```

The upstream is required, as an argument or as `UPSTREAM`. There is no default, so nothing here carries a private hostname. `PORT` (8899) and `OUTDIR` (`./captures`) do have defaults.

Then point the endpoint in `local-models.json` at `http://127.0.0.1:8899/v1`.

## Analysing

The extension's report handles triage. These two do things it structurally cannot:

**`diff-prompts.py a.json b.json`** - renders both captures through the real chat template and reports the first differing _byte_. The extension's `diverge()` is structural, so it names the stage (kwargs / tools / system / messages) but never the offset.

```
PROMPT_TEMPLATE=/path/to/chat_template.jinja uv run diff-prompts.py captures/003-*.json captures/007-*.json
```

Without `PROMPT_TEMPLATE` the rendered section is skipped and only the payload fields are compared, which is still enough to attribute a divergence.

`jinja2` is declared in a PEP 723 block at the top of the script, so `uv run` fetches it into an isolated env with no venv to manage. Plain `python3` works where jinja2 is already installed. `tool-blocks.py` is stdlib only.

**`tool-blocks.py a.json b.json`** - both tool arrays side by side, grouped into contiguous runs. Extensions register tools in blocks, so this shows at a glance whether a reordering is block-level (extension load order) or interleaved (something stranger). This was the single most diagnostic output of the original investigation.

## Tests

The extensions' tests follow the repo convention and live in `agent/tests/`, not here. They sit outside `extensions/` deliberately: pi loads every `extensions/*.ts` as an extension, so a test file in there would be executed as one at startup.

```
bun test tests/stable-tool-order.test.ts    # sortToolsByName + isLocalRequest
bun test tests/prompt-cache-doctor.test.ts  # fingerprint / diverge / buildReport
bun test tests/footer-stats.test.ts         # cache-rate maths and the footer highlight rule
```

`tests/footer-stats.test.ts` reimplements rather than imports, because the cache-rate maths lives inside an event handler and the footer highlight rule lives inside a render closure, neither with an exported seam. Keep it in step with the originals.

What lives here instead is `replay.mjs`, which runs `buildReport` over saved captures so the extension's verdict can be checked against a run whose answer is already known:

```
bun replay.mjs captures/
```

`bun` runs the TypeScript imports directly; plain `node` will not.

## Ruled out

Worth knowing so they are not re-investigated:

- **System prompt** - byte-identical at 29,169 chars throughout
- **`pi-subagents` prefix ordering** - correct by design; `promptMode: "append"` places the parent prompt verbatim first, and `"replace"` is a deliberate choice
- **pi's extension loader** - serial and deterministic
- **`reasoning_effort` position** - real on templates that render it into the system block, but `medium` emits zero bytes and is byte-identical to omitting the field, so it was inert in this workload

## Known limits

- The main session and its subagents legitimately carry different tools (38 vs 44) and different system prompts (20,190 vs 29,169 bytes). On a tools-first template they can never share a prefix. That is by design.
- `subagents.json` `maxConcurrent` above 1 against a single-slot server (`-np 1`) means concurrent spawns interleave through one slot and evict each other's prefix regardless of prompt identity.

## Privacy

`captures/` holds complete system prompts and conversation content. `diagnostics/captures/` is in `agent/.gitignore`; keep it that way. `**/fixtures/` is ignored too.

Nothing in these scripts names a host. The endpoint id in `tests/stable-tool-order.test.ts` is an opaque hash, not a URL.
