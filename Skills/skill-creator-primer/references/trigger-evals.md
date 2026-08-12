# Testing skill triggering

Trigger evals measure the activation decision: realistic queries, each labelled with whether the skill should activate, run against the live description. Use them to tune a description when over- or under-triggering is a risk.

## The eval set

An array of cases at `evals/<set>.json` beside the skill:

```json
[
  {"query": "a realistic request the skill should handle", "should_trigger": true},
  {"query": "a near-miss that shares keywords but needs something else", "should_trigger": false}
]
```

Write queries that are self-contained and substantive:

- Put any sample content (a sensitive snippet, a data row) inline - a query that only references an artifact ("here is the PDF") makes the agent go looking for it rather than do the work, so it never reaches the point of consulting a skill.
- The most valuable negatives are near-misses that a naive keyword match would trip on.

## Running the eval

Use the bundled `scripts/eval_triggering.py` (resolve it from the skill-creator-primer skill's `scripts/` directory). Run it outside any command sandbox (claude/node need network):

```bash
<skill-creator-primer>/scripts/eval_triggering.py \
  --skill-path <skill-dir> --eval-set <skill-dir>/evals/trigger.json
```

It installs the real skill into a throwaway project and reports, per query, how often the skill activated within the first N tool calls (default 3; `--within N`). `--runs`, `--workers` and `--timeout` have sensible defaults.

While tuning:

- Pass bar (the script's): a should-trigger query passes firing in at least half its runs; a should-not, fewer. Done when a full run passes every query; after two rounds short of that, stop and report the residual failures.
- Re-run only the affected queries with `--only SUBSTRING` (repeatable, case-insensitive substring match; bump `--runs` if you need a stabler read), then confirm with a full run at the end.
- Set `--model` to a mid-range model (e.g. Claude Sonnet): the strongest reasons its way to the right skill despite a weak description (masking under-triggering), the weakest misroutes in ways typical sessions won't, and a description that routes cleanly mid-range carries upward.
- Runs stream, are killed once the decision is made (the task never plays out), and are confined to a temp dir deleted afterwards.

Two calibration points:

- "Within the first N tool calls" rather than "as the very first action": on a tool-using task (read a file, query a database) the skill legitimately fires after an opening Read or Bash - what matters is that it activates early, not strictly first.
- These evals are a tuning aid, not a build gate: each query spawns `claude -p`, which is time consuming and non-deterministic, so run them by hand when tuning a description.

### Why it wraps claude with --setting-sources project

`claude -p` (which the runner drives) inherits the caller's user-global config:

- User-global SessionStart hooks are injected into every child process and steer it away from consulting skills - every query reads as a non-trigger and the eval returns a flat zero, masking the skill's real behaviour. `--setting-sources project` drops those hooks while keeping keychain auth.
- Avoid `--bare` and a redirected `CLAUDE_CONFIG_DIR`: both disable keychain reads and force auth to `ANTHROPIC_API_KEY`, so an OAuth/subscription login would land the subprocess logged out.

If real positives never fire even so, the description is likely under-triggering - usually because it reads as passive reference ("facts you may want") rather than naming the action or check to perform.

### Auto-optimising the description

The upstream skill-creator bundles `run_loop.py` to rewrite and re-score a description across iterations. It runs against the skill-creator harness, which tests a thin command proxy and judges only the first action, so it under-reports triggering for tool-using skills - treat its scores with that caveat and confirm with `eval_triggering.py`.
