---
name: code-review-recent-changes
description: Review recent changes since a fixed point (commit, branch, tag, or merge-base) across three independent axes - Standards, Spec, and Maintainability - producing severity-ordered findings with an explicit verdict. Use when the user wants to review a branch, a PR, or recent committed changes.
disable-model-invocation: true
metadata:
  source: Two-axis base adapted from https://github.com/mattpocock/skills; Maintainability axis distilled from the thermo-nuclear-code-quality-review skill (cursor-team-kit), with refinements from Matt Pocock's analysis of it. Standards smell baseline adapted from upstream's Fowler (Refactoring ch.3) baseline, with the structural smells folded into the local Maintainability axis.
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

Before going further, confirm the fixed point resolves (`git rev-parse <fixed-point>`) and the diff is non-empty. A bad ref or empty diff should fail here, not inside the parallel sub-agents.

### 2. Check for a spec

Scan the captured commit list and the user's request for a spec signal: an issue reference (`#123`, `Closes #45`, `!67`), a spec/PRD path the user passed, or an issue/PRD the user named. This is a cheap check - the commit list is already in context.

- A signal is present -> read `references/spec-review.md` and follow it to locate the spec and build the Spec sub-agent brief.
- No signal -> skip the Spec axis. Don't open the reference; note "no spec available" in the final report.

### 3. Identify the standards sources

Anything in the repo that documents how code should be written:

- `CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md`
- `CONTEXT.md` / `CONTEXT-MAP.md` (including per-directory ones); `docs/adr/` (architectural decisions are standards)
- `STYLE.md`, `STANDARDS.md`, `STYLEGUIDE.md` at the repo root or under `docs/`
- `.editorconfig`, `eslint.config.*`, `biome.json`, `prettier.config.*`, `tsconfig.json` - machine-enforced; note them but don't re-check what tooling already enforces.

Collect the list; the Standards sub-agent reads them.

On top of whatever the repo documents, the Standards axis always carries a **smell baseline** - a fixed set of Fowler code smells (_Refactoring_, ch.3) that applies even when the repo documents nothing. Two rules bind it:

- **The repo overrides.** A documented repo standard always wins; where it endorses something the baseline would flag, suppress the smell.
- **Always a judgement call.** Each smell is a labelled judgement call ("possible Primitive Obsession"), never a hard violation - and, like any standard here, skip anything tooling already enforces.

Each smell reads _what it is_ -> _how to fix_; match it against the diff:

- **Mysterious Name** - a function, variable, or type whose name doesn't reveal what it does or holds. -> rename it; if no clear name comes, the design's murky.
- **Data Clumps** - the same few fields or params keep travelling together (a type wanting to be born). -> bundle them into one type, pass that.
- **Primitive Obsession** - a primitive or string standing in for a domain concept that deserves its own type. -> give the concept its own small type.
- **Repeated Switches** - the same `switch`/`if`-cascade on the same type recurs across the change. -> replace with polymorphism, or one map both sites share.
- **Message Chains** - long `a.b().c().d()` navigation the caller shouldn't depend on. -> hide the walk behind one method on the first object.

The structural smells from the full Fowler baseline (Duplicated Code, Feature Envy, Shotgun Surgery, Divergent Change, Speculative Generality, Middle Man, Refused Bequest) live on the Maintainability axis instead, so they aren't double-reported.

### 4. Spawn the sub-agents in parallel

Send a single message with the `Agent` calls, all using the `general-purpose` subagent: Standards and Maintainability always, plus Spec if step 2 found a signal (use the brief from `references/spec-review.md`).

**Standards sub-agent** - include the diff command, commit list, the standards-source file list from step 3, and the smell baseline's two binding rules and five smell definitions pasted in full (the sub-agent has no other access to them). Brief:

> Read the standards docs, then the diff. Read beyond the diff where context matters - e.g. to tell whether a new helper duplicates a canonical one or breaks a sibling module's pattern. Report, per file/hunk: (a) every place the diff violates a documented standard - cite the standard (file + the rule); these can be hard violations. (b) any baseline smell you spot - name it and quote the hunk; these are always judgement calls, and a documented repo standard overrides the baseline. Skip anything tooling already enforces. Order findings worst-first. Under 400 words.

**Maintainability sub-agent** - include the diff command, commit list, and the `--stat` output. Brief:

> Audit the change for structural health and future changeability. Read beyond the diff: for any changed symbol, read its surrounding file and the modules it calls or is called by. Be ambitious - hunt for a "code judo" move that preserves behaviour while making the change dramatically simpler, deleting whole branches, helpers, or layers rather than rearranging them.
>
> Report two groups:
>
> (a) **Structure** (highest value). Concrete triggers: a file crossing the repo's documented size limit (or ~1000 lines / 5k tokens if none is documented) where the new code could be split out; a new conditional or special case bolted onto an unrelated flow that belongs behind its own abstraction; logic duplicated instead of reusing an existing canonical helper; a thin wrapper or pass-through that adds indirection without clarity; feature-specific logic leaking into a shared module; a method that reaches into another object's data more than its own (Feature Envy) - move it onto the data it envies; one logical change forcing scattered edits across many files in the diff (Shotgun Surgery) - gather what changes together into one module; one file or module edited for several unrelated reasons (Divergent Change) - split so each changes for one reason; a subclass or implementer ignoring or overriding most of what it inherits (Refused Bequest) - drop the inheritance, use composition; an optional prop the diff adds even though every call site supplies it, or an `any`/`unknown`/cast that hides an invariant that is actually fixed, or more broadly any speculative generality - abstraction, parameters, or hooks added for needs the spec doesn't have (agents reach for optionality to shrink a change's blast radius) - delete or inline until a real need shows; a half-finished decomposition or migration.
>
> (b) **Tests and seams.** Did the change make the code easier or harder to test and change? Is new behaviour covered? Did it add or remove a seam - a point where behaviour can be substituted or observed? Swallowed errors and silent fallbacks belong here.
>
> For each finding: state the problem, cite file + line, and give the specific restructuring you would make. Hold that restructuring to a bar - it must remove moving pieces, not relocate the same complexity or offer a tidier version of the same messy idea; if your fix doesn't make the code simpler on net, drop the finding. Label confidence (`high` or `worth-checking`). Order findings worst-first, structural regressions before legibility nits. Prefer a few high-conviction findings over a long list of cosmetic notes. Under 500 words.

### 5. Aggregate

Present the reports under `## Standards`, `## Spec`, and `## Maintainability`, verbatim or lightly cleaned. If the Spec axis was skipped, keep its heading and write "no spec available". Don't merge or rerank across axes - the separation is the point.

One exception, and it's de-duplication not reranking: if the same underlying issue surfaces on both Standards (as a smell) and Maintainability (as a structural finding), keep the Maintainability finding - it carries the proposed restructuring and confidence label - and drop the Standards duplicate.

Close with:

- A one-line tally per axis (number of findings, worst severity).
- An explicit **verdict**: `approve`, `approve with nits`, or `request changes`. Reserve `request changes` for blocker-class findings: a hard standard violation, a missing or incorrect spec requirement, or a high-confidence structural regression. A `worth-checking` Maintainability finding is advice, not a blocker - on its own it shouldn't drop the verdict below `approve with nits`. Name the single worst issue. Don't approve on correct behaviour alone - a change can work and still leave the codebase meaningfully messier.

## Gotchas

- **Stale base.** Reviewing against `main` while local `main` is behind `origin/main` computes the wrong merge-base, so the diff silently includes or drops the wrong commits. Fetch first, or pin the fixed point to `origin/main`.
- **Inline instead of parallel.** Running the axis briefs in this conversation rather than spawning them as real sub-agents collapses the context isolation that keeps the axes from polluting each other. Spawn them as separate `Agent` calls.
