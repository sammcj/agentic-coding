---
name: code-review-recent-changes
description: Review recent changes since a fixed point (commit, branch, tag, or merge-base) along three independent axes - Standards, Spec, and Maintainability - run as parallel sub-agents that read beyond the diff, then aggregated into severity-ordered findings with an explicit verdict. Use when the user wants to review a branch, a PR, or recent committed changes.
disable-model-invocation: true
metadata:
  source: Two-axis base adapted from https://github.com/mattpocock/skills; Maintainability axis distilled from the thermo-nuclear-code-quality-review skill (cursor-team-kit), with refinements from Matt Pocock's analysis of it.
---

# Code Review: Recent Changes

Review the diff between `HEAD` and a fixed point the user supplies, along three independent axes:

- **Standards** - does the code conform to this repo's documented conventions?
- **Spec** - does the code faithfully implement the originating issue / PRD / spec?
- **Maintainability** - is the change structurally healthy, or did it leave the codebase harder to change?

Each axis runs as its own **parallel sub-agent** so they don't pollute each other's context, then this skill aggregates their findings. Keep them separate: a change can pass one axis and fail another - code that follows every convention but implements the wrong thing (Standards pass, Spec fail), or does exactly what the issue asked while leaving the codebase messier (Spec pass, Maintainability fail). Separate reporting stops one axis from masking another.

## Review stance

Two ideas shape how the sub-agents work, so build them into the briefs:

- **Read outward from the diff.** An agent handed a diff tends to treat it as the edge of the world. Tell each sub-agent to look past it: for a changed symbol, read its surrounding function/file and the modules that call it or that it calls. A hunk that looks fine in isolation can duplicate an existing helper, contradict a sibling module's pattern, or leave a half-finished migration two files over.
- **Be ambitious on Maintainability; precise on Standards and Spec.** Standards and Spec are close to binary - a documented rule is violated or it isn't, a requirement is met or it isn't - so favour precision and don't manufacture findings. Maintainability is where the valuable, easy-to-miss findings live, so favour recall: propose a restructuring even when you're not fully sure, because a wrong suggestion costs the reader one quick "no", while a worthwhile one you never raise is one nobody gets to consider. To keep the wrong ones cheap to dismiss, every Maintainability finding carries a confidence label and concrete evidence.

## Process

### 1. Pin the fixed point

Whatever the user named is the fixed point - a commit SHA, branch name, tag, `main`, `HEAD~5`. Pass it through; don't be opinionated. If they didn't give one, ask: "Review against what - a branch, a commit, or `main`?" Don't proceed without it.

Capture three things once and reuse them across all sub-agents:

- Diff: `git diff <fixed-point>...HEAD` (three-dot, so the comparison is against the merge-base).
- Commits: `git log <fixed-point>..HEAD --oneline`.
- Size deltas: `git diff <fixed-point>...HEAD --stat` - the Maintainability axis uses this to spot files crossing a size boundary.

### 2. Check for a spec

Scan the captured commit list and the user's request for a spec signal: an issue reference (`#123`, `Closes #45`, `!67`), a spec/PRD path the user passed, or an issue/PRD the user named. This is a cheap check - the commit list is already in context.

- A signal is present → read `references/spec-review.md` and follow it to locate the spec and build the Spec sub-agent brief.
- No signal → skip the Spec axis. Don't open the reference; note "no spec available" in the final report.

### 3. Identify the standards sources

Anything in the repo that documents how code should be written:

- `CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md`
- `CONTEXT.md` / `CONTEXT-MAP.md` (including per-directory ones); `docs/adr/` (architectural decisions are standards)
- `STYLE.md`, `STANDARDS.md`, `STYLEGUIDE.md` at the repo root or under `docs/`
- `.editorconfig`, `eslint.config.*`, `biome.json`, `prettier.config.*`, `tsconfig.json` - machine-enforced; note them but don't re-check what tooling already enforces.

Collect the list; the Standards sub-agent reads them.

### 4. Spawn the sub-agents in parallel

Send a single message with the `Agent` calls, all using the `general-purpose` subagent: Standards and Maintainability always, plus Spec if step 2 found a signal (use the brief from `references/spec-review.md`).

**Standards sub-agent** - include the diff command, commit list, and the standards-source file list from step 3. Brief:

> Read the standards docs, then the diff. Read beyond the diff where context matters - e.g. to tell whether a new helper duplicates a canonical one or breaks a sibling module's pattern. Report, per file/hunk, every place the diff violates a documented standard. Cite the standard (file + the rule). Separate hard violations from judgement calls. Skip anything tooling already enforces. Order findings worst-first. Under 400 words.

**Maintainability sub-agent** - include the diff command, commit list, and the `--stat` output. Brief:

> Audit the change for structural health and future changeability. Read beyond the diff: for any changed symbol, read its surrounding file and the modules it calls or is called by. Be ambitious - hunt for a "code judo" move that preserves behaviour while making the change dramatically simpler, deleting whole branches, helpers, or layers rather than rearranging them.
>
> Report two groups:
>
> (a) **Structure** (highest value). Concrete triggers: a file crossing the repo's documented size limit (or ~1000 lines / 5k tokens if none is documented) where the new code could be split out; a new conditional or special case bolted onto an unrelated flow that belongs behind its own abstraction; logic duplicated instead of reusing an existing canonical helper; a thin wrapper or pass-through that adds indirection without clarity; feature-specific logic leaking into a shared module; an optional prop the diff adds even though every call site supplies it (agents reach for optionality to shrink a change's blast radius), or an `any`/`unknown`/cast that hides an invariant that is actually fixed; a half-finished decomposition or migration.
>
> (b) **Tests and seams.** Did the change make the code easier or harder to test and change? Is new behaviour covered? Did it add or remove a seam - a point where behaviour can be substituted or observed? Swallowed errors and silent fallbacks belong here.
>
> For each finding: state the problem, cite file + line, and give the specific restructuring you would make. Hold that restructuring to a bar - it must remove moving pieces, not relocate the same complexity or offer a tidier version of the same messy idea; if your fix doesn't make the code simpler on net, drop the finding. Label confidence (`high` or `worth-checking`). Order findings worst-first, structural regressions before legibility nits. Prefer a few high-conviction findings over a long list of cosmetic notes. Under 500 words.

### 5. Aggregate

Present the reports under `## Standards`, `## Spec`, and `## Maintainability`, verbatim or lightly cleaned. If the Spec axis was skipped, keep its heading and write "no spec available". Don't merge or rerank across axes - the separation is the point.

Close with:

- A one-line tally per axis (number of findings, worst severity).
- An explicit **verdict**: `approve`, `approve with nits`, or `request changes`. Reserve `request changes` for blocker-class findings: a hard standard violation, a missing or incorrect spec requirement, or a high-confidence structural regression. A `worth-checking` Maintainability finding is advice, not a blocker - on its own it shouldn't drop the verdict below `approve with nits`. Name the single worst issue. Don't approve on correct behaviour alone - a change can work and still leave the codebase meaningfully messier.

## Gotchas

- **Stale base.** Reviewing against `main` while local `main` is behind `origin/main` computes the wrong merge-base, so the diff silently includes or drops the wrong commits. Fetch first, or pin the fixed point to `origin/main`.
- **Inline instead of parallel.** Running the axis briefs in this conversation rather than spawning them as real sub-agents collapses the context isolation that keeps the axes from polluting each other. Spawn them as separate `Agent` calls.
