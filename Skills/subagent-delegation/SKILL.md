---
name: subagent-delegation
description: How to scope, brief and choose sub-agents when delegating work with the Agent tool - named vs forked agents, file ownership boundaries, model selection, and when a fork is the wrong choice. Use when delegating to one or more sub-agents, deciding between a named agent and a fork, or splitting parallel work across agents.
---

# Sub-agent delegation

Delegation is authorised standingly (see CLAUDE.md). This skill covers how to do it well.

## Briefing a sub-agent

- Instruct them to return only key information
- Define clear boundaries per agent. Specify which files each agent owns
- Include "you are one of several agents" in instructions
- Set explicit success criteria. Combine small updates to prevent over-splitting
- Sub-agents can compete and erase each other's changes - ensure no overlap
- If the task is simple and does not require careful consideration, reasoning or creativity (for example summarising simple web searches) you may use the sonnet model

## Named vs forked

**Named** (standard) sub-agents have their own context window - good for parallel research, inspection, or separate features. Default to a named sub-agent.

A **fork** inherits the main session's full conversation history, system prompt, tools, and model. Output isolation is preserved (only the final result returns) but input isolation is lost.

Fork only when the accumulated nuance of the main conversation is genuinely useful to the subtask AND the task doesn't benefit from a fresh perspective.

- Never fork code review, premise-checking, or any task that needs an adversarial reading - the fork inherits its own bias along with its context
- Fork suits: parallel design variations that must respect prior decisions, MCP queries whose answer depends on session context, multi-step tangents you'd otherwise need to recap
- Pass `isolation: "worktree"` when a fork will edit files speculatively, so its changes land in a separate git worktree instead of the working tree
