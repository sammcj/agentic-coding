# Testing skill triggering

A skill activates purely on its `description` - the agent reads descriptions and reasons about which to load. Trigger evals measure that decision: a set of realistic queries, each labelled with whether the skill should activate, run against the description so you can see it fire on the right requests and stay quiet on the rest. Use them to tune a description, especially when over-triggering or under-triggering is a risk.

## The eval set

An array of cases at `evals/<set>.json` beside the skill:

```json
[
  {"query": "a realistic request the skill should handle", "should_trigger": true},
  {"query": "a near-miss that shares keywords but needs something else", "should_trigger": false}
]
```

Write queries that are self-contained and substantive. Put any sample content (a sensitive snippet, a data row) inline - a query that only references an artifact ("here is the PDF") makes the agent go looking for it rather than do the work, so it never reaches the point of consulting a skill. The most valuable negatives are near-misses that a naive keyword match would trip on. Trivial one-step queries trigger nothing regardless of description, so they make poor tests.

## Running the eval

Use the bundled `scripts/eval_triggering.py` (resolve it from the skill-creator-primer skill's `scripts/` directory). Run it outside any command sandbox (claude/node need network):

```bash
<skill-creator-primer>/scripts/eval_triggering.py \
  --skill-path <skill-dir> --eval-set <skill-dir>/evals/trigger.json
```

It installs the real skill into a throwaway project and reports, per query, how often the skill activated within the first N tool calls (default 3; `--within N`). `--runs`, `--workers`, `--timeout` and `--model` all have sensible defaults. It streams each run and kills it as soon as the decision is made, so the model never plays the task out to completion, and every run is confined to a temp dir that is deleted afterwards.

### In the ai-toolkit repo

The script lives under this skill, and skills sit in `library/skills/`. From the repo root, run it against any skill that carries an eval set:

```bash
library/skills/skill-creator-primer/scripts/eval_triggering.py \
  --skill-path library/skills/netwealth-org \
  --eval-set library/skills/netwealth-org/evals/trigger.json
```

These evals are a tuning aid, not part of `uv run toolkit-test`: the build does not run or gate on them (they each spawn `claude -p`, which is time consuming and non-deterministic). The runner's own unit tests, which mock out `claude`, do run under `toolkit-test`.

Counting activation "within the first N tool calls" rather than "as the very first action" matters for skills that do real work: on a tool-using task (read a file, query a database) the skill legitimately fires after an opening Read or Bash, and what you care about is that it activates early, not strictly first.

### Why it wraps claude with --setting-sources project

`claude -p` (which the runner drives) inherits the caller's user-global config. If that config registers SessionStart hooks, those hooks are injected into every child process and steer it away from consulting skills - so every query reads as a non-trigger and the eval returns a flat zero, masking the skill's real behaviour. `--setting-sources project` drops those hooks while keeping keychain auth. Avoid `--bare` and a redirected `CLAUDE_CONFIG_DIR`: both disable keychain reads and force auth to `ANTHROPIC_API_KEY`, so an OAuth/subscription login would land the subprocess logged out.

If real positives never fire even so, the description is likely under-triggering - usually because it reads as passive reference ("facts you may want") rather than naming the action or check to perform.

### Auto-optimising the description

The upstream skill-creator bundles `run_loop.py` to rewrite and re-score a description across iterations. It runs against the skill-creator harness, which tests a thin command proxy and judges only the first action, so it under-reports triggering for tool-using skills - treat its scores with that caveat and confirm with `eval_triggering.py`.
