---
name: opencode
display_name: OpenCode
aliases: [opencode, open-code]
output_file: resources/outputs/opencode.md
version_scheme: semver
---

# OpenCode Profile

## Sources

- **Primary** (changelog to diff against):
  - https://opencode.ai/changelog - single long page with every release block, newest on top. Each block is anchored by a semver tag (e.g. `v1.4.10`) and a human date (e.g. `Apr 17, 2026`).
- **Supporting** (for context / linking):
  - https://opencode.ai/docs - docs index and "Intro" page, covers install, `/connect`, `/init`, and pointers into the rest of the docs tree.
  - https://opencode.ai/docs/config/ - JSON/JSONC config schema, precedence order (remote -> global -> project -> managed), and `.opencode/` directory layout for agents, commands, plugins, skills, tools, themes.
  - https://github.com/anomalyco/opencode - source repo and GitHub Releases (note: npm package is `opencode-ai`, Homebrew tap is `anomalyco/tap/opencode`; the project is maintained under the `anomalyco` org).

## Version Scheme

OpenCode ships semver releases (e.g. `v1.3.9`, `v1.4.0`, `v1.4.10`) and each release block on the changelog page also carries a human date like `Apr 17, 2026`. Releases are frequent (multiple per week - `v1.4.0` through `v1.4.10` land inside a fortnight), so lexical comparison of `v1.3.9` vs `v1.3.10` will be wrong; parse as proper semver (major.minor.patch) when computing "what's newer than `last_seen_version`". Patch numbers go double-digit, so string sort is unsafe. The date line is useful for display but the semver tag is the canonical identifier.

## Buckets

Group changelog entries under these headings when summarising. OpenCode's own changelog already uses these as `### ` subheadings inside each release block, so mirror them rather than inventing new ones.

- **Core**: server/runtime changes - providers, models, sessions, workspaces, auth, ACP, LSP, bash tool, telemetry (OTEL/OTLP), HTTP proxy. Highest-signal bucket; lead with this.
- **TUI**: terminal UI behaviour - keybinds, pickers, attachments (PDF drag-drop), `opencode run` flags, paste handling, model/provider selectors.
- **Desktop**: the desktop app - Windows backend, terminal connections, prompt submission, session review, diff rendering.
- **SDK**: generated JS SDK and OpenAPI types for `/providers`, session/shell endpoints, error surfaces when hitting older servers.
- **Extensions**: plugins, themes-as-packages, plugin install/auth behaviour, package-export option defaults.
- **Providers & Models**: carve-out from Core when a release is heavy on provider work (Anthropic reasoning levels, GitHub Copilot, OpenRouter, Azure `store=true`, Alibaba retries, Cloudflare AI Gateway, Claude Opus 4.7 xhigh reasoning). Flag but don't always break out - only if a release has 3+ provider-specific items.
- **Config & Permissions**: changes to the JSON config schema, `.well-known/opencode` remote config, managed settings, permission prompts, `--dangerously-skip-permissions`.

## Feature Link Table

The docs site has stable per-topic pages, so deep-link when relevant.

| Area | Doc URL |
|------|---------|
| Agents | https://opencode.ai/docs/agents/ |
| Commands | https://opencode.ai/docs/commands/ |
| Config | https://opencode.ai/docs/config/ |
| MCP servers | https://opencode.ai/docs/mcp-servers/ |
| Plugins | https://opencode.ai/docs/plugins/ |
| Skills | https://opencode.ai/docs/skills/ |
| Custom tools | https://opencode.ai/docs/custom-tools/ |
| Providers | https://opencode.ai/docs/providers/ |
| Models | https://opencode.ai/docs/models/ |
| LSP | https://opencode.ai/docs/lsp/ |
| Formatters | https://opencode.ai/docs/formatters/ |
| Keybinds | https://opencode.ai/docs/keybinds/ |
| Themes | https://opencode.ai/docs/themes/ |
| Permissions | https://opencode.ai/docs/permissions/ |
| ACP | https://opencode.ai/docs/acp/ |
| SDK | https://opencode.ai/docs/sdk/ |
| IDE | https://opencode.ai/docs/ide/ |
| CLI | https://opencode.ai/docs/cli/ |
| GitHub app | https://opencode.ai/docs/github/ |
| GitLab app | https://opencode.ai/docs/gitlab/ |
| OpenCode Zen | https://opencode.ai/docs/zen/ |

## Out of Scope

- Individual provider SDK compatibility fixes (e.g. "Cloudflare AI Gateway drops `max_tokens` for reasoning models") unless the user uses that provider - flag but don't lead.
- Generated SDK/OpenAPI type regenerations that don't change surface behaviour.
- Windows desktop backend lifecycle fixes unless the user is on Windows.
- Theme-only plugin package plumbing (unless the user asked about themes).
- Contributor attribution lines (`[(@handle)](...)`) - keep the change text, drop the trailing credit unless the user asked for it.

## Gotchas

- Entries aren't versioned as one-line-per-version; each release block contains several `### Core` / `### TUI` / `### Desktop` / `### SDK` / `### Extensions` subsections with bullet lists under them. The diff key is the semver tag (`v1.4.10`), not individual bullets.
- Patch versions go double-digit (`v1.3.17`, `v1.4.10`) - parse as semver, never lexicographic, or `v1.4.10` will sort before `v1.4.2`.
- The same bullet style ("Fix X", "Added Y") is used for both user-visible features and internal plumbing (e.g. "Fixed OTEL header parsing when a header value contains `=`"). Read the bullet before deciding it's user-facing.
- Many bullets name specific providers (Azure, OpenRouter, GitHub Copilot, Alibaba, Cloudflare AI Gateway, Claude Opus 4.7). These are only relevant to users of that provider - group them under Providers & Models and don't imply universal impact.
- The repo org is `anomalyco` (not `sst` or `opencode-ai`). If cross-referencing PRs or issues, use `github.com/anomalyco/opencode`. The npm package is `opencode-ai`.
