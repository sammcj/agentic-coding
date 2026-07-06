# Changelog

<!-- AI agents: After completing changes to this project, add a terse TLDR style bullet describing the change under today's date heading (## YYYY-MM-DD), newest date first. Create the date heading if it does not exist. No versioning is required. -->

## 2026-07-06

- Restructured SKILL.md layout (content unchanged): entry-point router up top, sections reordered into principles -> decide -> author -> verify clusters, Skill Writing Tips grouped by content/structure/steering, and the three validator fragments merged into one "Validating a Skill" section. Strays: title-cased "Prefer One Skill Over Many", fixed a doubled quote in the `allowed-tools` example.
- Added "Reviewing a Skill" (same criteria regardless of ownership; findings graded spec violation / primer violation / judgement call - only the first two block; fix by default, report when review-only) and Self-Review step 10: a fresh-context sub-agent (not a fork) reviews a newly created skill read-only.
- Description reworded, keeping the ANY-change catch-all - Sonnet trigger evals under-fired to 2/10 positives without it. A negative-trigger exclusion clause was trialled and dropped: the skill has never over-fired, so checklist item 9's precondition isn't met. Item 9 restored; item 4 and the conflict check reframed against co-active neighbours rather than "a library".
- Expanded `evals/trigger.json` with boundary probes (3 positives, 4 near-miss negatives). The new positives under-fire on the fixture-less harness (the target skill doesn't exist in the throwaway project) - weak signal, see `references/trigger-evals.md`.
- Scripts: `validate_skill.py` enforces the 30-55 word description aim (hard error over 65) and excludes housekeeping .md files (README, CHANGELOG, etc.) from the token report; `eval_triggering.py` gained a repeatable `--only SUBSTRING` filter; trigger evals now run against a mid-range model (e.g. Claude Sonnet) - the strongest masks under-triggering, the weakest misroutes atypically.
- Token Budget Guidance: when the branch test keeps nearly everything inline, a larger SKILL.md is the correct trade, judged by the deletion test (this primer qualifies).
- Re-verified the upstream-allowlist caveat against current skills-ref and the cached plugin (zero drift); noted `quick_validate.py` gates `package_skill.py`, so the error surfaces at packaging time.

## 2026-07-04

- Cut content duplicated from the co-loaded skill-creator: the pushy under-triggering example, the three-level progressive-disclosure list (kept the primer's branch-test delta), and the "trivial one-step queries" note in `references/trigger-evals.md`.
- Repointed the `disable-model-invocation` frontmatter bullet at "Invocation mode is a trade-off" (and Self-Review step 5) rather than "only if the user requests it", removing the contradiction.
- Added description-checklist item 9: when a skill over-fires, add a negative-trigger exclusion clause ("Do NOT use for X, use Y instead") naming the neighbouring intent.
- Removed wrong-repo content: the "In the ai-toolkit repo" section in `references/trigger-evals.md` (kept the general "within first N tool calls" note), the "Netwealth" reference in `scripts/validate_skill.py`, and "Skills in this toolkit" in SKILL.md.

## 2026-07-03

- Added "Routing when branches multiply": skills with many references should route loads via a one-level decision tree of need-phrased qualifiers -> reference pointers; trees carry which-one decisions only, never process. Informed by dmmulroy/cloudflare-skill and superpowers' writing-skills scoping rules.
- Added a Bundled File Layout bullet: many sibling reference domains should share a uniform file set so the next-level load needs no index.
- Strengthened description checklist item 3: a description that summarises the workflow invites the agent to act on the summary and skip the skill's branches.

## 2026-07-02

- Corrected the frontmatter reference against current Claude Code docs: added `paths`, `hooks` and `shell` fields, added the `xhigh` effort option, fixed `agent` semantics (subagent type used under `context: fork`), and noted `paths` as the sole non-reasoning gate on skill selection. `validate_skill.py`'s Claude Code field allowlist updated to match.
- Fixed the skill-creator install note: the marketplace add and plugin install pointed at different marketplaces; now installs `skill-creator@claude-plugins-official` with the matching `anthropics/claude-plugins-official` marketplace add as the fallback.
- Added a "Build with sub-agents in mind" writing tip: skills should mark fan-out and hand-off points (what each sub-agent needs, what it returns) rather than prescribing orchestration.
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
