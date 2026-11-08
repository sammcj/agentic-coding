---
name: grill-me
description: Interview the user relentlessly about a plan, decision, or idea until reaching shared understanding, resolving each branch of the decision tree. Use when user wants to stress-test their thinking, get grilled on a plan or design, or mentions "grill me".
metadata:
  source: Inspired by https://github.com/mattpocock/skills
---

# Grill me

Interview me relentlessly about every aspect of this until we reach a shared understanding. Map this as a **design tree**: every decision branches into the decisions that hang off it.


Work the tree in **rounds**. The **frontier** is every decision whose prerequisites are already settled: the questions you can ask _now_ without guessing at answers you haven't heard yet. Ask the whole frontier in one round: number each question and give your recommended answer. Then wait for the user's answers before the next round.

Each round the user answers reshapes the tree: settled decisions push the frontier outward and unblock questions that depended on them. Recompute the frontier and ask the next round. A question whose answer depends on another question still open in this round belongs to a _later_ round, not this one.


If a _fact_ can be found by exploring the environment (filesystem, tools, etc.), look it up rather than asking me. The _decisions_, though, are mine - put each one to me and wait for my answer.

Finding _facts_ is your job, never the user's. When a frontier question needs a fact from the environment (filesystem, tools, etc.), dispatch a sub-agent with a fresh context window to find it; don't ask the user for anything you could look up yourself. Don't block on it: a running exploration is an unsettled prerequisite, so only the questions downstream of it wait for the sub-agent to report; ask the rest of the frontier now. The _decisions_ are the user's: put each to them and wait.


Use the multiple choice question answer tool for questions with a discrete set of options. For each question, provide your recommended answer, worded so "yes" accepts it.

The session is done when the frontier is empty: every branch of the design tree visited, nothing left silently assumed.

Do not act on it until the user confirms you have reached a shared understanding.
