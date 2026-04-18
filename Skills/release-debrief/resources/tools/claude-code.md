---
name: claude-code
display_name: Claude Code
aliases: [claude-code, claudecode, cc]
output_file: resources/outputs/claude-code.md
version_scheme: semver
---

# Claude Code Profile

## Sources

- **Primary** (changelog to diff against):
  - https://code.claude.com/docs/en/changelog - official Claude Code changelog, one entry per semver release, dense line-item format.
- **Supporting** (for context / linking):
  - https://code.claude.com/docs/en/whats-new/ - weekly editorial summaries. Useful for context and wording, but occasionally omits smaller items - treat the raw changelog as source of truth.
  - https://code.claude.com/docs/en/llms.txt - doc index; handy for finding the right feature page to link.
  - https://platform.claude.com/docs/en/about-claude/models/whats-new-claude-4-7 - model "what's new" page when a release mentions a new Claude model.

## Version Scheme

Semver strings like `2.1.95`, `2.1.112`. Compare numerically by component, not lexicographically (`2.1.9` < `2.1.10`). On first run, surface the last 3 releases.

## Buckets

Group changelog entries under these headings. Buckets reflect Claude Code's feature surface area.

- **Hooks**: hook events, hook settings, matcher syntax, lifecycle changes.
- **MCP & Plugins**: MCP server support, plugin framework, plugin marketplaces.
- **CLI & Terminal**: slash commands, keybindings, status line, TUI/fullscreen, fast mode, interactive-mode tweaks.
- **Skills & Commands**: Skill tool, slash-command auto-discovery, user-invocable skills.
- **Subagents**: sub-agent launching, agent teams, worktree isolation.
- **Permissions & Sandboxing**: permission modes, sandbox filesystem/network rules, security model.
- **Memory & Config**: settings.json shape, env vars, `.claude` directory layout, CLAUDE.md behaviour.
- **Web & Desktop**: desktop app, Claude Code on the web, remote control, mobile push.
- **Context & Performance**: context window, checkpointing, auto-compaction, monitoring/costs.
- **Scheduled Tasks**: scheduled-task creation, management, cron semantics.
- **Channels & Events**: channels API, event streaming.

## Feature Link Table

Deep-link to the relevant doc page when a feature is non-trivial. All paths are under `https://code.claude.com/docs/en/`.

| Area | Doc Pages |
|------|-----------|
| Hooks | `/hooks`, `/hooks-guide` |
| Skills & Commands | `/skills`, `/commands` |
| MCP & Plugins | `/mcp`, `/plugins`, `/plugins-reference` |
| Subagents | `/sub-agents`, `/agent-teams` |
| CLI & Terminal | `/cli-reference`, `/interactive-mode`, `/keybindings`, `/statusline`, `/fast-mode`, `/fullscreen` |
| Memory & Config | `/memory`, `/settings`, `/claude-directory`, `/env-vars` |
| Permissions | `/permission-modes`, `/permissions`, `/sandboxing`, `/security` |
| Context & Performance | `/context-window`, `/checkpointing`, `/monitoring-usage`, `/costs` |
| Web & Desktop | `/desktop`, `/claude-code-on-the-web`, `/remote-control`, `/ultraplan` |
| Scheduled Tasks | `/scheduled-tasks` |
| Channels & Events | `/channels`, `/channels-reference` |
| Advanced | `/headless`, `/computer-use` |

## Out of Scope

Skip unless the user explicitly asks:

- Agent SDK changes (`/agent-sdk/*`) - separate product.
- Cloud providers (Bedrock, Vertex, Foundry), authentication, LLM gateway, model config.
- IDE extensions (VS Code, JetBrains), CI/CD integrations (GitHub Actions, GitLab), Slack, Chrome.

## Gotchas

- The changelog page is large. Fetch it via `WebFetch` or `ctx_fetch_and_index`, not Bash piping, to keep the main context lean.
- Don't conflate changelog entries with What's New summaries. The weekly summaries editorialise and occasionally omit smaller items, so treat the changelog as source of truth for the list and use the summaries only for colour.
- Some changelog entries span multiple `2.1.x` patch versions; deduplicate when the same feature is iterated over several releases in a single window.
