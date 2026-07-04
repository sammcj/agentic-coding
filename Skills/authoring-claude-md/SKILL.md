---
name: authoring-claude-md
description: Creating and maintaining CLAUDE.md project memory files and .claude/rules/ rule files that provide non-obvious codebase context. Use when (1) creating a new CLAUDE.md for a project, (2) adding architectural patterns or design decisions to existing CLAUDE.md, (3) capturing project-specific conventions that aren't obvious from code inspection, (4) organising instructions into path-scoped rule files.
---

# CLAUDE.md and Rules Authoring

Create effective CLAUDE.md files and `.claude/rules/` rule files that serve as project-specific memory for AI coding agents.

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

Use headings for clear organisation. Common sections: Architecture, Conventions, Gotchas, Testing. Use 2-4 sections and only include what adds value.

## When to Use `.claude/rules/` Instead

For larger projects, break instructions into separate files under `.claude/rules/`. Each `.md` file covers one topic. Prefer rules over a single CLAUDE.md when:

- Instructions are growing beyond 200 lines
- Different rules apply to different parts of the codebase (frontend vs backend, API vs CLI)
- Multiple team members maintain different sections
- Some instructions only matter when working with specific file types

### Rule File Basics

```
your-project/
├── .claude/
│   ├── CLAUDE.md           # Main project instructions
│   └── rules/
│       ├── code-style.md   # Always loaded
│       ├── testing.md      # Always loaded
│       └── security.md     # Always loaded
```

Files are discovered recursively, so subdirectories like `frontend/` and `backend/` work. Rules without `paths` frontmatter load at launch with the same priority as `.claude/CLAUDE.md`.

The same authoring principles apply to rule files: signal over noise, actionable context, no obvious information.

### Path-Specific Rules

Scope rules to specific files using YAML frontmatter with the `paths` field. These only load when Claude reads files matching the glob patterns, reducing noise and saving context.

```markdown
---
paths:
  - "src/api/**/*.ts"
---

# API Development Rules

- All API endpoints must include input validation
- Use the standard error response format
- Include OpenAPI documentation comments
```

Rules without a `paths` field apply unconditionally. Path-scoped rules trigger on file read, not on every tool use.

### User-Level Rules

Personal rules that apply across all your projects live at `~/.claude/rules/`. These load before project rules, giving project rules higher priority.

```
~/.claude/rules/
├── preferences.md    # Personal coding preferences
└── workflows.md      # Preferred workflows
```

### Rules vs Skills

Rules load every session (or when matching files are opened). For task-specific instructions that don't need constant context, use skills instead. Skills load only when invoked or when Claude determines they're relevant.

## What to Include

**Architectural decisions**: Why microservices over monolith, event-driven patterns, state management

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
- Code style guidelines: formatting rules, naming conventions, or patterns that linters enforce. Use ESLint, Prettier, Black, golangci-lint or similar, and Claude Code Hooks to run formatters.
- Generic advice: "Write good tests" adds no project-specific value.
- Setup steps: belong in README unless highly non-standard.
- Duplicate content: if it's in the README or existing docs, link to it rather than repeat it.
- Task-specific minutiae: database schemas, API specifications, deployment procedures belong in their own docs. Link to them rather than duplicating.
- Temporary notes: TODOs, one-off bug fixes, and temporary workarounds belong in code comments.
- Verbose descriptions: keep entries terse, drop long explanations.
- Kitchen sink entries: not every gotcha belongs here. Ask "Is this relevant across most coding sessions?" If no, it belongs in code comments or specific docs.
- Formatting over-emphasis: don't bold the start of every sentence or bullet, reserve emphasis for warnings that truly warrant it.

## Linking to Existing Documentation

Point to existing docs rather than duplicating content. Provide context about when to read them:

**Good**:
```markdown
# Architecture
Event-driven architecture using AWS EventBridge.

- For database schema: see src/database/SCHEMA.md when working with data models
- For auth flows: see src/auth/README.md when working with authentication
```

**Bad**: Copying schema tables, pasting deployment steps, or duplicating API flows into CLAUDE.md

## Writing Style

**Be specific**:
- Bad: "Use caution with the authentication system"
- Good: "Auth tokens expire after 1 hour. Background jobs must refresh tokens using `refreshToken()` in `src/auth/refresh.ts`"

**Be concise**:
- Bad: "It's important to note that when working with our database layer, you should be aware that..."
- Good: "Database queries: Use Prisma for CRUD, raw SQL for complex reports in `/queries`"

**Use active voice**:
- Bad: "Migrations should be run before deployment"
- Good: "Run migrations before deployment: `npm run migrate:prod`"

## When to Update

Add to CLAUDE.md when:
- Discovering a non-obvious pattern after codebase exploration or complex problem resolution
- Solving an issue that took significant investigation that will be encountered again by other agents
- Finding a gotcha that's not immediately clear from code

Don't add anything covered under What to Exclude (one-off fixes, temporary workarounds, info already in docs, verbose explanations).

## Spelling Conventions

Always use Australian English spelling

## Example Structure

```markdown
# Architecture
Event-driven architecture using AWS EventBridge. Services communicate via events, not direct calls.

Auth: JWT tokens with refresh mechanism. See src/auth/README.md for detailed flows when working on authentication.
Database schema and relationships: see src/database/SCHEMA.md when working with data models.

# Conventions
- API routes: Plural nouns (`/users`, `/orders`), no verbs in paths
- Error codes: 4-digit format `ERRR-1001`, defined in src/errors/codes.ts
- Feature flags: Check in middleware, not in business logic
- Dates: Always UTC in database, format client-side via src/utils/dates.ts
- Documentation: Use DocBlocks for public functions, never use "smart" formatting markdown

# Gotchas

**Cache race conditions**: Always acquire lock before checking cache status

**Background job authentication**: Tokens expire after 1 hour. Refresh using
`refreshToken()` in src/auth/refresh.ts before making API calls.

# Testing

- Tests should never have external API calls or dependencies.
- Run `make test` before committing.
```

## Token Budget

Aim for 1k-4k tokens for CLAUDE.md. Most projects fit in 100-300 lines. A single CLAUDE.md is fine for most projects - if exceeding budget, consider whether splitting into `.claude/rules/` files would help (especially if some content only applies to specific file types). If exceeding:
1. Reword to be more concise
2. Remove generic advice
3. Ensure there's no duplicated content

Estimate token count with `wc -c CLAUDE.md`, then divide the character count by roughly 4.

## Review Checklist

Before finalising:
- [ ] Nothing from What to Exclude slipped in (line numbers, code style, duplicated docs, temporary notes, verbose guidance)
- [ ] Wording is concise and not duplicated
- [ ] Sections only add non-obvious value
- [ ] Simple formatting, no smart quotes, no em dashes, no excessive bolding
- [ ] Information is unlikely to become stale quickly
- [ ] Prefer positive rules with a substitute ("use semicolons or periods to separate clauses") over bare prohibitions ("never use em-dashes")
- [ ] Focused on stable, long-term patterns
- [ ] Content is tight, concise and actionable, not verbose or narrative driven
