# rewrite-slop Rules

## Check the upstream sources when updating this skill

When asked to update or improve this skill, check whichever of these are available before deciding what to change. Each moves on its own schedule. None is required: skip any that is missing rather than trying to obtain it.

- If the `skill-creator-primer` skill is installed, its `scripts/validate_skill.py` holds detection this skill borrows from (`_FILLER_RULES`, blob and structure analysis, grouped findings). Reconcile any rule that exists in both.
- `github.com/louisabraham/load-bearing`, the ranking behind Tier 2. Re-fits daily.
- `github.com/berenslab/llm-excess-vocab`, the excess ratios behind Tier 3.

`references/refresh-vocabulary.md` carries the procedure and the traps. Follow it rather than re-deriving from scratch.

## Update CHANGELOG.md after changes

After making any change to this skill (SKILL.md, resources, scripts): You MUST update `CHANGELOG.md`:

- Add a concise TLDR of the change(s) as bullet point(s) under today's date heading (`## YYYY-MM-DD`, newest first), creating the heading if it doesn't exist. No versioning is required.
- Squash changes within the same day (do not add changes to changes).
