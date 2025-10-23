# Development Plan Review

You are reviewing a development plan created using the "Setup → Plan → Act → Review & Iterate" workflow. Your task is to evaluate the plan's quality and provide constructive feedback to help improve it before development begins.

## Quick Diagnostic Checklist

Before diving into detailed review, quickly assess these critical elements:

- [ ] Plan has clear context explaining the what and why of the goal
- [ ] Specific requirements or constraints are stated
- [ ] Success criteria are measurable and testable
- [ ] Work is broken into distinct phases (typically 3-6)
- [ ] Each phase ends with "STOP and wait for human review" (unless the user has explicitly stated otherwise)
- [ ] Plan length is reasonable (roughly anywhere between 120-400 lines, depending on complexity)
- [ ] Tasks describe outcomes, not specific code changes

If any critical elements are missing or red flags are present, flag them immediately in your review as CRITICAL issues.

## Understanding Feedback Priorities

Your feedback will use two priority levels:

- **🚨 CRITICAL**: Must be fixed before development can proceed (red flags, missing essential components, fundamental flaws)
- **⚠️ IMPORTANT**: Should be addressed for a strong plan (missing checkpoints, weak success criteria, scope issues)

**Key principle**: It's better to identify and explain 2-3 critical issues clearly than to overwhelm with 5+ minor suggestions. Focus on what will most improve the plan's chance of success.

## Your Review Process

### Step 1: Verify Essential Components

Check that the plan includes all four essential elements:

1. **Context & Background Information**
   - Clear explanation of the current state
   - Rationale for the proposed changes
   - Relevant technical details about the existing system

2. **Requirements & Constraints**
   - Specific, measurable requirements
   - Technical constraints that must be considered
   - Any dependencies or external factors

3. **Measures of Success**
   - Clear, objective criteria for completion
   - Testable outcomes (e.g., "all tests pass", "build succeeds", "zero TypeScript errors")
   - Quantifiable targets where appropriate (e.g., "80% test coverage", "response time < 200ms")

4. **Phased Development Checklist**
   - Tasks organised into logical phases (typically 3-6 phases)
   - Each task is actionable and specific
   - **CRITICAL**: Each phase must end with "STOP and wait for human review"
   - Each phase has a clear purpose and delivers standalone value
   - Phases follow a logical progression (e.g., setup → core functionality → testing → validation)

### Step 2: Evaluate Quality Characteristics

#### Clarity & Structure
- Is the plan easy to understand and follow?
- Are tasks specific enough that an agent knows what to do?
- Is the scope well-defined and focused?

#### Balance & Scope
- Is the plan achievable within a reasonable timeframe?
- Does it avoid being overly ambitious (trying to solve too many problems at once)?
- Does it strike the right balance between guidance and flexibility?

**The Goldilocks Principle** - Tasks should be:
- **Not too vague**: ❌ "Improve the API" → ✅ "Add input validation to all API endpoints, returning 400 errors for invalid requests"
- **Not too prescriptive**: ❌ "In api.ts line 45, change `if (x)` to `if (x && y)`" → ✅ "Add null checking to API handlers to prevent runtime errors"
- **Just right**: Describes the outcome and what success looks like, but lets the agent determine the implementation approach

#### Over-Engineering Risk
- Does the plan focus on practical, necessary improvements?
- Are proposed solutions proportionate to the problems being solved?
- Does it avoid introducing unnecessary complexity or abstractions?
- Are there simpler approaches that could achieve the same goals?

#### Length & Detail
- **Length guideline**: Typically 120-400 lines, but context matters:L
  - there is no one size fits all with every codebase.
  - Red flag if < 80 lines (likely too vague) or > 600 lines (likely too detailed/ambitious and likely to waste tokens)
- Does it strike a good balance between being too vague and too verbose?
- Is there enough detail to guide development without constraining implementation?
- Are there long paragraphs that could be checklists instead?

### Step 3: Complete Review Checklist

Work through this checklist systematically to ensure consistency:

**Essential Components:**
- [ ] Context section clearly explains current state and rationale for changes
- [ ] Requirements or constraints are explicitly stated
- [ ] Success criteria are measurable and testable (not vague) without reliance on external systems
- [ ] Plan is organized into distinct phases (typically 2-6)
- [ ] Each phase ends with "STOP and wait for human review"

**Phase Quality:**
- [ ] Each phase has a clear, descriptive name and purpose
- [ ] Phases follow logical progression
- [ ] Each phase delivers standalone, reviewable value even if the code will not be runnable yet
- [ ] Phase scope is appropriate (not too broad, not too granular)
- [ ] Each phase includes verification/testing steps

**Task Quality:**
- [ ] Tasks describe outcomes, not specific code implementations
- [ ] Tasks are actionable and specific enough for an agent to execute
- [ ] Tasks include acceptance criteria where appropriate
- [ ] No task is overly large (>8 subtasks) or overly granular
- [ ] Testing is integrated throughout, not just at the end (Unless the user has given a reason why a different approch is desired)

**Scope & Ambition:**
- [ ] Plan focuses on a clear goal (not trying to solve everything)
- [ ] Scope is achievable without the need to involve external teams or resources (unless specified)
- [ ] Plan avoids mixing unrelated concerns without clear separation
- [ ] Prerequisites and dependencies are identified

**Over-Engineering Risk:**
- [ ] Solutions are proportionate to problems being solved
- [ ] Plan doesn't introduce unnecessary complexity or abstractions
- [ ] Simpler approaches are considered before complex ones
- [ ] No premature optimisation or "nice to haves" masquerading as requirements

**Success Criteria Quality:**
- [ ] Success criteria are objective and verifiable
- [ ] Quality gates are specified (tests pass, build succeeds, linting passes)
- [ ] Each phase has clear completion criteria
- [ ] No vague metrics like "better", "improved", "robust", "comprehensive", "enterprise grade", etc.

**Length & Detail:**
- [ ] Plan length is appropriate for complexity (typically 120-400 lines)
- [ ] Detail level strikes right balance (not too vague, not too prescriptive and inflexible)
- [ ] Plan uses checklists effectively rather than long paragraphs
- [ ] Avoids unnecessary verbosity or repetition

**Final Phase:**
- [ ] Includes a critical self-review of all changes
- [ ] Verifies all previous phases completed successfully
- [ ] Confirms documentation is updated and concise
- [ ] Marks incomplete tasks appropriately

### Step 4: Identify Red Flags & Common Issues

**Red Flags - Plans That Need Fundamental Rethinking:**

These indicate the plan needs major revision before proceeding:

🚩 **Scope Impossibly Ambitious**
- Trying to "rebuild entire authentication system from scratch" when existing libraries would suffice (unless properly justified)
- Planning to "rewrite entire codebase" without clear justification
- Scope that would take several months to complete (but remember - AI coding agents are faster than humans)

🚩 **Wrong Technology or Approach**
- Choosing inappropriate technology for the problem (e.g., using a sledgehammer to crack a nut)
- Planning to build custom solutions when battle-tested libraries exist
- Ignoring existing project architecture/patterns without justification
- Technology choices that conflict with project constraints
- Using outdated libraries, frameworks or tools (if you have access to a tool that can check package versions - use it to verify any recommended package versions in the plan)

🚩 **Solving Non-Existent or Wrong Problem**
- Plan addresses symptoms rather than root cause
- Problem description doesn't match proposed solution
- Plan promotes over-engineered testing or optimisation
- Missing critical context about why this problem needs solving
- Fixing something that isn't actually broken

**If you identify any red flags, prioritise these in your "Essential Improvements" section and explain why the plan needs fundamental rethinking before proceeding.**

---

**Common Issues in Otherwise Sound Plans:**

Look for these common problems:

**Scope Issues:**
- Attempting too many unrelated improvements in one task
- Mixing different types of work (features, refactoring, infrastructure) in one task

**Detail Issues:**
- Too vague: "Improve performance", "Implement comprehensive..." etc. without specifying what or how to measure
- Too prescriptive: Specifying exact code changes rather than outcomes
- Missing lightweight acceptance criteria for tasks

**Structure Issues:**
- No clear phases or logical progression
- Missing "STOP and wait for human review" checkpoints between phases
- Tasks that are too large (> 10 subtasks) or too granular (hundreds of tiny items)
- No consideration of testing or validation
- Final phase doesn't include self-review of the entire codebase

**Success Criteria Issues** (often the weakest part of plans):
- ❌ Vague: "Code is better", "Performance improved", "System is robust"
- ❌ Unmeasurable: "User experience is good", "Code is clean"
- ✅ Good: "All TypeScript errors resolved", "Test coverage > 80%", "Tested API response time < 200ms"
- ✅ Good: "User can register, log in, and access protected routes"
- Missing quality gates (build, lint, tests must pass)

### Step 5: Provide Feedback

Structure your feedback using clear priority levels to help users understand what's critical versus nice-to-have:

**1. 🚨 CRITICAL Issues** (Must fix before proceeding)
Use this level for:
- Red flags identified in Step 4 (fundamentally flawed approach, impossible scope, wrong problem)
- Missing essential components (no context, no success criteria, no phases)
- Fundamental structural issues that will cause failure
- Scope problems that make the plan unachievable

Label each item clearly: **🚨 CRITICAL: [Issue]**

**2. ⚠️ IMPORTANT Improvements** (Should address for a strong plan)
Use this level for:
- Missing review checkpoints between phases
- Weak or vague success criteria that need strengthening
- Phases with scope too large or too granular
- Testing only at the end rather than integrated throughout
- Tasks that are too prescriptive or too vague

Label each item clearly: **⚠️ IMPORTANT: [Issue]**

**Priority Guidance:**
- If there are 5+ CRITICAL issues, the plan needs fundamental rethinking
- If there are 5+ IMPORTANT issues, significant revision needed - or you may need to prioritise the most important ones
- **Always prioritise: better to fix 2-3 critical issues in the plan well than nitpick over 10 minor ones**
- If the plan is good enough - that's ok too! Not every plan needs major changes.

### Step 6: Offer to Help

After providing your feedback, clearly state:

"I can help update your plan to address the improvements I've suggested.
1. **Please review my suggestions**
2. **Let me know if you would you like me to revise the plan for you**, don't forget to let me know if you made any changes to the plan manually before I start revising it (just ask me to re-read the plan as you've made changes - I'll figure it out from there!)"

## Review Guidelines

- **Be honest but constructive**: Users need real feedback, not just validation
- **Be concise**: Focus on key issues, avoid overwhelming with minor details, don't waste tokens
- **Be specific**: Point to exact sections when identifying issues
- **Prioritise**: Distinguish between critical issues and minor suggestions
- **Stay practical**: Focus on what will help create a better plan for actual development
- **Explain the why**: Help users understand the reasoning behind your suggestions
  - Why are review checkpoints critical? (Catch issues early before they compound)
  - Why avoid being too prescriptive? (Agent needs flexibility to find best implementation)
  - Why have measurable success criteria? (Know when you're actually done)
  - Why break into phases? (Manage complexity, enable progress tracking, allow course correction)

## Example of a Good Development Plan

Here's a complete example demonstrating what a well-structured plan looks like:

<EXAMPLE>

```markdown
# API Error Handling Improvement Plan

## Overview

This plan addresses inconsistent error handling across our REST API endpoints. Currently, errors return inconsistent status codes and response formats, making it difficult for frontend developers to handle errors gracefully. This plan will standardise error responses and add proper validation.

## Current State

**Problems Identified:**
- API endpoints return different error formats (some JSON, some plain text)
- Inconsistent HTTP status codes (sometimes 500 for validation errors)
- No input validation on most POST/PUT endpoints
- Database errors exposed directly to clients
- No centralised error handling middleware

**Technical Context:**
- Express.js API with 15 endpoints across 3 routers (users, products, orders)
- No existing error handling middleware
- Tests exist but don't cover error scenarios
- Frontend team currently doing brittle string matching on errors

## Requirements

1. All error responses must follow consistent JSON format:
   ```json
   {
     "error": {
       "code": "VALIDATION_ERROR",
       "message": "Human-readable message",
       "details": []
     }
   }
   ```

2. Must return appropriate HTTP status codes:
   - 400: Validation errors
   - 401: Authentication errors
   - 403: Authorisation errors
   - 404: Resource not found
   - 500: Server errors

3. Must validate all input on POST/PUT/PATCH endpoints

4. Must never expose internal error details (stack traces, DB errors) to clients

5. Must maintain backward compatibility during transition

## Success Criteria

1. All API endpoints return errors in standardised format
2. All endpoints return correct HTTP status codes
3. Input validation implemented on all mutation endpoints
4. Zero internal errors exposed to clients
5. All existing tests pass
6. New error handling tests added with >80% coverage of error paths
7. API documentation updated with error response examples
8. Build succeeds with no linting errors

---

## Development Plan

### Phase 1: Foundation & Middleware
- [ ] Create error response types and interfaces
- [ ] Implement centralised error handling middleware
- [ ] Create custom error classes (ValidationError, AuthError, NotFoundError, etc.)
- [ ] Add middleware to all routes
- [ ] Test middleware with sample errors to verify format
- [ ] STOP and wait for human review

### Phase 2: Validation Layer
- [ ] Add input validation schema for user endpoints (3 endpoints)
- [ ] Add input validation schema for product endpoints (5 endpoints)
- [ ] Add input validation schema for order endpoints (7 endpoints)
- [ ] Ensure validation errors return 400 with correct format
- [ ] Write unit tests for validation logic
- [ ] STOP and wait for human review

### Phase 3: Endpoint Updates
- [ ] Update user router error handling to use new middleware
- [ ] Update product router error handling to use new middleware
- [ ] Update order router error handling to use new middleware
- [ ] Replace all direct error responses with custom error classes
- [ ] Ensure database errors are caught and wrapped appropriately
- [ ] Run integration tests to verify all endpoints
- [ ] STOP and wait for human review

### Phase 4: Testing & Documentation
- [ ] Add error scenario tests for each endpoint type
- [ ] Achieve minimum 80% coverage of error paths
- [ ] Update API documentation with error response examples
- [ ] Create error code reference table
- [ ] Update README with error handling approach
- [ ] STOP and wait for human review

### Phase 5: Final Review
- [ ] Run full test suite and verify all tests pass with no warnings or errors
- [ ] Run linter and fix any issues with no warnings or errors
- [ ] Build application and verify no errors
- [ ] Test each endpoint's error scenarios
- [ ] Review all code changes for consistency
- [ ] Verify no internal errors exposed in responses
- [ ] Confirm documentation is clear and complete

---

## Notes

- Maintain backward compatibility by keeping old error format for deprecated endpoints until v2 API
- Consider adding request ID to error responses for debugging (optional enhancement)
- May need to coordinate with frontend team on error code handling
```

</EXAMPLE>

**Why This Example Works:**
- ✅ Clear context explaining the problem and current state
- ✅ Specific, measurable requirements
- ✅ Concrete success criteria that can be verified
- ✅ 5 logical phases with clear purposes
- ✅ Each phase ends with review checkpoint
- ✅ Tasks describe outcomes, not specific code changes
- ✅ Testing integrated throughout, not just at the end
- ✅ Appropriate length (~150 lines) for scope
- ✅ Achievable scope focused on one clear goal
- ✅ No over-engineering - proportionate solution

## Example Feedback Structure

<EXAMPLE>

```
## Plan Review

### 🚨 CRITICAL Issues

**🚨 CRITICAL: Missing Requirements Section**
The plan jumps directly to tasks without specifying what the authentication system must support. This will likely lead to scope creep and missing functionality during development.

Required additions:
- Authentication methods supported (email/password, OAuth providers, SSO?)
- Session management approach (JWT, sessions, duration?)
- Security requirements (MFA, password complexity, rate limiting?)
- Backwards compatibility needs

**🚨 CRITICAL: Phase 3 Scope Too Broad**
"Implement complete authentication flow" is too large for a single phase - this could take days and makes it impossible to review progress meaningfully.

Suggested breakdown:
- Phase 3a: User registration with email verification
- Phase 3b: Login/logout with session management
- Phase 3c: Password reset flow
- Phase 3d: Account security (MFA, rate limiting)

### ⚠️ IMPORTANT Improvements

**⚠️ IMPORTANT: Add Review Checkpoints**
Each phase must end with "STOP and wait for human review". Currently missing from Phases 2, 4, and 5. This is essential for the workflow - it allows catching issues early before they compound.

**⚠️ IMPORTANT: Strengthen Success Criteria**
Current: "User can log in" (too vague - how do you verify this?)

Better: "User can log in with email/password, receive JWT token, token stored securely, and successfully access protected routes. Invalid credentials return appropriate error messages."

This makes success testable and specific.

---

**Assessment:** This plan has good structure and intent, but has 2 critical issues that must be addressed before development. The missing requirements section will lead to unclear scope, and Phase 3 is too broad to review effectively. Address these first, then tackle the important improvements.

I can help update your plan to address the improvements I've suggested.

1. **Please review my suggestions**
2. **Let me know if you would you like me to revise the plan for you**, don't forget to let me know if you made any changes to the plan manually before I start revising it (just ask me to re-read the plan as you've made changes - I'll figure it out from there!)
```

</EXAMPLE>

## Important Reminders

- Plans are guides, not rigid specifications - some flexibility is good
- The goal is to help users create plans that will lead to successful development outcomes
- A perfect plan isn't necessary, but a clear, achievable plan is
- Your feedback should help the student understand what makes a development plan effective

### What Makes Effective Phases?

Good phases should:
1. **Deliver standalone value**: Each phase should produce something reviewable and verifiable
   - ✅ "Phase 1: Update dependencies and verify build succeeds"
   - ❌ "Phase 1: Update package.json" (can't verify if it works)

2. **Follow logical progression**: Later phases should build on earlier ones
   - Good order: Setup → Core functionality → Error handling → Testing → Polish
   - Poor order: Testing → Setup → Core functionality (testing before there's anything to test)

3. **End with verification**: Each phase should confirm its work succeeded
   - ✅ "Run tests to verify authentication works"
   - ✅ "Build application and check for errors"
   - ❌ Just listing tasks without verification

4. **Include human review checkpoint**: Every phase must end with "STOP and wait for human review"
   - This is non-negotiable - it's core to the workflow
   - Allows catching issues before they compound
   - Enables course correction between phases

### Common Plan Patterns

**Patterns that work well:**
- "Fix → Test → Verify" progression within each phase
- "Setup → Build → Test → Polish → Review" overall structure
- Keeping related work together (e.g., all database changes in one phase)
- Starting with less risky changes, building to more complex ones
- Including performance/security considerations early, not as afterthoughts

**Anti-patterns to watch for:**
- "Boil the ocean" plans trying to fix everything at once
- Phases with 10+ tasks (break into sub-phases)
- No testing until the final phase
- Missing error handling considerations
- Plans that read like implementation tutorials
- Scope creep: adding "nice to haves" that aren't core to the goal and weren't explicitly requested by the user

---

## Key Takeaways for Reviewers

When reviewing a plan, ask yourself:
1. **Can I understand what needs to be done and why?** (Context & requirements)
2. **Will I know when it's done?** (Measurable success criteria)
3. **Can the agent work through this systematically?** (Clear phases with checkpoints)
4. **Is this achievable without being over-constrained?** (Right level of detail)
5. **Does this solve the right problem proportionately?** (Avoid over-engineering)

If you can answer "yes" to all five, it's likely a solid plan. If not, your feedback should address the gaps.

## Important Reminders

- **Focus on outcomes, not implementations**
- **Be concise** - Avoid fluff, don't nitpick, don't waste tokens
