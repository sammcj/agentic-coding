---
last_seen_version: 2.1.108
last_updated: 2026-04-15
---

# Claude Code Changelog Summaries

## 2.1.89 → 2.1.108 (2026-04-15, first run digest)

### Context & Performance
- **Recap / `/recap` (2.1.108)**: returns context when you come back to a session. Configurable in `/config`; force with `CLAUDE_CODE_ENABLE_AWAY_SUMMARY` if telemetry is off.
- **1-hour prompt cache TTL (2.1.108)**: `ENABLE_PROMPT_CACHING_1H` env var across API key, Bedrock, Vertex, Foundry. `FORCE_PROMPT_CACHING_5M` to force shorter. Bedrock-only var is deprecated.
- **MCP tool search auto-mode by default (2.1.98)**: when MCP tool descriptions exceed 10% of context, they're deferred and discovered via `MCPSearch`. Disable by adding `MCPSearch` to `disallowedTools`.
- **Lazy language grammar loading (2.1.108)**: lower memory for file reads/edits/highlighting.
- **Faster file reads (2.1.91)**: 60% speed-up on files containing tabs/`&`/`$`.

### Skills & Commands
- **Skill tool can invoke built-in slash commands (2.1.108)**: model can discover and call `/init`, `/review`, `/security-review` via the Skill tool.
- **Skill hot-reload (2.1.97)**: skills in `~/.claude/skills` or `.claude/skills` go live without restart.
- **Forked sub-agent skills (2.1.97)**: `context: fork` in skill frontmatter runs a skill in an isolated sub-agent context. Pairs with `agent` field to pin agent type.
- **`/powerup` (2.1.90)**: interactive lessons with animated demos.
- **`/undo` is now an alias for `/rewind` (2.1.108)**.
- **Removed `/tag` and `/vim` (2.1.91)**: vim mode now via `/config` → Editor mode.

### Hooks
- **Conditional `if` filter on hooks (2.1.105)**: use permission-rule syntax (e.g. `Bash(git *)`) to filter when a hook runs, cutting process spawning.
- **Hooks can satisfy `AskUserQuestion` (2.1.105)**: `PreToolUse` hooks can return `updatedInput` alongside `permissionDecision: "allow"` for headless flows that gather answers via their own UI.
- **`updatedInput` with `ask` decision (2.1.97)**: hooks can act as middleware while still requesting consent.
- **Agent-scoped hooks (2.1.97)**: `PreToolUse`/`PostToolUse`/`Stop` hooks in agent frontmatter, scoped to that agent.
- **`hookSpecificOutput.sessionTitle` on `UserPromptSubmit` (2.1.94)**.

### Permissions & Sandboxing
- **Bash wildcard rules (2.1.97)**: `*` at any position, e.g. `Bash(npm *)`, `Bash(* install)`, `Bash(git * main)`.
- **Disable specific agents (2.1.97)**: `Task(AgentName)` in `disallowedTools` or settings permissions.
- **Sandbox security fixes (2.1.92)**: visible warning on silent disable when deps missing; `.git`/`.claude` no longer writable in `bypassPermissions`; `deny: ["mcp__server"]` now actually strips tools from the model's view; `sandbox.filesystem.allowWrite` works with absolute paths.
- **DNS cache commands removed from auto-allow (2.1.90)**: `Get-DnsClientCache`, `ipconfig /displaydns`.
- **Compound-command wildcard CVE fix (2.1.98)**: wildcard rules no longer match commands that contain shell operators.

### MCP & Plugins
- **`MCP list_changed` support (2.1.97)**: dynamic tool/prompt/resource refresh.
- **MCP OAuth via RFC 9728 (2.1.105)**: Protected Resource Metadata discovery.
- **`CLAUDE_CODE_MCP_SERVER_NAME`/`URL` for `headersHelper` (2.1.105)**: one helper can serve multiple servers.
- **Policy-blocked plugins enforced (2.1.105)**: hidden from marketplaces and uninstallable.
- **Stable plugin skill names (2.1.94)**: skills declared via `"skills": ["./"]` use the frontmatter `name`, not the directory basename.
- **`CLAUDE_CODE_PLUGIN_KEEP_MARKETPLACE_ON_FAILURE` (2.1.90)**: keep marketplace cache when `git pull` fails — useful offline.

### CLI & Terminal
- **Unified `Ctrl+B` backgrounding (2.1.97)**: backgrounds all foreground bash and agent tasks at once.
- **Streaming response text line-by-line (2.1.92)**.
- **Shift+Enter works out of the box (2.1.97)**: in iTerm2, WezTerm, Ghostty, Kitty.
- **Tmux passthrough notifications (2.1.92)**: terminal popups/progress reach the outer terminal with `set -g allow-passthrough on`.

### Memory & Config
- **`language` setting (2.1.97)**: configure response language (e.g. `language: "japanese"`). Diacritic-drop bug fixed in 2.1.108.
- **`respectGitignore` (2.1.97)**: extended to more file ops.
- **`IS_DEMO` env var (2.1.97)**: hides email/org for streaming/recordings.

### Defaults & Removals
- **Default effort raised medium → high (2.1.94)**: API key, Bedrock/Vertex/Foundry, Team, Enterprise. Control via `/effort`.

### Notable Fixes
- **Skills/files discovery on resume (2.1.97)**.
- **Auto mode now respects user boundaries (2.1.89)**: e.g. "don't push" honoured even when otherwise allowed.
- **`/compact` no longer fails with "context exceeded" (2.1.105)**.
- **Sensitive data redacted in debug logs (2.1.97)**: OAuth tokens, API keys, passwords.

Doc references: [hooks](https://code.claude.com/docs/en/hooks), [skills](https://code.claude.com/docs/en/skills), [plugins](https://code.claude.com/docs/en/plugins), [permissions](https://code.claude.com/docs/en/permissions), [sandboxing](https://code.claude.com/docs/en/sandboxing), [MCP](https://code.claude.com/docs/en/mcp), [memory](https://code.claude.com/docs/en/memory), [context window](https://code.claude.com/docs/en/context-window).
