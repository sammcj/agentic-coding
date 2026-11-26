# Commands

- Re-check the template and every example after changing a script, the template or an example: `python3 scripts/verify_examples.py`
- Lint the scripts: `uvx ruff check --line-length 110 scripts && uvx ruff format --line-length 110 --check scripts && uvx ty check scripts`
- Validate the skill: `uv run /Users/samm/.claude/skills/skill-creator-primer/scripts/validate_skill.py .`
- Trigger evals, run outside the command sandbox: `/Users/samm/.claude/skills/skill-creator-primer/scripts/eval_triggering.py --skill-path . --eval-set evals/trigger.json`

# Conventions

- No Java tooling. Every bundled spec must pass under `tla` (tla-rs, installed with `cargo install tla-checker`).
- Add a checker behaviour to the SKILL.md gotchas only after seeing it in a run or reading it in the tla-rs docs.
