# Critique: examining the reasoning in a source or article

How to subject a piece of content to critical-thinking analysis - argument structure, hidden assumptions, logical issues, bias risk, internal consistency - and report what holds up and what does not. This is the reasoning-quality counterpart to Audit. Where Audit asks "do the cited `raw/` sources support this article's claims?" (external fidelity), Critique asks "does the reasoning itself hold up?" (internal soundness), independent of whether any source backs it. Critique deliberately does not fact-check empirical claims against the world; that is Audit's job, or the user's. It is read-only and reports its findings; it never rewrites prose (the same authority boundary as Audit and Lint's heuristic checks).

## When to use this

- The user asks to critique, scrutinise, or stress-test the reasoning in a source or an article ("is this argument sound?", "what is this assuming?", "where is the bias here?").
- During Ingest, when a source is persuasive or argumentative rather than factual - an opinion piece, a vendor's case for its product, a strategy memo - and you want the reasoning risks on record before compiling it as if it were settled knowledge. Report them; let the user decide what to do. A common outcome is to attribute the claim rather than assert it, or to log an open question in `gaps.md`.
- During Query, when the user asks you to scrutinise an answer or the reasoning behind a wiki position rather than just retrieve it.
- Before acting on an article's recommendation in a real decision.

It is opt-in and never automatic. It operates on whatever the user points at: a `raw/` source, a `wiki/` article, or content pasted into the conversation. It does not require `raw/` to exist.

## The analysis

Keep the signal-to-noise ratio high: preserve the load-bearing reasoning and the specific flaws that matter, and do not pad the report. Work through the content in this order.

1. **Understand the argument first.** State it as the author would accept. If you cannot, you are not ready to critique - read again.
2. **Identify the core claim(s).** What is actually being asserted? Separate the conclusion from the points that support it.
3. **Examine the evidence offered.** Is it sufficient, relevant, and from credible sources? Judge the support the argument supplies, not whether the claim is true in the world.
4. **Spot logical issues.** Fallacies, unsupported leaps, circular reasoning, false dichotomies, appeals to authority or emotion, hasty generalisations. Empirical claims need evidence; normative claims need justified principles; definitional claims need consistency.
5. **Surface hidden assumptions.** What must be true for the argument to hold that the author never states?
6. **Consider what is missing.** Alternative explanations, contradictory evidence, unstated limitations.
7. **Assess internal consistency.** Does the argument contradict itself?
8. **Weigh the burden of proof.** Who needs to prove what? Is the evidence proportional to how significant or surprising the claim is?
9. **Check for competing priorities.** Were priorities asserted that are in unacknowledged conflict with each other?

## Output structure

Report in conversation using these sections.

**## Summary** - one sentence stating the core claim and your overall assessment of its strength.

**## Key Issues** - bullet the most significant problems, each with a brief note on why it matters. Where an argument is weak, say briefly how it could be strengthened; this separates fixable flaws from fundamental ones. Omit the section entirely if there are no real problems.

**## Questions to Probe** - two to five questions that would clarify ambiguity, test a key assumption, or reveal whether the argument survives scrutiny. Frame them as questions a decision-maker should ask before acting.

**## Bottom Line** - one or two sentences: overall verdict and the actionable takeaway.

## Guidelines

- Assume good faith. At worst people are misinformed or mistaken, not dishonest. Be charitable but rigorous.
- Apply the "so what" test. Even a real flaw only matters if it affects the conclusion or the decision at hand. Prioritise those; do not manufacture disagreement or nitpick.
- Critique the reasoning, not the person.
- Do not fact-check empirical claims unless they are obviously implausible or internally contradictory - that boundary keeps Critique distinct from Audit.
- Distinguish "flawed" from "wrong". Weak reasoning does not make a conclusion false, and a sound-looking argument can still reach a bad conclusion.
- Acknowledge the limits of your own analysis. Flag where your critique rests on an assumption or where you lack the domain context to judge.
- If the argument is sound, say so plainly. Do not invent criticism to fill the template.
- Be direct and concise. State problems without hedging.

## Many targets at once

To critique every article in a topic, or several sources together, dispatch one sub-agent per target in parallel, the way Audit fans out per source (`references/audit.md`). Give each sub-agent one target, this protocol, and the output structure; have it return the four sections. Sub-agents read only - they never edit the wiki. The orchestrator collects the reports and presents them grouped by target, weakest reasoning first.

## What Critique writes

Nothing, by default - like Audit, it is a report. With the user's go-ahead it may:

- **Crystallise** the analysis as a `type: archive` page citing the critiqued article or source, the same way a query answer is crystallised (see Query in SKILL.md). Useful when the critique is itself a durable conclusion worth keeping.
- **Open a gap.** A flagged unstated assumption or an unanswered question the critique surfaced can become a `question` entry in `wiki/gaps.md`, if evidence backs recording it (`references/gaps.md`).
- **Inform an Ingest edit.** If the critique was run on a source mid-ingest, its findings may change how the article is written - attributing a contested claim to its source rather than asserting it, or noting the conflict inline with an evidence chain. The user directs that; Critique itself only reports.

Always append the one-line critique entry to `wiki/log.md` (format in SKILL.md).

## Why no score

The verdict is the four-section report, not a number. A "reasoning quality: 0.7" invents precision the analysis cannot back, the same reason the rest of the skill refuses confidence scores. Point at the specific issue a reader can weigh, not at a float.
