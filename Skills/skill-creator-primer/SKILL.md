---
name: skill-creator-primer
description: Foundational skill-authoring knowledge to use alongside the skill-creator skill. You MUST load this skill before loading the skill-creator skill and whenever creating, updating or improving a skill.
---

# Skill Creator Primer

Note: If your environment does not have the `skill-creator` skill: Stop and ask the user to run `/plugin marketplace add anthropics/skills` then `skill-creator@claude-plugins-official` before proceeding, they may alternatively clone https://github.com/anthropics/skills and link it's `skills` directory to their local skills directory.

## How Skills Actually Work

Understanding these mechanics helps you design more effective skills.

**Skills are prompt-based context modifiers, not executable code.** When invoked, a skill:

1. Injects instructions into the conversation context (via hidden messages to the agent)
2. Modifies execution context by changing tool permissions and optionally switching models
3. Guides the agent's behaviour through detailed instructions

**Skill selection happens through pure LLM reasoning.** No algorithmic matching, keyword search, or intent classification. The agent reads skill descriptions in the `Skill` tool's prompt and uses language model reasoning to decide which skill matches. This makes the `description` field the single most critical element.

**Agents tend to under-trigger skills.** To combat this, make descriptions slightly assertive about when to activate. Instead of "Build dashboards for data", write "Build dashboards for data. Use this skill whenever the user mentions dashboards, data visualisation, metrics, or wants to display any kind of data."

**Progressive disclosure keeps context lean.** Three-level loading:

1. **Metadata** (name + description) - Always in context (~20-100 words)
2. **SKILL.md body** - Loaded only after triggering (<5k words)
3. **Bundled resources** - Loaded by the agent as needed (unlimited, scripts execute without reading)

The description must be both concise (to fit token budgets shared with all other skills) and comprehensive (to enable accurate selection).

## One Skill or Many?

When a user asks for several related skills, prefer a single skill with progressive disclosure over many narrow ones. Every skill's description sits in every agent's context permanently, so each new skill taxes the shared token budget and raises the chance of overlapping or confusable descriptions that misfire.

Merge when the skills share a trigger, a domain, or a workflow: keep one SKILL.md as the entry point and split the variation into `references/` files the agent loads on demand. Split into separate skills only when triggers are genuinely distinct (different user intents that should never co-activate) or when one variant needs different tool permissions or a different model.

Signs of skill creep to push back on: near-duplicate descriptions, a skill that only fires "as part of" another, or a set of skills that always load together.

## Degrees of Freedom

Match specificity to the task's fragility and variability:

**High freedom** (text instructions): Multiple approaches valid, decisions depend on context, heuristics guide approach.

**Medium freedom** (pseudocode/parameterised scripts): Preferred pattern exists, some variation acceptable, configuration affects behaviour.

**Low freedom** (specific scripts, few parameters): Operations fragile and error-prone, consistency critical, specific sequence required.

Think of Claude exploring a path: a narrow bridge with cliffs needs guardrails (low freedom), an open field allows many routes (high freedom).

## Claude Code Frontmatter & Extensions

These are Claude Code-specific fields not covered by the Agent Skills spec. Only include when specifically needed:

- `when_to_use`: Extra triggering context appended to the description in the skill listing (trigger phrases, example requests). Counts toward the 1,536-character description cap. Only include if the description alone underspecifies triggering
- `argument-hint`: Hint shown during autocomplete for expected arguments, e.g. `[issue-number]` or `[filename] [format]`. Only include if the skill accepts arguments
- `arguments`: Named positional arguments for `$name` substitution in the skill body. Accepts a space-separated string or a YAML list; names map to positions in order. Only include if the skill uses named substitutions
- `model`: Override the model. Set to `"inherit"` (default) or a specific model ID like `"claude-opus-4-7"`. Only include if the user requests it
- `effort`: Override effort level when the skill is active. Options: `low`, `medium`, `high`, `max`. Only include if the user requests it
- `context`: Set to `"fork"` to run in a forked sub-agent context. Useful for skills with extensive exploration or large outputs. Only include if the user requests it
- `disable-model-invocation`: Set to `true` to prevent Claude from auto-loading the skill. Use for side-effect workflows the user should trigger manually. Only include if the user requests it
- `user-invocable`: Skills appear as slash commands by default. Set to `false` to hide from the menu. Only include if the user requests it
- `agent`: Specify agent type (e.g., `"task"`). When omitted, runs in current agent context. Only include if the user requests it
- `allowed-tools`: Space-delimited pre-approved tools. Scope where possible, e.g. `"Read Write Bash(uv run scripts/*.py *) Grep WebFetch(domain:code.claude.com)""` (don't use the deprecated `:` syntax, e.g. `Bash(command:*)`, instead use `Bash(command *)`)
- `disallowed-tools`: Tools removed from the available pool while the skill is active (clears on the next user message). Use for autonomous skills that must never call a tool, e.g. `AskUserQuestion` in a background loop. Only include if the user requests it

### Upstream validators may have an incomplete frontmatter allowlist

The `skills-ref` library (and the skill-creator's `quick_validate.py`) may only recognise a subset that the Agent Skills spec documents and may error on every valid Claude Code extension fields: (`when_to_use`, `argument-hint`, `arguments`, `disable-model-invocation`, `user-invocable`, `disallowed-tools`, `model`, `effort`, `context`, `agent`).

The bundled `scripts/validate_skill.py` errors only on genuine spec violations and downgrades unknown-field detection to a warning, so documented extensions pass clean and a field newer than the linter won't block. If you instead run `quick_validate.py` or raw `skills-ref` and it fails only on one of these fields, the skill is still valid. The bundled validator also parses frontmatter with standard PyYAML rather than skills-ref's StrictYAML loader, so flow-style arrays (`allowed-tools: [Read, Write]`) pass instead of failing on a style preference.

Consider the docs https://code.claude.com/docs/en/skills#frontmatter-reference as authoritative.

## Skill File Layout

SKILL.md sits at the skill root. Bundle everything else into one of three directories so the layout is predictable across skills:

- `references/` - Markdown the agent reads on demand (reference material, detailed procedures, lookup tables). This is the progressive-disclosure tier; keep the depth here, not in SKILL.md.
- `assets/` - Files the skill copies or fills in (templates, boilerplate, config skeletons, document scaffolds, fonts, images).
- `scripts/` - Executable scripts the agent runs (`scripts/<name>.py`, `.sh`, etc.).

Put a markdown reference under `references/`, not `scripts/` or the root. Reserve `evals/` for trigger eval sets (see Testing Skill Triggering). Don't invent parallel directory names for the same purpose.

## Cross-Tool Portability

We build primarily for Claude Code, but a skill should work in any agentic coding tool that supports standard Agent Skills. Write to the portable core by default: a `name` and `description`, plain-Markdown instructions, and `references/`, `assets/`, `scripts/` for bundled content. Reserve the Claude Code extension fields above for when the skill genuinely needs them.

`compatibility:` is an optional field in the Agent Skills spec. Leave it out by default - a skill with no such field is assumed portable. Add it ONLY when the skill depends on something a single tool provides (a Claude Code slash-command trigger, a tool-specific frontmatter field, a vendor MCP server), naming that tool so authors and other tools can tell it apart from a portable skill:

```yaml
compatibility: claude-code    # or: github-copilot, microsoft-cowork
```

Name the tool(s) the skill targets. Keep tool-specific behaviour isolated so the portable path still works where the named tool's feature is absent.

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

The skill is for an AI agent to do the job. Auxiliary documentation adds clutter and wastes context.

## Capture Intent from Conversation

When a user says "turn this into a skill", extract the workflow from the current conversation before asking questions. Look for:

- Tools used and the sequence of steps taken
- Corrections the user made along the way
- Input/output formats observed
- Patterns that repeated across the conversation

Fill gaps with the user, then proceed to skill creation.

### Writing Effective Descriptions

The description is arguably the single most important part of a skill to get right.

It shares a token budget with all other skill descriptions and is always active in every agent's context across all conversations and along side other skills.

Below is a checklist of items you should loop through and consider when writing or reviewing a skill description. It is **critical** that you follow these guidelines to both ensure the skill triggers correctly but also that it does not interfere with other skills or bloat the agent's context.

#### Skill Description Checklist

1. **Be concise, keep it tight and focused**. This is _especially_ important for skill descriptions. Skills are for agent consumption, not human, and agent don't need verbose prose, they need clear, high signal instructions and workflows.
2. **Aim for 30-55 words** (and no more than 65!) which is approximately 1-2 sentences.
3. **Skill descriptions are solely for the purpose of the agent to decide whether to load the skill**. Descriptions should NOT contain instructions for the agent to follow once the skill has been activated, general information about the inner workings of the skill, or any other content that does not help the agent decide whether to load the skill. The description is _not_ a summary of the skill's content, but a guide for when to use it.
4. **Ensure the description is unique.** The description should not clash or be confused with other skill descriptions in the library.
5. **Use imperative phrasing**. Frame the description as an instruction to the agent: Use this skill when rather than This skill does The agent is deciding whether to act, so tell it when to act.
6. **Focus on user intent, not implementation**. Describe what the user is trying to achieve, not the skills internal mechanics. The agent matches against what the user asked for.

Loop over this checklist as you improve or provide feedback on a skill description.

#### Testing Skill Triggering

A skill activates purely on its `description`. To measure whether a description fires on the right requests and stays quiet on the rest - especially when over- or under-triggering is a risk - write trigger evals: realistic queries, each labelled with whether the skill should activate, scored against the live description.

Place an eval set at `evals/<set>.json` beside the skill and run it with the bundled `scripts/eval_triggering.py`. Read `references/trigger-evals.md` before writing or running skill evals.

---

## Skill Writing Tips

- **Don't state the obvious.** the agent already knows a lot about coding and has default opinions. Focus skill content on information that pushes the agent **out of** its normal way of thinking. If the agent would reliably do the right thing without your skill, that content is wasting tokens.
- **Knowing is not doing - keep process even when the agent knows the steps.** The test for cutting content is not "does the agent know this?" but "would the agent reliably do this, in this order, every time, without being told?" Declarative knowledge that lives in training data (how a well-known API behaves, what a design pattern is, standard language syntax) is recalled reliably, so restating it wastes tokens - cut it. A required workflow is different: the agent may know each step yet still default to its own approach or skip the sequence unless the skill commits it to that process. The trigger for enforcement, ordering constraints, gates, and checklists earn their tokens by changing what the agent _does_, not by teaching it something new. Cut the knowledge the agent already has; keep the enforcement that changes its behaviour. With this in mind, process guidance should be clear, actionable and concise.
- **Build a Gotchas section.** The highest-signal content in any skill is a Gotchas section listing common failure points the agent hits when using the skill. Build this up from real failures over time. A good Gotchas section often delivers more value than pages of general instructions.
- **Avoid railroading the agent.** Because skills are reusable across many different prompts and contexts, being too specific in instructions backfires. Give the agent the information it needs, but leave flexibility to adapt to the situation. Overly rigid instructions (heavy MUSTs, exact step sequences) break when the context shifts even slightly.
- **Think through the setup.** Some skills need user-specific configuration (e.g. which Slack channel, which database, API keys). Pattern: on first run, check for a config file; if missing, ask the user and store their answers. This avoids hardcoding values that differ per user or environment.
- **Avoid pink elephant guidance.** Naming specific unwanted behaviour activates it. For example saying "Never use the word delve" may plant the concept and result in the AI using it. Prefer positive instructions stating the desired behaviour. If you must prohibit something, pair it with the concrete alternative so the agent has somewhere to land. Specific banned-item lists (e.g. exact phrases to avoid) are fine when paired with replacements.
- **Do not add inline scripts within markdown.** Single commands / simple one liners are fine, but scripts should be their own files.
- **Use consistent terminology.** Pick one term per concept and use it throughout (always "field", not a mix of "field", "box", "element").
- Avoid deeply nested references
- For reference files (`references/*.md`) longer than 100 lines, include a concise table of contents at the top. This ensures the agent can see the full scope of available information even when previewing with partial reads.

Don't assume packages are installed.** List required packages and how to install them. Note that claude.ai can install from npm/PyPI, but the Claude API code execution environment has no network access.

### Writing Scripts

When a skill bundles scripts:

- **Solve, don't punt.** Handle error conditions in the script rather than failing and leaving the agent to improvise. A script that creates a missing file or falls back to a sensible default is more reliable than one that throws.
- **No voodoo constants.** Justify and document config values in a comment. If you can't explain why a timeout is 30s, the agent can't either.
- **State execution intent.** Make clear whether to run the script ("Run `extract_fields.py` to pull form fields") or read it as reference ("See `extract_fields.py` for the extraction algorithm"). Execution is usually preferred.
- **Don't assume packages are installed.** List required packages and how to install them. Note that claude.ai can install from npm/PyPI, but the Claude API code execution environment has no network access.

### Token Budget Guidance

The context window is a shared resource. Only add context the agent (current generation frontier models such as Claude Opus/Sonnet) doesn't already have. Challenge each piece: "Does the agent really need this?" and "Does this justify its token cost?"

If the `ingest` CLI tool is available, use `ingest *.md` to estimate token usage:

| Rating | Tokens |
|--------|--------|
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

```python
python scripts/extract_pdf_text.py <pdf-file>
```
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

## Self-Review Protocol

When a skill spans many files, fan the per-file read-only passes out to sub-agents in parallel (each reviews its own reference files for low-value prose and within-file repetition, returning a summary) - this is safe because reads don't collide. Cross-file checks like duplication between SKILL.md and reference files can't be split this way, since each agent sees only its slice; have the main agent reconcile those from the returned summaries. Keep edits to a single agent, or give each sub-agent a non-overlapping set of files to avoid clobbering each other's writes.

After creating or updating a skill, always perform a critical self-review:

1. Check for duplicated information across SKILL.md and reference files
2. Remove low-value prose, filler, and fluff
3. Thin the language - make important information prominent while reducing word count
4. Verify the description is concise (short) yet comprehensive enough for triggering (see Writing Effective Descriptions checklist)
5. Ensure no extraneous files were created
6. Frame guidance positively to avoid the pink elephant effect (see Writing Tips). Rewrite "don't do X" as "do Y", or pair the prohibition with the concrete alternative
7. If the skill carries trigger evals, confirm the eval set is current and runs cleanly (see Testing Skill Triggering)

**Verbosity is not rewarded - knowledge quality is.**

---

## Validating a Skill

Validate against the official Agent Skills specification:

```bash
uv run scripts/validate_skill.py <skill-directory>
```

Pass a real path, not `.` (skills-ref matches the directory's basename against the skill name, and `.` resolves to an empty basename). On a valid skill it also prints a token-budget estimate across the Markdown that SKILL.md transitively references, with a Great/Good/OK/Poor rating. Add `--tiktoken` (via `uv run --with tiktoken`) to count with the real tokeniser instead of the chars/token heuristic.

---

Reference agent skills specification (only use if required): https://agentskills.io/specification
