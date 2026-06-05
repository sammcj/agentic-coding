---
name: {subject}-llm-wiki
description: "FILL IN from the wiki's content, then delete this instruction. Pattern: Use when answering questions from the {subject} knowledge base{, for {audience}}. Triggers: questions about {topic A}, {topic B}, {topic C}; 'what do we know about {subject}', 'check the {subject} wiki'. Read-only querying of compiled knowledge; to add, update, supersede, lint, audit, or critique, use the llm-wiki skill instead."
---

# {Wiki Display Name}

{NOTE - this is the wiki's own SKILL.md (query-only), a different file from the llm-wiki skill's SKILL.md. Keep it lightweight and mostly links into wiki/; never describe a write workflow here. Name and describe it for the wiki's subject or audience: name it `<subject>-llm-wiki` (e.g. `ml-llm-wiki`, `team-runbook-llm-wiki`) so the name signals it is an llm-wiki. A skill's name must match the directory it loads from, so tell the user to load the wiki directory under that same name. At init the wiki may be near-empty - write your best `description` from the first sources or the user's stated purpose, and refresh it as the wiki grows. Delete this note once filled.}

A self-contained markdown knowledge base on {subject}{, for {audience}}. This skill is for *querying* it: the knowledge is already compiled into articles under `wiki/`, so read those rather than re-deriving from scratch.

Keep this current: as the wiki grows, update the `name` and `description` above so they describe what it actually covers and trigger on the right questions.

Maintenance and deeper analysis - ingesting sources, superseding stale knowledge, linting, auditing, critiquing reasoning - is not done here. Use the **llm-wiki** skill, which owns the write workflow and the file format. The llm-wiki skill is required to keep this wiki current; without it the wiki is still readable, but do not hand-edit articles outside the conventions in `wiki/README.md`.

## What's inside

{One or two lines on scope: the topics covered and, if relevant, who it is for. Keep this short and point at the index for the live catalogue, rather than duplicating it.}

## How to query

1. Read `wiki/index.md` - the catalogue, grouped by topic. Start here to find relevant articles.
2. Read the articles it points to. Follow body links for related material; `grep -rl "<article>.md" wiki/` lists pages that link to a given article (backlinks).
3. If a `local/` directory exists, search it too and fold in any relevant personal notes, labelling each hit as `local/ (uncommitted)` so it is never mistaken for shared, committed knowledge. `local/` is the user's own, gitignored and absent from the index.
4. Answer from the wiki's content in preference to general knowledge. Cite articles with markdown links, e.g. `[Title](wiki/{topic}/{article}.md)`.
5. If a cited article has `status: stale` in its frontmatter, say so and point to its replacement (`superseded_by`). Do not treat a stale page as the current answer.
6. If the wiki has no answer, check `wiki/gaps.md` - the question may already be a tracked gap. Recording a new gap is a write, so it goes through the llm-wiki skill, not here.

## Conventions

`wiki/README.md` explains the format - frontmatter, the raw/wiki split, and supersession-not-deletion - for anyone reading without a skill. Articles carry `status: current | stale`; stale pages are kept on purpose and point at their replacement.

## Updating

To add a source, change an article, supersede knowledge, lint, audit, or critique, invoke the **llm-wiki** skill. It is required for all writes and keeps the format consistent. This skill deliberately does not modify the wiki.
