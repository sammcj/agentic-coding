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

Run the bundled `<skill-creator-primer>/scripts/eval_triggering.py` outside any command sandbox (claude and node need network); `--help` covers the arguments and pass bar:

```bash
<skill-creator-primer>/scripts/eval_triggering.py \
  --skill-path <skill-dir> --eval-set <skill-dir>/evals/trigger.json
```

While tuning:

- Done when a full run passes every query; after two rounds short of that, stop and report the residual failures.
- Re-run only the affected queries with `--only`, then confirm with a full run at the end.
- If real positives never fire, the description is likely under-triggering - usually because it reads as passive reference ("facts you may want") rather than naming the action or check to perform.

### Auto-optimising the description

The upstream skill-creator bundles `run_loop.py` to rewrite and re-score a description across iterations. It runs against the skill-creator harness, which tests a thin command proxy and judges only the first action, so it under-reports triggering for tool-using skills - treat its scores with that caveat and confirm with `eval_triggering.py`.
