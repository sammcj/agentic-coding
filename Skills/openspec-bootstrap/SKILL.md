---
name: openspec-bootstrap
description: Use when setting up OpenSpec in a repo for the first time, or editing a repo's `openspec/config.yaml`
metadata:
  version: 2026-10-22
---

The config steers every artifact agents write later. Its main job is keeping a change's artifacts at the outcome level. Artifacts that prescribe implementation detail go stale as soon as the implementation drifts, and agents then spend effort resyncing them. The template's `context` states that principle, with contracts as the one exception.

## Workflow

1. Create a task per step below, phrased with its completion criterion, then work them to completion.
2. If `openspec/` is missing, run `openspec init --tools <the agents this repo uses>`. Done when `openspec/config.yaml` exists.
3. Read the README, CLAUDE.md/AGENTS.md, the build entrypoint (Makefile or similar) and any planning or decision docs. Done when you can name what the project is, its hard constraints and where decisions live.
4. Copy `assets/config.yaml` from this skill's directory to the project as `openspec/config.yaml`, then fill it in.
  - Keep it short. Include only what agents must take into account when working with OpenSpec in this project.
  - Add a repo-specific rule only when the repo's docs show it needs one.
  - If a config with real content already exists, merge into it instead: keep its repo-specific facts and replace rules that prescribe internal code.
  - Delete any placeholder line you can't fill and note it for step 7.
  - Done when `rg -n '<[^>]+>' openspec/config.yaml` finds nothing.
5. Check every rule you wrote against the template's `context`. Remove any rule that tells future agents to prescribe implementation detail.
6. Confirm the YAML parses: `python3 -c 'import yaml,sys; yaml.safe_load(open(sys.argv[1]))' openspec/config.yaml`.
7. Report the deleted placeholders to the user as questions rather than guessing values.

## Gotchas

- Rules are appended to the schema's built-in artifact instructions (`schemas/<schema>/schema.yaml` in the installed OpenSpec package). Those already cover spec scope, per-task verification and per-group tests. Write rules only for what the repo needs beyond them.
- `context` should point to files (CLAUDE.md, decision docs) rather than copying their commands or facts, which then drift.
- `operations` supports only `apply` and `archive`. OpenSpec only warns about other keys at instruction time, so a YAML parse misses them.
- Explore reads only `context` and `rules`. Behaviour wanted outside a single artifact or apply/archive goes in `context`.
- Archive blocks on unchecked task boxes, so the template's Human checks rule uses plain bullets. Keep that wording when merging into an existing config.
- Sub-agents never read the config. Rules they must follow go in `apply` guidance as something the main agent puts in each brief.
- Changes already in flight keep their current artifacts. The new rules apply to new changes.
