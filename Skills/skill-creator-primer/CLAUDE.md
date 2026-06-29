# skill-creator-primer Rules

- Content in this skill should be concise / terse and direct in nature.

## Use of references within this primer skill

- With this skill creator primer skill, it's actually somewhat expected that it's own SKILL.md may be a bit larger than other skills, as we want to ensure as much of the information that is almost always certainly needed is always available in context so the agent doesn't have to make decisions about what references to read, and so it places value on the content of this skills instruction over those of the ones it's reviewing.
- Any pointers to ./references/*.md must have clear instructions as to when the consuming agent MUST read them (e.g. the scenario when they apply).
- You do NOT need to add items that were changes to other items within the same date (e.g. if you add "added skill description ..." you don't need to also add "improved skill scription ..." if you did so on the same date)

## Update CHANGELOG.md after changes

After making any change to this skill (SKILL.md, references, scripts, evals etc.): You MUST update `CHANGELOG.md`:
- Add a concise TLDR of the change(s) in a bullet point(s) under today's date heading (`## YYYY-MM-DD`, newest first), creating the heading if it doesn't exist. No versioning is required.
- Update the `version` metadata in `SKILL.md` to the current date (YYYY-MM-DD) to reflect the change.
