# Glean CLI Command Reference

Detailed flags, subcommands, and worked examples for every `glean` command. The authoritative source for the version installed locally is always `glean schema <command>` - fall back to this file when the user wants a quick reminder or you need to draft a command without an extra round-trip.

Global flags (`--output`, `--json`, `--dry-run`) apply to every command and are documented in `SKILL.md`. They are omitted from the per-command tables below to keep them focused on what's specific.

## Read-only commands

### glean search

Search for content across the company's indexed sources. Returns JSON.

```bash
glean search [flags] [query]
```

| Flag                              | Type     | Default                    | Notes                                                                                |
| --------------------------------- | -------- | -------------------------- | ------------------------------------------------------------------------------------ |
| `--query`                         | string   | -                          | Search query. Also accepted as a positional argument. Required.                      |
| `--datasource`                    | []string | -                          | Filter by datasource (repeatable). e.g. `--datasource confluence --datasource slack` |
| `--type`                          | []string | -                          | Filter by document type (repeatable).                                                |
| `--tab`                           | []string | -                          | Filter by result tab IDs (repeatable).                                               |
| `--page-size`                     | int      | 10                         | Results per page.                                                                    |
| `--max-snippet-size`              | int      | 0                          | Max snippet size in characters (0 = default).                                        |
| `--facet-bucket-size`             | int      | 10                         | Max facet buckets per result.                                                        |
| `--fetch-all-datasource-counts`   | bool     | false                      | Return counts for all datasources.                                                   |
| `--response-hints`                | []string | `[RESULTS QUERY_METADATA]` | Sections to include in the response.                                                 |
| `--return-llm-content`            | bool     | false                      | Return expanded LLM-friendly content (longer snippets, more context).                |
| `--query-overrides-facet-filters` | bool     | false                      | Allow query operators to override facet filters.                                     |
| `--disable-spellcheck`            | bool     | false                      | Skip spellcheck.                                                                     |
| `--disable-query-autocorrect`     | bool     | false                      | Skip automatic query corrections.                                                    |
| `--timeout`                       | int      | 30000                      | Request timeout in ms.                                                               |

Examples:

```bash
glean search "vacation policy" | jq '.results[].document.title'

glean search --json '{
  "query":"Q1 reports",
  "pageSize":5,
  "datasources":["confluence","drive"]
}' | jq .

# Tighter result for an LLM downstream
glean search "incident response" --return-llm-content --page-size 3 \
  | jq '.results[] | {title: .document.title, content: .clusteredResults}'
```

### glean chat

Talk to Glean Assistant. Streams an AI answer to stdout, citing the underlying documents.

```bash
glean chat [flags] [message]
```

| Flag        | Type   | Default | Notes                                                          |
| ----------- | ------ | ------- | -------------------------------------------------------------- |
| `--message` | string | -       | The message. Also accepted as a positional argument. Required. |
| `--save`    | bool   | true    | Save the chat session to the user's history.                   |
| `--timeout` | int    | 30000   | ms.                                                            |

Examples:

```bash
glean chat "What are the company holidays?"

glean chat --json '{
  "messages":[
    {"author":"USER","messageType":"CONTENT","fragments":[{"text":"What is our PTO policy?"}]}
  ]
}'
```

When chaining a chat into other tooling, set `--save=false` so transient programmatic queries don't pollute the user's history.

### glean documents

Retrieve metadata, contents, permissions, or AI summaries for indexed documents.

```bash
glean documents <subcommand> [flags]
```

| Subcommand        | Purpose                                    |
| ----------------- | ------------------------------------------ |
| `get`             | Retrieve a document by URL or ID.          |
| `get-by-facets`   | Retrieve documents matching facet filters. |
| `get-permissions` | Inspect who has access to a document.      |
| `summarize`       | Generate an AI summary of a document.      |

Examples:

```bash
glean documents summarize --json '{"documentId":"DOC_ID"}' | jq -r .summary
```

For `get`, `get-by-facets`, and `get-permissions` request body shapes (which take URL specs, facet filters, and document references respectively), run `glean schema documents <subcommand>` and inspect `.flags."--json".schema` before constructing the payload. Glean's REST surface for these endpoints accepts several alternative input shapes and the schema is the source of truth.

### glean entities

Look up people, teams, and custom entities.

```bash
glean entities <subcommand> [flags]
```

| Subcommand    | Purpose                          |
| ------------- | -------------------------------- |
| `list`        | List entities by type and query. |
| `read-people` | Get detailed people profiles.    |

`--json` is required (no positional shortcut).

Example (the only documented shape - for `list`, run `glean schema entities list` to see the supported body):

```bash
glean entities read-people --json '{"query":"smith"}' | jq '.[] | {name, email, title}'
```

### glean messages

Retrieve a specific indexed message (Slack, Teams, etc.) by ID.

```bash
glean messages get --json '{"messageId":"MSG_ID"}' | jq .
```

`--json` is required.

### glean insights

Pull search and usage analytics.

```bash
glean insights get --json '{"insightTypes":["SEARCH"]}' | jq .
```

`--json` is required. The `insightTypes` array drives the report shape.

### glean agents

List, inspect, and run Glean AI agents (LangChain-style published workflows).

```bash
glean agents <subcommand> [flags]
```

| Subcommand | Purpose                                |
| ---------- | -------------------------------------- |
| `list`     | List all available agents.             |
| `get`      | Get details of a specific agent.       |
| `schemas`  | Get input/output schemas for an agent. |
| `run`      | Run an agent.                          |

Examples:

```bash
glean agents list | jq '.[] | {id, name}'

glean agents schemas --json '{"agentId":"agent_id"}' | jq .

glean agents run --json '{"agentId":"agent_id","input":{"query":"test"}}'
```

Inspect the agent's `schemas` output before constructing a `run` payload - agent inputs are agent-specific.

### glean tools

List and run platform tools (server-side integrations exposed by Glean).

```bash
glean tools <subcommand> [flags]
```

| Subcommand | Purpose                        |
| ---------- | ------------------------------ |
| `list`     | List available platform tools. |
| `run`      | Execute a platform tool.       |

```bash
glean tools list | jq '.[].name'
```

For `run`, inspect `glean schema tools run` to see the expected body - tool parameters are tool-specific.

### glean answers (read side)

```bash
glean answers list | jq '.[] | {id, question}'
glean answers get --json '{"answerId":"ANS_ID"}' | jq .
```

## Write / admin commands

All of these mutate state in the customer's Glean tenant. Use `--dry-run` first.

### glean collections

Curated sets of documents.

```bash
glean collections <subcommand> [flags]
```

| Subcommand    | Purpose                              |
| ------------- | ------------------------------------ |
| `list`        | List all collections.                |
| `get`         | Get a specific collection.           |
| `create`      | Create a new collection.             |
| `update`      | Update a collection.                 |
| `delete`      | Delete a collection.                 |
| `add-items`   | Add documents to a collection.       |
| `delete-item` | Remove a document from a collection. |

```bash
glean collections list | jq '.[] | {id, name}'
glean collections create --json '{"name":"On-call runbooks"}' --dry-run
```

For `add-items`, `delete-item`, `update`, and `delete`, run `glean schema collections <subcommand>` to confirm the request body shape before sending.

### glean pins

Promote a document to the top of search results for given queries.

```bash
glean pins <subcommand> [flags]
```

| Subcommand                                  | Purpose        |
| ------------------------------------------- | -------------- |
| `list`, `get`, `create`, `update`, `remove` | Standard CRUD. |

```bash
glean pins list | jq '.[].id'
```

For `create`, `update`, and `remove`, the body shape is documented in `glean schema pins <subcommand>` - check it before constructing the payload.

### glean shortcuts

Manage go-links (e.g. `go/wiki` -> an internal URL).

```bash
glean shortcuts <subcommand> [flags]
```

| Subcommand                                  | Purpose        |
| ------------------------------------------- | -------------- |
| `list`, `get`, `create`, `update`, `delete` | Standard CRUD. |

```bash
glean shortcuts list | jq '.results[].inputAlias'

glean shortcuts create --json '{
  "data":{
    "inputAlias":"runbook/oncall",
    "destinationUrl":"https://confluence.example.com/oncall"
  }
}'
```

Note the nested `data:` wrapper on create/update - easy to miss.

### glean announcements

Time-bounded company announcements that surface across the Glean UI.

```bash
glean announcements <subcommand> [flags]
```

| Subcommand                   | Purpose             |
| ---------------------------- | ------------------- |
| `create`, `update`, `delete` | Standard mutations. |

```bash
glean announcements create --json '{"title":"Company Update","body":"..."}' --dry-run
```

The schema may require additional fields (start/end timestamps, target audiences) - confirm with `glean schema announcements create` before sending a real announcement.

### glean answers (write side)

```bash
glean answers list | jq '.[].id'
```

Body shapes for `create`, `update`, and `delete` are documented in `glean schema answers <subcommand>`. Run that before constructing a payload.

### glean verification

Document review workflows.

```bash
glean verification <subcommand> [flags]
```

| Subcommand | Purpose                                    |
| ---------- | ------------------------------------------ |
| `list`     | List documents pending verification.       |
| `verify`   | Mark a document as verified.               |
| `remind`   | Send a verification reminder to its owner. |

```bash
glean verification list | jq '.[].document.title'
```

For `verify` and `remind`, the body shape is in `glean schema verification <subcommand>` - check it first.

### glean activity

Log user activity events and submit relevance feedback. Mostly used by integrations, not interactive users.

```bash
glean activity report --json '{"events":[{"action":"VIEW","url":"https://example.com"}]}'
```

`--json` is required for both subcommands. The `feedback` body shape is documented in `glean schema activity feedback`.

### glean api

Raw authenticated HTTP request to any Glean REST endpoint. Use this only when no dedicated subcommand exists.

```bash
glean api <path> [flags]
```

| Flag          | Type                          | Default | Notes                                           |
| ------------- | ----------------------------- | ------- | ----------------------------------------------- |
| `--method`    | GET\|POST\|PUT\|DELETE\|PATCH | GET     | HTTP method.                                    |
| `--raw-field` | string                        | -       | Inline JSON body as a string.                   |
| `--input`     | string                        | -       | Path to a JSON file to use as the request body. |
| `--preview`   | bool                          | false   | Print the request without sending.              |
| `--dry-run`   | bool                          | false   | Same as `--preview`.                            |
| `--raw`       | bool                          | false   | Print raw response without syntax highlighting. |
| `--no-color`  | bool                          | false   | Disable colorised output (useful when piping).  |

Example:

```bash
glean api search --method POST \
  --raw-field '{"query":"test","pageSize":3}' \
  --no-color | jq .results
```
