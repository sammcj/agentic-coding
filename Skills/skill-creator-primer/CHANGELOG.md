# Changelog

<!-- AI agents: After completing changes to this project, add a terse TLDR style bullet describing the change under today's date heading (## YYYY-MM-DD), newest date first. Create the date heading if it does not exist. No versioning is required. -->

## 2026-09-03

- Selecting content: don't pre-document a tool's failures; ship the run-and-read loop, and when pre-empting is tempting, give the tool a mode that reports what is still owed.
- Writing Scripts: usage lives in the script's `--help` and named arguments; the skill names the script and when to run it.
- Duplication now names text-to-script copies (a script's `--help`, docstring, header); Self-Review step 1 checks within SKILL.md, across references and against scripts, keeping one copy in the latest-loaded place.
- Writing Scripts: one-line header; a comment block restating what the name, `--help` and code say is duplication.
- `validate_skill.py` resolves its arguments, so `.` validates (test added); the "pass a real path" workaround line is gone from SKILL.md. Scripts with required arguments print full `--help` when run bare.
- `eval_triggering.py` args carry `help=` (pass bar, `--within` rationale, mid-range `--model` guidance); `trigger-evals.md` drops what `--help` and the script now say, including the `--setting-sources` subsection (now a comment beside the command it explains).
- Script headers cut to one line (validator, eval runner, hook, lister); the why moved beside the code it explains. `render_report.py` keeps only its cross-cutting contracts.
- SKILL.md fixes: the `shell` field line no longer contains a literal bang-backtick block (the loader was executing it); one accurate line on when spec checks and the PostToolUse token report run; stale `model` example replaced; all bundled-script paths use the `<skill-creator-primer>/scripts/` form. `html-report.md` loses its `--tiktoken` and "hand back the path" duplicates.
- New failure mode `Tool compensation`: prose standing in for a missing tool mode. Self-Review step 4 rules it out before the compression pass.

## 2026-09-02

- New `dense-run` SIGNAL: 3+ consecutive units of 90+ words, or 2+ list items of 70+. A heading, fence, table row or quote ends a run; a blank line or a blob does not, the run names its longest member, and a run made only of blobs is left to the blob list. `_structure` returns it as a fifth value. Flags 2% of installed skills.
- Findings carry a confidence. `POSSIBLE` maps a rule to its caveat (`americanism`, `dense-run`); the text report prints it after `?` on the rule's line, and the page marks the rule yellow, prefixes its rows `?`, ranks them last, counts them apart in the strip and splits the brief into "Findings, fix these" and "Possible, read before changing". Invisible characters are certain (red), everything else probable (orange); blobs move from the red tint to orange, bold keeps blue, code grey.
- New `invisible` FACT: no-break, figure and narrow spaces, zero-width space, word joiner, BOM (including at byte 0) and private-use glyphs, across frontmatter and fences. Marked on the page as the code point. U+200C/D left out for emoji.
- `americanism` widened on measurement: `-izable`/`-izability`/`-izational`, `parallel`, twenty more `-our` stems, the `-re` family, `pretense`, `counselor`, `enrollment`, `fulfillment`, `installment`, `willful`, `acknowledgment`, `sizable`, `aging`, `airplane`, `mold`, `plow`, `smolder`. Newly excluded: `math`, `harbor`, `distill`. The words the rule must catch and must not now live in `tests/test_validate_skill.py`.
- Report: shaded lines carry `data-why`; an unwritable `-o` path is one stderr line naming `-o`; the legend is headed Confidence; before-and-after gains a dense-runs pair.

## 2026-09-01

- New `americanism` check: American spellings flagged against Australian house style, in its own rule table beside the lexical no-ops and reported on its own line, since a no-op is a word to cut and an Americanism a word to respell. Stems are explicit rather than a general `\w+ize` pattern, which eats "sizes", "prized" and "capsized". Flags 48 of 110 installed skills.
- Left out of that rule on purpose, measured against the corpus: the agent nouns (`analyzer`, `optimizer`, `serializer`), which almost always carry a component's name into prose - respelling would rename the thing; `dialog` (Claude Code's own permission dialog, and the HTML element); `catalog`; `tokenize`; `program`, which is Australian in computing; and `license`/`practice`, where the correct form turns on noun versus verb.
- Fixed: the primer's own description-length rule ran only inside `lint()`, which hard-requires skills-ref, so a 119-word description reported nothing at all on the stdlib `--report-only` path the post-edit hook runs, or in the HTML report on a machine without that optional install. It now runs wherever PyYAML is available - it needs nothing else - via a new `skill_description()` that parses the frontmatter properly, since the field is regularly a folded `>-` scalar a regex reader miscounts.
- Bold's `HEAVY` band renamed `SLOPPY`.
- New `bold` check in the validator, mechanising a rule the primer had nothing behind: mid-sentence bold as a rate per 1000 words, banded HEAVY over 6.0 and ABUSED at 12.0, with an absolute count gate so a short skill cannot band on one span. Calibrated over 110 installed skills - skills run far cleaner than general prose, so the thresholds sit lower than a prose checker's; 4% flag and 2% band abused, and every one carried the same shape. Set at 5.0 first, which caught two more sitting right on the line and read as nagging.
- Bold that opens a line is exempt at any volume - a bullet lead, a `**Date:**` label, a bold line standing in for a heading - which is the shape the primer teaches. Table rows are exempt entirely, matching how `_structure` already classes them: a trailing badge in a cell (`**macOS only**`) is labelling, and counting those flagged reference tables of keybindings and config options. Words are counted over the same lines the spans come from, so a script-heavy skill cannot dilute the rate with fenced code.
- On the report bold is one row however many spans it covers, since it is a rate: its bar reads against the abuse threshold rather than against the term counts, and it is marked in blue rather than on the accent the no-ops own. Clicking the row holds every span, which is the only way to see the density the row names. `_bold` hands its spans over already placed, so the page marks the ones the rate is made of and never the exempt leads.
- `_filler_scan` splits into `_blank_inline_code` plus a strip, so bold and the no-op rules blank code the same way; a mark shared by two findings now spans both, where a bold opening first used to cut a longer no-op off at its closing asterisks.
- New `ruff.toml` at line-length 120 (E4, E7, E9, F, W, I, B, SIM, UP, RUF, C4, ISC, PIE, FURB; `UP031` ignored, since the HTML templates carry five or six positional values each). Whole-line comment blocks rewrapped to match - at 88 an explanation ran to six lines where four say it. Docstrings left alone: several break their lines deliberately.
- The report gains a **Copy brief** button in the footer, beside the date: the findings as plain text, grouped one line per rule with each rule's reason and a few instances to find it by, sized to paste into a coding agent. Capped at 12 kinds and 6 examples each, since the receiving agent has a context budget. The clipboard API is not available on `file://` in every browser, so it falls back to a hidden textarea and then to revealing the brief for hand-selection.
- Every finding now carries a **reason** - what fired and what to do instead - on hover, in a caption under the list that holds while a finding is selected, and in the brief. A rule name alone says nothing to someone reading the page without the primer open, which is every reader the page is for.
- Page and brief read one shared `Finding` list rather than each walking the validator, so the copied text cannot disagree with the page it came from.
- Fixed: clicking a highlighted word in the document showed no reason. Marks carried a term but no `data-why`, so the caption fell back to its idle text; a mark shared by two rules also selected nothing, since its key holds both terms.
- Fixed: the accent never reached a bar. `.bar:first-of-type` matched the band div above the rows, so the largest file was never marked; the lead bar is now set explicitly.
- The file heading in the document column scrolls with its file. Pinned, it detached from the text it named and read as a stray bar.
- Fixed: typing in the search box threw. It read `dataset.term` across every `tr.pick`, and the structure rows carry only `data-goto`.

## 2026-08-31

- New `scripts/render_report.py` renders a skill's findings as one self-contained HTML page: a panel of measurements beside the full source with every finding marked in place. `--against OTHER_DIR` adds a before-and-after cell. Output goes to the platform temp directory, never inside the skill. Run it under `uv` for the spec cell; plain `python3` renders the rest and names the missing dependency. To feed it, `_structure` findings now carry an inclusive line span - `(size, path, first line, last line, opening)` - so a whole unit can be shaded rather than its opening line, and `_filler_scan` is factored out of `_filler` so anything placing a finding preprocesses the line the same way the detector did.
- `SKILL.md` gains a routing entry and a pointer under "Validating a Skill" that gate the renderer behind an explicit ask for a report, a page or a visual; `references/html-report.md` covers running it.

## 2026-08-20

- `validate_skill.py` reports lexical no-ops under SIGNALS: sentence-initial filler, puffery adjectives, filler verbs, and negation-antithesis contrasts, skipping frontmatter, fenced blocks, and inline code. Detection only, never gated - a skill may mean "robust" literally. Findings group one line per distinct term (`[puffery] "comprehensive" x3 - path:line, ...`), capped at 10 terms and 6 locations, so a repeated word is one action rather than one report line per hit. The word list lives in the script, not `SKILL.md`: a banned-word list is dead weight in an always-loaded file and naming unwanted behaviour in prose primes it.
- Self-review step 2 gains the **swap test** for contrast pairs alongside the deletion test.
- `metadata.token-budget` becomes `metadata.skill-lint.max-load-tokens`: namespaced so another tool's key in the free-form `metadata` bag cannot collide, and named for what it caps (worst-case load, not SKILL.md alone, and not an allowance the agent spends at runtime). The nesting is matched, not assumed - the key is honoured only under a `skill-lint:` parent, still by regex so the stdlib-only `--report-only` path the post-edit hook runs keeps working. Report lines say "declared max-load-tokens".
- Restored the primer's own ceiling at 10000 (was 11000). Worst-case load is 9720.

## 2026-08-17

- Removed the description word-count anchors that authors were padding up to: checklist item 2 and `assets/skill-template.md` now say "1-2 sentences" and name the validator's bound as a ceiling. "Structure over prose" drops "around 20 words" for "a single short sentence".
- `validate_skill.py`: `DESCRIPTION_WORDS_MIN` 30 -> 15 (the old floor warned on any tight description, instructing authors to pad), and all three length findings name only the cap and the cure - no target range, since the printed number came back on every run regardless of the doc text. Length findings split into `description_findings()`, covered by `DescriptionLengthTests`.

## 2026-08-13

- `validate_skill.py` takes multiple skill directories in one invocation, each report headed by its path with a pass count at the end; single-skill output is unchanged, so the post-edit hook is unaffected. A missing path or `SKILL.md` fails only that skill, and optional dependencies (PyYAML, skills-ref, tiktoken) are resolved before the first report prints. Serial by measurement: the work is GIL-bound regex, so a 4-thread pool ran 50% slower over all 64 installed skills (276ms vs 184ms) and a process pool broke even at best.
- New `tests/test_validate_skill.py`: 45 stdlib `unittest` cases over `validate_skill.py` (prose percentage, blob and fence detection, reference discovery incl. `resources/`, declared budgets, exit codes, lint). Verified to fail when the bugs they cover are reintroduced. `CLAUDE.md` gained a Tests section requiring they be run and extended after any `scripts/` change.
- `validate_skill.py`: paragraph-prose percentage now attributes words per unit rather than per line, and counts a paragraph as prose only past `PROSE_UNIT_MIN = 40` words. A standalone sentence carries one instruction - structurally a bullet without the marker - so a skill of one-line directives read as ~98% prose when it needed no work (grill-me and handoff went 98% -> 0%, graphify 70% -> 30%). The percentage now discriminates instead of flagging everything.
- New `metadata.token-budget: <int>` frontmatter escape hatch for a deliberately branchy skill: honoured only with a trailing `#` comment justifying the ceiling, in which case the load passes with the budget noted and no cure advice; past it, or undefended, the normal bands apply. Read by regex so the stdlib-only `--report-only` path keeps working. The primer declares 11000.
- Report fixes in `validate_skill.py`: the OK/Poor cure line routes to SIGNALS when a reference drives the rating and stays in FACTS only when SKILL.md does (FACTS is always-loaded cost); the corpus line counts every file including SKILL.md, and is dropped where a single reference already names them all; finding lists cap at 20 rather than 5 (`BLOB_LIST_MAX`) so a skill with 25 long fences shows enough to act on.
- Worst-case load is now described as a lower bound on one branch firing - a branch chaining several references costs more - in SKILL.md and the `_budget` docstring. Same correction to the blob-detection comment: it is form-invariant per unit, but splitting one unit into several smaller ones does clear the threshold.

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
