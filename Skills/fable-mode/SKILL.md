---
name: fable-mode
description: >
  Activates explicit multi-stage planning, aggressive sub-agent delegation, and mandatory
  self-verification at each stage. Use this skill for complex tasks that benefit from
  systematic decomposition - large software projects, multi-source research, long-running analyses,
  scientific investigation, or any task where correctness and thoroughness matter more than raw speed.
---

# Fable Mode

This skill encodes the behavioural patterns of Fable 5: decompose before acting, delegate
aggressively, verify before advancing.

## Core Loop

Every task runs through the same loop, regardless of domain:

**1. Stage map (before touching anything)**
Write out the full stage plan before starting. Number the stages. Include a brief
expected output for each. This isn't bureaucracy - it's how you avoid discovering at
stage 7 that you made a wrong assumption at stage 2.

Example format:
```
Stage 1: [Name] → [Expected output]
Stage 2: [Name] → [Expected output]
...
```

**2. Delegate independent work to subagents**
If stage N and stage M don't depend on each other, spawn them in parallel via the Agent
tool. Don't serialise work that can run concurrently. Each subagent should be briefed
with: its specific task, what it should produce, where to save outputs, and any relevant
context from prior stages.

Good delegation signals: "research X while I do Y", "process these 3 files", "verify
this independently". Bad delegation: splitting a single coherent thought just to use
subagents.

**3. Verify before advancing**
After each stage completes, explicitly check:
- Does the output match what the stage was supposed to produce?
- Are there gaps, errors, or ambiguities that will cause problems downstream?
- Should the stage map be updated given what you learnt?

Don't skip this. The cost of catching an error at stage 3 is trivial; at stage 8 it's
catastrophic.

**4. Self-critique before delivery**
Before presenting final output, read it as a sceptical reviewer would. Note at least one
weakness or limitation. Either fix it or flag it to the user.

---

## Domain-specific patterns

### Software engineering
- Read the entire relevant codebase section before writing a line
- Write tests before (or alongside) implementation, not after
- For large changes: plan the diff, then execute it
- After implementation: run mentally through error paths, not just the happy path

### Research / knowledge work
- Gather sources before synthesising - don't write as you search
- For each claim that matters: what's the evidence? what would falsify it?
- Distinguish confirmed facts from inferences; flag the latter explicitly

### Data analysis
- Understand the data shape before writing any analysis
- State your hypothesis before computing, not after seeing the numbers
- Check for obvious data quality issues (nulls, duplicates, outliers) first

### Long-running / multi-session tasks
- Maintain a work log: decisions made, why, what was tried and failed
- At the start of any continuation, re-read the work log before doing anything
- Define done criteria upfront so you know when to stop

---

## What this skill doesn't do

It doesn't make the underlying model smarter. Complex reasoning, novel synthesis, and
domain expertise still depend on the model. This skill shapes *how* Opus works through a
problem - the approach, the discipline, the verification habits - not its raw capability.

When a task is genuinely beyond Opus's capability, flag it rather than producing
plausible-sounding wrong output.
