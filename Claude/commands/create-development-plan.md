---
description: Create a development plan
allowed-tools: [Read, Write, Edit, Glob, Bash]
---

# Development Plan Creation

You have been working with the user to understand their goal. Now you will create a structured development plan using a development plan & checklist workflow that can guide development work systematically.

## Your Task

**Step 0: Scope Assessment**

Before creating a plan, you MUST assess whether this work requires a formal development plan and what tier of plan is appropriate.

**Assessment Criteria:**

Ask yourself these questions:

1. **Complexity indicators** - Does this change:
   - Affect multiple subsystems or cross architectural boundaries?
   - Require breaking changes or API modifications?
   - Impact backwards compatibility or existing integrations?
   - Involve complex business logic or security-critical code?
   - Require changes to data models or database schema?

2. **Scope indicators** - Is this:
   - A single-file change with obvious solution?
   - A focused feature within one subsystem?
   - A multi-system feature requiring coordination?
   - An architectural change affecting core patterns?

3. **Scale indicators** - Count the concrete work:
   - How many files will likely be touched? (1-2, 3-10, >10)
   - How many new tests will be needed? (None, few, comprehensive suite)
   - How many subsystems are affected? (1, 2-3, >3)
   - How many integration points need updating? (None, few, many)

**Decision Tree:**

- **No plan needed**: Single file, <5 tasks, obvious solution → Just do the work
- **Micro plan** (target <80 lines): Bug fix, dependency update, simple refactor within single subsystem → Use simplified template
- **Standard plan** (target 100-250 lines): Focused feature, single subsystem with tests, moderate complexity → Full template, 2-4 phases
- **Complex plan** (target 250-400 lines): Multi-system feature, architectural changes, high complexity → Full template, 4-6 phases
- **Too large** (>400 lines projected): Consider splitting into multiple plans or questioning scope with user

**Escalation triggers** - STOP and discuss with user if:
- Involves architectural decisions beyond current scope
- Dependencies on unavailable resources
- Unclear complex requirements that need significant clarification
- Fundamental approach or technology choices are uncertain

Once you've assessed the scope, proceed with the appropriate level of planning.

**Step 1: Gather Context (if working with existing code)**

If there is existing code in the project that may be relevant to the goal and that you haven't already analysed:
1. Read relevant files in the project directory
2. Examine existing documentation (README.md, docs/, CONTRIBUTING.md, etc.)
3. Analyse codebase structure, dependencies, and package versions
4. Identify coding conventions and patterns currently used
5. Review existing tests to understand expected behaviour and testing patterns

**Step 2: Deep Thinking**

Use ultrathink (think deeply) about your understanding of the user's requirements, context, constraints and goal based on your discussion so far and any code/documentation you've reviewed.

Consider:
- What is the actual problem being solved? (Not just symptoms)
- What assumptions am I making that should be validated?
- Are there simpler approaches I haven't considered?
- What could go wrong during implementation?
- Does the proposed solution align with existing architecture?

**Step 3: Create the Plan**

Create a development plan (in `DEVELOPMENT_PLAN.md` unless specified otherwise) that SHALL:
1. Concisely and clearly document what needs to be done and why
2. Break work into checklists within logical, reviewable phases
3. Provide enough guidance without over-constraining implementation
4. Set measurable, objective success criteria
5. Be executable by an AI coding agent in a fresh session without further context other than any existing files in the project
6. Include a "Working Notes" section where the executing agent can track complex issues and troubleshooting attempts
7. Use specification-style language (MUST/SHALL/SHOULD) for requirements and constraints

## Plan Structure

Your plan MUST include these essential components (adjust detail level based on scope tier):

### 1. Overview & Current State

**Overview:**
- What problem are you solving or feature are you building?
- Why does this need to be done? (Business value, technical debt, bug fix, etc.)
- Brief summary of the approach (1-3 sentences)

**Current State:**
- What's the current situation?
- What specific problems or limitations exist?
- Relevant technical context (tech stack, architecture, existing patterns)
- What have you already investigated or learned during discussion?

### 2. Requirements & Constraints

Use specification-style language to make requirements unambiguous:

**Functional Requirements** (What the solution MUST do):
- Use "MUST" for mandatory requirements
- Use "SHOULD" for strongly recommended but not mandatory
- Use "MAY" for optional features
- Example: "The API MUST return 400 errors for invalid input"
- Example: "Error messages SHOULD include field-level validation details"

**Technical Constraints** (What MUST be respected):
- Architectural patterns that MUST be followed
- Compatibility requirements (e.g., "MUST maintain backwards compatibility with v2.x API")
- Performance requirements (e.g., "Response time MUST be <200ms for 95th percentile")
- Security requirements (e.g., "User input MUST be sanitised before database queries")

**Exclusions** (What MUST NOT change):
- Existing APIs that MUST remain unchanged
- Dependencies that MUST NOT be upgraded
- Patterns or approaches that MUST be avoided

**Prerequisites**:
- Dependencies that MUST be available
- Configuration that MUST be in place
- Access or permissions required

**Make every requirement specific, testable, and unambiguous.** Avoid vague statements like "should be robust" or "must be user-friendly".

### 3. Unknowns & Assumptions (only if applicable)

Document what's unclear or assumed - this surfaces gaps early, but keep it relevant and concise:

**Unknowns:**
- Things that may need clarification during development
- Areas where more information would help

**Assumptions:**
- What you're assuming is true for the plan to work
- Dependencies you assume are available
- Expected behaviour based on current understanding

If everything is clear and no assumptions are being made, you can omit this section.

### 4. Success Criteria

Define clear, concise, objective, measurable criteria for completion:

✅ **Good success criteria, e.g:**
- "All TypeScript compilation errors resolved"
- "Test coverage >80% for new error handling code"
- "API response time <200ms for all endpoints"
- "User can register, log in, and access protected routes"
- "Build succeeds with zero warnings or errors"
- "All existing tests pass"

❌ **Avoid vague criteria, e.g:**
- "Robust/comprehensive/enterprise-grade solution"
- "Good user experience"

**Include quality gates:**
- Linting must pass without warnings or errors
- All tests must pass locally without depending on external services
- Build must succeed

### 5. Development Plan (Phased Checklist)

Break the work into **2-6 logical phases** that:
- Contain a checklist of tasks (and subtasks if required)
- Follow a clear progression (lint -> build → test → critical self review & fixes -> human review and approval)

**For each phase:**
- Give it a clear, concise and descriptive name
- List 3-8 specific tasks (if more, break into sub-phases)
- Describe **outcomes**, not specific code changes
- Include verification/testing steps
- Add a "Perform a critical self-review of your changes and fix any issues found" task
- **End each phase with "STOP and wait for human review"** (unless user explicitly requested otherwise)

## The Goldilocks Principle

Tasks should describe **what** needs to be achieved, not **how** to implement it:

❌ **Too Vague:**
- "Improve the API"
- "Fix performance issues"
- "Add better error handling"

❌ **Too Prescriptive:**
- "In api.ts line 45, change `if (x)` to `if (x && y)`"
- "Create file called UserService.ts with methods getUser(), createUser(), deleteUser()"
- "Use exactly this code: [code snippet]"

✅ **Just Right:**
- "Add input validation to all API endpoints, returning 400 errors for invalid requests"
- "Add null checking to API handlers to prevent runtime errors"
- "Implement centralised error handling middleware for consistent error responses"

**The sweet spot:** Specific enough that an agent knows what success looks like, flexible enough that the agent can determine the best implementation approach.

## Phase Design Guidelines

### Good Phase Structure

Each phase should:

1. **Have a clear purpose**
   - ✅ "Phase 1: Foundation & Dependencies"
   - ❌ "Phase 1: Various updates"

2. **Deliver reviewable value**
   - ✅ "Update dependencies and verify build succeeds"
   - ❌ "Update package.json" (can't verify it works yet)

3. **Follow logical order**
   - e.g. Setup → Core functionality → Error handling → Testing → Review

4. **Include verification**
   - ✅ "Run tests to verify error handling works correctly"
   - ✅ "Build application and confirm no errors or warnings"
   - ❌ Just listing tasks without verification

5. **End with review checkpoint**
   - Every phase must include a task: `Perform a critical self-review of your changes and fix any issues found`
   - Every phase must end: `- [ ] STOP and wait for human review`

### Phase Size

- **Too small:** 1-2 trivial tasks per phase (overhead of constant review)
- **Too large:** >10 tasks in a phase (break into sub-phases)
- **Just right:** 3-8 tasks that together achieve a coherent milestone

## Red Flags to Avoid

Before finalising your plan, check you haven't created these problems:

🚩 **Scope Impossibly Ambitious**
- Trying to rebuild entire systems from scratch when simpler or off the shelf solutions exist (unless explicitly requested)
- Multiple unrelated major changes bundled together in a task

🚩 **Wrong Technology or Approach**
- Building custom solutions when battle-tested libraries exist
- Ignoring existing project architecture/patterns
- Using outdated libraries or frameworks (use the tools available to you to check you're recommending the latest stable versions unless the user specifies otherwise)
- Over-engineering simple problems

🚩 **Solving Non-Existent or Wrong Problem**
- Addressing symptoms rather than root causes
- Solution doesn't match the problem described
- Over-engineered testing or premature optimisation

🚩 **Missing Prerequisites**
- Assuming infrastructure/tools that don't exist
- Requiring access not available
- Dependencies on external teams (unless explicitly acceptable)

## Length & Detail Guidelines

Plan length MUST align with scope assessment. Use these tiers:

**Micro Plan (<80 lines):**
- Single subsystem change
- Bug fix or simple refactor
- Simplified structure: Problem → Solution → Tasks → Success Criteria
- 1-2 phases maximum
- Example: Dependency update, simple bug fix, config change

**Standard Plan (100-350 lines):**
- Focused feature within single subsystem
- Moderate complexity with testing
- Full structure with 2-4 phases
- Clear requirements and success criteria
- Example: New API endpoint, UI component, service integration

**Complex Plan (350-600 lines):**
- Multi-system feature
- Architectural changes
- Full structure with 4-6 phases
- Detailed requirements, constraints, and unknowns
- Example: Authentication system, major refactor, new core feature

**Red Flag (>600 lines):**
- Plan is likely too large or too prescriptive
- Consider: Splitting into multiple plans, reducing scope, or discussing with user
- If legitimately complex: Break into sub-projects with separate plans

**Writing Style:**
- Use checklists, not essays
- Be scannable and actionable
- Use specification language for requirements (MUST/SHALL/SHOULD)
- Don't include specific code changes unless necessary (e.g. if you had to research online to understand a complex implementation detail)
- Be concise - don't waste tokens on fluff, but provide enough information that the plan could be provided to a fresh agent in a new session
- Avoid marketing language - focus on technical clarity

## Testing Strategy

**Avoid leaving all testing until the end.** Instead:

- Add testing tasks within each phase where appropriate
- "Fix → Test → Verify" pattern within phases
- Set coverage targets if appropriate (e.g., ">80% for new code")
- Final phase should verify everything together, not be the only testing phase

## Plan Template

Use this structure (scale detail to scope tier):

```markdown
# [Descriptive Plan Title]

## Overview

[What you're building/fixing and why - 2-3 sentences]

## Current State (if applicable)

**Problems Identified:**
- [Concise specific problem 1]
- [Concise specific problem 2]

**Technical Context:**
- [Tech stack details with verified to be up to date package versions if adding or changing dependencies]
- [Existing architecture/patterns]
- [Relevant constraints]

## Requirements

**Functional Requirements:**
1. [The system MUST...]
2. [The API SHOULD...]
3. [Users MAY...]

**Technical Constraints:**
1. [Solution MUST maintain backwards compatibility with...]
2. [Response time MUST be <Xms for...]
3. [Code MUST NOT...]

**Prerequisites:**
1. [Dependency X version Y.Z MUST be available]
2. [Access to Z MUST be configured]

## Unknowns & Assumptions (if applicable)

**Unknowns:**
- [Things that are unclear and may need clarification during development]
- [Areas where more information would be helpful]

**Assumptions:**
- [What we're assuming is true for this plan to work]
- [Dependencies we assume are available]
- [Behaviour we're assuming based on current understanding]

## Success Criteria

1. [Measurable criterion 1]
2. [Measurable criterion 2]
3. [Quality gate: linter passes]
4. [Quality gate: tests pass]
5. [Quality gate: build succeeds]
6. [Quality gate: human review]

---

## Development Plan

### Phase 1: [Descriptive Phase Name]
- [ ] [Outcome-focused task 1]
  - [ ] [Subtasks if needed]
- [ ] [Outcome-focused task 2]
- [ ] [Outcome-focused task 3]
- [ ] [Verification task]
- [ ] Perform a critical self-review of your changes and fix any issues found
- [ ] STOP and wait for human review

### Phase 2: [Descriptive Phase Name]
- [ ] [Outcome-focused task 1]
- [ ] [Outcome-focused task 2]
- [ ] [Outcome-focused task 3]
- [ ] [Verification task]
- [ ] Perform a critical self-review of your changes and fix any issues found
- [ ] STOP and wait for human review

[Continue with additional phases...]

### Phase [N]: Final Review
- [ ] Run full test suite and verify all tests pass
- [ ] Run linter and fix any issues
- [ ] Build application and verify no errors or warnings
- [ ] Perform critical self-review of all changes
- [ ] Verify all success criteria met
- [ ] Confirm documentation is updated and concise

---

## Notes

[Any optional notes but do not add potential future enhancements that the user has not requested]

---

## Working Notes (Optional - for executing agent use)

**Purpose:** This section is available for the executing agent to track complex issues, troubleshooting attempts, and problem-solving progress during development.

**When to use:**
- Encountering persistent bugs or issues that require multiple solution attempts
- Tracking what has been tried and ruled out for a specific problem
- Documenting complex debugging steps or investigation findings
- Keeping notes on temporary workarounds or decisions made during implementation

**Format:** Use this space freely - bullet points, links to documentation you found you needed, outstanding error messages, whatever helps track your problem-solving process but try to keep it updated ask you solve issues.

---
```

## Before You Finish

Run through this checklist:

- [ ] Scope assessment completed - tier (micro/standard/complex) is appropriate for the work
- [ ] Plan has clear overview explaining what and why
- [ ] Current state/problems clearly documented
- [ ] Requirements use specification language (MUST/SHALL/SHOULD) and are testable
- [ ] Unknowns and assumptions documented (if applicable)
- [ ] Success criteria are measurable (no vague terms like "better", "improved", "robust")
- [ ] 2-6 logical phases with clear progression (1-2 for micro, 2-4 for standard, 4-6 for complex)
- [ ] Each phase ends with "STOP and wait for human review"
- [ ] Tasks describe outcomes, not code implementations
- [ ] Testing integrated throughout, not just at the end
- [ ] No red flags (reasonable scope, appropriate tech, solving real problems)
- [ ] Length matches tier (<80 micro, 100-350 standard, 350-600 complex)
- [ ] Final phase includes comprehensive review
- [ ] Working Notes section included
- [ ] British / Australian spelling used throughout (NO AMERICAN SPELLING ALLOWED!)
- [ ] Plan is specific enough to guide work but flexible enough to allow good implementation decisions
- [ ] Critical self-review completed (considered design-critic review)

## Critical Self-Review

Before presenting the plan to the user, you MUST perform a critical self-review:

1. **Alignment check**: Does this plan actually solve the user's stated problem? Am I solving symptoms or root causes?

2. **Scope check**: Is the scope realistic and focused, or have I crept beyond the original goal? Does it match my initial scope assessment?

3. **Complexity check**:
   - Does this need a dev plan at all, or is it simple enough to just do?
   - Is the plan tier (micro/standard/complex) appropriate for the work?
   - Am I over-engineering or under-specifying?

4. **Clarity check**: Could a different AI agent read this plan in a fresh session and know exactly what to do? Are requirements unambiguous?

5. **Assumptions check**: Are there hidden assumptions that should be documented in the Unknowns & Assumptions section?

6. **Trade-offs check**: Have I considered alternative approaches? Is this the most proportionate solution?

7. **Red flags check**: Review the "Red Flags to Avoid" section - does your plan have any of these issues?

8. **Design-critic check** (RECOMMENDED): Consider performing a quick design-critic style review your plan before user presentation:
   - Challenge architectural decisions
   - Identify over-engineering or complexity
   - Question technology choices
   - Validate that requirements match the stated problem

If you identify issues during this review, you MUST revise the plan before presenting it to the user.

## After Creating the Plan

Present the plan to the user with the following information (filling in the brackets):

"I've created a [micro/standard/complex] development plan based on our discussion. This plan:
- [Brief 1-line summary of what it achieves]
- Is organised into [N] phases with review checkpoints
- Targets approximately [X] lines and [estimated time] to complete
- Includes a Working Notes section where the executing agent can track complex issues if needed

**Scope tier**: [Micro/Standard/Complex] - [brief justification]

**Next steps:**
1. Please review the plan and either let me know if anything needs adjusting or make any changes you'd like
2. When ready, **start a fresh session** with your AI coding agent and provide them this plan to begin Phase 1

Would you like me to make any changes to the plan?"

## Important Reminders

- **Focus on outcomes, not implementations** - Let the executing agent make good technical decisions
- **Be specific but flexible** - Clear success criteria, flexible approach
- **Avoid over-engineering** - Solve the actual problem proportionately
- **Break into reviewable chunks** - Phases should deliver standalone value
- **Testing throughout** - Not just at the end
- **Use the user's context** - Reference specific files, technologies, and constraints they've requested
- **Be concise** - Avoid fluff, don't waste tokens

Remember: A good plan is clear enough to guide systematic work, but flexible enough to allow the executing agent to make smart decisions about implementation details.
