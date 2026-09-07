# Machine Learning Wiki

<!-- Note this is an EXAMPLE CLAUDE.md file for the EXAMPLE llm-wiki -->

This repository is an **LLM wiki**: a knowledge base on transformer architectures, attention cost and efficiency, and long-context scaling, compiled into plain markdown under `wiki/` and maintained by an AI agent at the user's direction - the user curates sources and asks questions; the agent does the bookkeeping.

To work with it, start by reading `SKILL.md` in this directory - it explains how to query the wiki and the conventions to follow. The article catalogue is `wiki/index.md`; the format is described in `wiki/README.md`.

**If the `llm-wiki` skill is available and not already active, activate it.** It owns the workflow for every change to the wiki - ingesting sources, superseding stale knowledge, linting, auditing - and keeps the format consistent. Without it, treat the wiki as read-only and do not hand-edit articles outside the `wiki/README.md` conventions. `raw/` is immutable source material.

## Scope

- **Mode**: personal
- **Purpose**: track how transformer architectures scale, and what the cost of attention means in practice.
- **In scope**: transformer internals, attention cost and efficiency, long-context scaling, and the papers and posts behind them.
- **Out of scope**: model release news, vendor benchmarks, and anything about running or serving models in production.
- **Horizon**: ongoing.

Check an incoming source against this before ingesting it. A source outside the scope is a conversation with the user, not a judgement call to make silently. If the wiki has genuinely outgrown this block, say so and let the user decide whether to widen the scope or start a separate wiki - do not widen it yourself.

## General rules

- Always use Australian English spelling.
- Always use plain ASCII punctuation (straight quotes, single hyphens), Do NOT use any "smart" formatting such as smart quotes, em-dashes, en-dashes or non-breaking spaces.

## Git commits

When you have completed all work, you may wish to ask the user if they'd like you to commit your changes to git, if doing so ensure your git commit message is clear and concise as to what has been added or improved.

(Sample note: this example wiki lives in `examples/` within the llm-wiki repo.)
