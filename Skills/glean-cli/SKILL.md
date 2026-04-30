---
name: glean-cli
description: Provides knowledge on using the `glean` CLI tool to access company knowledge and documents through Glean. Use when the user asks you to use Glean to search, read or otherwise access knowledge from their company's Confluence, Slack, Google Drive Files (Slides, Documents, Sheets) etc.
---

# Glean CLI

`glean` is a local CLI that authenticates to a company's Glean instance and exposes its REST API. It can search the corporate index, talk to Glean Assistant, look up people, fetch and summarise documents, and manage Glean-side resources (collections, pins, go-links, announcements, curated answers, agents, verification workflows).

Output is JSON on stdout, errors on stderr, exit code reflects success. This makes the CLI ideal for piping into `jq`.

## Prerequisite check

Before using anything in this skill, make sure the binary is on `$PATH`:

```bash
command -v glean
```

The `glean` CLI command is provided by `brew install gleanwork/tap/glean-cli`

If the command isn't found, you shoulkd ask the user if they wish you to install it for them.

If unauthenticated (run `glean auth status` upon authentication errors) and the user is at a terminal: `glean auth login` (browser OAuth). For CI or scripts, set `GLEAN_API_TOKEN` and `GLEAN_HOST` env vars instead - credentials resolve in the order: env vars -> system keyring -> `~/.glean/config.json`.

## Always introspect first

`glean schema` is the source of truth for commands and flags - Glean ships updates, and the schema reflects whatever version is installed locally. Before invoking a command you haven't used in this session, run:

```bash
glean schema <command>          # full machine-readable schema for one command
glean schema | jq '.commands'   # list every available command
```

The reference file in this skill (`references/commands.md`) is a fast lookup, but if `glean schema` disagrees, schema wins.

## Calling pattern

```bash
glean <command> [subcommand] [flags]
```

Three flags are global and worth knowing up front:

| Flag                            | Purpose                                                                                                                                    |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `--output <json\|ndjson\|text>` | Default `json`. Use `ndjson` when streaming results to a pipeline.                                                                         |
| `--json '<payload>'`            | Send a complete JSON request body. Overrides every other flag - use this for any non-trivial request, the schema documents the body shape. |
| `--dry-run`                     | Print the request that would be sent, send nothing. Always use this before any create/update/delete operation.                             |

Short positional flags exist for ergonomic queries (`glean search "vacation policy"`, `glean chat "what are the holidays?"`), but anything beyond a single string should go through `--json`.

## Commands at a glance

Read-only:

| Command           | Use for                                                      |
| ----------------- | ------------------------------------------------------------ |
| `glean search`    | Find documents across all enterprise sources.                |
| `glean chat`      | Ask Glean Assistant a question; streams an AI answer.        |
| `glean documents` | Fetch a doc's metadata, content, permissions, or AI summary. |
| `glean entities`  | Look up people, teams, or custom entities.                   |
| `glean messages`  | Read a specific Slack/Teams message by ID.                   |
| `glean insights`  | Pull search/usage analytics.                                 |
| `glean agents`    | List, inspect, and run Glean AI agents.                      |
| `glean tools`     | List and run Glean platform tools.                           |
| `glean answers`   | List/get curated Q&A pairs.                                  |

Write/admin:

| Command               | Use for                                                                |
| --------------------- | ---------------------------------------------------------------------- |
| `glean collections`   | Create/update/delete document collections; add/remove items.           |
| `glean pins`          | Promote a document to the top of results for given queries.            |
| `glean shortcuts`     | Manage go-links (e.g. `go/wiki`).                                      |
| `glean announcements` | Create/update/delete time-bounded company announcements.               |
| `glean answers`       | Create/update curated answers.                                         |
| `glean verification`  | Mark documents verified; send verification reminders.                  |
| `glean activity`      | Log user activity events; submit relevance feedback.                   |
| `glean api`           | Raw authenticated HTTP call to any Glean REST endpoint (escape hatch). |

For flag-level detail and worked examples on any of these, read `references/commands.md` - it's organised by command in the same order as the tables above.

## Common workflows

**Search and pipe into jq.** Search returns JSON with a `results` array; each result has a `document` with `title`, `url`, `id`, `snippets`, etc.

```bash
glean search "incident response runbook" | jq '.results[] | {title: .document.title, url: .document.url}'
```

**Find then summarise.** Combine search with the summarise subcommand:

```bash
DOC_ID=$(glean search "Q1 OKRs" | jq -r '.results[0].document.id')
glean documents summarize --json "{\"documentId\":\"$DOC_ID\"}" | jq -r .summary
```

**Ask a question.** For any "what does our company say about X" question, prefer `glean chat` over `glean search` - Glean Assistant cites the underlying documents in its response.

```bash
glean chat "How do I expense international travel?"
```

**Look up a person.**

```bash
glean entities read-people --json '{"query":"Jane Smith"}' | jq '.[0] | {name, email, title, department}'
```

## Gotchas

- **Don't echo tokens.** `GLEAN_API_TOKEN` is sensitive; never `echo` it, log it, or include it in error messages or commit it to a file. Use it via env var only.
- **Always `--dry-run` first for writes.** Any `create`, `update`, `delete`, `verify`, `remind`, `add-items`, `delete-item`, or `report` action sends data into the customer's Glean tenant. Print the body first, get the user's confirmation if it's not their explicit ask, then send.
- **`--json` overrides everything.** If both `--json` and individual flags are supplied, the JSON body wins - silently. Don't mix the two.
- **Schema, not memory.** Flag names and JSON body shapes evolve between Glean releases. If you pass a body and the API rejects it, run `glean schema <command>` and check the current shape rather than guessing.
- **`glean api` is the escape hatch, not the default.** If a dedicated subcommand exists for what you're doing (e.g. `glean search` rather than `glean api search`), prefer it - the dedicated command has nicer ergonomics and a stable contract.
- **Errors land on stderr.** When piping into `jq` or another consumer, capture stderr separately so you can surface the real error message rather than a "parse error: unexpected end of JSON" downstream.
- **Search results aren't always document objects.** `results[]` may contain promoted answers, people, or pinned items - when working programmatically, branch on `.type` or guard with `.document?`.
