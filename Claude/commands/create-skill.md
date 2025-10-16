---
description: Create or edit a Claude Skill with guided assistance and best practices
allowed-tools: [Read, Write, Edit, Glob, Bash]
argument-hint: "[skill-name or path]"
---

# Claude Skill Builder Assistant

You are helping the user create or edit a Claude Code Skill. Skills are modular capabilities that Claude automatically invokes when relevant to the user's request (unlike slash commands which are manually triggered).

## Understanding Skills

**What Skills Are:**
- Autonomous capabilities stored as SKILL.md files with optional supporting files
- Automatically triggered by Claude based on the description matching user requests
- Can be global (also known as personal) (~/.claude/skills/) or project-level (.claude/skills/)

**Skills vs Slash Commands:**
- Skills: Model-invoked automatically when relevant
- Slash Commands: User-triggered manually with /command

**Why Skills Exist:**
Skills extend Claude's capabilities with specialised knowledge or procedures that aren't in the training dataset. They're dynamically loaded only when needed, avoiding the token cost of always having this information in context. This means:
- Skills should include ALL contextual information needed to perform the task
- They provide domain-specific knowledge (APIs, workflows, standards) that would be too large to always include in agent rules
- They enable capabilities that require up-to-date or project-specific information
- The user may provide specialised context or documentation as part of the skill content

Think of skills as "just-in-time" knowledge modules that teach Claude how to handle specific scenarios.

## Initial Discovery Phase

Before creating or editing a skill, ask the user:

1. **Are they creating a new skill or editing an existing one?**
   - If editing: Ask for the skill name or path, and if it's global or in the project, then read the existing SKILL.md file

2. **What task or capability should this skill handle?**
   - Focus on ONE specific capability
   - Understand the user's workflow and pain points

3. **When should Claude invoke this skill?**
   - What keywords or scenarios trigger it?
   - This informs the description field

4. **What scope is needed?**
   - Personal skill (~/.claude/skills/) - just for this user
   - Project skill (.claude/skills/) - shared with team via git

5. **What tools should it use?**
   - Note: You only need to ask which tools to allow if the user or your conversation indicates special tools are needed for the skill
   - Should it be read-only or allow writing?
   - Web access? (WebFetch, WebSearch)

6. **What contextual information is needed?**
   - Does this require domain-specific knowledge not in Claude's training data?
   - Are there specific APIs, workflows, or standards to document?
   - Does the user have documentation or examples to include?
   - What background knowledge is essential for performing this task?

## Where to get more information on skills if required

- https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview
- https://docs.claude.com/en/docs/agents-and-tools/agent-skills/best-practices

## Skill Structure Requirements

### Frontmatter (YAML)

Required fields:
```yaml
---
name: Skill Name Here
description: Third-person description of what the skill does and when to use it
---
```

Optional fields:
```yaml
allowed-tools: [Read, Write, Edit, Bash]  # Restrict tools for security
model: claude-opus-4-20250514  # Override default model if needed
```

### Naming Rules

**name field:**
- Maximum 64 characters
- Use gerund form (verbs ending in -ing): "Processing PDFs", "Analysing Logs"
- **Be specific**, do not use generic or vague names

**description field:**
- Maximum 1024 characters
- Written in third person: "This skill helps..." not "I help..."
- MUST include BOTH:
  - What the skill does
  - When to use it (trigger conditions/keywords)
- Example: "This skill analyses application logs for errors and patterns. Use when debugging issues, investigating failures, or reviewing system behaviour."

## Content Guidelines

### Keep SKILL.md Focused and Concise

- Target: Under 500 lines for SKILL.md
- Every sentence should justify its token cost
- Use progressive disclosure: reference separate files for detailed content
- **Be concise but complete**: Include ALL contextual information needed to perform the task
- If the user has performed research on a specialised domain knowledge or asked you to do so - make sure you provide it in the skill
- Avoid verbosity, but don't omit critical context, terminology, or procedures
- Balance: Concise writing + Complete information = Effective skill

### Specificity Levels

Match detail level to task fragility:

- **High freedom** (flexible tasks): Text instructions, general guidance
- **Medium freedom** (preferred patterns): Pseudocode, workflow steps
- **Low freedom** (error-prone): Specific commands, exact scripts

### Organisation Patterns

If the skill needs extensive content, split into separate files:

**Pattern 1 - Reference Model:**
- SKILL.md: High-level guide
- FORMS.md: Templates and formats
- REFERENCE.md: Detailed documentation
- EXAMPLES.md: Example outputs

**Pattern 2 - Domain Split:**
- SKILL.md: Overview and routing
- finance-data.md: Finance-specific handling
- sales-data.md: Sales-specific handling

**Pattern 3 - Progressive Disclosure:**
- SKILL.md: Basic instructions
- advanced-usage.md: Complex scenarios (referenced when needed)

**Key rule:** Keep references ONE level deep from SKILL.md

### Content to Include

- **Clear workflows**: Sequential steps with validation loops
- **Templates**: Show exact output format expected
- **Examples**: Concrete demonstrations
- **Edge cases**: Common failure scenarios
- **Validation steps**: How to verify success

### Content to Avoid

- Time-sensitive information (dates, versions that change)
- Inconsistent terminology
- Over-general advice that doesn't guide behaviour
- Unnecessary context or background
- Vague names

## Testing Strategy

1. **Create test scenarios FIRST** (before extensive documentation)
2. **Establish baseline**: Try skill with minimal instructions
3. **Iterative refinement**: Add only what's needed to pass tests
4. **Test across models**: Verify behaviour on Haiku, Sonnet, and Opus

## Implementation Steps

Once you understand the requirements:

1. **Check for existing skills**
   - Look in ~/.claude/skills/ and .claude/skills/
   - Avoid duplicating functionality

2. **Draft the frontmatter**
   - Write a compelling, specific description
   - Set appropriate tool restrictions

3. **Write core instructions**
   - Start with essential workflow
   - Use clear, direct language
   - Include examples

4. **Add supporting files if needed**
   - Create separate files for large content
   - Reference them from SKILL.md

5. **Create the skill file(s)**
   - Place in correct directory (personal vs project)
   - Ensure SKILL.md exists with proper frontmatter

6. **Validation checklist:**
   - [ ] Name is gerund form, under 64 characters
   - [ ] Description is third person, under 1024 characters
   - [ ] Description explains BOTH what and when
   - [ ] SKILL.md is under 500 lines
   - [ ] Includes ALL necessary contextual information (APIs, terminology, procedures)
   - [ ] Concise writing without unnecessary verbosity
   - [ ] allowed-tools specified appropriately
   - [ ] Instructions are clear and actionable
   - [ ] Examples provided for complex outputs
   - [ ] British English spelling used throughout

## Examples of Well-Scoped Skills

**Good:** "Processing PDF Documents - Extracts text, tables, and images from PDF files. Use when analysing PDF content, converting documents, or extracting structured data."

**Too broad:** "Helping with Documents - Assists with various document tasks."

**Good:** "Analysing Git History - Reviews commit patterns, identifies contributors, and summarises changes. Use when investigating code evolution, preparing changelogs, or auditing contributions."

**Too narrow:** "Counting Commits - Counts the number of commits in a repository."

## Your Task

Now that you understand skill creation, guide the user through building their skill:

1. Ask the discovery questions above
2. Draft the skill structure based on their answers
3. Show them the complete SKILL.md content
4. Create the file(s) in the appropriate location
5. Provide testing suggestions

Remember: Focus on creating a single, well-defined capability that Claude can reliably invoke when appropriate.
