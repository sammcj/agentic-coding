---
last_seen_version: 2.1.112
last_updated: 2026-04-17
---

# Claude Code Changelog Summaries

## 2.1.109 → 2.1.112 (2026-04-17)

### CLI & Terminal
- **`/tui` command + `tui` setting (2.1.110)**: `/tui fullscreen` switches to flicker-free rendering inside the current conversation. New `autoScrollEnabled` config turns off auto-scroll in fullscreen.
- **`/focus` command (2.1.110)**: `Ctrl+O` now only toggles normal/verbose transcript; focus view is separate. Focus mode writes more self-contained summaries since you only see the final message.
- **PR status dot in footer (2.1.111)**: coloured dot shows the current branch's PR state (approved/changes-requested/pending/draft) with a clickable link.
- **`Ctrl+G` external editor improvements (2.1.110)**: optional commented context of Claude's last response; shortcut now listed in help menu (2.1.111).
- **Vim normal-mode history nav (2.1.111)**: arrow keys fall through to history navigation when the cursor can't move further.
- **Shimmer thinking status + extended-thinking progress hint (2.1.109/2.1.111)**.

### Skills & Commands
- **`/team-onboarding` (2.1.111)**: generates a teammate ramp-up guide from your local usage patterns.
- **`/commit-push-pr` auto-posts PR URLs to Slack (2.1.111)** when a Slack MCP server is configured.
- **`/copy` available to all users (2.1.111)**.
- **`ToolSearch` as notification (2.1.111)**: results appear as a brief toast instead of inline noise.

### Web & Remote Control
- **Mobile push notifications (2.1.110)**: Claude can push to your phone when Remote Control + "Push when Claude decides" are on.
- **Remote Control runs more commands (2.1.110)**: `/context`, `/exit`, `/reload-plugins` work from mobile/web.
- **`--resume`/`--continue` resurrects unexpired scheduled tasks (2.1.110)**.
- **`/ultraplan` auto-creates a cloud env (2.1.111)**; hidden in plan mode when the org/auth can't reach Claude Code on the web.

### Memory & Config
- **`CLAUDE.md` from `--add-dir` roots (2.1.111)**: opt-in via `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1`.
- **OS CA store trusted by default (2.1.111)**: enterprise TLS proxies work out of the box; set `CLAUDE_CODE_CERT_STORE=bundled` to revert.
- **Timestamped, rotated config backups (2.1.111)**: keeps 5 most recent to prevent data loss.

### Permissions & Sandboxing
- **Background agents prompt for permissions before launch (2.1.111)**.
- **`Bash(*)` now accepted as equivalent to `Bash` (2.1.111)**.
- **OTEL sensitive attributes gated (2.1.111)**: spans honour `OTEL_LOG_USER_PROMPTS`/`OTEL_LOG_TOOL_DETAILS`/`OTEL_LOG_TOOL_CONTENT`.
- **Command-injection fix in LSP `which` fallback (2.1.111)**: POSIX path.

### Plugins & MCP
- **`/plugin` Installed tab reshuffled (2.1.110)**: attention items + favourites on top, disabled folded away, `f` favourites the selection.
- **Plugin install honours `plugin.json` dependencies (2.1.110)** even when the marketplace entry omits them; lists auto-installed deps.
- **Managed-hooks/plugin warnings (2.1.111)**: `/plugin` and `claude plugin update` surface refresh failures instead of silently reporting stale versions.

### SDK & Headless
- **SDK `query()` cleanup on early exit (2.1.111)**: subprocess and temp files are released when consumers `break` from `for await` or use `await using`.
- **Brief mode retry (2.1.111)**: one retry when Claude returns plain text instead of a structured message.

### Tasks
- **Delete tasks via `TaskUpdate` (2.1.111)**.

### Notable Fixes
- **opus-4-7 auto-mode availability (2.1.112)**: fixed "claude-opus-4-7 is temporarily unavailable".
- **Session compaction on resume (2.1.111)**: no longer loads full history instead of the compact summary.
- **Memory leak in long sessions (2.1.111)**: virtual scroller kept dozens of historical message-list copies.
- **Agents ignoring user mid-task messages (2.1.111)**.
- **MCP hanging on SSE/HTTP disconnects + non-streaming retry hangs (2.1.110)**.
- **Skills with `disable-model-invocation: true` failing via `/<skill>` mid-message (2.1.110)**.
- **Wide-char (emoji/CJK) rendering artefacts, ghost-text flicker, diff view on resize (2.1.111)**.

Doc references: [cli](https://code.claude.com/docs/en/cli-reference), [interactive mode](https://code.claude.com/docs/en/interactive-mode), [remote control](https://code.claude.com/docs/en/remote-control), [plugins](https://code.claude.com/docs/en/plugins), [memory](https://code.claude.com/docs/en/memory), [permissions](https://code.claude.com/docs/en/permissions), [scheduled tasks](https://code.claude.com/docs/en/scheduled-tasks).

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
