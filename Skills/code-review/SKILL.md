---
name: code-review
description: Use this skill after completing multiple, complex software development tasks before informing the user that work is complete.
---

# Code Review After Completing Complex Software Development Tasks

Run a structured review over the changes in scope. Two modes:

- **Reviewing work you just completed, or told to fix** - review, then apply and verify the fixes.
- **Asked only to review** - stop at clear, actionable feedback and let the user decide what to act on. Don't start editing.

## Workflow

1. Spawn parallel sub-agents to critically review the changes, splitting the work by review axis (below) or by area of the codebase.
2. Compile their findings into a concise numbered list, each tagged critical/medium/low.
3. Verify every finding against the actual code before reporting or acting on it. Sub-agents report false positives, and acting on a phantom issue makes the code worse.

## Applying Fixes

Fix mode only. If you were asked only to review, stop at step 3 and report your findings.

1. Fix the confirmed issues.
2. Re-run the project's lint/test/build pipeline.
3. Read each fix to confirm it resolves its finding and didn't break the original task or introduce a new problem. A green pipeline proves mechanical correctness only.
4. Stop after this single verification pass; don't recurse into a fresh full review.

If a finding is especially complex or keeps recurring, use the systematic-debugging skill to get to the root cause.

## Review Axes

Direct sub-agents to evaluate the changes across these dimensions. The questions below are illustrative, not a fixed checklist. Apply the ones that fit and raise the concerns that actually matter for this codebase's language, domain, and conventions:

- **Correctness** - Does it do what the task required? Are edge cases (null, empty, boundary) and error paths handled, not just the happy path? Do the tests actually exercise the new behaviour?
- **Readability** - Are names and control flow clear to someone who didn't write this? Could it be simpler or shorter? Is each abstraction earning its complexity?
- **Architecture** - Does it follow existing patterns and module boundaries, or introduce a new one without justification? Is there duplication that should be shared? A new dependency the existing stack already covers?
- **Security** - Is untrusted input validated at boundaries? Any secrets in code or logs? Any injection (SQL, shell, path), missing authorisation checks, or external data used unsafely in logic or output?
- **Performance** - What's costly for this kind of code: algorithmic complexity, repeated work or allocations in hot paths, N+1 queries, unbounded fetches, missing pagination, synchronous behaviour or blocking work on the critical path?

Create checklists or TODOs for yourself (or the sub-agents) to ensure your coverage is thorough.

## Calibration

- The bar is "does this improve the codebase," not "is this how I would have written it." Don't invent problems just to have something to report, and don't rewrite working code over style preference.
- Don't soften or rubber-stamp real problems either. State them plainly and quantify the impact where you can ("this N+1 adds ~50ms per row" beats "this might be slow").
- Passing tests are necessary, not sufficient. They don't catch architecture, security, or readability problems, so review those regardless.

## Dead Code

Refactors leave orphans. After changing code, list anything now unused (replaced functions, components, constants) and ask before removing it, rather than deleting silently or leaving it to rot.

## Sub-Agent Guidelines

Where appropriate use sub-agents to parallelise your work and reduce context bloat in the main conversation.

- Tell sub-agents to keep output concise, actionable, and focused on your changes, not minor style nitpicks.
- Give them only the context they can't infer from the code itself.
- Scope each agent to clear boundaries so they don't overlap or review unrelated code.

## Reporting

The fixes, or the findings are the deliverable, so open with the (concise) outcome, not preamble or a description of your process.

- **Review-only:** the findings ordered by severity, each as `file:line`, the problem, and a concrete fix. If nothing substantive turned up, say so in a line.
- **Fix mode:** what you fixed, then what you didn't and why. List deferred or out-of-scope findings one line each so the user can decide, and note the pipeline result.

State real issues plainly and drop the hedging ("might want to consider", "could potentially"); tag anything optional as low and move on. Batch style nitpicks into a single note rather than scattering them. Don't close with a summary that restates the list. A short report flagging the few things that count beats a long one padded with the obvious.
