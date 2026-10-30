# openspec-bootstrap

A Claude Code skill that sets up [OpenSpec](https://github.com/Fission-AI/OpenSpec) in a repo so agents write short, outcome-level change artifacts instead of implementation plans that go stale.

## Use

In the target repo, run `/openspec-bootstrap` or ask Claude to "set up OpenSpec". The skill:

1. Runs `openspec init` if needed
2. Reads the repo's docs to learn what the project is and where its decisions live
3. Installs the `lean` schema to `openspec/schemas/lean/`
4. Writes `openspec/config.yaml` from the template, keeping only repo-specific rules
5. Asks you about anything it couldn't fill in

It also covers later edits to a repo's `openspec/config.yaml` or schema.

## What's in it

- `SKILL.md` - workflow and gotchas the agent follows
- `assets/config.yaml` - config template: project context, artifact rules, apply and archive guidance
- `assets/schemas/lean/` - the schema and its templates

## The `lean` schema

A fork of OpenSpec's `spec-driven` with the same proposal → specs → design → tasks flow. The differences:

- Each fact lives in one artifact. Specs hold behaviour, design holds decisions and contracts, tasks hold verification.
- Design has a Contracts section for exact names and formats of anything crossing a boundary. Other artifacts refer to it.
- Word budgets: about 300 for the proposal, 500 for the design and 10 tasks.
- Tasks name the requirement they prove, not test cases.
- Tests and docs land with the task group that needs them, not in a final group.

## Upgrading OpenSpec

1. `brew upgrade openspec`
2. Run `openspec update` in each repo that uses it
3. Compare `lean` with a fresh `openspec schema fork spec-driven` using `git diff --no-index --word-diff`, and carry over upstream fixes
4. Update the fork version noted in `SKILL.md`
