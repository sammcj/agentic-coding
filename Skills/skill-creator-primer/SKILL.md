---
name: skill-creator-primer
description: Foundational skill-authoring knowledge to use alongside the skill-creator skill. You MUST always load this skill before loading the skill-creator skill, when creating or updating skills.
---

# Skill Creator Primer

Note: If your environment does not have the `skill-creator` skill: Stop and ask the user to run `/plugin marketplace add anthropics/skills` then `skill-creator@claude-plugins-official` before proceeding.

## How Skills Actually Work

Understanding these mechanics helps you design more effective skills.

**Skills are prompt-based context modifiers, not executable code.** When invoked, a skill:

1. Injects instructions into the conversation context (via hidden messages to Claude)
2. Modifies execution context by changing tool permissions and optionally switching models
3. Guides Claude's behaviour through detailed instructions

**Skill selection happens through pure LLM reasoning.** No algorithmic matching, keyword search, or intent classification. Claude reads skill descriptions in the `Skill` tool's prompt and uses language model reasoning to decide which skill matches. This makes the `description` field the single most critical element.

**Claude tends to under-trigger skills.** To combat this, make descriptions slightly assertive about when to activate. Instead of "Build dashboards for data", write "Build dashboards for data. Use this skill whenever the user mentions dashboards, data visualisation, metrics, or wants to display any kind of data."

**Progressive disclosure keeps context lean.** Three-level loading:

1. **Metadata** (name + description) - Always in context (~20-100 words)
2. **SKILL.md body** - Loaded only after triggering (<5k words)
3. **Bundled resources** - Loaded by Claude as needed (unlimited, scripts execute without reading)

The description must be both concise (to fit token budgets shared with all other skills) and comprehensive (to enable accurate selection).

## Degrees of Freedom

Match specificity to the task's fragility and variability:

**High freedom** (text instructions): Multiple approaches valid, decisions depend on context, heuristics guide approach.

**Medium freedom** (pseudocode/parameterised scripts): Preferred pattern exists, some variation acceptable, configuration affects behaviour.

**Low freedom** (specific scripts, few parameters): Operations fragile and error-prone, consistency critical, specific sequence required.

Think of Claude exploring a path: a narrow bridge with cliffs needs guardrails (low freedom), an open field allows many routes (high freedom).

## Claude Code Frontmatter Extensions

These are Claude Code-specific fields not covered by the Agent Skills spec. Only include when specifically needed:

- `argument-hint`: Hint shown during autocomplete for expected arguments, e.g. `[issue-number]` or `[filename] [format]`. Only include if the skill accepts arguments
- `model`: Override the model. Set to `"inherit"` (default) or a specific model ID like `"claude-sonnet-4-6"`. Only include if the user requests it
- `effort`: Override effort level when the skill is active. Options: `low`, `medium`, `high`, `max`. Only include if the user requests it
- `context`: Set to `"fork"` to run in a forked sub-agent context. Useful for skills with extensive exploration or large outputs. Only include if the user requests it
- `disable-model-invocation`: Set to `true` to prevent Claude from auto-loading the skill. Use for side-effect workflows the user should trigger manually. Only include if the user requests it
- `user-invocable`: Skills appear as slash commands by default. Set to `false` to hide from the menu. Only include if the user requests it
- `agent`: Specify agent type (e.g., `"task"`). When omitted, runs in current agent context. Only include if the user requests it
- `allowed-tools`: Space-delimited pre-approved tools. Scope where possible, e.g. `"Read Write Bash(uv run scripts/*.py *) Grep"`

## Token Budget Guidance

The context window is a shared resource. Only add context Claude doesn't already have. Challenge each piece: "Does Claude really need this?" and "Does this justify its token cost?"

If the `ingest` CLI tool is available, use `ingest *.md` to estimate token usage:

| Rating | Tokens |
|--------|--------|
| Great  | 1k-5k  |
| Good   | 5k-9k  |
| OK     | 9k-12k |
| Poor   | 12k+   |

Aim for <4k tokens in the main SKILL.md. Move detailed content to reference files.

## What to Not Include in a Skill

Skills should only contain files that directly support functionality.

**DO NOT** create:

- README.md, CHANGELOG.md, INSTALLATION_GUIDE.md, QUICK_START.md, SUMMARY.md
- User-facing documentation or setup procedures
- Context about the creation process itself
- Fluff, filler, otherwise inconsequential content that doesn't support execution of the skill's function
- A table of contents or index of the skill content within the same file
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

## Self-Review Protocol

After creating or updating a skill, always perform a critical self-review:

1. Check for duplicated information across SKILL.md and reference files
2. Remove low-value prose, filler, and fluff
3. Thin the language - make important information prominent while reducing word count
4. Verify the description is concise (short) yet comprehensive enough for triggering
5. Ensure no extraneous files were created

**Verbosity is not rewarded - knowledge quality is.**

## Writing Tips

**Don't state the obvious.** Claude already knows a lot about coding and has default opinions. Focus skill content on information that pushes Claude *out of* its normal way of thinking. If Claude would do the right thing without your skill, that content is wasting tokens.

**Build a Gotchas section.** The highest-signal content in any skill is a Gotchas section listing common failure points Claude hits when using the skill. Build this up from real failures over time. A good Gotchas section often delivers more value than pages of general instructions.

**Avoid railroading Claude.** Because skills are reusable across many different prompts and contexts, being too specific in instructions backfires. Give Claude the information it needs, but leave flexibility to adapt to the situation. Overly rigid instructions (heavy MUSTs, exact step sequences) break when the context shifts even slightly.

**Think through the setup.** Some skills need user-specific configuration (e.g. which Slack channel, which database, API keys). Pattern: on first run, check for a config file; if missing, ask the user and store their answers. This avoids hardcoding values that differ per user or environment.

Do not add inline scripts within markdown, single commands / simple one liners are fine, but scripts should be their own files.

## Gotchas

**The skill-creator's `quick_validate.py` has an incomplete frontmatter allowlist.** It only recognises Agent Skills spec properties (`name`, `description`, `license`, `allowed-tools`, `metadata`, `compatibility`) and will incorrectly reject valid Claude Code extension fields like `argument-hint`, `model`, `effort`, `context`, `disable-model-invocation`, `user-invocable`, and `agent`. If validation fails on one of these fields, the skill is still valid. Refer to the official docs at https://code.claude.com/docs/en/skills#frontmatter-reference for the authoritative list.

## Validating a Skill

Validate against the official Agent Skills specification:

```bash
uv run scripts/validate_skill.py <skill-directory>
```

---

Reference agent skills specification (only use if required): https://agentskills.io/specification
