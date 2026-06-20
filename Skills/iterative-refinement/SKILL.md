---
name: iterative-refinement
description: >
  Disciplined, measurable iteration for a substantial refinement or investigation: loop against
  verifiable pass/fail conditions, fan work out to subagents, and keep the main context lean. Use
  when improving something measurable over repeated cycles (tuning a metric or detector, refactoring
  against a regression bar), chasing a surprising or suspicious number, or driving a long multi-step
  task where delegation and context discipline matter. Not for one-shot edits or quick lookups that
  don't warrant a loop.
---

# Iterative refinement with verifiable conditions

Improve any system (script, pipeline, prompt, doc, config, dataset) by looping against measurable pass/fail conditions while keeping the main thread's context lean. Task-agnostic. The aim is to make "is it good yet?" a single repeatable command, catch each regression at the edit that caused it, and keep load-bearing reasoning in cheap, auditable steps.

Use this as a toolkit, not a script. Each method below earns its place by what it prevents, and that reasoning is stated inline so you can judge when it applies. Reach for the methods the situation calls for, scale them to the stakes, and adapt or skip what doesn't fit; they compose well, but no fixed subset is mandatory and this skill can't anticipate every task you'll point it at. When a method clearly fits, lean into it fully rather than half-applying it. The judgement of which to use, and how hard, stays yours.

## The loop

1. Turn the goal into a pass/fail rubric with explicit thresholds. "Useful" isn't checkable; "contamination < 2%, both naive and effective ratios reported, every input row classified, prints `Overall: PASS`" is.
2. Bake the rubric into the artifact as a self-check it prints. The artifact computes its own metrics and prints `[PASS]/[FAIL]` per condition, so the check can't drift out of sync with the code the way an external checklist does. Now any party (you, a subagent, the user) re-verifies with one command.
3. Change one layer, re-run the check. Catch each regression at the edit that caused it, not three edits later.
4. Loop on a fast slice, not the full dataset. Size the slice so a run takes seconds, not minutes. Run the full corpus only at checkpoints, when a layer is structurally complete and at sign-off, since that's where rare signals and period splits actually appear and the cost is justified.
5. Keep a frozen held-out slice the loop never touches, and confirm against it before sign-off. Looping hard on one slice optimises the rubric for that slice (Goodhart on your own metric); the held-out slice is what proves the gain generalised rather than memorised.
6. When all conditions pass but value remains, write a stricter rubric and loop again. Stop when a cycle yields nothing material.

## Writing good conditions

- Cheap to evaluate: exit code, grep, a printed PASS line, a line count. If checking costs as much as the work, you won't loop.
- Falsifiable with a number in it. "< 2%", not "low".
- Tied to the goal, not a proxy. A metric can pass while the output is useless, so pair aggregates with a meaningfulness audit (below) that samples real outputs.
- Reconciliation invariants are programmatic gates between steps that catch silent bugs: classified counts must sum to the total; naive and effective measures must bracket reality.
- Track cost alongside correctness. A rubric that watches only accuracy hides regressions in the dimensions that also matter: tool-call count, token consumption, wall-clock, and error rate. A change that "passes" but doubles tokens is a finding, not a success.

## Context-window economics

Every byte a tool returns stays in context and taxes every later turn. This is context engineering: treat the window as the scarcest resource, because reasoning quality degrades with depth (context rot) well before any hard limit. Three mitigations, highest leverage first:

1. Think-in-code. To _process_ output (filter/count/parse/aggregate), run code over it and print only the answer; raw bytes never enter the conversation. Reading bytes is justified only when you'll _edit_ them. The context-mode `ctx_execute` tools do this in a sandbox when available.
2. Return conclusions, not transcripts. A subagent's tool history stays in its context; only its final message returns. A task worth 50 file-reads costs you one paragraph. Forbid the subagent from pasting file bodies or full reports.
3. Locate before reading. Print the line numbers or symbols you need with one targeted query, then read only that span.

Reasoning degrades in bands: roughly 0-100k tokens is peak, 100-150k still strong, 150-200k noticeably softer, and auto-compaction looms around a third of the window. Budget against the bands, not the ceiling. Bring the main thread's irreversible state (task list, strategy notes, decisions) up to date _before_ you approach compaction; a summary written ahead of time survives, working memory you were relying on may not. If a single task can't fit the smart zone, that's a signal to decompose and delegate, not to push through.

## Delegation and subagents

Push work off the main thread whenever it produces more bytes than its conclusion is worth.

- Delegate bulk reads/scans (raw bytes stay in the subagent) and well-scoped edits.
- For a delegated edit, give a tight spec: the objective, the exact variables/contracts it may touch, hard "don't touch X" boundaries, the output format, and the SAME machine-checkable acceptance loop you'd run. It inherits your verification standard and returns a compact summary.
- State invariants up front so framing can't drift (for example: assess on effective metrics, never relabel the workflow "degraded", keep output lean). Cheaper to state than to repair.
- Named subagent (fresh context) for research, inspection, or anything needing an unbiased read. Fork (inherits your context) only when accumulated nuance helps and a fresh view wouldn't. Never fork a review, audit, or premise-check; a fork inherits your blind spots.
- Disjoint ownership when running several at once; overlapping write scope means they erase each other.
- Verify what returns: a summary is a claim. Spot-check load-bearing results with a cheap command, or have a second independent agent check.

## Fan-out topology

Match it to the write-pattern:

- Sequential single subagent when edits hit the same region of one file; parallelism only causes merge collisions.
- Parallel read-only subagents when subtasks mutate nothing shared. Best fit for a meaningfulness audit: one samples classifier false-negatives, one judges detector precision, one sanity-checks counts, same data, no writes, can't conflict. Send them in one batch so they truly run in parallel.
- Git-worktree agents only when agents must write concurrently, or to race competing variants for a winner. They cost setup and disk; don't use when read-only or sequential suffices.
- Scale the fleet to the task's complexity, and say so when you cap coverage. Rough budget: a simple lookup is one agent and a few tool calls; a broad audit is many agents in parallel. Fan-out multiplies token spend by agent count (a parallel multi-agent sweep can run on the order of 10-15x a single-threaded pass), so "ran 5 of 20" must never read as "covered everything".

## Accuracy and verifiability

- Replicate before trusting. Reproduce a surprising number independently before acting on it; matching the original exactly proves you're measuring the same thing, then you can decompose it. A surprising aggregate is a hypothesis, not a finding.
- Fix the measurement before the output. Suspect the instrument first. A measurement artifact is a construct-validity threat: the metric isn't measuring what its name claims. The fix is usually upstream (classification, provenance, sampling), not a better keyword list downstream.
- Question imported benchmarks. Borrowed thresholds often assume a workflow you're not running (a Read:Edit ratio looks "degraded" only if you ignore that reads were routed through other tools).
- Report naive and effective side by side. Keep the flawed metric visible next to the corrected one so the gap is auditable rather than hidden.
- Meaningfulness audit. Aggregates hide false positives. Sample flagged items and judge them; estimate precision/recall on real data, not in theory.
- Calibrate any judge before you trust it. An LLM-as-judge has its own failure modes (rewards verbosity, favours its own phrasing, drifts across a run). Check a sample of its verdicts against your own judgement first; only then let its aggregate stand in for yours.
- Evaluate end state, not just per-step output. For a loop that mutates state (files, a database, a running system), assert on the final result and the invariants it must satisfy, not only on each intermediate artifact. Output audits miss bugs that surface only in the accumulated state.
- Make outputs auditable. Emit example matches alongside counts so a human can spot-check the classifier without rerunning it.

## Regression recovery

When a fix won't hold after a few tries, stop pushing on the same line:

- Re-read the contract. Is the metric measuring what you think?
- Prefer fixing input/measurement over patching output.
- Escalate a genuinely stuck subtask to a fresh subagent running a systematic-debugging / Fagan-inspection pass: give it the symptom, the failed attempts, and the violated invariant, and let it root-cause from scratch. A fresh agent with an explicit protocol breaks loops repeated patching won't, and keeps the thrashing out of the main context.

## Staying on task

A live task list is the backbone of completeness, not bureaucracy. Stand one up before the first loop iteration and keep it current as you work, marking items done and adding new ones the moment they surface. It's the one piece of state that reliably survives compaction, so treat it as the source of truth for what's done and what's left, not an afterthought you reconstruct at the end.

- Decompose generously; err toward too many tasks, not too few. A task you can complete in one step is the right size; "fix everything" is not.
- Exactly one item in-progress at a time. Mark it before starting, complete it before moving on.
- Add a follow-up the instant you discover it, even mid-edit. Discoveries that live only in working memory die at compaction.
- Encode delegated work as tasks too: what the agent is doing and its acceptance condition. An interrupted session then resumes from the list without re-deriving state.
- Put load-bearing findings in the task description, not just the chat; task text survives compaction, conversation may not.

## Prior art (why this works)

This playbook assembles established techniques. Reach for the named version when you want to go deeper or justify the approach.

| Practice here | Established name | Origin |
|---|---|---|
| The rubric-and-self-check loop | evaluator-optimizer pattern; eval-driven development | Anthropic, _Building Effective Agents_; Hamel Husain, _Your AI Product Needs Evals_ |
| Critique-then-revise iteration | Reflexion; Self-Refine | Shinn et al. 2023; Madaan et al. 2023 |
| Reconciliation invariants between steps | programmatic gates | Anthropic, _Building Effective Agents_ |
| Fix the measurement before the output | construct validity; Goodhart's law | Cronbach & Meehl 1955 |
| Meaningfulness audit and judge calibration | LLM-as-judge failure modes | Zheng et al. 2023 (MT-Bench) |
| Context economics, conclusions-not-transcripts | context engineering; context rot; compaction | Anthropic, _Effective Context Engineering for AI Agents_ |
| Read-only parallel auditors that vote | self-consistency; orchestrator-workers | Wang et al. 2022; Anthropic, _Multi-Agent Research System_ |

For a worked example of the whole chain (a "frustration spike" that turned out to be a measurement artifact), see `references/worked_example.md`.

## Checklist

A prompt to confirm what applies to the task in front of you, not a gate every task must clear. Skip the lines that don't fit.

- [ ] Goal is a pass/fail rubric with numeric thresholds
- [ ] Rubric baked into the artifact as a printed self-check
- [ ] Cost dimensions tracked alongside accuracy (tokens, tool calls, errors)
- [ ] Fast slice for the loop; full run plus a frozen held-out slice at sign-off
- [ ] Bulk reads/edits delegated; only conclusions return
- [ ] Invariants stated so delegates can't undo deliberate choices
- [ ] Independent checks fanned out read-only; worktrees only for parallel writes or competing variants
- [ ] Surprising numbers replicated before action
- [ ] Naive and corrected metrics reported side by side
- [ ] Meaningfulness audit on sampled outputs; judge calibrated before its aggregate is trusted
- [ ] End state asserted, not just per-step output
- [ ] On regression: question the measurement, fix upstream, escalate to structured debugging
- [ ] Plateau -> stricter rubric, or stop
