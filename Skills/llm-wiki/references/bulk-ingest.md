# Bulk and parallel ingest

How to bring many sources into the wiki at once without losing the synthesis, dedup, and cross-linking that make a wiki worth more than a folder of notes.

## When to use this

Default to plain single-source ingest. Reach for this protocol when you have many sources to bring in together (for example a folder of meeting transcripts) or when one agent would run out of context partway through. A handful of sources is fine to ingest serially; the fan-out overhead is not worth it for small batches.

## The shape: map then reduce

Sub-agents extract in parallel (the expensive, context-heavy part). One orchestrator compiles serially (the part that must see the whole wiki). The compile stays serial on purpose: dedup, conflict detection, evidence merging, and cross-linking all need a single consistent view, and that is exactly what parallel writers destroy.

## Step 0: prepare (orchestrator)

- List the source files for the batch.
- Decide the topic taxonomy: read the existing `raw/` and `wiki/` topic directories, pick or extend the set, and write it down. This fixed list goes to every extractor so they cannot invent divergent names for one thing.
- Choose a batch size per sub-agent: large enough to be worth a context, small enough to finish reliably.

## Map: extractor sub-agents (parallel)

Give each sub-agent its file list, the fixed topic list, and this contract:

- You are one of several extractors. You own only `raw/<your-topic>/`. Do not write to `wiki/`, `index.md`, or `log.md`.
- For each source: apply the secret and PII filter, save it under `raw/` following the naming rules in SKILL.md, then return a proposal. Do not compile.
- Rich-format sources (PDF, slides, documents, images) convert to markdown per `references/rich-format-ingest.md` before extraction: `raw/` stays markdown-only.
- For long or noisy sources (transcripts, chat logs), extract atoms faithfully: the `claims` list with `evidence` is exactly the atom extraction and anchoring from `references/high-fidelity-ingest.md`. Preserve exact terms, numbers, and hedging; set `net_new` honestly.
- Your final message is the data the orchestrator merges, so return the proposals and nothing else.

One ingest proposal per source:

```
source_raw: raw/<topic>/<file>.md       # the file you wrote
topic: <one of the assigned topics>
target:
  mode: merge | new
  article: <existing article to merge into, or proposed new title + slug>
claims:
  - claim: <one durable claim, decision, or fact>
    evidence: <short quote or section reference from the source>
entities: [people, projects, decisions]
conflicts: <anything that appears to contradict an assigned topic or known article, else empty>
cross_links: [<related article titles>]
net_new: yes | restates-known          # transcript triage: does this add anything new?
```

## Reduce: orchestrator (serial)

1. Collect every proposal.
2. Sort by the source's meeting or published date. Applying oldest to newest makes "newer supersedes older" resolve deterministically despite parallel extraction.
3. Group by target concept. Several proposals about one concept become a single article whose evidence chain lists every supporting source. This "many sources, one well-supported claim" consolidation is only possible with all proposals in view, and it is the main reason the compile is serial.
4. Triage `net_new`. A `restates-known` source keeps its raw file but folds in as added evidence to an existing claim rather than spawning a new article. Avoid compiling noise.
5. Apply writes to `wiki/` one at a time, resolving conflicts (annotate inline with an evidence chain) and supersession (mark the old page stale with `superseded_by` and a callout) against the now-stable state.
6. Update `index.md` and `log.md` once, as the sole writer. Use a single batch log entry:
   ```
   ## [YYYY-MM-DD] ingest | batch: <label> (<N> sources)
   - Created: <article title>
   - Updated: <article title>
   - Superseded: <old title> -> <new title>
   ```
7. Cascade once across the touched topics, now that every article in the batch exists.
8. Checkpoint, then commit (see below).

## The review checkpoint (the quality gate)

Before committing, present a digest and wait for the user's go-ahead:

- sources ingested, and any skipped as `restates-known`
- articles created, merged (with how many sources back each), and superseded
- conflicts surfaced, for the user to judge
- anything the orchestrator was unsure where to file

Only after approval, `git commit` the batch. This pause is deliberate. Bulk ingest is where a wiki quietly fills with thin, duplicated pages, and a human glance at the batch boundary is the cheapest place to catch it. Quality over volume.

## Advanced: parallel compile

Only when reduce throughput is the genuine bottleneck. Partition by `wiki/` topic so each compile sub-agent owns a disjoint `wiki/<topic>/`. Keep `index.md` and `log.md` single-writer: each owner returns its index rows and log lines as data, and the orchestrator assembles them. Disjoint ownership is the rule; any overlap means agents erase each other's work.

## Resumability

A batch can stop partway. Raw files are written first and are independent, so a re-run can skip any source already compiled (check the log for what landed). Commit per batch so a bad batch reverts cleanly with one `git revert`.

## Gotchas

- **One concept, one article.** The most common bulk failure is two agents creating near-duplicate pages. The orchestrator's group-by-concept step prevents it, which is why extractors never create wiki pages.
- **Date order matters.** Without sorting, concurrent supersessions land in arbitrary order and the wrong claim can win.
- **`index.md` and `log.md` have exactly one writer, ever.** Almost every corruption traces back to this rule being broken.
- **Watch the index size.** Past a few hundred pages a single `index.md` gets heavy to read in one pass; consider per-topic index sections before a large batch makes it worse.
