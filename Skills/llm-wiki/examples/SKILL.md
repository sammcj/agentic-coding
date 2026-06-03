---
name: ml-llm-wiki
description: "Use when answering questions from this machine-learning knowledge base. Triggers: questions about transformers, attention cost and efficiency, and long-context scaling; 'what do we know about attention', 'check the ML wiki'. Read-only querying of compiled knowledge; to add, update, supersede, lint, or audit, use the llm-wiki skill instead."
context: fork
allowed-tools: Read Grep Glob Agent
---

# Machine Learning Wiki

A self-contained markdown knowledge base on transformer architectures, attention cost and efficiency, and long-context scaling. This skill is for _querying_ it: the knowledge is already compiled into articles under `wiki/`, so read those rather than re-deriving from scratch.

Keep this current: as the wiki grows, update the `name` and `description` above so they describe what it actually covers and trigger on the right questions.

(Sample note: this example wiki lives in `examples/` within the llm-wiki repo. To load it as a skill, place the directory in your skills path named `ml-llm-wiki`, so the directory matches the `name` above.)

Maintenance - ingesting sources, superseding stale knowledge, linting, auditing - is not done here. Use the **llm-wiki** skill, which owns the write workflow and the file format. The llm-wiki skill is required to keep this wiki current; without it the wiki is still readable, but do not hand-edit articles outside the conventions in `wiki/README.md`.

## What's inside

One topic so far, `machine-learning`: how attention works, why its memory cost was once thought to be a hard quadratic limit and why that turned out to be an implementation artefact, and what makes long context practical.

## How to query

1. Read `wiki/index.md` - the catalogue, grouped by topic. Start here to find relevant articles.
2. Read the articles it points to. Follow body links for related material; `grep -rl "<article>.md" wiki/` lists pages that link to a given article (backlinks).
3. Answer from the wiki's content in preference to general knowledge. Cite articles with markdown links, e.g. `[Attention Efficiency](wiki/machine-learning/attention-efficiency.md)`.
4. If a cited article has `status: stale`, say so and point to its replacement. Here, `attention-cost.md` is stale and superseded by `attention-efficiency.md`.
5. If the wiki has no answer, check `wiki/gaps.md` - the question may already be a tracked gap. Recording a new gap is a write, so it goes through the llm-wiki skill, not here.

## Conventions

`wiki/README.md` explains the format - frontmatter, the raw/wiki split, and supersession-not-deletion - for anyone reading without a skill. Articles carry `status: current | stale`; stale pages are kept on purpose and point at their replacement.

## Updating

To add a source, change an article, supersede knowledge, lint, or audit, invoke the **llm-wiki** skill. It is required for all writes and keeps the format consistent. This skill deliberately does not modify the wiki.

## Tips

- Use sub-agents with well defined goals, scope and context to parallelise work and reduce context rot in the main conversation.
