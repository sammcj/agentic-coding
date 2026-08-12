# Initialisation: creating a wiki and its entry points

Triggers on the first Ingest into a directory with no `wiki/`. Check whether `raw/` and `wiki/` exist. Create only what is missing; never overwrite an existing file.

## Files to create

- `raw/` - directory, with a `.gitkeep`.
- `wiki/` - directory, with a `.gitkeep`.
- `wiki/README.md` - orientation doc, from `references/templates/wiki-readme-template.md`.
- `wiki/index.md` - heading `# Knowledge Base Index`, empty body; per-topic bullet form in `references/templates/index-template.md`.
- `wiki/log.md` - heading `# Wiki Log`, empty body.
- `wiki/gaps.md` - `type: Gap Register` frontmatter, heading `# Knowledge Gaps`, empty body (`references/gaps.md`).
- `.gitignore` (project root) - from `references/templates/wiki-gitignore-template.md`. Excludes `local/` and per-machine editor noise so the wiki lives in git cleanly. Keep an existing one; merge in the `local/` line if it is missing.
- `SKILL.md` (project root) - the query-only skill, from `references/templates/wiki-skill-template.md`. See below.
- `CLAUDE.md` (project root) - project memory for the wiki repo, from `references/templates/wiki-claude-md-template.md`. See below.

`local/` is not created at init; it appears the first time the user stores personal content there (`references/local-content.md`).

## The wiki as a skill (root `SKILL.md`)

This file lets an agent load the wiki as an Agent Skill and *query* it without the llm-wiki skill present. It is a different file from llm-wiki's own SKILL.md: lightweight, mostly links into `wiki/index.md` and `wiki/README.md`, and read-only. Exact format: `references/templates/wiki-skill-template.md`.

- **Name and describe it from the content.** Name it `<subject>-llm-wiki` (e.g. `ml-llm-wiki`, `team-runbook-llm-wiki`), taking the prefix from the wiki's subject or audience so the name signals it is an llm-wiki. A skill's name must match the directory it loads from, so tell the user to load the wiki directory under that name. Write a `description` that says what the wiki is for and names concrete trigger topics. At init the wiki may be near-empty - write your best guess from the first sources or the user's stated purpose, and refresh `name` and `description` as it grows.
- **Query only; writes go through llm-wiki.** The file routes every add, update, supersede, lint and audit back to the llm-wiki skill, and reminds the user that llm-wiki is required to keep the wiki current. It must not describe a write workflow of its own. When you create it, tell the user the llm-wiki skill must stay installed to maintain the wiki.
- Created at init, never overwritten. Lint reports a missing one and offers to add it to wikis that predate this (`references/lint.md`).

## The wiki's `CLAUDE.md`

Project memory: an agent auto-loads it whenever the wiki repo is its working directory, no skill required. It complements the root SKILL.md - SKILL.md loads by description match, CLAUDE.md by location, so CLAUDE.md is the entry point for an agent working *inside* the wiki.

Keep it tiny: state what the repo is, point the agent at the root SKILL.md to learn how to interface with the wiki, and tell it to activate the **llm-wiki** skill if available (otherwise treat the wiki as read-only and route writes through it). It defers the query steps to SKILL.md rather than repeating them. Template: `references/templates/wiki-claude-md-template.md`. Created once, never overwritten; lint reports a missing one and offers to add it.
