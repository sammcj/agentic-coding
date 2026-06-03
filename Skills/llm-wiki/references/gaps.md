# Gaps: tracking what the wiki does not yet cover

`wiki/gaps.md` is the register of known unknowns. If `index.md` is "what we know" and `log.md` is "what we did", `gaps.md` is "what we don't know yet". It is a maintained markdown file at the `wiki/` root, the same level as the index and the log, and it follows the same rules: plain markdown, relative links, a greppable prefix, and git as the audit trail.

A gap is a first-class but lightweight citizen. It uses the same lifecycle grammar as the rest of the wiki: filtered at capture, ranked by evidence rather than a score, closed by a resolution link rather than deleted, and found by grep plus the lint heuristics that already exist. No new field types, no database, no background process.

## What is and is not a gap

Two kinds carry the weight:

- **`wanted`** - a concept that articles reference or mention but that has no page of its own. The genuine "dangling node": an edge points at something that was never written.
- **`question`** - a known unknown. A source raised it without answering, or a user asked it and the wiki had no answer.

Not a gap:

- **An orphan page** (a page nothing links to) is a *connectivity* problem, not missing knowledge. The article exists; it needs a See Also, not a gap entry. Orphans stay in Lint where they are.
- **A broken link to a page that should exist** is a Lint repair (find the same-named file and fix the path), not a gap. Only a reference to a concept that genuinely has no article becomes a `wanted` gap.
- **Anything outside the wiki's subject.** A question the wiki was never meant to answer is not a gap in it. Filter these out at capture.

## Entry format

Group entries by topic, mirroring `index.md`. Within a topic, list open entries first, then resolved ones. Each entry is a level-3 heading with a greppable prefix, followed by evidence lines:

```markdown
# Knowledge Gaps

Known unknowns. Open gaps are ranked by evidence of demand, never by a score.

## machine-learning

### [open] question | How does FlashAttention-2 improve on the original?
- Raised by: [Attention Efficiency](machine-learning/attention-efficiency.md)
- Asked: 2026-05-20, 2026-06-02

### [open] wanted | Online softmax
- Referenced by: [Attention Efficiency](machine-learning/attention-efficiency.md)
- Noted: 2026-05-10

### [resolved] question | Is attention's quadratic memory cost a hard limit? -> [Attention Efficiency](machine-learning/attention-efficiency.md) (2026-05-27)
```

`grep "^### \[open\]" wiki/gaps.md` lists every open gap, the same way the log's `## [` prefix lists recent activity. The heading is `### [<status>] <kind> | <title>`, where status is `open` or `resolved` and kind is `wanted` or `question`. A resolved entry appends `-> [Article](path) (YYYY-MM-DD)` to its title line and keeps no evidence lines; the link is the record.

Links inside `gaps.md` use the same `topic/article.md` form as `index.md` (the file sits at the `wiki/` root). Quote-style markdown links, not wikilinks, so it renders on GitHub.

### Evidence, not a score

This is where a gap earns the same discipline as a claim. Never write `priority: high` or a number. State the support, which a reader can check:

- **Referenced by** - the articles that point at the missing concept. This comes straight from grep, so it is verifiable and cheap to refresh rather than hand-maintained.
- **Asked** - the dates a query missed on this gap. Each miss appends a date. A gap asked five times outranks one asked once, and the dates prove it.
- **Raised by** - the article or raw source that surfaced an open question.
- **Noted** - the date the gap was first recorded.

The user sorts open gaps by this evidence to decide what to research or ingest next. The register answers "what should I read about next" with facts, not a guessed ranking.

## Capture: where gaps come from

Gaps are recorded only during operations the user runs. There is no crawler. Each existing operation already touches the natural capture point.

**Ingest.** While compiling:

- A load-bearing open question the source raises but does not answer goes into `gaps.md` as a `question`, instead of being buried in article prose. (High-fidelity ingest already pulls open questions out as atoms; this is where the durable ones land - see `references/high-fidelity-ingest.md`.)
- A forward reference to a concept that has no article yet is a `wanted` gap, recorded as you write the link.
- Conversely, if the ingest creates the article that answers an existing gap, close it (see Lifecycle). Filling a gap and forgetting to close it leaves a false unknown on the register.

**Query.** The strongest signal, because a missed query is demonstrated demand:

- When the wiki cannot answer, or answers only partially, propose recording it. If a matching gap exists, append today's date to its `Asked` line; otherwise create a `question` entry with `Raised by` the query.
- Propose, do not auto-write: the user confirms, and only for questions inside the wiki's subject. A plain query still writes nothing on its own; the gap is added with the user's go-ahead.

**Lint.** Lint already detects gaps but reports them into the chat, where they evaporate. Give the findings a durable home, split along Lint's existing two-tier authority (`references/lint.md`):

- Deterministic, safe to write: auto-close a `wanted` gap whose article now exists, resolve gap links, and prune resolved gaps on retention. (Creating a gap is not deterministic - deciding a mentioned concept warrants a page is judgement.)
- Heuristic, propose only: "concept mentioned often but no page" and thin coverage are proposed as `wanted` gaps, and an open `question` an article now answers is proposed for closing. The user confirms; never auto-authored into articles.

## Lifecycle: gaps close, they do not vanish

This is supersession applied to absence. A filled gap is marked `[resolved]`, linked to the article that closed it, and dated. It is kept, not deleted, because "we did not know X until article Z filled it on date Y" is worth keeping, the same reason a superseded page is kept.

- **Closing.** Change `[open]` to `[resolved]`, drop the evidence lines, and append `-> [Article](path) (date)`. A `wanted` gap auto-closes deterministically once an article of that name exists. A `question` closes when the article that answers it is written and linked, which is judgement, so it happens at ingest time or when Lint proposes it.
- **Retention.** Resolved entries are pruned on the same git-backed rule as `log.md`: when the wiki is a git repo, keep recent resolved entries and let git carry the rest, leaving a recovery marker. If the wiki is not a git repo, do not prune. Open gaps are never pruned.

## Filter at capture

The one rule that keeps `gaps.md` from rotting into an endless TODO list: record only gaps with evidence behind them. A passing mention is not a `wanted` page; a concept referenced by an article, or asked about in a query, is. An idle "we could also cover X" is not a `question`; an unknown a source or a user actually raised is. This is "filter at ingest, not in retention" applied to gaps: decide what is worth tracking when it arrives, so cleanup later is rare.

## What this never does

- No priority numbers or confidence floats. Evidence only.
- No background scanning or autonomous writes. Capture happens inside ingest, query, and lint, all user-invoked.
- No new dependencies, database, or embeddings. One markdown file, grep, and the heuristics Lint already runs.
- No deleting resolved gaps outside git-backed retention. The history is the point.
- No auto-authoring an article to fill a gap. Lint surfaces and proposes; the user directs the fill, the same boundary as every other heuristic check.
