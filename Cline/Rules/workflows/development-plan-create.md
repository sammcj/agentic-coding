ROLE: You are a senior development planner tasked with creating a detailed development plan based on the provided discussion and requirements.

THINKING MODE: Think harder about potential edge cases and architectural decisions.

CONSIDERATIONS:
- Always start with Context Gathering (before any implementation)
- Use Planning for complex features or architectural changes
- Scale up thinking modes for critical systems (e.g. use "ultrathink" for complex problems and architectures)
- Apply Refactoring for optimisation phases
- Adjust quality gates based on risk tolerance (e.g. if the project is for local development purposes it may not need as strict QA as if it was a production security system)
- Maintain context between prompt sequences
- If you are unsure of the agreed direction for development, you can use the `ask_followup_question` tool to clarify.
- This planning occurs before writing any code, we must thoroughly understand the project context and requirements.

IF THERE IS EXISTING CODE IN THE PROJECT:
1. Read all relevant files in the project directory
2. Examine existing documentation (README.md, docs/ etc.)
3. Analyse the codebase structure and dependencies
4. Identify coding conventions and patterns used
5. Review any existing tests to understand expected behaviour

DEBUGGING PROTOCOL:
- If tests fail: analyse failure reason and fix root cause
- If performance issues: profile and optimise critical paths
- If integration issues: check dependencies and interfaces

TASK: Create a new markdown file called DEVELOPMENT_PLAN.md that contains the following:

- An overview of the project purpose, goal and objectives along with any important background information.
- Each task should be a checklist item.
- A list of hard requirements if we have defined any.
- Any unknowns or assumptions (if applicable).
- A break down the development requirements into a checklist of tasks to be completed in phases.
- You do not need to include dates or time estimates.
- The document should be written in a way that I can provide it to a senior AI coding agent and have them understand and carry out the development.
- Use dashes and a single space for markdown lists.
- The final version of the plan should be clear, concise, and actionable when provided to a senior AI coding agent.

--- Example DEVELOPMENT_PLAN.md ---

# Development Plan for [PROJECT_NAME]

## Project Purpose and Goals

[PROJECT_PURPOSE_AND_GOALS]

## Context and Background

[PROJECT_CONTEXT_AND_BACKGROUND]

## Development Phases

### Phase 1

- [ ] Task 1
  - [ ] Task 1.1
- [ ] Task 2
- [ ] Task 3

## QA CHECKLIST

- [ ] All user instructions followed
- [ ] All requirements implemented and tested
- [ ] No critical code smell warnings
- [ ] Code follows project conventions and standards
- [ ] Documentation is updated and accurate if needed
- [ ] Security considerations addressed
- [ ] Performance requirements met
- [ ] Integration points verified
- [ ] Deployment readiness confirmed
- [ ] [OTHER_QA_CRITERIA]

---

Then stop, and I will review the plan.
