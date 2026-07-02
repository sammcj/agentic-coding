---
name: prompt-fable
description: Write, review, or migrate prompts, system prompts, and skills targeting Claude Fable 5.
disable-model-invocation: true
---

# Prompting Claude Fable 5

Fable 5 (`claude-fable-5`) is Anthropic's Mythos-class model above Opus. `claude-mythos-5` is the same model without safety classifiers (limited release). This skill covers only what differs from prior Claude models; standard prompt engineering still applies.

## Hard constraints

- Never instruct the model to echo, transcribe, or explain its internal reasoning in response text. This triggers `stop_reason: "refusal"`. When migrating prompts or skills, audit for "show your thinking" / "explain your reasoning step by step in your answer" language. Any reasoning surfaced should be a concise summary.
- Safety classifiers refuse on request shape, not intent.

## Deprescribe when migrating

Instruction following is strong enough that one brief instruction replaces an enumerated behaviour list. Prompts and skills written for earlier models are often too prescriptive for Fable 5 and degrade its output. When migrating: delete instructions, test default behaviour, and re-add only what measurably changes it. Heavy MUSTs, exact step sequences, and case-by-case enumeration are the smell.

## Failure modes and tested mitigations

Each mitigation below is a condensed version of Anthropic's tested instruction; drop the relevant one into the system prompt when the failure appears.

- **Overplans ambiguous tasks**: "When you have enough information to act, act. If weighing a choice, give a recommendation, not an exhaustive survey."
- **Unrequested refactoring/tidying at high effort**: "Don't add features, refactor, or abstract beyond what the task requires. Do the simplest thing that works. Only validate at system boundaries."
- **Fabricated progress claims on long runs**: "Before reporting progress, audit each claim against a tool result from this session. If something is not yet verified, say so explicitly." (In Anthropic's testing this nearly eliminated fabricated status reports.)
- **Acts when the user was only asking**: "When the user is describing a problem or thinking aloud, the deliverable is your assessment. Report findings and stop; don't apply a fix until asked."
- **Ends turn on a promise ("I'll now run X") deep into long sessions**: "Before ending your turn, check your last paragraph. If it is a plan, a question, or a promise about work not done, do that work now with tool calls."
- **Suggests wrapping up when shown a token countdown**: hide context-budget counts from the model, or add: "You have ample context remaining. Do not stop, summarise, or suggest a new session on account of context limits."
- **Unreadable summaries after long agentic runs (arrow chains, invented labels)**: "Your final summary is for a reader who didn't see the work. Outcome first, complete sentences, spell out terms, drop the working shorthand."

## Scaffolding patterns that pay off

- **Give the reason, not only the request.** Fable 5 connects intent to context rather than inferring it: "I'm working on [larger task] for [who]. They need [what the output enables]. With that in mind: [request]."
- **Subagents.** Fable 5 dispatches parallel subagents readily and manages long-lived ones well. State when delegation is appropriate; prefer async communication over blocking on each return. Fresh-context verifier subagents outperform self-critique for long runs.
- **Memory.** Performance improves markedly given a place to record lessons across runs: one lesson per file, one-line summary at top, update rather than duplicate, delete wrong notes.
- **send-to-user tool.** For long async agents, a client-side tool whose input is rendered verbatim to the user. Defining it is not enough: Fable 5 rarely calls it without elicitation in the system prompt ("when you have content the user must read verbatim, call send_to_user"). Keep narration out of it.
- **Aim high.** Assign tasks harder than you'd give prior models; testing only simple workloads undersells the capability range.
