# High-fidelity ingest for long-form and noisy sources

How to compile a transcript, chat log, long article, or interview into the wiki without silently dropping or softening the detail that makes it worth keeping. Compiling a long source straight to prose is where load-bearing claims, exact numbers, and named entities quietly disappear. These steps are a checklist against that.

## When to use this

Reach for it when one compile pass could lose detail: meeting and call transcripts, chat and Slack logs, long articles and threads, interview or research notes. Skip it for short, clean, single-claim sources (a release note, a definition, a one-page post); the normal Compile in SKILL.md already handles those, and the extra discipline is overhead there.

## The steps

1. **Extract atoms before prose.** Read the source once and pull the durable items into a flat list first: decisions, commitments, claims, numbers, named entities, open questions, action items. Note where each came from. Only then write the article from that list. The atom list is the checklist that catches what writing-from-memory drops.

2. **Right-size the unit.** Do not force a sprawling source into one page. A meeting that covered three decisions across two topics becomes the articles those decisions belong to (merge or new, per SKILL.md), not a single "meeting notes" dump. One raw file can legitimately feed several wiki articles.

3. **Preserve exact terms, numbers, and epistemic status.** Keep the source's own terminology, figures, and hedging. "We will probably move to Postgres in Q3" is not "the team decided to move to Postgres." Do not harden a maybe into a decision, round away a load-bearing number, or flatten a disagreement into consensus. Distil the wording; preserve the meaning and the certainty.

4. **Anchor load-bearing claims to the source.** For a claim the wiki will lean on (a decision, a commitment, a surprising or contested fact), make it checkable. The Raw line already links the source file; for the heaviest claims, also quote the key sentence inline next to its raw link, and point at where in the source it lives - a section heading, a page, a transcript timestamp, the date of a post - so a reader can verify it without re-reading the whole source:
   ```
   > "We're standardising on Postgres for all new services from Q3." ([Planning call](../../raw/infra/2026-05-03-planning-call.md), [00:12:30])
   ```
   This is a prose practice, not a required field. Reserve it for claims that carry weight; quote-anchoring everything just rebuilds the transcript. The locator is also what lets an audit (`references/audit.md`) check the claim against the exact spot rather than the whole file.

5. **Triage explicitly, and say so.** Long noisy sources are mostly filler. Decide what is durable knowledge versus chatter. "Nothing here is new" or "restates a known article" is a valid outcome: keep the raw file, fold anything real in as added evidence to an existing claim, and do not spawn a thin page. Compiling noise is worse than compiling nothing.

6. **Faithfulness self-review.** After writing, re-read the source once against your article and ask: did any load-bearing claim, number, or named entity get dropped, softened, or overstated? Fix before finishing. This second pass is cheap and catches exactly the drift long sources cause.

## Keep the raw file faithful

The raw file is the safety net you anchor back to, so do not over-clean it. Strip only secrets and PII (per SKILL.md); leave speaker labels, timestamps, and structure intact. In a transcript those are signal: they tell you who committed to what and when.

## In bulk ingest

When extractor sub-agents handle transcripts (see `references/bulk-ingest.md`), the same discipline applies to the proposal each returns: the `claims` list is the atom extraction, `evidence` is the anchor, and `net_new` is the triage. Apply steps 1, 3, and 5 inside each extractor; the orchestrator handles right-sizing and the faithfulness pass at compile time.
