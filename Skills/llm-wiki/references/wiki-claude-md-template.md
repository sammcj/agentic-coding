# {Wiki Display Name}

{NOTE - this is the wiki's CLAUDE.md: project memory an agent auto-loads whenever its working directory is this repo, no skill required. It is a different file from the root SKILL.md (the query-only skill, loaded by description match). Keep it tiny - it points at the entry point, it is not the manual. Fill in {Wiki Display Name} and {subject}, then delete this note.}

This repository is an **LLM wiki**: a knowledge base on {subject}, compiled into plain markdown under `wiki/` and maintained by an AI agent at the user's direction - the user curates sources and asks questions; the agent does the bookkeeping.

To work with it, start by reading `SKILL.md` in this directory - it explains how to query the wiki and the conventions to follow. The article catalogue is `wiki/index.md`; the format is described in `wiki/README.md`.

**If the `llm-wiki` skill is available and not already active, activate it.** It owns the workflow for every change to the wiki - ingesting sources, superseding stale knowledge, linting, auditing - and keeps the format consistent. Without it, treat the wiki as read-only and do not hand-edit articles outside the `wiki/README.md` conventions. `raw/` is immutable source material.

## General rules

- Always use Australian English spelling.
- Always use plain ASCII punctuation (straight quotes, single hyphens), Do NOT use any "smart" formatting such as smart quotes, em-dashes, en-dashes or non-breaking spaces.

## Git commits

When you have completed all work, you may wish to ask the user if they'd like you to commit your changes to git, if doing so ensure your git commit message is clear and concise as to what has been added or improved.
