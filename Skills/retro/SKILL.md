---
name: retro
description: Retrospective on a coding session that proposes changes to the agent's environment (checks, pointers, steering, tooling) so the next run goes better.
disable-model-invocation: true
compatibility: claude-code
argument-hint: "[session-id or transcript path]"
metadata:
  source: https://github.com/mattpocock/skills (adapted)
---

# Retro

Propose improvements to the agent's **environment** based on where a session struggled. Propose only: change nothing until the user picks a candidate. Fix the environment, not the code the session produced (that is `code-review`).

## Steps

1. Create a task per step below, each with its completion criterion.
2. Get the session record:
   - No session named: use the current conversation.
   - Session named, or the current one is too long to recall reliably: run `python3 scripts/session_digest.py <id-or-path>` (`--list N --project <repo>` to find it). Digest each subagent transcript it lists when the struggle happened there.
3. Mark the **struggle moments**: errors, retries, hook blocks, long searches, oversized results, compactions, user corrections, wrong turns. Cite each by digest call number (`#12`) or by quoting the user.
4. Read the repo's existing checks (`Makefile`, `package.json` scripts, pre-commit config, CI workflows, `.claude/settings.json` hooks). A check that exists but is unwired or broken is the finding, in place of a new one.
5. Map each struggle moment to a candidate using the categories below. Drop any candidate you can't trace to a struggle moment.
6. Present candidates ranked by severity: cost of the struggle times how often it will recur. Each candidate states the moment, the fix, and the file it lands in.

## Categories

- **Navigation**: the agent took long to find a file or fact. Fix: a pointer from a file it already reads.
- **Automated checks**: the agent made a mistake a tool could catch. Fix: lint rule, type, test, pre-commit hook, CI job, or a Claude Code PreToolUse/PostToolUse hook. A repo with no **guardrail** (no pre-commit hook and no CI running lint/typecheck/test) is a finding in itself.
- **Coding standards**: the reviewer missed a mistake. Classify it first. **Mechanical** (banned API, import shape, file location, fixed syntax) gets a deterministic check. **Judgement call** (cross-file consistency, matching surrounding style) goes in the repo's standards doc (`CODING_STANDARDS.md` or `CONTRIBUTING.md`). `code-review` reads only what the repo documents, so a new standards doc also needs a one-line pointer from the project `CLAUDE.md`.
- **Steering bloat**: global `~/.claude/CLAUDE.md`, project `CLAUDE.md`/`AGENTS.md`, `.claude/rules/`, auto-memory `MEMORY.md`, SessionStart hook context, or model-invoked skill descriptions are large. Fix: move instructions into checks or standards, path-scope them into rules, or tighten a skill description or make it user-invoked.
- **No-ops**: steering lines the agent already obeys by default, or ignored anyway. Fix: delete, or replace with a check. Treat each as a candidate for the deletion test, judged on one session.
- **Skills**: a skill failed to fire, fired wrongly, or its instructions misled the agent. Fix: its description or body.
- **Tool economy**: a tool call was expensive for what it returned (see oversized results in the digest), or the agent repeated a call. Fix: a cheaper command, a script, or a narrower tool.
- **Information access**: the agent lacked information it needed. Fix: tee dev server logs to a file, read-only access to a service, a docs pointer.
- **Sandbox and permissions**: a sandbox or hook block cost retries. Fix: the command pattern the agent should have used, or a sandbox/permission rule change for the user to make.

## Placement

The implementer has the most context pressure: it explores, writes code and debugs. The reviewer gets a diff. Put rules where there is room to apply them.

- Steering files (`CLAUDE.md`, `AGENTS.md`, SessionStart hooks) load into every session. Reserve them for navigation pointers and rules that apply to every task.
- A recurring mistake becomes a failing check before it becomes prose.
- Judgement rules go to the reviewer's standards doc, not `CLAUDE.md`. Extend an existing doc before writing a new one.
- A user preference correction belongs in auto-memory as a `feedback` memory. Repo facts belong in the repo.

## Applying a picked candidate

Load the matching skill before editing:

- `CLAUDE.md` or `.claude/rules/` -> `authoring-claude-md`
- A skill -> `skill-creator-primer`
- Hooks, permissions or settings -> `update-config`

Run a proposed check against the repo before letting it block anything.
