---
name: skill-creator-primer
description: Foundational skill-authoring knowledge to use alongside the skill-creator skill. You **MUST** load this skill before the skill-creator skill whenever creating, editing, reviewing, improving, or contributing a skill - its frontmatter, body, evals, or description, including checking a description for trigger conflicts with other skills, or when you are making ANY changes to ANY agent skill.
metadata:
  version: 2026-07-02
---

# Skill Creator Primer

Note: If your environment does not have the `skill-creator` skill: Stop and ask the user to install `skill-creator@claude-plugins-official` (running `/plugin marketplace add anthropics/claude-plugins-official` first if that marketplace isn't registered) before proceeding; they may alternatively clone https://github.com/anthropics/skills and link its `skills` directory to their local skills directory.

## Predictable Process, Not Identical Output

A skill wrangles determinism out of a stochastic system where applicable. What it makes predictable is the _process_ - the agent taking the same steps each run - not the _output_. A brainstorming skill should predictably diverge: its tokens vary, its behaviour doesn't. This is the lens for the rest of this primer: triggering, structure, steering, and pruning are all levers on process consistency, and cost and maintainability follow from it. Judge any change by whether it makes the agent behave more consistently, given what that particular skill is for.

## Track Each Step as a Task

Before you create, update, or review a skill, create a task (todo) for each step of the work - the primer sections you'll apply, plus a self-review pass - then work them to completion, marking each done as you go. This is the primer's own defence against premature completion: with the finish line in view, the agent tends to make the visible edit and skip the review. Tracked tasks keep the whole process in front of you so none of it gets dropped. Scale the ceremony to the change: substantial skill work warrants a task per step; a trivial edit still earns its description update, a trigger-conflict check, and a self-review pass, tracked or not.

## How Skills Actually Work

**Skills are prompt-based context modifiers, not executable code.** When invoked, a skill:

1. Injects instructions into the conversation context (via hidden messages to the agent)
2. Modifies execution context by changing tool permissions and optionally switching models
3. Guides the agent's behaviour through detailed instructions

**Skill selection happens through pure LLM reasoning.** No algorithmic matching, keyword search, or intent classification (the optional `paths` frontmatter, a file-glob gate, is the sole exception). The agent reads skill descriptions in the `Skill` tool's prompt and uses language model reasoning to decide which skill matches. This makes the `description` field the single most critical element.

**Agents tend to under-trigger skills.** To combat this, make descriptions slightly assertive about when to activate. Instead of "Build dashboards for data", write "Build dashboards for data. Use this skill whenever the user mentions dashboards, data visualisation, metrics, or wants to display any kind of data."

**Progressive disclosure keeps context lean.** Three-level loading:

1. **Metadata** (name + description) - Always in context (~20-100 words)
2. **SKILL.md body** - Loaded only after triggering (<5k words)
3. **Bundled resources** - Loaded by the agent as needed (unlimited, scripts execute without reading)

**Branches decide what to disclose.** Inline what every branch of the skill needs; push behind a context pointer (a bundled file) only what a single branch reaches. A pointer's _wording_, not its target, decides whether the agent follows it - a must-have target behind a weak pointer is a variance bug, so sharpen the wording before settling for inlining. When in doubt for this primer, keep almost-certainly-needed material inline so the agent never has to decide whether to read it.

**Invocation mode is a trade-off, choose it deliberately.** Model-invoked skills cost context load: every description sits in the agent's context on every request and competes for attention, and the agent may decline to fire even a well-matched skill - so model-invocation demands trigger evals to confirm it fires (see "Testing Skill Triggering"). User-invoked skills (`disable-model-invocation: true`) cost cognitive load instead: the description stays out of every agent session - freeing context for unrelated work - but the user must remember the skill exists and trigger it with a slash command. TLDR: default to model-invoked so the agent can discover it mid-task; switch to user-invoked when the skill is needed only occasionally and the user will reliably reach for it. When the right mode isn't obvious, give the user both options with a one-line pro/con each and let them pick.

The description must be both concise (to fit token budgets shared with all other skills) and comprehensive (to enable accurate selection).

## Skills vs Custom Agents

Before writing a skill, confirm a skill is the right vehicle:

- **Skill** - knowledge, a detailed workflow, or helper tools the agent loads on demand within its current context.
- **Custom agent** - a persona with its own context window and world view, carrying at most a lightweight workflow. Adversarial or fresh-perspective work (review, red-teaming, premise-checking) belongs here precisely because the separate context stops it inheriting the caller's assumptions.
- **They compose** - an agent can load skills, so shared knowledge still lives in a skill even when a persona needs its own context.

## Prefer one skill over many

When a request spans several related capabilities, default to a single skill that uses progressive disclosure rather than a separate skill per capability:

- **Why one wins** - every extra skill adds a description that is always in every agent's context, competes with the others at selection time, and risks overlapping triggers. This is skill bloat.
- **How to consolidate** - fold the related behaviours into one SKILL.md and push each one's detail into bundled `references/` the agent loads on demand.
- **When to split** - only when the skills trigger on genuinely distinct intents or carry conflicting tool or permission needs.

## Degrees of Freedom

Match specificity to the task's fragility and variability:

**High freedom** (text instructions): Multiple approaches valid, decisions depend on context, heuristics guide approach.

**Medium freedom** (pseudocode/parameterised scripts): Preferred pattern exists, some variation acceptable, configuration affects behaviour.

**Low freedom** (specific scripts, few parameters): Operations fragile and error-prone, consistency critical, specific sequence required.

Think of Claude exploring a path: a narrow bridge with cliffs needs guardrails (low freedom), an open field allows many routes (high freedom).

## Claude Code Frontmatter & Extensions

These are Claude Code-specific fields not covered by the Agent Skills spec. Only include when specifically needed:

- `argument-hint`: Hint shown during autocomplete for expected arguments, e.g. `[issue-number]` or `[filename] [format]`. Only include if the skill accepts arguments
- `arguments`: Named positional arguments for `$name` substitution in the skill body. Accepts a space-separated string or a YAML list; names map to positions in order. Only include if the skill uses named substitutions
- `model`: Override the model. Set to `"inherit"` (default) or a specific model ID like `"claude-opus-4-7"`. Only include if the user requests it
- `effort`: Override effort level when the skill is active. Options: `low`, `medium`, `high`, `xhigh`, `max`. Only include if the user requests it
- `context`: Set to `"fork"` to run in a forked sub-agent context. Useful for skills with extensive exploration or large outputs. Only include if the user requests it
- `disable-model-invocation`: Set to `true` to prevent Claude from auto-loading the skill. Use for side-effect workflows the user should trigger manually. Only include if the user requests it
- `user-invocable`: Skills appear as slash commands by default. Set to `false` to hide from the menu. Only include if the user requests it
- `agent`: Subagent type used when `context: "fork"` is set (defaults to general-purpose); has no effect without it. Only include if the user requests it
- `paths`: Glob patterns that limit when the skill activates. Only include if the skill is scoped to particular files or directories
- `hooks`: Hooks scoped to this skill's lifecycle. Only include if the skill needs a hook while active
- `shell`: Shell used for inline `` !`command` `` blocks (`bash` or `powershell`). Only include if the skill uses them
- `allowed-tools`: Space-delimited pre-approved tools. Scope where possible, e.g. `"Read Write Bash(uv run scripts/*.py *) Grep WebFetch(domain:code.claude.com)""` (don't use the deprecated `:` syntax, e.g. `Bash(command:*)`, instead use `Bash(command *)`)
- `disallowed-tools`: Tools removed from the available pool while the skill is active (clears on the next user message). Use for autonomous skills that must never call a tool, e.g. `AskUserQuestion` in a background loop. Only include if the user requests it
- `when_to_use`: Avoid. It's just appended to the description and shares the same character budget, so it adds no space - put any trigger phrases in the description itself rather than splitting them across two fields.

### Upstream validators may have an incomplete frontmatter allowlist

The `skills-ref` library (and the skill-creator's `quick_validate.py`) only recognise the six Agent Skills spec properties (`name`, `description`, `license`, `allowed-tools`, `metadata`, `compatibility`) and will error on every valid Claude Code extension field (`when_to_use`, `argument-hint`, `arguments`, `disable-model-invocation`, `user-invocable`, `disallowed-tools`, `model`, `effort`, `context`, `agent`).

The bundled `scripts/validate_skill.py` errors only on genuine spec violations and downgrades unknown-field detection to a warning, so documented extensions pass clean and a field newer than the linter won't block. If you instead run `quick_validate.py` or raw `skills-ref` and it fails only on one of these fields, the skill is still valid. The bundled validator also parses frontmatter with standard PyYAML rather than skills-ref's StrictYAML loader, so flow-style arrays (`allowed-tools: [Read, Write]`) pass instead of failing on a style preference.

Consider the official docs at https://code.claude.com/docs/en/skills#frontmatter-reference as the authoritative, version-current list.

## Write Skills to Run Across Agents

Skills in this toolkit should work on any tool that supports standard Agent Skills. Claude Code is our primary target, but GitHub Copilot and others read the same format, so keep wording and tooling portable rather than silently Claude Code-only:

- Say "the agent", not "Claude Code" or "Copilot", when referring to whatever runs the skill.
- Favour the spec's standard frontmatter and portable commands; reach for the Claude Code-specific extension fields above only when the skill genuinely needs them.
- Omit `compatibility:` by default. Add it only when a skill is genuinely tied to one tool, to declare that in frontmatter rather than baking the assumption into prose - e.g. `compatibility: claude-code`, `github-copilot`, or `microsoft-cowork`. A tool-agnostic skill leaves it unset.

## What to Not Include in a Skill

Skills should only contain files that directly support functionality.

**DO NOT** create:

- README.md, CHANGELOG.md, INSTALLATION_GUIDE.md, QUICK_START.md, SUMMARY.md (unless requested by the user)
- User-facing documentation or setup procedures
- Context about the creation process itself
- Fluff, filler, otherwise inconsequential content that doesn't support execution of the skill's function
- A table of contents or index of the main SKILL.md content
- Content that an agent could easily infer or would know to access without the skill
- Rich file formats (e.g. zip, pptx, png, pdf etc.) unless they're a template (AI is most efficient with text and tools, bundled file formats add overhead and complexity)

The skill is for an AI agent to do the job; auxiliary documentation adds clutter and wastes context.

## Bundled File Layout

Standardise where bundled files live so skills stay predictable across the toolkit:

- `references/` - Markdown the agent reads as reference (the loaded-on-demand layer of progressive disclosure).
- `scripts/` - executable scripts the agent runs.
- `assets/` - templates the agent copies or fills in, plus non-text artefacts like SVGs and icons. Prefer referencing these from an external source over committing them; bundled binaries add weight and context overhead with no benefit to the agent.

## Capture Intent from Conversation

When a user says "turn this into a skill", extract the workflow from the current conversation before asking questions. Look for:

- Tools used and the sequence of steps taken
- Corrections the user made along the way
- Input/output formats observed
- Patterns that repeated across the conversation

Fill gaps with the user, then proceed to skill creation.

## Writing Effective Descriptions

The description is arguably the single most important part of a skill to get right. It shares a token budget with every other skill's description and is always active in the agent's context.

### Skill Description Checklist

**Create tasks / TODOs for each of the following** and loop over them to improve or provide feedback until the description follows our best practices:

1. **Be concise, keep it tight and focused**. This is _especially_ important for skill descriptions. Skills are for agent consumption, not human; agents don't need verbose prose, they need clear, high-signal instructions and workflows.
2. **Aim for 30-55 words** (and no more than 65!) which is approximately 1-2 sentences.
3. **Skill descriptions are solely for the purpose of the agent deciding whether to load the skill**. Descriptions should NOT contain instructions for the agent to follow once the skill has been activated, general information about the inner workings of the skill, or any other content that does not help the agent decide whether to load the skill. The description is _not_ a summary of the skill's content, but a guide for when to use it.
4. **Ensure the description is unique.** The description should not clash or be confused with other skill descriptions in the library. See "Check for Description Trigger Conflicts" below to compare it against every existing skill.
5. **Use imperative phrasing**. Frame the description as an instruction to the agent: Use this skill when rather than This skill does. The agent is deciding whether to act, so tell it when to act.
6. **Focus on user intent, not implementation**. Describe what the user is trying to achieve, not the skill's internal mechanics. The agent matches against what the user asked for.
7. **Front-load the leading word**. The description is where a leading word does its invocation work, so lead with it. If the same word lives in the user's prompts, docs, and code, invocation lands harder.
8. **One trigger per branch, no synonym padding**. Give one trigger for each distinct branch the skill handles; synonyms that rename a single branch are duplication that spends context without widening coverage. Cut identity already stated in the skill body.

### Check for Description Trigger Conflicts

A description is a discovery trigger: the agent picks a skill by reading descriptions and matching them to the request. Two skills conflict when an agent, reading both triggers, cannot reliably tell which one a request should load. That is the only thing this check looks for - skills covering related ground are fine and expected.

To check a new or edited description against the rest of a skills library, list every skill's directory, name, and description, then compare:

```bash
python3 scripts/list_descriptions.py path/to/skills
```

It is standard-library Python (no PyYAML, ripgrep, or yq), so it runs against any skills directory. Group skills that share a verb or object (create/edit, diagram, review, test), then compare those pairwise - looking for shared intent without a disambiguator, not merely shared words.

A pair is ACCEPTABLE when a clear disambiguator is present in the trigger:

- Different target tool, language, or file type - the agent routes on it. An intentional family on a shared template (go / rust / python: "activate when working on `<language>` projects") is fine; the language is the routing signal, so do not flatten it.
- Different phase or scope of the same activity (plan vs implement; one file vs the whole repo).
- One is a primer or sub-skill the other explicitly names.

A pair is a CONFLICT when:

- The triggers are interchangeable: either could match the same request equally.
- One description is a verbatim subset of the other with no added distinction.
- They claim the same activity on the same object with no routing signal between them, so it cannot be reasoned when to pick one over the other.

ACCEPTABLE - near-identical wording, but the tool name routes cleanly:

> mermaid-diagrams: "...creating or updating mermaid diagrams. Provides guidance on mermaid best practices."
> excalidraw-diagrams: "...create or update Excalidraw diagrams. Provides guidance on Excalidraw best practices."

CONFLICT - one trigger is a verbatim subset of the other, with no distinguishing "use when":

> domain-model: "Grilling session that challenges your plan against the existing domain model. Use when user wants to stress-test a plan against their project's language..."
> grill-with-docs: "Grilling session that challenges your plan against the existing domain model..." (identical opening, no distinguishing trigger)

On a real conflict, pick the lightest fix that restores routing: sharpen one description's "use when" to name what is distinct, narrow one skill's scope, or merge the two if they are genuinely the same skill. Do not rewrite descriptions that already route cleanly just because they read alike.

### Testing Skill Triggering

A skill activates purely on its `description`. To measure whether a description fires on the right requests and stays quiet on the rest - especially when over- or under-triggering is a risk - write trigger evals: realistic queries, each labelled with whether the skill should activate, scored against the live description.

Place an eval set at `evals/<set>.json` beside the skill and run it with the bundled `scripts/eval_triggering.py`. **Read `references/trigger-evals.md`** before writing or running skill evals.

---

## Skill Writing Tips

- **Don't state the obvious.** the agent already knows a lot about coding and has default opinions. Focus skill content on information that pushes the agent **out of** its normal way of thinking. If the agent would reliably do the right thing without your skill, that content is wasting tokens.
- **Knowing is not doing - keep process even when the agent knows the steps.** The test for cutting content is not "does the agent know this?" but "would the agent reliably do this, in this order, every time, without being told?" Declarative knowledge that lives in training data (how a well-known API behaves, what a design pattern is, standard language syntax) is recalled reliably, so restating it wastes tokens - cut it. A required workflow is different: the agent may know each step yet still default to its own approach or skip the sequence unless the skill commits it to that process. Enforcement, ordering constraints, gates, and checklists earn their tokens by changing what the agent _does_, not by teaching it something new.
- **Build a Gotchas section.** The highest-signal content in any skill is a Gotchas section listing common failure points the agent hits when using the skill. Build this up from real failures over time. A good Gotchas section often delivers more value than pages of general instructions.
- **Avoid railroading the agent.** Because skills are reusable across many different prompts and contexts, being too specific in instructions backfires. Give the agent the information it needs, but leave flexibility to adapt to the situation. Overly rigid instructions (heavy MUSTs, exact step sequences) break when the context shifts even slightly.
- **Build with sub-agents in mind.** Sub-agents parallelise independent work and keep bulky intermediate output out of the main conversation. Where a skill's workflow has steps that could fan out - per-item passes, independent research questions, read-only sweeps - mark the hand-off: what each sub-agent needs, and what it should return (a summary, a verdict, a file path; not a raw dump). Suggest fan-out points rather than prescribing orchestration; the model running the skill may coordinate sub-agents better than the one authoring it today.
- **Think through the setup.** Some skills need user-specific configuration (e.g. which Slack channel, which database, API keys). Pattern: on first run, check for a config file; if missing, ask the user and store their answers. This avoids hardcoding values that differ per user or environment.
- **Avoid pink elephant guidance.** Naming specific unwanted behaviour activates it. For example saying "Never use the word delve" may plant the concept and result in the AI using it. Prefer positive instructions stating the desired behaviour. If you must prohibit something, pair it with the concrete alternative so the agent has somewhere to land. Specific banned-item lists (e.g. exact phrases to avoid) are fine when paired with replacements.
- **Steer with leading words.** Pick one pretrained, meaning-dense term per concept and repeat it throughout (always "field", not a mix of "field", "box", "element"); the agent echoes the term in its reasoning and the prior it carries steers behaviour. **Read `references/steering.md`** whenever a skill won't comply (the agent ignores an instruction, skips or finishes a step early), when you are choosing or strengthening a leading word, or when a skill has multi-step procedures that need completion criteria - it covers leading words, completion criteria, and defending against premature completion.
- **Make task-tracking the first step of any encoded workflow.** When a skill encodes a multi-step workflow, write its first step as an instruction to the agent: create a task (todo) for each step of the workflow, then work them to completion. The visible checklist keeps the agent on task and improves completeness - the same defence against premature completion this primer applies to itself (see "Track Each Step as a Task").
- **Co-locate a concept's parts.** Keep a concept's definition, rules, and caveats under one heading rather than scattered, so reading one part brings its neighbours. The test: a skill should read like documentation written for the agent. This differs from duplication (one meaning repeated in two places); scattering fragments a single meaning across many.
- **Do not add inline scripts within markdown.** Single commands / simple one liners are fine, but scripts should be their own files.
- Avoid deeply nested references.
- For reference files (`references/*.md`) longer than 100 lines, include a concise table of contents at the top. This ensures the agent can see the full scope of available information even when previewing with partial reads.

### Writing Scripts

When a skill bundles scripts:

- **Solve, don't punt.** Handle error conditions in the script rather than failing and leaving the agent to improvise. A script that creates a missing file or falls back to a sensible default is more reliable than one that throws.
- **No voodoo constants.** Justify and document config values in a comment. If you can't explain why a timeout is 30s, the agent can't either.
- **State execution intent.** Make clear whether to run the script ("Run `extract_fields.py` to pull form fields") or read it as reference ("See `extract_fields.py` for the extraction algorithm"). Execution is usually preferred.
- **Lean on the standard library; declare real deps inline.** A stdlib-only script runs anywhere with no setup, so prefer it. When a script genuinely needs a third-party package, run it with `uv` and declare the dependency in [PEP-723](https://peps.python.org/pep-0723/) inline metadata at the top of the script - the dependency then travels with the file instead of relying on the environment being pre-provisioned.

### Token Budget Guidance

The context window is a shared resource. Only add context the agent (frontier models) doesn't already have. Challenge each piece: "Does the agent really need this?" and "Does this justify its token cost?"

Validating a skill with `scripts/validate_skill.py` (resolve it from this skill's `scripts/` directory) reports a token count and budget rating alongside the spec checks. It counts only the Markdown that SKILL.md actually references (transitively), so a stray unreferenced file does not inflate the figure. It does not run automatically - invoke it against a skill when you want a measurement:

```bash
uv run <skill-creator-primer>/scripts/validate_skill.py <skill-dir>
```

The count uses a chars/4.12 heuristic calibrated against tiktoken; add `--tiktoken` (run via `uv run --with tiktoken`) to count with the real tokeniser instead.

| Rating | Tokens |
| ------ | ------ |
| Great  | 1k-5k  |
| Good   | 5k-9k  |
| OK     | 9k-12k |
| Poor   | 12k+   |

Aim for <4k tokens in the main SKILL.md. Move detailed content to reference files.

### Examples

Good example (concise, actionable):

```
## Extract PDF text

Use pdfplumber for text extraction:

`python scripts/extract_pdf_text.py <pdf-file>`

```

Bad example (verbose):

```
## Extract PDF text

PDF (Portable Document Format) files are a common file format that contains
text, images, and other content. To extract text from a PDF, you'll need to
use a library. There are many libraries available for PDF processing, but
pdfplumber is recommended because it's easy to use and handles most cases well.
First, you'll need to install it using pip. Then you can use the code below...
```

---

## Failure Modes

A big or unreliable skill is a symptom. Diagnose it against these five named modes, each with its cure. Two distinctions to hold: _relevance_ asks whether a line still bears on the task; _no-op_ asks whether it changes behaviour versus the default - a line can be relevant and still a no-op. And the no-op test is model-relative, settled by running the skill, not by debate.

| Failure mode | What it is | Cure |
| ------------ | ---------- | ---- |
| Premature completion | Ending a step before it's done | Sharpen the completion criterion; then hide later steps (see `references/steering.md`) |
| Duplication | The same meaning in more than one place | One source of truth per step and per reference item |
| Sediment | Stale layers that accumulate because adding feels safer than deleting | A pruning discipline: restructure into branches, then delete what no branch needs |
| Sprawl | Simply too long, even when every line is live and unique | Progressive disclosure: split by branch (the branch test under "How Skills Actually Work") or into a separate sequenced skill |
| No-op | A line the model already obeys by default | A stronger leading word, or deletion (apply the deletion test) |

## Self-Review Protocol

When a skill spans many files, fan the per-file read-only passes out to sub-agents in parallel (each reviews its own reference files for low-value prose and within-file repetition, returning a summary) - this is safe because reads don't collide. Cross-file checks like duplication between SKILL.md and reference files can't be split this way, since each agent sees only its slice; have the main agent reconcile those from the returned summaries. Keep edits to a single agent, or give each sub-agent a non-overlapping set of files to avoid clobbering each other's writes.

After creating or updating a skill, always perform a critical self-review. **Create and complete tasks / TODOs for each of the following**:

1. Check for duplicated information across SKILL.md and reference files
2. Remove low-value prose, filler, and fluff. Apply the **deletion test** to suspect lines: cut the passage and ask whether the agent's behaviour would change. If it wouldn't, the line is a no-op - leave it deleted (see "Failure Modes" for what counts as a no-op).
3. Thin the language - make important information prominent while reducing word count
4. Verify the description is concise (short) yet comprehensive enough for triggering (see the Writing Effective Descriptions checklist)
5. Decide the invocation mode (see "Invocation mode is a trade-off"). If the skill is clearly one the agent should discover mid-task, leave it model-invoked; if it's needed only occasionally and the user will reach for it, set `disable-model-invocation: true` to keep its description out of every session. In doubt, present the user both options with a one-line pro/con each and let them choose.
6. Ensure no extraneous files were created
7. Frame guidance positively to avoid the pink elephant effect (see Skill Writing Tips). Rewrite "don't do X" as "do Y", or pair the prohibition with the concrete alternative
8. Deterministic tools are used for deterministic outcomes. If a script can perform a task, have the agent call that script rather than relying on interpreted instructions.
9. If the skill has evals, the evals are up to date and run without issue.

**Verbosity is not rewarded - knowledge quality is.**

---

## Validating a Skill

Validate against the official Agent Skills specification:

`uv run scripts/validate_skill.py <skill-directory>`

Pass a real path, not `.` (skills-ref matches the directory's basename against the skill name, and `.` resolves to an empty basename). On a valid skill it also prints a token-budget estimate across the Markdown that SKILL.md transitively references, with a Great/Good/OK/Poor rating (see "Token Budget Guidance" for the `--tiktoken` option).

---

Reference agent skills specification (only use if required): https://agentskills.io/specification
