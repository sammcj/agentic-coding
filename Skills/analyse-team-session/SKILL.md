---
name: analyse-team-session
description: Use when reviewing an agent team session export for quality, when asked to "analyze this team session", "review my agent team run", "what went wrong with this session", "how can I improve my agent team usage", or when provided a markdown team session transcript and asked for feedback on agent teams effectiveness.
---

# Analyse Team Session

Analyse an agent team session export against the official Claude Code agent teams best practices. Produce a structured report with a suitability verdict, scorecard, actionable recommendations, and an improved prompt rewrite.

**Core Principle**: Every recommendation must cite a specific best practice from the official docs and quote specific evidence from the session. No vague assessments.

## When to Use

- User provides a team session export and wants feedback
- User asks how to improve their agent team usage
- User wants to know if a task was a good fit for agent teams
- After running an agent team, to identify what to do differently next time

Do NOT use for:
- Analysing solo (non-team) Claude Code sessions
- General Claude Code usage advice unrelated to agent teams

## Workflow

### Step 1: Read the session export

Read the full markdown session export file. If too large, read in chunks.

Extract these elements:

- **Team name** and session ID
- **Duration** and agent list
- **Original user prompt** - the first user message that kicked off the team
- **Team structure** - lead + teammates, their roles, models used
- **Task list** - tasks created, assigned, completed (look for TaskCreate/TaskUpdate calls)
- **Communication flow** - DMs between teammates (SendMessage calls), broadcasts
- **Tool calls** - what each agent did (reads, edits, web fetches, etc.)
- **Final output** - what the lead produced as the end result

### Step 2: Fetch the official documentation

Fetch the latest agent teams best practices using WebFetch:

1. `https://code.claude.com/docs/en/agent-teams` - best practices, when to use, architecture, limitations
2. `https://code.claude.com/docs/en/costs` - the "Agent team token costs" and "Manage agent team costs" sections

These are the authoritative source for all rubric evaluations. If WebFetch fails, inform the user that analysis cannot proceed without the official docs.

### Step 3: Evaluate against the rubric

Apply each of the 8 categories below. For each one:

- **Rate it**: Gap (not followed), Partial (attempted but incomplete), or Strong (well-executed)
- **Quote evidence**: Cite specific passages from the session export
- **Explain**: Reference the specific best practice from the official docs

#### 1. Suitability

Was this task a good fit for agent teams? Compare against the official "When to use agent teams" criteria:

- Does it involve parallel exploration that adds real value?
- Do agents need to communicate with each other, not just report back?
- Does it match strong use cases (research/review, new modules, competing hypotheses, cross-layer coordination)?
- Or does it match anti-patterns (sequential tasks, same-file edits, heavy dependencies)?

If the task would have been better served by subagents or a single session, say so directly and explain why.

#### 2. Context Sharing

Did teammates get enough context in their spawn prompts? The docs say to "include task-specific details in the spawn prompt" because teammates don't inherit the lead's conversation history.

- Were spawn prompts specific about what to do, where to look, and what format to report in?
- Or were they vague, forcing teammates to spend turns figuring things out?

#### 3. Task Sizing

Were tasks appropriately scoped? The docs define three buckets:

- **Too small**: coordination overhead exceeds the benefit
- **Too large**: teammates work too long without check-ins, increasing risk of wasted effort
- **Just right**: self-contained units that produce a clear deliverable

The docs suggest 5-6 tasks per teammate keeps everyone productive and lets the lead reassign work if someone gets stuck.

#### 4. Communication Quality

Did teammates communicate in ways that added value? This is the core differentiator from subagents.

- Did teammates share findings with each other?
- Did any teammate challenge or build on another's findings?
- Was there genuine cross-pollination, or did they work in isolation?

If teammates never messaged each other, the task could have used subagents instead - flag this.

#### 5. File Conflict Avoidance

Did the task structure avoid multiple teammates editing the same files? The docs warn that two teammates editing the same file leads to overwrites.

If this was a review/research task with no file edits, mark as N/A and note why.

#### 6. Lead Orchestration

Did the lead delegate effectively? The docs warn that the lead sometimes starts implementing tasks itself instead of waiting for teammates.

- Did the lead create tasks, assign them, and wait for results?
- Or did it start doing work itself?
- Did it synthesise findings from all teammates into a coherent output?

#### 7. Cost Efficiency

Were costs managed appropriately? The docs recommend:

- Use Sonnet for teammates (balances capability and cost)
- Keep teams small (token usage is roughly proportional to team size)
- Keep spawn prompts focused (everything in the prompt adds to context from the start)
- Clean up teams when work is done (idle teammates continue consuming tokens)

#### 8. Cleanup

Was the team properly shut down and cleaned up? The docs say to always use the lead to clean up and to shut down teammates first via shutdown requests.

- Were teammates gracefully shut down?
- Did the lead run team cleanup?
- Or did the session end with no cleanup?

### Step 4: Write the analysis report

Save the report to `.claude/output/<team-name>-analysis.md`. Actionable content comes first, detailed evidence last.

Use this structure:

```
# Agent Team Session Analysis: <team-name>

**Session:** <session-id> | **Team:** <team-name>
**Duration:** <duration> | **Agents:** <comma-separated list>
**Analysis date:** <today's date>

---

## Suitability Verdict

[1-2 paragraphs assessing whether this task was a good fit for agent teams.
If not, explain what approach would have been better and why. Be direct.]

**Verdict:** Good fit / Marginal fit / Poor fit

---

## Summary

| Category | Rating |
|----------|--------|
| Suitability | [Strong/Partial/Gap] |
| Context Sharing | [Strong/Partial/Gap] |
| Task Sizing | [Strong/Partial/Gap] |
| Communication Quality | [Strong/Partial/Gap] |
| File Conflict Avoidance | [Strong/Partial/Gap/N/A] |
| Lead Orchestration | [Strong/Partial/Gap] |
| Cost Efficiency | [Strong/Partial/Gap] |
| Cleanup | [Strong/Partial/Gap] |

---

## Top Recommendations

[3-5 recommendations ranked by impact. Each must be specific, actionable,
and reference what happened in the session.]

1. **[Category]** - [Recommendation with concrete example of what to change]
2. ...

---

## Improved Prompt

If the original prompt could be rewritten following all best practices,
here's what it would look like:

[Rewrite the user's original prompt incorporating all recommendations.
This should be ready to copy-paste for their next run.]

---

## Detailed Rubric Scorecard

### 1. Suitability - [Rating]

**Evidence:**
> [Quoted passages from the session export]

**Assessment:** [Explanation referencing specific best practice from the docs]

### 2. Context Sharing - [Rating]

**Evidence:**
> [Quoted passages]

**Assessment:** [Explanation]

[...continue for all 8 categories...]
```

After writing the report, tell the user where it was saved and give a 2-3 sentence summary of the key findings.

## Quality Checklist

- [ ] All 8 rubric categories evaluated with evidence and doc references
- [ ] Suitability verdict is direct and honest (not hedging)
- [ ] Recommendations are specific and actionable (not "improve communication")
- [ ] Improved prompt is a complete, ready-to-use rewrite
- [ ] Every rating cites a specific passage from the session export
- [ ] Every assessment references a specific best practice from the official docs
- [ ] Report saved to `.claude/output/<team-name>-analysis.md`

## Common Pitfalls

1. **Vague ratings**: Saying "Communication was Partial" without quoting the actual messages (or lack thereof). Always cite evidence.
2. **Hedging the verdict**: If it was a poor fit for agent teams, say so. The point of the analysis is honest feedback, not diplomacy.
3. **Generic recommendations**: "Improve task sizing" is useless. "Split the single review task into 3 focused sub-tasks (voice, engagement, accuracy) with 2-3 checkpoints each" is actionable.
