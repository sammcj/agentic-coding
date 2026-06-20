# Worked example: catching a false signal

A run through the whole method on a real case, refining a session-analysis script. The headline finding turned out to be a measurement artifact. The point isn't the specific numbers; it's the chain of moves, each of which a step in the loop would prompt.

The report claimed user frustration rose 52% between two periods, a clean, alarming number.

1. **Replicate.** Reproduced 12.0% -> 18.2% exactly from the raw logs. Matching the original proved the instrument was being read the same way, not that the conclusion was sound.
2. **Look at the inputs, not the aggregate.** Sampled the flagged messages. Most weren't typed by the user; they were task notifications, agent summaries, and compaction dumps logged under the user role, carrying words like "broken" and "wrong" as technical vocabulary.
3. **Decompose.** The machine-injected share of "prompts" had nearly doubled (21% -> 39%) between the two periods. That shift alone produced the entire "spike."
4. **Fix upstream.** Classify provenance, then run sentiment on hand-typed messages only. The 52% rise collapsed to +8%, inside noise.
5. **Don't trust the fix's aggregate either.** A meaningfulness audit on the new directed-frustration detector found about 15% precision (subagent "read the file" templates and bare substring hits dominating the matches). Rebuilt it pronoun-gated, then re-sampled to confirm the precision actually moved.

Lesson chain: a surprising aggregate is a hypothesis, not a finding; suspect the measurement before the subject; fix the input over the output; and audit the fix the same way you audited the original. Each move maps to a rubric condition or an accuracy check, which is what keeps the chain from stopping early at a plausible but wrong answer.
