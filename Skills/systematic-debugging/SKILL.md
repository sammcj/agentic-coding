---
name: systematic-debugging
description: Applies a modified Fagan Inspection methodology to resolve persistent bugs and complex issues. Use when several fix or debugging attempts have already failed and a methodical root-cause analysis warranting a Fagan inspection is needed. For first-pass diagnosis of a reproducible bug or regression use diagnose-hard-problem. Do not use for simple troubleshooting.
---

# Systematic Debugging with Fagan Inspection

This skill applies a modified Fagan Inspection methodology for systematic problem resolution when facing complex problems or stubborn bugs that have resisted multiple fix attempts.

## Process Overview

Create tasks for each of the four phases, then work them to completion, marking each done before starting the next.

Follow these four phases sequentially. Do not skip phases or attempt fixes before completing the inspection.

### Phase 1: Initial Overview

Establish a clear understanding of the problem before analysis:

- **Explain the problem** in plain language without technical jargon
- **State expected behaviour** - what should happen
- **State actual behaviour** - what is happening instead
- **Document symptoms** - error messages, logs, observable failures
- **Context** - when does it occur, how often, under what conditions
- **Prior fix attempts** - list each attempt, what it changed, and why it failed; treat these as eliminated hypotheses that Phase 3 must account for

**Output:** A clear problem statement that anyone could understand.

### Phase 2: Systematic Inspection

Perform a line-by-line walkthrough as the "Reader" role in Fagan Inspection. **Identify defects without attempting to fix them yet** - this is pure inspection.

Check against these defect categories:

1. **Logic Errors**
2. **Boundary Conditions**
3. **Error Handling**
4. **Data Flow Issues**
5. **Integration Points**

**Think aloud** during this phase. For each section of code:
- State what the code is intended to do
- Identify any discrepancies between intent and implementation
- Flag assumptions or unclear aspects
- Use ultrathink to think deeper on complex sections

**Output:** A categorised list of identified defects with line numbers and specific descriptions.

### Phase 3: Root Cause Analysis

After identifying issues, trace back to find the fundamental cause - not just symptoms.

**Five Whys Technique:**
- Ask "why" repeatedly (at least 3-5 times) to get to the underlying issue
- State each "why" explicitly in your analysis
- Example:
  - Why did the API call fail? → Because the request was malformed
  - Why was it malformed? → Because the data wasn't serialised correctly
  - Why wasn't it serialised? → Because the serialiser expected a different type
  - Why did it expect a different type? → Because the schema was updated but code wasn't
  - Root cause: Schema versioning mismatch between services

**Consider:**
- Environmental factors (configuration, dependencies, runtime environment)
- Timing and concurrency (race conditions, async issues)
- Hidden assumptions in the code or system design
- Historical context (recent changes, migrations, updates)

**State assumptions explicitly:**
- "I'm assuming X because..."
- "This presumes that Y is always..."
- Flag any assumptions that need verification

**Output:** A clear statement of the root cause, the chain of reasoning that led to it, and any assumptions that need validation.

### Phase 4: Solution & Verification

Now propose specific fixes for each identified issue.

**For each proposed solution:**
1. **Describe the fix** - what code/configuration changes are needed
2. **Explain why it resolves the root cause** - connect it back to Phase 3 analysis
3. **Consider side effects** - what else might this change affect
4. **Define verification steps** - how to confirm the fix works

**Verification Planning:**
- Specific test cases that would have caught this bug
- Manual verification steps
- Monitoring or logging to add
- Edge cases to validate

**Output:** A summary of findings (key defects and root cause), a prioritised list of proposed fixes with rationale, and a verification plan for confirming the fixes work.

## Important Guidelines

- **Complete each phase thoroughly** before moving to the next
- **Flag unclear aspects** rather than guessing - if something is uncertain, say so
- **Use available tools** - read files, search code, run tests, check logs
- **Focus on systematic analysis** over quick fixes
- **Validate flagged aspects** - after completing all phases, revisit any unclear points and use the think tool with "ultra" depth if needed to clarify them

## Final Output

After completing all four phases, unless the user indicates otherwise, proceed to implement the proposed solutions.

## When This Skill Should NOT Be Used

- For simple, obvious bugs with clear fixes
- When the first debugging attempt is still underway
- For new features (this is for debugging existing code)
- When the problem is clearly environmental (config, infrastructure) and doesn't require code inspection
