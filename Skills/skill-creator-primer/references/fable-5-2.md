# Fable 5.2 Addendum

A review lens for skills that run on Claude Fable 5.2 or Mythos 5.2. Authored skills stay portable: apply a cure only where it is harmless on other models.

- **Reasoning in the response** - an instruction to write out the agent's reasoning or thinking can return a `reasoning_extraction` refusal. Cure: ask for the decision and its evidence.
- **Think-less lines** - "answer directly, without deliberating" is a no-op at `medium` effort and above. Cure: delete the line and set `effort` in frontmatter.
- **`effort` below `high`** - early stops are more likely on multi-step workflows. Cure: sharpen each step's completion criterion (see `steering.md`). Re-test any effort value tuned on another model.
- **Standing delegation lines** - the model delegates readily when invited. Cure: each fan-out point states what a sub-agent costs, when it is worth it, and what brief it gets.
- **Hard style limits** - word and sentence caps are applied literally and make prose choppy. Cure: state the aim and its reason, and keep a hard cap only where a tool enforces it.
- **Accumulated cautions** - Gotchas phrased as "never X" suppress routine work such as retries. Cure: prune entries whose reason is gone, and name the steps that need no approval.
- **Ownership** - a skill that wants duplicated code merged says the agent owns the code. A scope-limiting rule elsewhere does not cancel that sentence.
