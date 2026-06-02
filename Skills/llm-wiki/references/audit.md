# Audit: verifying articles against their sources

How to check that a wiki article's claims are actually supported by the `raw/` sources it cites. This operationalises the "evidence, not confidence" principle: rather than trust a provenance link, read the source and confirm it says what the article claims. Audit is read-only and reports its findings; it never rewrites article prose (the same authority boundary as Lint's heuristic checks).

## When to use this

- After a large or noisy ingest, to confirm load-bearing claims survived compilation intact.
- Before leaning on an article for an important decision.
- Periodically on a topic, the way you would lint, but deeper.
- When Lint flags an archive whose cited sources have changed, or a possible contradiction, and you want to settle it against the raw text.

It is not automatic and not part of every ingest. Auditing reads every cited source in full, so reserve it for the articles that matter.

## Claim extraction

1. Read the target article. List the claims that carry provenance: the headline assertions in Overview and the body sections, every inline quote, and anything a Sources or Raw line is meant to back. Skip generic framing and common knowledge. A labelled edge in a concept map is a claim too - the relationship it asserts between two nodes; list every edge and treat it like any other claim.
2. Map each claim to the `raw/` file(s) that should support it, using the Raw line and any inline raw links. A load-bearing claim with no cited source is itself a finding: the article asserts something its provenance does not cover.
3. Group the claims by the raw file that backs them. Each group becomes one sub-agent task.

## Parallel verification

Dispatch one sub-agent per cited raw source, in parallel. This mirrors the bulk-ingest discipline (`references/bulk-ingest.md`): each sub-agent reads exactly one source and judges only the claims assigned to it, so reads never overlap and the orchestrator aggregates a consistent set of verdicts.

Give each sub-agent:
- The path to the one `raw/` file it owns.
- The list of claims, verbatim from the article, that cite that file (with the locator if the article gives one).
- The verdict schema below, with an instruction to quote the supporting passage and to default to `unsupported` when the source does not clearly back the claim.

Per-claim verdict:

| Verdict | Meaning |
|---------|---------|
| `supported` | The source states or directly entails the claim. Return the passage. |
| `partial` | The source backs part of the claim, or a weaker version of it. Return the passage and say what is missing. |
| `unsupported` | The source does not back the claim, or contradicts it. Say which. |
| `source-missing` | The cited raw file is absent or unreadable. |

Sub-agents read only. They never edit `wiki/`, `raw/`, `index.md`, or `log.md`.

## Aggregation and report

The orchestrator collects the verdicts and reports in conversation, grouped by article, worst verdicts first:
- For every `partial`, `unsupported`, and `source-missing`, show the claim and the passage the source actually contains (or note its absence), so the user can act.
- Give the counts: claims checked, supported, partial, unsupported, source-missing.

Do not rewrite the article. A failed claim is a finding for the user, who directs the follow-up:
- Soften or correct an overstated claim (an Ingest edit, bumping `updated`).
- Supersede the article if a source has moved on (the supersession flow in SKILL.md).
- Accept a `partial` and add the missing qualifier inline.

Append the one-line audit entry to `wiki/log.md` (format in SKILL.md). If the user wants the audit kept, crystallise it as a `type: archive` page citing the audited article, the same way a query answer is crystallised.

## Why categorical verdicts, not scores

A verdict points at a passage the reader can check; a number like `0.72` cannot be checked and invents precision the evidence does not have. This is the same reason the rest of the skill refuses confidence scores. The audit's job is to surface the passage, not to grade it.
