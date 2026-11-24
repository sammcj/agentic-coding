---
name: authoring-claude-md
description: Use when creating, editing, auditing or pruning CLAUDE.md, AGENTS.md or .claude/rules/ files.
---

# CLAUDE.md, AGENTS.md and Rules Authoring

Create effective CLAUDE.md, AGENTS.md and `.claude/rules/` files that serve as project-specific memory for AI coding agents. Guidance for CLAUDE.md also applies to AGENTS.md and rule files unless stated otherwise: signal over noise, actionable context, no obvious information.

## Purpose

CLAUDE.md files and rule files provide AI agents with:
- Non-obvious conventions, architectural patterns and gotchas
- Confirmed solutions to recurring issues
- Project-specific context not found in standard documentation
- Path-scoped instructions that only load when relevant files are touched

**Not for**: obvious patterns, duplicating documentation, or generic coding advice.

## Core Principles

- **Signal over noise**: Every sentence must add non-obvious value. If an AI agent could infer it from reading the codebase, omit it.
- **Actionable context**: Focus on "what to do" and "why it matters", not descriptions of what exists.
- **Solve real friction, not theoretical concerns**: Add to CLAUDE.md based on actual problems encountered, not hypothetical scenarios. If you repeatedly explain the same thing to Claude, document it. If you haven't hit the problem yet, don't pre-emptively solve it.

## Structure

Use headings for clear organisation. Common sections: Commands, Conventions, Gotchas. Use 2-4 sections and only include what adds value.

## Where Each Instruction Belongs

- Every session needs it: root CLAUDE.md, or root AGENTS.md if the repo uses it
- One directory, maintained by its owners: nested CLAUDE.md, or nested AGENTS.md if the repo uses it
- One file type, or scattered paths: path-scoped rule
- Multi-step procedure, or reference only some tasks need: skill
- Must hold every time without exception: hook or permission deny rule. CLAUDE.md is guidance the agent can judge not to apply
- Personal, all projects: `~/.claude/CLAUDE.md` or `~/.claude/rules/`
- Personal, one project: gitignored `CLAUDE.local.md` (see AGENTS.md below first)

`@path` imports organise content but load with the importing file, so they save no context.

## AGENTS.md

By default Claude Code reads AGENTS.md only when there is no `CLAUDE.md`, `.claude/CLAUDE.md` or `CLAUDE.local.md` in the working directory or above. `~/.claude/CLAUDE.md` doesn't count. Adding one stops every AGENTS.md loading for sessions started in that directory or below, parent directories included, except those imported. A nested one also replaces its sibling AGENTS.md when the session starts above it. Some versions and sessions can't read AGENTS.md directly and need the import too.

- Repo uses AGENTS.md: put shared instructions there
- Claude-specific content needed: create a CLAUDE.md starting with `@AGENTS.md`, with only the Claude-specific lines below it. Parent and nested AGENTS.md files then each need a sibling CLAUDE.md importing them, or the setting below
- `CLAUDE.local.md` needed and no CLAUDE.md imports AGENTS.md: have the user set **Project instructions** to `claude-md-and-agents-md` in `/config`. The setting is personal, so use imports for anything teammates need
- CLAUDE.md says in prose to read AGENTS.md: replace the sentence with an `@AGENTS.md` import
- CLAUDE.md is a symlink to AGENTS.md: edit AGENTS.md, as Edit and Write refuse to write through the link

## Rule Files

Each `.md` file under `.claude/rules/` covers one topic and is discovered recursively. Move part-specific content to path-scoped rules when CLAUDE.md approaches 200 lines, or when conventions differ by file type or area (one whole directory: see Where Each Instruction Belongs).

Scope a rule with `paths` frontmatter, the only field Claude Code reads:

```markdown
---
paths:
  - "src/api/**/*.ts"
---

- Validate request bodies with the schemas in `src/api/schemas/`
```

- Loads when the agent reads, writes or edits a matching file, including a simple `cat` or `head` of one
- Without `paths`, or with YAML that doesn't parse, it loads every session
- User-level and project rules both load and neither overrides the other. The agent may follow either, so keep them consistent

## What to Include

**Verification commands**: exact test, single-test, lint, typecheck and build commands. The command that checks the work is often the most useful line in the file.

**Misleading code**:
- "`src/legacy/` is live but don't copy its patterns into new code"
- "`tools/shim/` looks unused, the release job imports it"

**Architectural decisions**: the reason for a choice the code can't show, such as why services communicate by events

**Non-obvious conventions**:
- "Use `_internal` suffix for private APIs not caught by linter"
- "Date fields always UTC, formatting happens client-side"
- "Avoid ORM for reports, use raw SQL in `/queries`"

**Recurring issues**:
- "TypeError in auth: ensure `verify()` uses Buffer.from(secret, 'base64')"
- "Cache race condition: acquire lock before checking status"

**Project patterns**: Error handling, logging, API versioning, migrations

## What to Exclude

- Line numbers: files change and references break. Use descriptive paths: "in `src/auth/middleware.ts`" not "line 42"
- Obvious information: "We use React" (visible in package.json). LLMs are in-context learners and pick up patterns from codebase exploration.
- Architecture and layout descriptions: the agent reads the repo itself. Keep only the decisions and reasons.
- Lines that push effort or delegation: "think harder", "be thorough", "double-check your work", "use subagents", token budgets, hard word caps. These add cost or side effects on current models. Set effort in the agent's settings and give a check to run instead.
- Code style guidelines: formatting rules, naming conventions, or patterns that linters enforce. Use ESLint, Prettier, Black, golangci-lint or similar, and Claude Code Hooks to run formatters.
- Generic advice: "Write good tests" adds no project-specific value.
- Setup steps: belong in README unless highly non-standard.
- Duplicate content: if it's in the README or existing docs, link to it rather than repeat it.
- Task-specific minutiae: database schemas, API specifications, deployment procedures belong in their own docs or a skill. Link to them rather than duplicating.
- Temporary notes: TODOs, one-off bug fixes, and temporary workarounds belong in code comments.
- Verbose descriptions: keep entries terse, drop long explanations.
- Kitchen sink entries: not every gotcha belongs here. Ask "Is this relevant across most coding sessions?" If no, it belongs in a path-scoped rule, code comments or specific docs.
- Formatting over-emphasis: don't bold the start of every sentence or bullet, reserve emphasis for warnings that truly warrant it.

## Conflict Audit

Before adding a line, check it against what else is already loaded: the user-level `~/.claude/CLAUDE.md`, sibling rule files, and any skill covering the same ground. Instructions that clash ("leave documentation as appropriate" next to "never add comments") make the agent resolve the contradiction before it can start work, and it won't resolve it the same way every session.

Keep each topic in one place:

- Already stated elsewhere: leave it there rather than restating it
- Narrower than an existing rule: write it as an exception that names what it overrides ("repo-wide we run Prettier; `/legacy` keeps its existing formatting")
- Genuinely at odds with a user-level or global rule: raise it with the user instead of silently overriding

Path-scoped rules refine the root CLAUDE.md for the files they match; they shouldn't reverse it.

## Linking to Existing Documentation

Point to existing docs rather than duplicating content. Provide context about when to read them:

- Good: "Database schema: see src/database/SCHEMA.md when working with data models"
- Bad: Copying schema tables, pasting deployment steps, or duplicating API flows into CLAUDE.md

## Writing Style

**Be specific**:
- Bad: "Use caution with the authentication system"
- Good: "Auth tokens expire after 1 hour. Background jobs must refresh tokens using `refreshToken()` in `src/auth/refresh.ts`"

**Be concise**:
- Bad: "It's important to note that when working with our database layer, you should be aware that..."
- Good: "Database queries: Use Prisma for CRUD, raw SQL for complex reports in `/queries`"

**State rules plainly**, with scope, reason and any exception together. Current models take "never" literally and over-apply ALL CAPS or IMPORTANT. If a plain line is still missed, shorten the file or use a hook.
- Bad: "IMPORTANT: NEVER edit migrations"
- Good: "Don't edit a migration already on main, as it has run in production. Add a new one"

Keep the strength of an existing ban. Turn it into "ask before" only if the user wants the agent to have that option.

**Name approvals exactly**, including the routine steps that need none:
- Bad: "Be careful and check before making changes"
- Good: "Ask before force-pushing or dropping a table. Retrying failed commands and running tests need no approval"

**Code ownership**: add "You are the owner and long-term maintainer of this codebase, and its design is up to you." only when the user wants the agent to restructure as it works. It also brings unrequested changes, and a scope rule doesn't cancel it.

## When to Update

Add an entry when the user asks, or when:
- The agent makes the same mistake a second time
- A review catches something the agent should have known about this codebase
- The user retypes a correction from an earlier session
- A new contributor would need the same context

Prune an entry when its reason has gone, a path or command it names no longer exists, a linter or hook now enforces it, or the code now shows it. Check with the user before removing or loosening a safety rule.

Don't add anything covered under What to Exclude (one-off fixes, temporary workarounds, info already in docs, verbose explanations).

## Spelling Conventions

Always use Australian English spelling

## Example Structure

```markdown
# Commands
- Test: `pnpm test`, one file: `pnpm vitest run path/to/file.test.ts`
- Lint and typecheck: `pnpm lint && pnpm tsc --noEmit`

# Conventions
- Errors: use the helpers in src/lib/errors.ts rather than raw strings
- Feature flags: check in middleware, not in business logic
- Dates: UTC in the database, format client-side via src/utils/dates.ts
- Auth: see src/auth/README.md when changing token flows

# Gotchas
- src/legacy/ is live but don't copy its patterns into new code
- Cache: acquire the lock before checking status, as concurrent workers race
```

## Token Budget

Aim for under 200 lines and 1k-4k tokens per CLAUDE.md. A single CLAUDE.md is fine for most projects. If exceeding:
1. Reword to be more concise
2. Remove generic advice
3. Ensure there's no duplicated content
4. Move content that only some files or tasks need (see Where Each Instruction Belongs)

Estimate token count with `wc -c CLAUDE.md`, then divide the character count by roughly 4.

## Verification

- Loading: ask the user to run `/context all` and check **Memory files**. Nested CLAUDE.md files and path-scoped rules load on demand, so they won't be listed.
- Audits and large rewrites: run the bundled `claude-api` skill with `prompt-audit <path>` (users can type `/doctor prompt-audit <path>`) and judge each finding. Skip it for small edits, as it loads a lot of context.

## Review Checklist

Before finalising:
- [ ] Nothing from What to Exclude slipped in (line numbers, code style, duplicated docs, temporary notes, verbose guidance)
- [ ] Wording is concise and not duplicated
- [ ] Sections only add non-obvious value
- [ ] Simple formatting, no smart quotes, no em dashes, no excessive bolding
- [ ] Information is unlikely to become stale quickly
- [ ] Prefer positive rules with a substitute ("use semicolons or periods to separate clauses") over bare prohibitions ("never use em-dashes")
- [ ] Every named path and command exists
- [ ] Content is tight, concise and actionable, not verbose or narrative driven
