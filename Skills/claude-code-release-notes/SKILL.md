---
name: claude-code-release-notes
description: >-
  Summarises the delta between a tool's latest release and the last summary the user saw.
  Use when the user asks about what's new, the latest release, release notes, or the changelog
  of one of the supported tools: Claude Code, OpenCode, llama-swap, or llama.cpp.
allowed-tools: >-
  Read Write Edit Grep Glob
  WebFetch(domain:claude.com)
  WebFetch(domain:opencode.ai)
  WebFetch(domain:github.com)
  WebFetch(domain:raw.githubusercontent.com)
  Bash(gh release list *)
  Bash(gh release view *)
  Bash(gh api *)
  Bash(open *)
metadata:
  author: 'Sam McLeod (adapted from Arjen Schwarz)'
---

# Release Notes Catch-Up

Summarise what's changed in a supported tool since the user last ran this skill against it. No walkthroughs, no exercises. Focused digest of the delta.

## Supported Tools

Each tool has a **profile** in `resources/tools/<tool>.md` (source URLs, buckets, gotchas) and an **output file** in `resources/outputs/<tool>.md` (last-seen version and summary history). Resolve both paths relative to this `SKILL.md`, not the user's current working directory.

| Tool | Aliases the user may type | Profile | Output |
|------|---------------------------|---------|--------|
| Claude Code | claude-code, claudecode, cc | `resources/tools/claude-code.md` | `resources/outputs/claude-code.md` |
| OpenCode | opencode, open-code | `resources/tools/opencode.md` | `resources/outputs/opencode.md` |
| llama-swap | llama-swap, llamaswap | `resources/tools/llama-swap.md` | `resources/outputs/llama-swap.md` |
| llama.cpp | llama-cpp, llama.cpp, llamacpp | `resources/tools/llama-cpp.md` | `resources/outputs/llama-cpp.md` |

Tool selection: match the tool from the user's prompt against the aliases above. If the user names something not in this table, reply with the supported list and stop.

## Flow

1. **Load the tool profile.** Read `resources/tools/<tool>.md`. It tells you where to fetch the changelog, how the version scheme works, which buckets to group under, what to drop, and what to watch out for. Treat the profile as authoritative for that tool.

2. **Read state.** Load the tool's output file. Parse `last_seen_version` from the frontmatter. If the file is missing, empty, or has no frontmatter version, treat as a first run: summarise the **last 3 releases** per the profile's version scheme, without prompting.

3. **Fetch the current changelog.** Use `WebFetch` or `ctx_fetch_and_index` against the profile's **Primary** source. Pull **Supporting** sources only when you need context for an entry (config schema comparison, API doc linking, editorial summary for colour).

4. **Identify the delta.** Keep entries newer than the stored version, up to the latest release. Compare versions using the scheme in the profile:
   - `semver` - parse major.minor.patch and compare numerically per component.
   - `build-number` - strip any prefix (`b`, `v`) and compare as integer.
   - `github-release-tag` - use GitHub's release order (chronological).

   Never compare version tags as lexicographic strings.

5. **Summarise.** Group entries under the profile's **Buckets**. For each item:
   - One line on what it is.
   - One line on why it matters or when you'd reach for it.
   - A doc link (from the profile's Feature Link Table, or the release page itself) when the feature is non-trivial.

   Apply the profile's **Out of Scope** list to drop low-signal entries. Apply the profile's **Gotchas** when deciding how to parse, group, or flag things. Keep tone dense and direct. Flag anything experimental, breaking, or schema-affecting prominently.

6. **Persist state.** Use `Edit` (or `Write` if the output file doesn't yet exist) to update the tool's output file:
   - Set `last_seen_version` in the frontmatter to the latest version from the fetched changelog (the single newest one, even if the summary covers a range).
   - Set `last_updated` to today's date (ISO format).
   - Prepend a new `## <version> (<date>)` section under `# <Tool> Changelog Summaries` containing the bucketed summary you just presented. When a single run covers multiple versions, use a range heading: `## <oldest> → <newest> (<date>)`.
   - Keep only the newest **two** `##` sections. If adding the new section would leave three or more, remove the oldest so exactly two remain.

   Confirm in one line: `Updated resources/outputs/<tool>.md to <version>.` If the run fails or the user aborts before the summary is delivered, leave the file alone.

7. **Open the output file.** After a successful write, run `open </absolute/path/to/resources/outputs/<tool>.md>` so the user can read the summary in their default markdown viewer.

## Storage File Format

Each output file follows this shape:

```markdown
---
last_seen_version: 2.1.112
last_updated: 2026-04-17
---

# <Tool> Changelog Summaries

## <version> (<date>)

### <Bucket>
- ...

## <prior version> (<prior date>)

### <Bucket>
- ...
```

`<version>` in the heading can be a single version (`2.1.112`) or a range when one run covered several (`2.1.109 → 2.1.112`). `last_seen_version` in the frontmatter is always the single newest version. At most two `##` sections: newest at top, prior run directly below. When prepending, drop the oldest.

## Scope Overrides

- **Explicit version** ("what's new since 2.1.90"): use the user's version instead of `last_seen_version`. Still persist state unless they say not to.
- **Date range** ("everything in the last 2 weeks"): use changelog dates rather than version. Still persist state.
- **Area filter** ("just hooks"): filter the delta to that area, but still persist state. Note the filter in the new section's heading: `## <version> (<date>, hooks only)`.
- **No persist** ("don't update state"): skip step 6, tell the user state was not persisted.

## Common Gotchas

- Resolve `resources/tools/<tool>.md` and `resources/outputs/<tool>.md` relative to this `SKILL.md`. Users invoke the skill from arbitrary working directories.
- Version parsing differs per tool - always read the profile's **Version Scheme** section before comparing. Don't assume semver.
- If the stored version is newer than anything in the fetched changelog (user bumped it manually, or the source hasn't updated yet), say so plainly and don't invent a delta.
- Use `Edit` to prepend the new section and remove the oldest so only two remain. Fall back to `Write` only when the file doesn't yet exist.
- Don't mix tools in one output file. Each tool owns its own output file.
- First-run heuristic (last 3 releases) applies per tool, not per invocation. If the user ran the skill on Claude Code yesterday and asks about OpenCode today, OpenCode is still a first run.
