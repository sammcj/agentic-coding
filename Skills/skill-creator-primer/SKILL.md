---
name: skill-creator-primer
description: You **MUST** load this skill before the skill-creator skill AND before making ANY change to, or conducting a review of ANY Agent Skill. Triggers include creating, editing, reviewing, or contributing to any part of an Agent Skill (description, frontmatter, body, references, scripts, trigger evals, conflicts, etc).
metadata:
  version: 2026-09-01
  skill-lint:
    max-load-tokens: 10000 # primer skill accepted as being larger
hooks:
  PostToolUse:
    - matcher: "Edit|Write"
      hooks:
        - type: command
          command: python3 "$HOME/.claude/skills/skill-creator-primer/scripts/hook_report_skill_tokens.py"
---

# Skill Creator Primer

Note: If the `skill-creator` skill is missing: stop and ask the user to install `skill-creator@claude-plugins-official` (registering the marketplace first via `/plugin marketplace add anthropics/claude-plugins-official` if needed), or to clone https://github.com/anthropics/skills and link its `skills` directory into their local skills directory.

Route to an entry point by the task in front of you (which-one routing per "Routing when branches multiply", not a content index):

- Creating a new skill -> start at "Capture Intent from Conversation" and work forward.
- Editing an existing skill -> the sections covering what you're changing, then the "Self-Review Protocol".
- Reviewing a skill, or a diff to one -> "Reviewing a Skill".
- Tuning a description or its triggering -> "Writing Effective Descriptions".
- Producing a report, page or visual of a skill's findings -> `references/html-report.md`.

## Predictable Process, Not Identical Output

A skill wrangles determinism out of a stochastic system where applicable. What it makes predictable is the _process_ - the agent taking the same steps each run - not the _output_. A brainstorming skill should predictably diverge: its tokens vary, its behaviour doesn't. This is the lens for the rest of this primer: triggering, structure, steering, and pruning are all levers on process consistency; cost and maintainability follow. Judge any change by whether it makes the agent behave more consistently, given what that particular skill is for.

## Track Each Step as a Task

Before you create, update, or review a skill, create a task (todo) for each step of the work - the primer sections you'll apply, plus a self-review pass - each phrased with its completion criterion, then work them to completion.

- This is the primer's own defence against premature completion: with the finish line in view, the agent tends to make the visible edit and skip the review. Tracked tasks keep the whole process in front of you.
- Scale the ceremony to the change: substantial skill work warrants a task per step; a trivial edit still earns its description update, a trigger-conflict check, and a self-review pass, tracked or not.

## How Skills Actually Work

**Skills are prompt-based context modifiers.** When invoked, a skill:

1. Injects SKILL.md instructions into the conversation context
2. Modifies execution context by changing tool permissions and optionally switching models
3. Guides the agent's behaviour through concise instructions

**Skill selection happens through pure LLM reasoning.** No algorithmic matching, keyword search, or intent classification (the optional `paths` frontmatter, a file-glob gate, is the sole exception). The agent reads descriptions in the `Skill` tool's prompt and reasons about which matches. This makes the `description` field the single most critical element.

**Branches decide what to disclose.** Inline what every branch of the skill needs; push behind a context pointer (a bundled file) only what a single branch reaches. A pointer's _wording_, not its target, decides whether the agent follows it - a must-have target behind a weak pointer is a variance bug, so sharpen the wording before settling for inlining. When in doubt for this primer, keep almost-certainly-needed material inline so the agent never has to decide whether to read it.

**Routing when branches multiply.** When a skill fans out to many references, write the load decision as a decision tree: each branch a one-line qualifier, each leaf a reference pointer.

- Phrase the qualifier as the task's need, not the target's name - the agent routes by matching its task against it: "key-value (config, sessions, cache) -> `references/kv.md`".
- Keep the tree one level deep with mutually exclusive branches - every routing hop is a decision the agent can get wrong.
- Below a handful of references, skip the tree - plain pointers with sharp wording cost less than a routing layer.
- Trees carry which-one decisions only - reference material wants tables, sequences want numbered lists.

**Invocation mode is a trade-off** - choose it deliberately.

- Model-invoked: the description sits in the agent's context on every request and competes for attention, and the agent may decline to fire even a well-matched skill - so write trigger evals to confirm it fires (see "Testing Skill Triggering").
- User-invoked (`disable-model-invocation: true`): the description stays out of every agent session, but the user must remember the skill exists and trigger it with a slash command.

Default to model-invoked for mid-task discovery; switch to user-invoked when the skill is occasional and the user will reliably reach for it. When the right mode isn't obvious, give the user both options with a one-line pro/con each.

---

## Skills vs Custom Agents

Before writing a skill, confirm a skill is the right vehicle:

- **Skill** - knowledge, a detailed workflow, or helper tools the agent loads on demand within its current context.
- **Custom agent** - a persona with its own context window and world view, carrying at most a lightweight workflow. Adversarial or fresh-perspective work (review, red-teaming, premise-checking) belongs here precisely because the separate context stops it inheriting the caller's assumptions.
- **They compose** - an agent can load skills, so shared knowledge still lives in a skill even when a persona needs its own context.

## Prefer One Skill Over Many Closely Related Skills

When a request spans several related capabilities, default to a single skill that uses progressive disclosure rather than a separate skill per capability:

- **Why one wins** - every extra skill adds a description that is always in every agent's context, competes with the others at selection time, and risks overlapping triggers. This is skill bloat.
- **How to consolidate** - fold the related behaviours into one SKILL.md and push each one's detail into bundled `references/` the agent loads on demand.
- **When to split** - only when the skills trigger on genuinely distinct intents or carry conflicting tool or permission needs.

---

## Capture Intent from Conversation

When a user says "turn this into a skill", extract the workflow from the current conversation before asking questions. Look for:

- Tools used and the sequence of steps taken
- Corrections the user made along the way
- Input/output formats observed
- Patterns that repeated across the conversation

Fill gaps with the user, then proceed to skill creation.

Draft inside the primer's `assets/skill-template.md`: copy it into the new skill directory as `SKILL.md`, fill the placeholders, delete unused sections.

## Writing Effective Descriptions

The description is the single most important part of a skill to get right. It shares a token budget with every other skill's description and is always active in the agent's context.

### Skill Description Checklist

**Create a task per item below**, judge each pass/fail; done when all pass. Re-check the set after any edit - one fix can break another (an added clause can blow the word cap):

1. **Be concise.** Skills are for agent consumption; agents need clear, high-signal triggers, not verbose prose.
2. **Keep it to 1-2 sentences.** The validator's word cap is a ceiling, never a target to fill.
3. **Descriptions are solely for the agent deciding whether to load the skill.** No instructions for after activation, and no summary of the skill's content or inner workings - a workflow summary invites the agent to act on the summary and skip the skill's branches.
4. Ensure the description is distinct. It must not be confusable with neighbouring skills - similar names, the same verb/object, or overlapping situational triggers. The co-active set varies per deployment, so distinctiveness comes from a tight, specific trigger; when the neighbours are enumerable, run "Check for Description Trigger Conflicts" below.
5. Use imperative phrasing. Frame the description as an instruction to the agent: Use this skill when rather than This skill does. The agent is deciding whether to act, so tell it when to act.
6. Focus on user intent, not implementation. Describe what the user is trying to achieve, not the skill's internal mechanics. The agent matches against what the user asked for.
7. Front-load the leading word. The description is where a leading word does its invocation work, so lead with it. If the same word lives in the user's prompts, docs, and code, invocation lands harder.
8. One trigger per branch, no synonym padding. Give one trigger for each distinct branch the skill handles; synonyms that rename a single branch are duplication that spends context without widening coverage. Cut identity already stated in the skill body.
9. When a skill over-fires, add a negative-trigger exclusion clause. Name the neighbouring intent and where it belongs instead - "Do NOT use for X, use Y instead" - so the agent can route away from the skill as well as toward it.

### Check for Description Trigger Conflicts

Two skills conflict when an agent, reading both descriptions, cannot reliably tell which one a request should load - that is the only thing this check looks for; skills covering related ground are fine. Run the check against the neighbours you can enumerate: the skills installed beside it, or the repo it is being contributed to.

To compare a new or edited description against a set of skills, list each skill's directory, name, and description:

```bash
python3 scripts/list_descriptions.py path/to/skills
```

The script is stdlib-only Python (no PyYAML, ripgrep, or yq), so it runs anywhere. Group skills sharing a verb or object (create/edit, diagram, review, test), then compare pairwise for shared intent without a disambiguator - not merely shared words.

A pair is ACCEPTABLE when a clear disambiguator is present in the trigger:

- Different target tool, language, or file type - the agent routes on it. Intentional families on a shared template (go/rust/python: "activate when working on `<language>` projects") are fine; the language is the routing signal, so do not flatten it.
- Different phase or scope of the same activity (plan vs implement; one file vs the whole repo).
- One is a primer or sub-skill the other explicitly names.

A pair is a CONFLICT when:

- The triggers are interchangeable: either could match the same request equally.
- One description is a verbatim subset of the other with no added distinction.
- They claim the same activity on the same object with no routing signal between them.

ACCEPTABLE - near-identical wording, but the tool name routes cleanly:

> mermaid-diagrams: "...creating or updating mermaid diagrams. Provides guidance on mermaid best practices."
> excalidraw-diagrams: "...create or update Excalidraw diagrams. Provides guidance on Excalidraw best practices."

CONFLICT - one trigger is a verbatim subset of the other, with no distinguishing "use when":

> domain-model: "Grilling session that challenges your plan against the existing domain model. Use when user wants to stress-test a plan against their project's language..."
> grill-with-docs: "Grilling session that challenges your plan against the existing domain model..." (identical opening, no distinguishing trigger)

On a real conflict, pick the lightest fix: sharpen one description's "use when" to name what is distinct, narrow one skill's scope, or merge genuinely identical skills. Leave descriptions that already route cleanly alone, however alike they read.

### Testing Skill Triggering

A skill activates purely on its `description` - the agent reads descriptions and reasons about which to load. To measure whether a description fires on the right requests and stays quiet on the rest - especially when over- or under-triggering is a risk - write trigger evals: realistic queries, each labelled with whether the skill should activate, scored against the live description.

Place an eval set at `evals/<set>.json` beside the skill and run it with the bundled `scripts/eval_triggering.py`. **Read `references/trigger-evals.md`** before writing or running skill evals.

## Degrees of Freedom

Match specificity to the task's fragility and variability:

**High freedom** (text instructions): Multiple approaches valid, decisions depend on context, heuristics guide approach.

**Medium freedom** (pseudocode/parameterised scripts): Preferred pattern exists, some variation acceptable, configuration affects behaviour.

**Low freedom** (specific scripts, few parameters): Operations fragile and error-prone, consistency critical, specific sequence required.

Think of the agent exploring a path: a narrow bridge with cliffs needs guardrails (low freedom), an open field allows many routes (high freedom).

## Skill Writing Tips

### Selecting content

- **Don't state the obvious.** the agent already knows a lot about coding and has default opinions. Focus skill content on information that pushes the agent out of its normal way of thinking. If the agent would reliably do the right thing without your skill, that content is wasting tokens.
- **Knowing is not doing.** The test for cutting is not "does the agent know this?" but "would the agent reliably do this, in this order, every time, without being told?" Cut declarative knowledge that lives in training data (well-known APIs, design patterns, standard syntax) - it's recalled reliably. Keep required workflow: the agent may know each step yet still default to its own approach or skip the sequence unless the skill commits it. Enforcement, ordering constraints, gates, and checklists earn their tokens by changing what the agent _does_, not teaching it something new.
- **Build a Gotchas section.** The highest-signal content in any skill is a Gotchas section listing common failure points the agent hits when using the skill. Build this up from real failures over time. A good Gotchas section often delivers more value than pages of general instructions.

### Structuring the skill

- **Structure over prose.** Write instructions as numbered steps or bullets, one action each, a single short sentence; reserve paragraphs for concepts. Prose buries the logic the agent has to act on. The same applies to frontmatter, `argument-hint`, and JSON-schema description fields: a few precise words, not a paragraph. Telegraphic fragments (dropped articles, `error -> fix` pairs) are fine for gotchas, checklists, and fact lists; avoid fragments where they'd blur a concept, sequence, or steering nuance. See the second pair under "Examples".
- **Co-locate a concept's parts.** Keep a concept's definition, rules, and caveats under one heading rather than scattered, so reading one part brings its neighbours. The test: a skill should read like documentation written for the agent. This differs from duplication (one meaning repeated in two places); scattering fragments a single meaning across many.
- **Build with sub-agents in mind.** Sub-agents parallelise independent work and keep bulky intermediate output out of the main conversation. Where steps could fan out (per-item passes, independent research questions, read-only sweeps), mark the hand-off: what each sub-agent needs and what it returns (a summary, verdict, or file path - not a raw dump). Suggest fan-out points rather than prescribing orchestration; the model running the skill may coordinate better than the one authoring it.
- **Think through the setup.** Some skills need user-specific configuration (e.g. which Slack channel, which database, API keys). Pattern: on first run, check for a config file; if missing, ask the user and store their answers. This avoids hardcoding values that differ per user or environment.
- **Do not add inline scripts within markdown.** Single commands / simple one liners are fine, but scripts should be their own files; the validator flags fenced blocks over 10 lines. When a skill bundles scripts, write them well (see "Writing Scripts" below).
- Avoid deeply nested references.
- For reference files (`references/*.md`) longer than 100 lines, include a concise table of contents at the top, so the agent sees the full scope even under partial reads.

### Steering the agent

- **Avoid railroading the agent.** Skills are reused across many prompts and contexts, so overly rigid instructions (heavy MUSTs, exact step sequences) break when the context shifts. Give the agent the information it needs and leave flexibility to adapt. Calibrate prescriptiveness with "Degrees of Freedom" above.
- **Avoid pink elephant guidance.** Naming specific unwanted behaviour activates it ("Never use the word delve" plants delve). Prefer positive instructions stating the desired behaviour. If you must prohibit something, pair it with the concrete alternative so the agent has somewhere to land. Specific banned-item lists (e.g. exact phrases to avoid) are fine when paired with replacements.
- **Steer with leading words.** Pick one plain pretrained, meaning-dense term per concept and repeat it throughout (always "field", never a mix of "field", "box", "element"); the agent echoes the term in its reasoning and its prior steers behaviour - a coined term carries no prior. **Read `references/steering.md`** when a skill won't comply (ignored instruction, skipped or early-finished step), when choosing or strengthening a leading word, or when multi-step procedures need completion criteria - it covers leading words, completion criteria, and defending against premature completion.
- **Make task-tracking the first step of any encoded workflow.** Write the workflow's first step as an instruction to the agent: create a task (todo) per step, phrased with its completion criterion, then work them to completion - the same defence against premature completion this primer applies to itself (see "Track Each Step as a Task").

### Writing Scripts

When a skill bundles scripts:

- **Solve, don't punt.** Handle error conditions in the script rather than failing and leaving the agent to improvise. A script that creates a missing file or falls back to a sensible default is more reliable than one that throws.
- **No voodoo constants.** Justify and document config values in a comment. If you can't explain why a timeout is 30s, the agent can't either.
- **State execution intent.** Make clear whether to run the script ("Run `extract_fields.py` to pull form fields") or read it as reference ("See `extract_fields.py` for the extraction algorithm"). Execution is usually preferred.
- **Lean on the standard library**; declare real deps inline. A stdlib-only script runs anywhere with no setup, so prefer it. When a script genuinely needs a third-party package, run it with `uv` and declare the dependency in [PEP-723](https://peps.python.org/pep-0723/) inline metadata at the top of the script, so the dependency travels with the file.

### Token Budget Guidance

Challenge each piece: "Does the agent need this, and does it justify its token cost?"

- Aim for <4k tokens in the main SKILL.md; move detailed content to references.
- A reference loads whole when its branch fires: many small branch-gated references are cheap; one huge reference costs its branch the full amount - split or thin it like an oversized SKILL.md.
- The quality bar (blobs, deletion test, failure modes) applies to every referenced file equally.
- The 4k aim assumes branchy content: when almost every activation needs almost every section, a larger SKILL.md is the correct trade, judged by the deletion test rather than the count (this primer qualifies; see "Branches decide what to disclose").
- Measure with the bundled validator (see "Validating a Skill").

### Examples

Good example (concise, actionable):

```
## Extract PDF text

Use pdfplumber for text extraction:

`python scripts/extract_pdf_text.py <pdf-file>`

```

Bad example (verbose, wrapped):

```
## Extract PDF text

PDF (Portable Document Format) files are a common file format that contains
text, images, and other content. To extract text from a PDF, you'll need to
use a library. There are many libraries available for PDF processing, but
pdfplumber is recommended because it's easy to use and handles most cases well.
First, you'll need to install it using pip. Then you can use the code below...
```

Good example (instructions as structure):

```
1. Run the skill's evals if present.
2. On failure, tune the description and re-run.
```

Bad example (the same instructions, buried in prose, wrapped):

```
When you begin the review you should first check whether the skill has evals,
and if it does, run them before anything else, keeping in mind that failures
may mean the description needs tuning, in which case you should revisit it
and run them again.
```

## Bundled File Layout

Standardise where bundled files live so skills stay predictable across the toolkit:

- `references/` - Markdown the agent reads as reference (the loaded-on-demand layer of progressive disclosure).
- `scripts/` - executable scripts the agent runs.
- `assets/` - templates the agent copies or fills in, plus non-text artefacts like SVGs and icons. Prefer referencing these from an external source over committing them; bundled binaries add weight and context overhead with no benefit to the agent.
- When `references/` spans many sibling domains, give each domain the same file set (e.g. `<domain>/patterns.md`, `<domain>/gotchas.md`, omitting any that would be empty) so the agent knows what exists at the next level without reading an index.

## What to Not Include in a Skill

Skills should only contain files that directly support functionality.

**DO NOT** create:

- README.md or other human-facing documentation or setup procedures (unless requested by the user)
- Context about the creation process itself
- Fluff, filler, otherwise inconsequential content that doesn't support execution of the skill's function
- A table of contents or index of the main SKILL.md content
- Content that an agent could easily infer or would know to access without the skill
- Rich file formats (e.g. zip, pptx, png, pdf etc.) unless they're a template (AI is most efficient with text and tools, bundled file formats add overhead and complexity)

## Write Skills to Run Across Agents

Skills should work on any tool that supports standard Agent Skills. Claude Code is our primary target, but GitHub Copilot and others read the same format, so keep wording and tooling portable rather than silently Claude Code-only:

- Say "the agent", not "Claude Code" or "Copilot", when referring to whatever runs the skill.
- Favour the spec's standard frontmatter and portable commands; reach for the Claude Code-specific extension fields below only when the skill genuinely needs them.
- Omit `compatibility:` by default. Add it only when a skill is genuinely tied to one tool, to declare that in frontmatter rather than baking the assumption into prose - e.g. `compatibility: claude-code`, `github-copilot`, or `microsoft-cowork`. A tool-agnostic skill leaves it unset.

## Claude Code Frontmatter & Extensions

These are Claude Code-specific fields not covered by the Agent Skills spec. Only include when specifically needed:

- `argument-hint`: Hint shown during autocomplete for expected arguments, e.g. `[issue-number]` or `[filename] [format]`. Only include if the skill accepts arguments
- `arguments`: Named positional arguments for `$name` substitution in the skill body. Accepts a space-separated string or a YAML list; names map to positions in order. Only include if the skill uses named substitutions
- `model`: Override the model. Set to `"inherit"` (default) or a specific model ID like `"claude-opus-4-7"`. Only include if the user requests it
- `effort`: Override effort level when the skill is active. Options: `low`, `medium`, `high`, `xhigh`, `max`. Only include if the user requests it
- `context`: Set to `"fork"` to run in a forked sub-agent context. Useful for skills with extensive exploration or large outputs. Only include if the user requests it
- `disable-model-invocation`: Set to `true` to prevent Claude from auto-loading the skill. Use for side-effect workflows the user should trigger manually. Choose this mode deliberately per "Invocation mode is a trade-off" above (and Self-Review step 6), not only on user request
- `user-invocable`: Skills appear as slash commands by default. Set to `false` to hide from the menu. Only include if the user requests it
- `agent`: Subagent type used when `context: "fork"` is set (defaults to general-purpose); has no effect without it. Only include if the user requests it
- `paths`: Glob patterns that limit when the skill activates. Only include if the skill is scoped to particular files or directories
- `hooks`: Hooks scoped to this skill's lifecycle. Only include if the skill needs a hook while active
- `shell`: Shell used for inline `` !`command` `` blocks (`bash` or `powershell`). Only include if the skill uses them
- `allowed-tools`: Space-delimited pre-approved tools. Scope where possible, e.g. `"Read Write Bash(uv run scripts/*.py *) Grep WebFetch(domain:code.claude.com)"` (don't use the deprecated `:` syntax, e.g. `Bash(command:*)`, instead use `Bash(command *)`)
- `disallowed-tools`: Tools removed from the available pool while the skill is active (clears on the next user message). Use for autonomous skills that must never call a tool, e.g. `AskUserQuestion` in a background loop. Only include if the user requests it
- `when_to_use`: Do not use.

---

## Validating a Skill

Validate against the official Agent Skills specification with the bundled `scripts/validate_skill.py` (resolve it from this skill's `scripts/` directory). It does not run automatically - invoke it against a skill when you want a check or a measurement:

```bash
uv run <skill-creator-primer>/scripts/validate_skill.py <skill-dir> [<skill-dir> ...]
```

Pass a real path, not `.` (skills-ref matches the directory's basename against the skill name, and `.` resolves to an empty basename).

Several skills can be passed at once: each report is headed by its path, with a pass count at the end. The exit code fails if any skill fails.

On a valid skill it also prints a token-budget estimate and rating alongside the spec checks. It counts only the Markdown that SKILL.md actually references (transitively), so a stray unreferenced file does not inflate the figure. The count uses a chars/4.12 heuristic calibrated against tiktoken; add `--tiktoken` (run via `uv run --with tiktoken`) to count with the real tokeniser instead.

- Great: 1k-5k tokens
- Good: 5k-9k tokens
- OK: 9k-12k tokens
- Poor: 12k+ tokens

- The rating judges the worst-case load (SKILL.md + largest single reference - a lower bound on one branch firing; a branch chaining several references costs more), not the corpus total, so progressive disclosure isn't penalised. Enforced by exit code - Poor fails, OK warns, the message naming the driving file.
- A skill whose branch test genuinely keeps nearly everything inline can declare `metadata.skill-lint.max-load-tokens: <int>` in its frontmatter, with a trailing `#` comment justifying the ceiling. It caps the worst-case load (SKILL.md plus the largest reference), not SKILL.md alone. Loads within it pass with the ceiling noted and no cure advice; past it the normal bands apply. An undeclared comment voids the ceiling - the justification is the point, so reach for this only after the deletion test has already run.
- Findings are FACTS (over-long description, over-budget load, blobs in SKILL.md: always-loaded cost, fix them) or SIGNALS (large references, blobs or 10+ line code fences within them: branch-loaded, judge waffle against earned detail). Three or more reference blobs draw a warning - the load rating trusts references to stay tight.
- A blob is any text unit of 100+ words, any shape (paragraph, list item, quote, table row): prose long enough to bury instructions (see "Buried instructions" in Failure Modes). The blob list feeds the compression pass in the Self-Review Protocol.
- While this primer is active, a PostToolUse hook re-runs the report (`--report-only`, stdlib-only) after every SKILL.md edit, keeping the budget in view across the session.

When the user asks for a skill report, a page, or a visual of the findings, **read `references/html-report.md`** and run the renderer it describes. The text report above covers every other case.

### Upstream validators may have an incomplete frontmatter allowlist

`skills-ref` (and skill-creator's `quick_validate.py`, which gates packaging via `python -m scripts.package_skill` - the failure surfaces as "Validation failed") may recognise only six core spec properties (`name`, `description`, `license`, `allowed-tools`, `metadata`, `compatibility`) and error on every valid Claude Code extension field (`when_to_use`, `argument-hint`, `arguments`, `disable-model-invocation`, `user-invocable`, `disallowed-tools`, `model`, `effort`, `context`, `agent`). A skill failing only on one of those fields is still valid.

The bundled `validate_skill.py` errors only on genuine spec violations and downgrades unknown fields to warnings, so documented extensions and fields newer than the linter pass. It also parses frontmatter with PyYAML rather than skills-ref's StrictYAML, so flow-style arrays (`allowed-tools: [Read, Write]`) pass.

The official docs at https://code.claude.com/docs/en/skills#frontmatter-reference are the authoritative, version-current list.

## Failure Modes

Diagnose an oversized or unreliable skill against these modes and apply the cure.

- **Premature completion** - ending a step before it's done. Cure: sharpen the completion criterion, then hide later steps (see `references/steering.md`).
- **Duplication** - the same meaning in more than one place, including restating a source the text cites as authoritative. Cure: one source of truth per step and per reference item.
- **Sediment** - stale layers that accumulate because adding feels safer than deleting. Cure: a pruning discipline - restructure into branches, then delete what no branch needs.
- **Sprawl** - simply too long, even when every line is live and unique. Cure: progressive disclosure - split by branch (the branch test under "How Skills Actually Work") or into a separate sequenced skill.
- **No-op** - a line the model already obeys by default; a relevant line can still be a no-op. Model-relative - test by running the skill. Cure: a stronger leading word, or deletion (apply the deletion test).
- **Buried instructions** - instructions or logic carried in paragraph prose or oversized list items, in the body or in description/frontmatter/schema fields. Cure: convert per "Structure over prose" (Skill Writing Tips); the validator's blob list locates offenders.
- **Fossilised diff** - the body narrates its own history: ticket IDs, amendment notes, superseded mechanisms, rationale addressed to a reviewer. Cure: state current behaviour only, readable to an agent that never saw a prior version; provenance lives in the changelog and git.

## Self-Review Protocol

When a skill spans 3+ references, fan the per-file read-only passes out to parallel sub-agents (each reviews its own files for low-value prose and within-file repetition, returning a summary) - reads don't collide. Cross-file checks (e.g. duplication between SKILL.md and references) can't be split; the main agent reconciles those from the summaries. Keep edits to one agent, or give each sub-agent non-overlapping files.

After creating or updating a skill, you **MUST** always perform a critical self-review using the primer. **Create and complete tasks / TODOs for each of the following**:

1. Check for duplicated information across SKILL.md and reference files
2. Remove low-value prose and filler. Apply the **deletion test**: cut the passage; if the agent's behaviour wouldn't change, it's a no-op - leave it deleted (see "Failure Modes"). For a contrast pair ("not X, it's Y"), apply the **swap test**: if reversing it reads as well, the contrast carries nothing - state the claim directly.
3. Thin the language - make important information prominent while reducing word count.
4. Run the validator (see "Validating a Skill"); at an OK or Poor rating, run a compression pass:
   - Extract a checklist of every rule, step, and gotcha from the current draft.
   - Dispatch a fresh-context sub-agent (never the drafting context - it's attached to its own prose) to rewrite at ~75% (OK) or ~60% (Poor) of the word count, converting instruction-bearing paragraphs into steps and bullets, deleting provenance and justification riders, and returning only the rewrite. Prefer a `compression-editor` agent when the environment defines one.
   - Accept the rewrite only after verifying every checklist item survives; one round is the default. State the token delta in your change summary.
5. Verify the description is concise (short) yet complete enough for triggering (see the Writing Effective Descriptions checklist)
6. Decide the invocation mode: model-invoked for mid-task discovery, user-invoked (`disable-model-invocation: true`) when occasional and user-remembered; in doubt, offer the user both (see "Invocation mode is a trade-off").
7. Ensure no extraneous files were created
8. Frame guidance positively to avoid the pink elephant effect (see Skill Writing Tips). Rewrite "don't do X" as "do Y", or pair the prohibition with the concrete alternative
9. Deterministic tools are used for deterministic outcomes. If a script can perform a task, have the agent call that script rather than relying on interpreted instructions.
10. If the skill has evals, the evals are up to date and run without issue.
11. For a newly created skill: once the steps above pass, dispatch a fresh-context sub-agent (not a fork - see "Skills vs Custom Agents") to activate the skill-creator-primer and skill-creator skills and review the new skill read-only per "Reviewing a Skill" below, returning graded findings. Action the spec and primer violations, decide each judgement call, then re-validate; one round is the default. Without sub-agents, ask the user to run the review in a fresh session.
12. Re-run the validator if any step after 4 changed the skill; the review closes on a passing gate.

**Verbosity is not rewarded - knowledge quality is.**

## Reviewing a Skill

The review criteria are the same whether the skill is yours or someone else's. Read the full skill (SKILL.md plus every referenced file) before judging any diff - a clean-looking edit can duplicate or contradict a reference you haven't seen. Then:

1. Validate mechanically first - see "Validating a Skill" (spec and token budget).
2. Diagnose against "Failure Modes"; report each finding by mode, with its cure.
3. If the description changed, hold it to the "Skill Description Checklist" and "Check for Description Trigger Conflicts"; run the skill's trigger evals only when over- or under-triggering is in question - they are a tuning aid, not a gate.
4. For a diff, confirm the description and reference pointers still match the skill's branches after the change (see "How Skills Actually Work").
5. Grade every finding: spec violation, primer violation (cite the section), or judgement call. Only the first two block.

Fix what you find by default; report the graded findings instead when the situation is review-only - you have no write tools (a critical-review sub-agent), or the fixes belong to the contribution's author. Self-review inherits the author's assumptions - use fresh eyes or a fresh-context agent (see "Skills vs Custom Agents").

Remember: **Less is more. Skills MUST be concise! When in doubt write skill content in a TLDR format.**
