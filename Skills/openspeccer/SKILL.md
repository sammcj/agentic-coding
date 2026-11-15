---
name: openspeccer
description: Use when the user wants to open or browse an OpenSpec project's dashboard, or asks which OpenSpec changes are in flight or how far along one is. Do NOT use for creating, editing, verifying or archiving changes; use the OpenSpec workflow skills for those.
metadata:
  version: 2026-10-12
---

openspeccer is a read-only local web dashboard for any repository holding an `openspec/` directory. It is stdlib Python and needs no install. Run `<this-skill-dir>/scripts/serve.py --help` for every option.

## Workflow

Find the repo: pass the user's repo path, or omit it and the script searches upward from the current directory for `openspec/`. Then follow the one branch the request matches, creating a task per step of that branch, each with its completion criterion.

### Status question ("what's in flight?")

1. Run `serve.py <repo> --summary` and answer from its output. For one change's artifacts and tasks, use `--change <slug>`. `--json` prints the whole snapshot; send it to a file and read only what you need. Done once you have answered, with no server started.

### Dashboard

1. Start `serve.py <repo>` as a background process. Done when a line containing `serving <name> at <url>` appears, or the process exits; on exit, report its stderr to the user.
2. Always give the user the URL. Pass `--no-open` in headless or remote sessions, and when re-running against a server that is already up.
3. To stop it, end the background process you started, using the PID or task handle you captured at launch.

## Gotchas

- Re-running for the same repo reuses the running server and prints `already serving`, so Dashboard step 1 is safe to repeat.
- A server you did not start (no handle from this session) belongs to the user. Leave it running.
- The OpenSpec CLI is optional and only feeds the Schemas and Commands pages. Without it, only project schemas show and Commands is empty. For a CLI outside `PATH`, set `OPENSPECCER_OPENSPEC_BIN`.
- Active changes from every git worktree are aggregated by default.
- The page updates as files change, so there is nothing to refresh after editing artifacts.
