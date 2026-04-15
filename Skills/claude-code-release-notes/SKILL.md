---
name: claude-code-release-notes
description: >-
  Summarises what's new in the latest Claude Code releases. Use when the user asks about
  the latest Claude Code release, release notes, changelog, or what's new in Claude Code.
metadata:
  author: 'Sam McLeod (adapted from Arjen Schwarz)'
---

# Claude Code Changelog Catch-Up

Summarise what's changed in Claude Code since the user last ran this skill. No interactive walkthrough, no exercises. Just a focused digest of the delta.

## Storage File

All state lives in `resources/cc-summary.md` inside the skill's directory (resolve relative to this `SKILL.md`, not the user's current working directory). It has two jobs:

1. Hold the last-seen Claude Code version in YAML frontmatter.
2. Accumulate a rolling log of previously generated summaries so the user has a history they can re-read without rerunning the skill.

Expected shape:

```markdown
---
last_seen_version: 2.1.90
last_updated: 2026-04-15
---

# Claude Code Changelog Summaries

## 2.1.95 (2026-04-15)

### Hooks
- ...

### MCP & Plugins
- ...

## 2.1.90 (2026-03-28)
...
```

Newest summary goes at the top of the body, directly under the `# Claude Code Changelog Summaries` heading. Keep older sections intact.

## Flow

1. **Read state.** Load `resources/cc-summary.md`. Parse `last_seen_version` from the frontmatter. If the file is missing, empty, or has no frontmatter version, treat this as a first run: ask the user which version to start from, or offer a digest of roughly the last 10 releases as a default.

2. **Fetch the current changelog.** Get `https://code.claude.com/docs/en/changelog` using `WebFetch` or `ctx_fetch_and_index`. Also check `https://code.claude.com/docs/en/whats-new/`. The weekly summaries there often have more context than the raw changelog lines.

3. **Identify the delta.** Keep entries newer than the stored version, up to the latest release. Compare versions numerically by component (e.g. `2.1.90` < `2.1.100`), not lexicographically.

4. **Summarise.** Group changes into sensible buckets (Hooks, MCP & Plugins, CLI & Terminal, Skills & Commands, Subagents, Permissions & Sandboxing, Memory & Config, Web & Desktop, Context & Performance, Scheduled Tasks). For each item:
   - One line on what it is
   - One line on why it matters or when you'd reach for it
   - A link to the relevant doc page when the feature is non-trivial (see table below)

   Keep the tone dense and direct. Flag anything experimental or niche. Don't pad with generic commentary.

5. **Persist state.** Use `Edit` (or `Write` if the file is missing) to update `resources/cc-summary.md`:
   - Set `last_seen_version` in the frontmatter to the latest version from the changelog.
   - Set `last_updated` to today's date (ISO format).
   - Prepend a new `## <version> (<date>)` section under `# Claude Code Changelog Summaries` containing the same bucketed summary you just presented to the user.
   - Leave existing history untouched.

   Confirm in one line: `Updated cc-summary.md to X.Y.Z.` If the run fails or the user aborts before the summary is delivered, leave the file alone.

## Scope Overrides

- If the user specifies a version explicitly ("what's new since 2.1.90"), use their version instead of the stored one. Still persist state at the end unless they say not to.
- If the user asks for everything in the last N days or weeks, use changelog dates rather than the stored version.
- If the user asks about a specific area only (e.g. "just hooks"), filter the delta to that area but still persist state at the end. Note the filter in the new summary section's heading (e.g. `## 2.1.95 (2026-04-15, hooks only)`).

## Source Material

Primary:
- Changelog: `https://code.claude.com/docs/en/changelog`
- What's New summaries: `https://code.claude.com/docs/en/whats-new/`
- Doc index: `https://code.claude.com/docs/en/llms.txt`

Feature pages to link when relevant:

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

Out of scope unless explicitly asked:
- Agent SDK (`/agent-sdk/*`): separate product
- Cloud providers (Bedrock, Vertex, Foundry), authentication, LLM gateway, model config
- IDE extensions (VS Code, JetBrains), CI/CD integrations (GitHub Actions, GitLab), Slack, Chrome

## Gotchas

- The changelog page is large. Fetch it via `WebFetch` or `ctx_fetch_and_index`, not Bash piping, to keep the main context lean.
- Version strings are semver-ish. `2.1.9` is older than `2.1.10`, so don't compare them as strings.
- If the stored version is newer than anything in the changelog (e.g. the user bumped it manually, or the changelog page hasn't updated yet), say so plainly and don't invent a delta.
- Don't conflate changelog entries with What's New summaries. The weekly summaries editorialise and occasionally omit smaller items, so treat the changelog as the source of truth for the list and use the summaries only for colour.
- Resolve `resources/cc-summary.md` from the skill's own directory, not the user's current working directory. The user may invoke the skill from any project.
- When updating `resources/cc-summary.md`, use `Edit` to prepend the new section. Only fall back to `Write` when the file doesn't yet exist. Never blow away the accumulated history.
