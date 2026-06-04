# Distilling an external source into the wiki

How to extract the valuable content from a verbose external source - a meeting transcript, call notes, a long document or thread that lives outside the wiki - and keep a high-signal extract in `raw/` instead of the whole thing. The user wants the substance summarised, not the source retained in full.

## When to use this

Use it when all three hold: the source lives outside the wiki (a file the user names, a paste, a link), it is verbose enough that keeping it verbatim is not worth it, and the user wants the valuable content extracted rather than the source preserved. Typical phrasing is "extract the useful content from this transcript and add it to the wiki".

- If the user wants the full source kept faithfully, use `references/high-fidelity-ingest.md` instead: same atom discipline, but the verbatim source stays in `raw/`.
- If the source is a rich format (PDF, slides, docx), convert it to markdown first per `references/rich-format-ingest.md`, then distil that markdown.

## What changes about `raw/`

Normally a `raw/` file is the verbatim source - the immutable ground truth Audit checks the wiki against. A distilled extract is not that. It is already a derived artefact, an LLM's reading of a source that is being discarded. Mark it so, and be honest about the weaker guarantee:

- Frontmatter carries `fidelity: distilled`. A verbatim raw omits the field, or sets `fidelity: verbatim`.
- `original:` records what happened to the source: `external` (it still exists, untouched, outside the wiki) or `discarded` (not retained anywhere - it had been placed in `raw/` and was deleted after the review gate, or it was an ephemeral paste).

The trade is real. Once the source is gone, Audit can only check that an article claims no more than the extract supports; it can no longer confirm the extract itself reflects the original. The verification that matters therefore happens once, here, at ingest, against the source while it is still present. That is what the review gate below is for.

## Distil by removing, not by summarising

The failure mode is context collapse: a summary compresses many specific statements into one general sentence and the specifics evaporate. Avoid it by treating distillation as subtraction, not paraphrase. Cut filler and repetition; keep every distinct durable atom in the source's own words. The extract is shorter because the noise is gone, not because the meaning was generalised.

**Safe to drop:** greetings, scheduling and logistics, tech troubleshooting ("can you hear me"), off-topic personal chat, filler words and false starts, and any point already captured being restated.

**Looks like filler but is signal - keep it:** hedging and uncertainty ("probably", "we think", "not sure"), dissent and objections that did not win, who said or committed to what, the rationale for a decision and the alternatives rejected, exact numbers, dates, names and versions, conditionals ("if X then Y"), parked items, open questions, and action items with their owners. These are exactly what a naive summary discards, and they are usually why the source was worth reading.

Distil "we'll probably move to Postgres in Q3, though Sam flagged the auth-DB migration cost" to a line that keeps the hedge, the owner of the objection, and the quarter - not to "the team decided to adopt Postgres".

## The steps

1. **Convert if needed.** Rich format to markdown first (`references/rich-format-ingest.md`); the converted markdown is working material to distil from, not the raw file you keep. Defer that protocol's "delete the original binary" step until the review gate passes - the reviewer still needs the source.
2. **Extract atoms.** Pull the durable items into a flat list - decisions, claims, numbers, entities, conditionals, open questions, action items - noting where each sits in the source. This is the `references/high-fidelity-ingest.md` atom step; the list is the checklist that catches what writing-from-memory drops.
3. **Render source-shaped.** Write the extract the way the source ran (agenda items, chronology, threads), not by wiki concept: one source, one extract. Keep terms, figures, and epistemic status. Call out decisions, action items, and open questions explicitly; an open question the wiki cannot answer also belongs in `wiki/gaps.md` (`references/gaps.md`).
4. **Anchor the heavy claims now.** For the claims the wiki will lean on, lift the key sentence as a verbatim quote with its locator (timestamp, section, page) into the extract while the source is still in front of you. After the source is gone the extract is the only anchor, so these quotes must be exact.
5. **Hand off to a reviewer** (next section) and fix what it finds.
6. **Save and dispose.** Write the extract to `raw/<topic>/` with `fidelity: distilled`, following the naming rules in SKILL.md. Leave an external source untouched (`original: external`). Only when the source had already been placed in `raw/` do you delete it, along with any binary you converted from it, and only after the reviewer passes (`original: discarded`). This is the same verified-then-discard gate `references/rich-format-ingest.md` uses for binaries.
7. **Compile to `wiki/`** as normal, citing the distilled extract on the article's Raw line.

## The review gate (separate sub-agent)

When you judge the extract done, do not trust your own read of it - hand off to a fresh named sub-agent for a critical review. A self-review, or a fork that inherits this conversation, carries the extractor's blind spots with it; an independent reader holding the source does not. This review is mandatory, and it is the gate that licenses discarding the source, so it must run while the source is still available.

Give the reviewer:

- the full source text (or its path) and the distilled extract;
- the keep and drop lists above, so it judges against the same bar;
- a clear goal: find anything durable that was dropped, softened, overstated, mis-attributed, or generalised from a specific; confirm every inline quote is verbatim and its locator correct; flag any filler that leaked in.

Ask it to return findings, not a rewrite. It reads only; it never edits the wiki or the extract.

```
verdict: pass | revise
findings:
  - type: dropped | softened | overstated | misattributed | quote-drift | filler-leak
    severity: high | low
    detail: <what was wrong, and where in the source - quote the passage>
```

Apply the high-severity findings, re-run the reviewer if the changes were substantial, and treat the extraction as done only on `pass`. Then, and only then, dispose of the source.

## In bulk ingest

When distilling many sources at once, slot the review between extract and compile: each source runs extract, then critical review, then proposal, with the reviewer a different sub-agent from the extractor, and the orchestrator compiles serially as in `references/bulk-ingest.md`. The reviewer's pass is per source; the orchestrator still owns the cross-source dedup, supersession, and cascade.
