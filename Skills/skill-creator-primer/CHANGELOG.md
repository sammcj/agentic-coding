# Changelog

<!-- AI agents: After completing changes to this project, add a terse TLDR style bullet describing the change under today's date heading (## YYYY-MM-DD), newest date first. Create the date heading if it does not exist. No versioning is required. -->

## 2026-07-02

- Added a "Writing Scripts" bullet: prefer the standard library, and when a real third-party dep is needed, run with `uv` and declare it via PEP-723 inline metadata so the dependency travels with the script.
- Added a "Skills vs Custom Agents" section: skills for knowledge/workflows/tools loaded into the current context; custom agents for a persona with its own context (adversarial/fresh-perspective work); the two compose.
- Reformatted "Skills vs Custom Agents" and "Prefer one skill over many" from prose paragraphs into concise heading + bullets (no content change).

## 2026-06-30

- Reworked the `when_to_use` frontmatter bullet to discourage it (just appends to the description, shares the same char budget); dropped the `maxSkillDescriptionChars`/1,536-char detail.
- Pruned restatement and preamble from SKILL.md (no-op intro, duplicate phrasing, validator `--tiktoken` duplication, trimmed "Knowing is not doing"); fixed the "Check for Description Trigger Conflicts" cross-reference. No workflow or decision content removed.
- Sharpened the invocation-mode guidance with a TLDR decision rule: user-invoked (`disable-model-invocation: true`) keeps a rarely-needed skill's description out of every agent session (context efficiency) at the cost of user cognitive load; when unclear, present the user both options with pros/cons. Added a matching Self-Review step to decide invocation mode.
- Reframed the predictability section heading to "Predictable Process, Not Identical Output" and reworded the body so it scopes consistency to what each skill is for, rather than asserting a blanket goal.
- Added a Skill Writing Tip: when a skill encodes a multi-step workflow, make its first step instruct the agent to create a task per step, to keep it on task and improve completeness.
- Self-review fixes: consistent "leg work" term in steering.md, corrected the Sprawl-row cross-reference, and scaled the "Track Each Step as a Task" ceremony to change size (was over-prescriptive for trivial edits).

- Added concepts from Matt Pocock's "Building Great Agent Skills": predictability as the organising principle (inline), the branch test for inline-vs-disclosed reference (inline), and a deletion-test/no-op bullet in the Self-Review Protocol.
- Added `references/steering.md` (leading words, completion criteria, premature completion) with clear "when to read" pointers in SKILL.md for it and `trigger-evals.md`.
- Added a "Track Each Step as a Task" directive so the agent creates a todo per step when creating, updating, or reviewing skills, guarding against premature completion.
- Added invocation-mode trade-off (context load vs cognitive load) to "How Skills Actually Work"; two description-checklist items (front-load the leading word, one trigger per branch); a co-location Skill Writing Tip; and a "Failure Modes" diagnostic table (premature completion, duplication, sediment, sprawl, no-op). Deduplicated so Failure Modes is the single source for the no-op definition; the deletion-test procedure lives in the Self-Review Protocol and references it.
- Added CHANGELOG.md and CLAUDE.md to track future changes to the skill.
