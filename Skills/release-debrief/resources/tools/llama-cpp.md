---
name: llama-cpp
display_name: llama.cpp
aliases: [llama-cpp, llama.cpp, llamacpp]
output_file: resources/outputs/llama-cpp.md
version_scheme: build-number
---

# llama.cpp Profile

Server-focused. This profile covers `llama-server` (under `tools/server/`): HTTP API, server CLI flags, sampling and chat-template behaviour exposed through the server, new model and multimodal architectures the server can serve, and backend changes only when they show up as user-visible server performance or new serving capability. Everything else (non-server CLIs, library internals, model-arch work that doesn't reach the server, conversion-script hygiene) is out of scope.

## Sources

- **Primary** (releases to diff against):
  - https://github.com/ggml-org/llama.cpp/releases. Tags are `b<N>` (e.g. `b8833`). Each release body has one auto-generated title line derived from a single squash-merged commit, followed by the full commit message inside a `<details>` block, then a fixed "Assets" section listing per-platform binaries (macOS/iOS/Linux/Android/Windows/openEuler). Release notes are not curated, there is no "Highlights" section, and there is no CHANGELOG.md at the repo root.
- **Supporting** (for context / linking):
  - https://raw.githubusercontent.com/ggml-org/llama.cpp/refs/heads/master/tools/server/README.md. Current user-facing `llama-server` docs: features list, CLI flags (common, sampling, server-specific), and HTTP API endpoint reference.
  - https://github.com/ggml-org/llama.cpp/issues/9291. Pinned "server changelog" tracker issue, referenced from the server README for long-running feature history.

## Version Scheme

Tags use a monotonically increasing build number: `b<N>` where `N` is the CI build counter (currently `b8833`, 2026-04-17). Every merge to `master` produces a tagged release, so there is no semver, no minor/major distinction, and no pre-release channel. Compare versions by stripping the leading `b` and doing an integer compare: `int(tag[1:])`. Do not lexicographically sort tag strings, `b9000` sorts before `b8833` as a string.

## Buckets

Bucket by commit prefix parsed from the first non-empty line of the release body (or the release title, which is the same string). Everything should answer the question "does this change affect a user running `llama-server`?"; if not, drop it (see Out of Scope). Map server-relevant commits into:

- **HTTP API and endpoints**: `server:` commits that add/change endpoints, response shapes, streaming behaviour, OAI/Anthropic compatibility, function calling, multimodal over HTTP, `/slots`, `/props`, `/health`, `/metrics`, the built-in web UI. This is the highest-signal bucket.
- **Server CLI flags and config**: `server:` commits that add, rename, deprecate, or change defaults on `llama-server` flags (`--host`, `--port`, `--ctx-size`, `--parallel`, `--cont-batching`, `--jinja`, `--chat-template`, `LLAMA_ARG_*` env vars, etc.). Breaking flag changes are load-bearing for users' launch scripts.
- **Sampling and chat templates (server-visible)**: `tokenizer:`, `autoparser:`, chat template parsing, jinja handling, tool-call parsing - but only when the change is exposed through the server's request/response or the `--chat-template` / `--jinja` flags. Purely library-internal parser work goes in Out of Scope.
- **Model and multimodal support**: `model:`, `models:`, `mtmd:`, and supporting `convert:` / `tokenizer:` work that lets `llama-server` load or serve a new architecture, vision/audio encoder, or chat template. New model families are high-signal even when only part of the commit sequence is server-facing - summarise the end-to-end story (arch added, conversion supported, chat template landed, server can serve it). Skip library-only arch work that doesn't reach the server.
- **Server performance and serving capability**: backend commits (`CUDA:`, `metal:`, `vulkan:`, `sycl:`, `hexagon:`, `rpc:`, `ggml-cpu:`, KV cache type additions, speculative decoding wiring) when they produce a measurable server-side speed-up, enable a new device for serving, or change default kernel selection. Drop pure kernel refactors.
- **Serving-relevant quantisation**: new quant types or KV cache types that can be loaded and served. Plain GGUF conversion-script changes that don't touch server loading belong in Out of Scope.
- **Server build and packaging**: Docker images for `llama-server`, new platform tarballs that include the server binary, CUDA/ROCm toolchain version bumps in published assets. Skip pure CMake plumbing.

## Feature Link Table

The server README has stable slugified anchors per heading. Use these for deep-link summaries.

| Area | Anchor / URL |
|------|--------------|
| Features list | https://github.com/ggml-org/llama.cpp/tree/master/tools/server#llamacpp-http-server |
| CLI arguments (common / sampling / server) | https://github.com/ggml-org/llama.cpp/tree/master/tools/server#usage |
| API endpoints index | https://github.com/ggml-org/llama.cpp/tree/master/tools/server#api-endpoints |
| `POST /completion` | https://github.com/ggml-org/llama.cpp/tree/master/tools/server#post-completion-given-a-prompt-it-returns-the-predicted-completion |
| `/v1/chat/completions` (OAI) | https://github.com/ggml-org/llama.cpp/tree/master/tools/server#openai-compatible-api-endpoints |
| `POST /embedding` and `/v1/embeddings` | https://github.com/ggml-org/llama.cpp/tree/master/tools/server#post-embedding-generate-embedding-of-a-given-text |
| `POST /reranking` | https://github.com/ggml-org/llama.cpp/tree/master/tools/server#post-reranking-rerank-documents-according-to-a-given-query |
| `POST /infill` | https://github.com/ggml-org/llama.cpp/tree/master/tools/server#post-infill-for-code-infilling |
| `GET /props`, `GET /slots`, `GET /health` | https://github.com/ggml-org/llama.cpp/tree/master/tools/server#api-endpoints |
| Multimodal (HTTP) | https://github.com/ggml-org/llama.cpp/tree/master/tools/server#multimodal-support |
| Built-in tools (function calling) | https://github.com/ggml-org/llama.cpp/tree/master/tools/server#built-in-tools-support |
| Server changelog tracker | https://github.com/ggml-org/llama.cpp/issues/9291 |

Always link to the specific `b<N>` release page alongside the server README anchor when a change is user-visible.

## Out of Scope

This profile is server-only. Drop everything below unless the user explicitly asks for broader coverage.

- Non-server CLI binaries entirely: `llama-cli`, `llama-run`, `llama-bench`, `llama-quantize`, `llama-mtmd-cli`, `llama-embedding`, `llama-gguf-hash`, and friends. Any `cli:` prefix, any change scoped to `tools/main/`, `tools/run/`, `tools/bench/`, `tools/quantize/`, `tools/imatrix/`, etc.
- Library internals: `ggml :`, `ggml-ext`, `ggml-cpu:` kernel refactors, `llama :` internal changes, header moves, symbol renames, graph or allocator tweaks that don't alter server behaviour.
- The `sync : ggml` commits that pull upstream ggml changes. Always drop by default.
- Backend work (`CUDA:`, `metal:`, `vulkan:`, `sycl:`, `opencl:`, `hexagon:`, `rpc:`, `ggml-webgpu:`) that is a pure kernel tweak, op addition, or refactor with no user-visible server impact. Only keep backend commits that produce a measurable server speed-up, enable a new device for serving, or change server defaults.
- Model conversion tooling (`convert:`, `convert-hf-to-gguf`, tokeniser conversion) when it is pure script hygiene - refactors, error-message tweaks, or format fixups for models that were already convertible and servable. Keep conversion changes that unblock a new architecture or chat template for `llama-server`.
- Model-architecture commits that land an internal implementation but don't yet reach the server (no conversion, no chat template, no `llama-server` path). Flag these as "staged for future support" only if the user asks for a broader model-support view.
- CI tweaks (`ci :`), CMake plumbing that isn't a new user-facing build flag, test-only changes (`server: tests: ...`, generic `tests:`), doc changes unless the doc describes a new server feature.
- `examples/` folder churn outside `tools/server/`.
- Asset/binary list changes unless the change adds, removes, or bumps a server-relevant platform or CUDA/ROCm toolchain.
- Python SDK / bindings changes (`python :`, `libs :` in `gguf-py`) unless they expose a new server feature.

## Gotchas

- Tag `b<N>` sorts wrong as a string. Strip the `b` and compare as integer: `sorted(tags, key=lambda t: int(t[1:]))`. `b9000 > b8999` lexicographically is only coincidentally correct.
- Release cadence is extreme. Observed 30 tags in roughly 3 days (2026-04-14 to 2026-04-17), and 73 tags in the preceding ~7 days. A week-long delta commonly exceeds 50 releases. Group aggressively by bucket, deduplicate near-identical titles (e.g. multiple `CUDA:` kernel tweaks), and skip trivial entries.
- Each release body is a single squash commit, not a multi-item changelog. Do not look for bullet lists of changes per release, parse the commit title line for the prefix and the PR number (`(#21611)`).
- Prefix separators vary: `server:`, `server :`, `CUDA:`, `[SYCL]`, `ggml-cpu:`. Normalise to lowercase and strip brackets and whitespace before bucketing.
- `mtmd:` prefix means multimodal tokeniser/decoder work. It is user-visible for vision/audio models and belongs in "Model support", not "Server".
- Asset list is long (macOS arm64/x64/Kleidi, iOS XCFramework, Linux x64/arm64/s390x with CPU/Vulkan/ROCm/OpenVINO variants, Android arm64, Windows x64/arm64 with CPU/CUDA 12/CUDA 13/Vulkan/SYCL/HIP, openEuler 310p/910b). Strip it from summaries, only surface diffs when a new platform or toolchain version is added.
- `tools/server/README.md` uses GitHub slugified anchors (lowercase, spaces to `-`, punctuation stripped). Construct anchors from the heading text rather than guessing.
- Release notes do not flag breaking changes explicitly. Watch for commits that rename CLI flags (`LLAMA_ARG_*` env vars), change default values (the README calls out several `--no-*` toggles), remove deprecated flags (e.g. `-dt, --defrag-thold` is marked DEPRECATED in current README), or change endpoint response shapes. Treat these as high-priority entries.
- First-run default of 3 releases is misleadingly narrow for llama.cpp - at the current cadence that can be under an hour of changes and mostly noise. On a genuine first run, ask the user what window they want (a day, a week, or a specific tag) before committing to the 3-release default.
