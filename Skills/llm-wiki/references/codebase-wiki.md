# Domain recipe: documenting a codebase

An optional set of conventions for when the wiki's subject is a codebase rather than external reading. The core skill is unchanged - `raw/` and `wiki/`, ingest, supersession, lint, audit, all as in SKILL.md. This adds topic and naming conventions that fit source code, and a rule for where the wiki ends and the repo's own docs begin.

Use it when the user points the wiki at a repository. Ignore it otherwise; the skill is domain-agnostic by default.

## What goes where: wiki vs the repo's own docs

The repo's README and inline docs already cover how to set up and run the code. The wiki covers what those leave out: why the code is shaped this way, how the pieces fit, and the decisions behind them. Do not copy setup steps or API signatures the code already documents; link to them. An article earns its place by explaining context that is not reconstructable from a glance at the code.

## Topics and naming

Use these topic directories under `wiki/`, and prefix article slugs so the kind is visible in a link:

| Topic | Slug prefix | Holds |
|-------|-------------|-------|
| `modules` | `mod-` | What a module or package does, its responsibilities, and how it relates to others. |
| `apis` | `api-` | Public interfaces, contracts, and how callers are meant to use them. |
| `decisions` | `dec-` | Why a choice was made: the options, the trade-off, the constraint. The ADR role. |
| `flows` | `flow-` | How a request, job, or data path moves through the system end to end. |

These are a starting set, not a straitjacket; add a topic when the code genuinely needs one. The one-level-of-subdirectories rule still holds.

## Sources for a codebase wiki

`raw/` still holds the immutable source material. For a codebase that means the durable artefacts you compiled from, not the live code:
- README, ADRs, design docs, RFCs, CONTRIBUTING.
- CI config and manifests (what the build and release actually do).
- Captured output that explains behaviour: a profiling run, a schema dump, an incident write-up.

Compile in dependency order so early articles ground later ones: README and design docs first, then ADRs, then CI and manifests, then the entry points and core modules.

## Reconstructed decisions

Often the only record of why something was done is the code and the git history. When you infer a decision rather than read it from a doc, write it as a `decisions` article and say so: mark it as reconstructed, cite the commits or files it was inferred from (in the Raw line or inline), and keep the certainty honest. "Inferred from commit abc123; no written rationale found" is the claim, not "the team decided". This is the epistemic-status discipline of `references/high-fidelity-ingest.md` applied to code archaeology.

## Drift

Code moves, and an article describing a module that has since been rewritten is stale knowledge. The supersession flow handles it: when a later source (a new ADR, a refactor's commit) replaces the old account, mark the old article `status: stale`, point `superseded_by` at the replacement, and keep it - it still explains why the previous structure existed. Audit (`references/audit.md`) is the tool for checking whether an article still matches the code and docs it cites.
