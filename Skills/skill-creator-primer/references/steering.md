# Steering the Agent

How to make a skill produce the same _process_ every run. Two levers: leading words (anchor what the agent does and when the skill fires) and leg work (force thoroughness on the current step).

## Leading words

A leading word (Leitwort) is a compact term already in the model's pretraining, repeated as a token rather than spelled out in a sentence. The agent echoes it in its reasoning and output, and the prior the word carries steers behaviour - a few tokens stand in for a paragraph. It works twice: in the body it anchors execution; in a description it anchors invocation.

- **Prefer a pretrained word.** A coined word recruits no priors, so you pay in definition tokens what a known word gives free. Reach for an existing term first; coin one only when none fits, then define it once.
- **Use one word per concept, repeated.** Consistency is what builds the distributed definition across the skill. Where you can, use the same word in your prompts, docs, and code so invocation lands too.
- **Verify it fired.** Watch the reasoning traces adopt the phrase. If they don't, the word is too weak - pick a stronger one.

Example: instead of "don't build layer by layer, build a thin end-to-end slice first", say _vertical slice_ - a known term that triggers the prior in two words. Refactoring shape: "fast, deterministic, low-overhead" collapses to _tight_; "be thorough" (too weak to beat the default) becomes _relentless_.

## Completion criteria

End every step on a criterion the agent can check. It carries two independent properties:

- **Clarity** - can the agent tell done from not-done? A vague bound ("understanding reached") lets it declare done and move on; a sharp bound resists that.
- **Demand** - how much it requires. "Every modified model accounted for" forces leg work that "produce a change list" does not. Demand can also bind a body of flat reference ("every rule applied"), giving a step-less skill an exhaustiveness bar.

The strongest criteria are both checkable and exhaustive.

## Premature completion

The failure where the agent's attention slips to _being done_ and it skimps the current step. It's a tug-of-war: visible later steps pull the agent forward, the completion criterion resists. Defend in order:

1. **Sharpen the criterion first** - local and cheap.
2. **Only if the criterion is irreducibly fuzzy _and_ you observe the rush**, hide the later steps by splitting the step into its own skill so the agent sees one step at a time (this is _leg work_: with the end goal out of view, the agent invests fully in the current phase).

Hiding only works across a real context boundary - a user-invoked hand-off or a subagent dispatch. An inline model-invoked call leaves the later steps in context and clears nothing.
