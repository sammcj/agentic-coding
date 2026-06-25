---
description: Critically self-review your changes and fix what you find, delegating when the change is large
argument-hint: "[optional focus or extra context]"
---

Critically review your recent changes and fix any issues you find. Choose one of the two paths below, based on the size of the change. When in doubt, delegate - the cost is low and the unbiased read is the point.

## Option A: Review it yourself (small or simple changes)

For a single file, or one focused fix or feature: Re-read what you changed with a sceptical eye - correctness, completeness, regressions, over-engineering, unwarranted verbosity - and fix what you find directly.

## Option B: Delegate to the reviewer (larger changes)

For changes spanning multiple files, features, or fixes: Delegate to the `critical-reviewer` subagent(s) for a fresh, unbiased read, then act on what they report.

- A fresh reviewer catches what you've talked yourself into, and keeps the review reasoning out of your context.
- The reviewer is read-only and returns prioritised findings (each with a severity and a `file:line` location); you triage by severity and apply the fixes.

When you delegate:

- **Brief it well.** The agent operates outside of this conversation's context. Give it: the list of changed files (names only, e.g. `git diff --name-only`), the task you were originally asked to do and what was in / out of scope, and anything intentional that looks wrong but isn't.
- **Parallelise only on independent slices.** Spawn one reviewer per group of changes that don't interact (by subsystem, layer, or requirement), and give each an explicit boundary - the files or area it owns - so they don't overlap. When slices share an interface or contract, brief at least one reviewer on both sides, or use a single reviewer - a fresh reviewer that sees only one side can't catch the interaction. Don't split for its own sake.
- **Stay fresh by default.** A fresh reviewer gives the unbiased read that makes self-review worth doing. Fork only if the review genuinely needs this conversation's nuance; never fork it for the adversarial read, since a fork inherits this agent's bias and defeats the point.
- **Fix what's real.** Apply the fixes for genuine findings, then verify (build, tests, lint). Push back on findings that are wrong rather than changing correct code to satisfy them.
- **Write the brief in terse notes.** Keywords and bullets, not full prose; the reviewer is a capable model, not an audience.

---

`$ARGUMENTS`
