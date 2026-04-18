---
name: llama-swap
display_name: llama-swap
aliases: [llama-swap, llamaswap]
output_file: resources/outputs/llama-swap.md
version_scheme: build-number
---

# llama-swap Profile

## Sources

- **Primary** (releases to diff against):
  - https://github.com/mostlygeek/llama-swap/releases - GitHub releases cut by a bot. Tags are monotonic build numbers (`v164`, `v170`, ..., `v202`). Bodies are usually empty or a one line note; the useful content is the auto-generated `## Changelog` block (commit list, often with PR numbers).
- **Supporting** (for context / linking):
  - https://raw.githubusercontent.com/mostlygeek/llama-swap/refs/heads/main/config.example.yaml - always-current example config with inline comments for every key. Use to validate whether a release changed the schema.
  - https://github.com/mostlygeek/llama-swap/blob/main/docs/configuration.md - prose docs for config keys (`ttl`, `macros`, `matrix`, `hooks`, `env`, `aliases`, `filters`).
  - https://raw.githubusercontent.com/mostlygeek/llama-swap/refs/heads/main/config-schema.json - JSON schema referenced by the YAML modeline; useful to confirm a new/renamed key.

## Version Scheme

Tags are `v<N>` where `N` is a monotonically increasing integer build number, not semver. Newer tag = larger integer (`v202` is newer than `v164`). "Newer than last_seen_version" is a numeric compare on the integer suffix. Do NOT sort tags lexicographically (`v99` would appear after `v200`). Strip the leading `v` and compare as ints. Assets are named `llama-swap_<N>_<os>_<arch>.tar.gz` without the `v`.

## Buckets

Group release entries under these headings. Assign by reading the commit prefix in the auto-generated changelog (e.g. `proxy:`, `config:`, `docker/unified:`, `ui-svelte:`, `docs:`, `ci:`, `build(deps):`).

- **Proxy / routing**: Request handling, new upstream endpoints (`/v1/messages`, `/v1/images/generations`, `/sdapi`, `/infill`), metrics capture, timeouts, panic recovery. Commits usually prefixed `proxy:` or `proxy,proxy/config:`.
- **Model lifecycle (swap / matrix / groups)**: The solver-based `matrix` swap DSL (added in v202, #646), legacy `groups`, preload/evict behaviour, TTL, concurrent model orchestration.
- **Config / YAML schema**: New top-level keys or per-model fields, `macros` (including macro-in-macro, v164), macro expansion in new places (peer `apiKey`, `filters`, `name`, `description`), schema validation in CI.
- **UI / playground (ui-svelte)**: The bundled Svelte UI - new tabs (Rerank, v195), request/response capturing, Vite upgrades, frontend security fixes.
- **Docker / build**: `docker/unified` image variants (rootless, CUDA, ik_llama.cpp), `CMAKE_CUDA_ARCHITECTURES` build arg, static llama.cpp builds, custom base image support.
- **Observability / metrics**: Metrics endpoint behaviour, wall-clock duration preservation, in-memory metrics buffer, loading-state streaming in the `reasoning` field.
- **Fixes / hardening**: Bug fixes with no new surface area (panic recovery, natural model sort, security patches). Use for items that don't fit the feature buckets above.

## Feature Link Table

Deep-linkable anchors in `docs/configuration.md` are limited, so prefer linking to `config.example.yaml` line references or the feature row in the docs table. PR numbers resolve via `https://github.com/mostlygeek/llama-swap/pull/<N>`.

| Area | Anchor / URL |
|------|--------------|
| `matrix` (solver-based concurrent models) | https://github.com/mostlygeek/llama-swap/blob/main/config.example.yaml (search `matrix:`) / PR #646 |
| `groups` (legacy concurrent models) | https://github.com/mostlygeek/llama-swap/blob/40e39f7/config.example.yaml#L334-L396 |
| `macros` | https://github.com/mostlygeek/llama-swap/blob/main/config.example.yaml (search `macros:`) |
| `hooks` (only `on_startup.preload` today) | https://github.com/mostlygeek/llama-swap/blob/main/config.example.yaml (search `hooks:`) |
| Model `cmd` / `cmdStop` / `proxy` / `checkEndpoint` / `ttl` / `env` / `aliases` / `filters` | https://github.com/mostlygeek/llama-swap/blob/main/docs/configuration.md |
| Config schema (JSON) | https://raw.githubusercontent.com/mostlygeek/llama-swap/refs/heads/main/config-schema.json |
| Unified Docker image | https://github.com/mostlygeek/llama-swap/tree/main/docker/unified |

## Out of Scope

Skip unless the user asks: `build(deps):` bumps (picomatch, Vite minor bumps, etc.) that don't change runtime behaviour, `ci:` workflow tweaks that don't ship in the binary, README wording fixes, asset-list boilerplate in the release page, and dependency security advisories that are already fixed by the bump itself.

## Gotchas

- Release tags are `v<build-number>`, not semver. `v202` is newer than `v99`, but alphabetical sort puts `v99` last. Always parse the integer.
- Release bodies are usually empty. The real changelog is the auto-generated commit list under `## Changelog`. Some tags (e.g. v164, v180, v185, v195) are single-commit releases, so one line in the changelog is the whole release.
- `groups` is legacy as of v202 and replaced by the new `matrix` solver (PR #646). A config can use `matrix` OR `groups`, never both - config loading errors out otherwise. Flag any user on an older build who writes `groups:` that they should plan to migrate.
- Config schema changes are load-bearing: when keys move, are renamed, or gain required subkeys, users' YAML stops validating against `config-schema.json`. Call schema-affecting commits out prominently and cross-reference the current `config.example.yaml`.
- The bundled UI (`ui-svelte`) ships inside the binary; a `ui-svelte:` security or Vite bump is still a user-facing change, not pure frontend housekeeping.
