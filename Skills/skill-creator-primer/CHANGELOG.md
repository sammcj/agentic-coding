# Changelog

<!-- AI agents: After completing changes to this project, add a terse TLDR style bullet describing the change under today's date heading (## YYYY-MM-DD), newest date first. Create the date heading if it does not exist. No versioning is required. -->

## 2026-08-12

Loop-engineering pass - sharpened fuzzy loop exits into checkable criteria:

- Description checklist: pass/fail verdict per item, exit on all-pass, re-check the set after any edit (replaces "until it follows best practices").
- Trigger evals (`references/trigger-evals.md`): stated the script's pass bar (fires in at least half of runs) and a stop condition - full-run all-pass, or report residual failures after two rounds.
- Self-Review gained step 12: re-run the validator if any step after 4 changed the skill, closing the gate for the edit path (step 11 covered new skills only).
- Task-tracking guidance (both spots + template step 1): each task phrased with its completion criterion.

Anti-verbosity defences: recent models (Opus/Sonnet 5) author skills as narrative prose and "be concise" instructions decay mid-session, so enforcement moved from prose into deterministic tooling and process. Designed via adversarial persona sub-agent reviews; anti-patterns drawn from real rejected PRs.

- `validate_skill.py` gates the token budget by exit code: Poor fails, OK warns, judged on worst-case load (SKILL.md + largest single reference - what one branch firing costs) rather than corpus total, so progressive disclosure isn't penalised; the OK/Poor message names the driving file and its cure.
- Report output is sectioned to route the reading agent's attention: FACTS (over-long description, over-budget load, SKILL.md blobs - always-loaded, fix) / SIGNALS (reference blobs, code fences over 10 lines - branch-loaded, judge earned detail vs waffle; 3+ reference blobs warn) / INFO (prose %, blob definition).
- Blob detection: a blob is any text unit of 100+ words, form-invariant across paragraphs, list items, quotes and table rows so reshaping can't dodge it; listed with file:line, word count and opening quote. Threshold calibrated on real skills (80-95w flagged mostly dense-but-earned units). Stdlib-only `--report-only` mode.
- Reference discovery gained a bare-basename fallback ("see api-design.md" with references/ implied) - swift-development had 9.8k tokens invisible to the old counter.
- New PostToolUse hook in primer frontmatter (`hook_report_skill_tokens.py`): re-injects the report after any edit to a skill's Markdown (SKILL.md or a reference under a directory holding one; housekeeping files excluded) - the mechanical replacement for a human nudging "cut the word count". Hook command uses an explicit `$HOME` path; `${CLAUDE_SKILL_DIR}` expands empty in current Claude Code.
- Failure Modes gained "Buried instructions" (logic in paragraphs or oversized list items, incl. frontmatter/schema description fields; cure: new "Structure over prose" tip + example pair) and "Fossilised diff" (body narrating its own history: ticket IDs, amendment notes, superseded mechanisms; cure: state current behaviour, provenance lives here and in git). Duplication widened to restating a cited source; leading-words rule warns against coined vocabulary. "Structure over prose" allows telegraphic fragments for gotchas, checklists and fact lists (not where they'd blur a concept, sequence, or steering nuance) - from a caveman-style review. All inline - no anti-patterns reference, so review naming never depends on a routing decision.
- Self-Review step 4: conditional fresh-context compression pass at OK/Poor rating (~75%/~60% word target; converts prose to steps, deletes provenance and justification riders; verified against an extracted rule checklist); token delta stated in change summaries. Prefers a `compression-editor` agent when the environment defines one (created today at `~/.claude/agents/compression-editor.md`, outside this repo).
- New `assets/skill-template.md`: creation drafts inside its structure, denying the narrative prior a blank page.
- The primer's own prose compressed and restructured (compression-editor review rounds plus a formatting pass): dense paragraphs and the Failure Modes table converted to bullets, decorative bold stripped (kept run-in tip names, critical directives, must-read pointers), checklist item 3 tightened to the load-decision rule, upstream-validators deduplicated, "Claude" -> "the agent" per the portability rule. Kept repetition that does steering work. Declined relocating the frontmatter extensions to a reference - nearly every creation flow needs it inline. Ends at worst-case load 9354 [OK], zero blobs, 31% paragraph prose.

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
