---
name: llm-wiki
description: "Use when building or maintaining a self-contained personal knowledge base (an LLM wiki) in plain markdown. Triggers: ingesting sources into a wiki, querying wiki knowledge, linting wiki health, auditing article claims against their sources, critiquing a wiki source's reasoning, superseding stale knowledge, 'add to wiki', 'LLM wiki' or 'Karpathy wiki'."
argument-hint: "[ingest | query | lint | audit | critique] [input]"
---

# LLM Wiki

A personal knowledge base in plain markdown. Sources land in `raw/` (immutable); you compile them into `wiki/` articles you own. Local markdown with YAML frontmatter, readable on GitHub, openable as an Obsidian vault. No servers, no databases, no embeddings.

Core idea (Karpathy): the LLM writes and maintains the wiki; the human chooses sources and asks questions. Knowledge is compiled once at ingest.

## Invocation

**Query is the default.** Ingest, Lint, Audit and Critique are the four deliberate operations, each opted into by its verb or by a request that plainly calls for it. Anything else is a Query against the wiki: a bare question, "what do I know about X", "summarise everything on Y". No `query` keyword needed.

A leading mode argument routes straight to that operation:

- `ingest` (alias `add`) - trailing text is the source: a URL, a path, or pasted content.
- `lint` - health checks; no further input.
- `audit` - trailing text names the article or topic to verify.
- `critique` (alias `scrutinise`) - trailing text names the article, topic, or pasted content to examine.
- `query` (alias `ask`) - forces query handling when a question could look like another operation.

Otherwise route natural language to Ingest, Lint, Audit or Critique only when it clearly calls for one; answer everything else as a Query.

### Always required, and scenario-gated

Every operation, always:

- Act only on the user's request; never background-write.
- Compile any write from a source already in `raw/`, never straight from a live URL or an external path.
- Update `wiki/index.md` and append `wiki/log.md` on any write.
- Bump an article's `updated` whenever its content changes.
- Replace outdated knowledge by superseding it, never by deleting or editing in place.

Everything else is scenario-gated. Match your task against a branch below and read that file before acting - a pointer is an instruction to open the file, not a citation. When unsure, read it: cheaper than corrupting the wiki by guessing.

- Ingesting any source -> `references/ingest.md`
- No `wiki/` yet, so this ingest initialises one -> `references/init.md`
- Source is a PDF, Word file, slides, images, or a spreadsheet -> `references/rich-format-ingest.md`
- User wants the high-signal content rather than the whole source -> `references/distilled-ingest.md`
- Source is a transcript, chat log, interview notes, or a long noisy article -> `references/high-fidelity-ingest.md`
- Many sources at once, or one pass would exhaust context -> `references/bulk-ingest.md`
- The wiki's subject is a codebase -> `references/codebase-wiki.md`
- Drawing or maintaining a mermaid concept map -> `references/concept-map.md`
- Recording or closing a knowledge gap -> `references/gaps.md`
- Personal, uncommitted content under `local/` -> `references/local-content.md`
- Working directory holds several wikis side by side -> `references/multiple-wikis.md`
- Saving an answer into the wiki as an archive page -> `references/archive.md`
- Old-format wiki, or a question about `type`, index form, or log form -> `references/okf.md`
- Running graphify over the wiki as a read-only lens -> `references/graphify.md`

Lint, Audit and Critique each gate their own reference from their section below.

## Design philosophy

For anything the sections below do not cover.

- **Filter at ingest, not in retention.** Decide what is worth keeping, and strip secrets, when a source arrives.
- **Supersession, not decay.** Knowledge does not expire on a timer. When new information replaces old, mark the old article stale, point it at the replacement, and keep it: a superseded decision still explains the current state.
- **Evidence, not confidence scores.** Never attach a number like `0.85` to a claim. State which sources confirm it, which contradict it, when it was last confirmed.
- **Git is the audit trail.** History and rollback come from version control, not bespoke versioning fields. Recommend a git repo.
- **Invocation-driven, human in the loop.** You act when the user asks; no background automation writes to the wiki unsupervised. The user curates; you do the bookkeeping.
- **Text-only and self-contained.** Plain markdown, relative links, YAML frontmatter. Ordinary tools (grep, git, the agent's file and web tools) are fine. External servers, vector stores, embedding pipelines, knowledge-graph databases, and multi-agent sync or governance layers are not - index plus grep covers a personal wiki's scale.

## Architecture

Under the user's project root:

**raw/** - Immutable source material, the source of truth. Read, never modify. Topic subdirectories, e.g. `raw/machine-learning/`.

**wiki/** - Compiled articles you own. One level of topic subdirectories only: `wiki/<topic>/<article>.md`. Four special files:
- `wiki/README.md` - orientation for anyone opening the wiki without this skill. Mostly static; created at init.
- `wiki/index.md` - global catalogue in OKF index form: per-topic sections of `* [Title](path) - summary`, no Updated column. The entry point for queries.
- `wiki/log.md` - append-only operation log with a greppable prefix.
- `wiki/gaps.md` - register of known unknowns: concepts referenced but unwritten, questions the wiki cannot answer.

**local/** (optional) - Personal markdown kept out of git: drafts, working notes, private sources. A sibling of `raw/` and `wiki/`, excluded by the wiki `.gitignore`. Exempt from the index, log, gaps, cascade and audit. One rule: `local/` may link into `wiki/` and `raw/`, but no committed file may ever link into `local/` (broken for other clones; it leaks the path into git). Full rules and promotion path: `references/local-content.md`.

**SKILL.md** (this file) - the schema layer. Templates live in `references/`.

### File format

Every article and raw file starts with YAML frontmatter, then standard markdown. Frontmatter is machine-readable (Obsidian Properties, Dataview queries); body links render on GitHub and in Obsidian's graph and backlinks.

Article frontmatter:

```yaml
---
title: Transformer Architectures
type: concept          # concept | entity | archive
topic: machine-learning
resource:              # optional canonical URI of the asset an entity describes
created: 2026-04-03
updated: 2026-04-03
status: current        # current | stale
superseded_by:         # relative path to replacement, set only when status: stale
tags: [transformers, attention]
aliases: []
---
```

- `updated` is the canonical "knowledge last changed" date; lint reads it. It changes when content changes, not when the file is touched. The index does not carry it (OKF keeps freshness in frontmatter).
- `type: archive` marks crystallised query answers (`references/archive.md`); archives are point-in-time and never cascade-updated.
- `resource` is the canonical URI of the asset an `entity` article describes (table, service, API, repo), distinct from the body Sources/Raw provenance lines. Optional, absent for abstract `concept` articles. Mirrors the OKF `resource` field (`references/okf.md`).
- `status` and `superseded_by` drive supersession (see Ingest > Conflicts and supersession). Leave `superseded_by` empty for current articles.
- `tags` and `aliases` are optional, for Obsidian and Dataview.

The wiki is a superset of an Open Knowledge Format (OKF) v0.1 bundle, so OKF tooling reads it with no export. **On meeting an older-format wiki mid-Lint or mid-Ingest, on creating or migrating `type` fields, or on any question about index or log form, you MUST read `references/okf.md` and follow it.**

### Links and paths

Inside `wiki/` files, all links are relative to the current file:
- Same topic: `[Other Article](other-article.md)`
- Different topic: `[Other Article](../other-topic/other-article.md)`
- Raw file: `[Source](../../raw/topic/file.md)` (two levels up to project root)

In conversation output, use project-root-relative paths, e.g. `wiki/topic/article.md`. `superseded_by` uses the same file-relative form as body links.

### Special files

`wiki/README.md` covers the raw/wiki split, frontmatter fields, supersession-not-deletion, and what index.md, log.md and gaps.md are, for a reader without this skill. Keep it high-level and static; point at this file's procedures rather than copying them. Template: `references/templates/wiki-readme-template.md`.

`wiki/index.md` is the agent's first read on any query: hand-maintained, canonical even where Dataview can generate parts.

`wiki/log.md` is append-only and chronological; git history holds the canonical record. OKF update-log form:

- Newest-first `## YYYY-MM-DD` date headings; `grep "^## " wiki/log.md | head` returns recent dates.
- One bullet per operation under its heading, led by a bold operation word: `**Ingest**`, `**Query**`, `**Lint**`, `**Audit**`, `**Critique**`, plus `**Supersession**`.
- Append under today's heading, creating it at the top when absent.
- Keep bullets lean: link the articles touched; the article body and git diff carry what changed.

`wiki/gaps.md` registers known unknowns in two entry kinds:

- `wanted` - a concept articles reference but no page covers.
- `question` - something a source raised or a user asked that the wiki cannot answer.

Entries are grouped by topic and ranked by evidence of demand - which articles reference the gap, how often asked - never by a score. Captured during ingest, query and lint, never by a background process; closed by a resolution link rather than deletion. Greppable: `grep "^### \[open\]" wiki/gaps.md`. Full format, capture rules, lifecycle: `references/gaps.md`.

### Initialisation

Initialisation triggers only on the first Ingest into a directory with no `wiki/`. **Before creating anything you MUST read `references/init.md` and follow it.**

If Query or Lint cannot find the wiki structure, check for several wiki subdirectories (each with its own `wiki/` and `raw/`) - a multi-wiki setup of independent llm-wikis side by side, not an uninitialised wiki. Only when neither is present, tell the user: "Run an ingest first to initialise the wiki." Do not auto-create. **Read `references/multiple-wikis.md` before querying or maintaining across several wikis.**

---

## Ingest

Fetch a source into `raw/`, then compile it into `wiki/` - always both.

**Before ingesting you MUST read `references/ingest.md` and follow it.**

### Decide how much of the source to keep

Decide before fetching; it sets what lands in `raw/`.

- **Verbatim (default)** - a faithful copy, the immutable ground truth Audit checks against. Use it unless the user asks otherwise.
- **Distilled** - high-signal content only, filler removed. Choose it when the user asks for "the valuable content", "the high-signal parts", "the useful bits", "just the signal", "the key points", "what matters" or similar. Follow `references/distilled-ingest.md`, which distils by _removing_ filler rather than generalising specifics away, and ends in a mandatory separate-sub-agent review so nothing load-bearing is cut.

Pick one mode per source. A rich format (a docx transcript, a PDF) does not decide it: convert to markdown first, then keep or distil per the chosen mode. If a long, noisy source carries no instruction either way, ask rather than defaulting to a verbatim dump.

**Compile only from `raw/`.** Land every source as markdown in `raw/` before compiling, never straight from a live URL or an external path (a temp file vanishes, a URL changes; the Raw link must persist). A markdown file already in `raw/` compiles directly.

### Judgement calls during compile

**Persuasive sources.** When a source argues rather than reports - an opinion piece, a vendor's case, a strategy memo - consider a Critique pass (`references/critical-analysis.md`) before compiling it as settled knowledge. Report the reasoning risks and let the user decide; often the outcome is attributing a contested claim to its source, or logging the question in `gaps.md`.

**Long-form and noisy sources.** Transcripts, chat logs, long articles and interview notes carry detail one compile pass silently drops. Follow `references/high-fidelity-ingest.md`: list the durable items (decisions, claims, numbers, named entities, open questions) first, write the article from that list, then re-read the source once against the article. Keep the source's exact terms, figures and hedging; anchor the heaviest claims with an inline quote and a locator (section, page, timestamp) beside their raw link. Short single-claim sources need only the normal compile.

**Concept maps (optional).** When several articles relate in a way prose handles poorly - branching, convergence, a supersession or causal chain - a small mermaid diagram can earn its place (`references/concept-map.md`). A map in a `current` article is load-bearing: it carries a `map-sources` marker and is maintained on cascade updates. A map in a `type: archive` page is a dated snapshot.

### Conflicts and supersession

Check whether the new source disagrees with existing content.

- **Disagreement, both views still plausible** -> Annotate the conflict inline with an evidence chain, attributing each side: "Uses Redis for caching ([Source A](...), [Source B](...)); [Source C](...) reports Memcached." Do not pick a winner with a number. If the conflicting claims live in separate articles, note it in both and cross-link them.

- **New source clearly replaces old knowledge** -> Supersede, do not delete. On the old article: set `status: stale` and `superseded_by:` to the replacement's path, and add a callout directly under the title:
  ```
  > [!warning] Superseded by [New Article](new-article.md) (2026-04-03). Kept for history.
  ```
  Create or update the replacement as a normal `current` article, mentioning in prose what it replaces. Git history preserves the rest.

### Bulk and parallel ingest

For many sources at once, or when a single pass would exhaust context, parallelise the extract and keep the compile serial. Full protocol and ingest-proposal schema: `references/bulk-ingest.md`.

These rules keep a parallel batch from corrupting the wiki:

- **Pre-assign the topics before fan-out.** Read existing `raw/` and `wiki/` topics, fix the topic set for the batch, and hand it to every sub-agent so they cannot invent divergent names.
- **Sub-agents extract; they do not compile.** Each writes only under `raw/<assigned-topic>/` and returns a structured proposal, never touching `wiki/`, `index.md`, or `log.md`.
- **The orchestrator is the sole writer to `wiki/`, `index.md`, and `log.md`.** It merges proposals against one view: combine same-concept proposals into one article with a shared evidence chain, apply in source-date order so supersession resolves newest-first, then cascade and update the index and log once.
- **Checkpoint before committing.** Present a digest (created, merged, superseded, conflicts surfaced) and wait for the user before the batch `git commit`. Ten well-supported articles beat fifty thin ones.

---

## Query

Search the wiki and answer questions. Triggers: "What do I know about X?", "Summarise everything on Y", "Compare A and B".

### Steps

1. Read `wiki/index.md` to locate relevant articles.
2. Read those articles. For connections the index misses, follow body links and backlinks: `grep -rl "article-name.md" wiki/` lists linking pages.
3. Synthesise an answer. Prefer wiki content over training knowledge. Cite with markdown links: `[Article Title](wiki/topic/article.md)` (project-root-relative).
4. Note when a cited article is `status: stale`, and point to its replacement.
5. If `local/` exists, search it too, labelling each hit `local/ (uncommitted)` so it is never mistaken for shared knowledge (`references/local-content.md`). A query runs against one wiki; never silently fold in another of the user's. If the question spans wikis, say so and ask which to draw on (`references/multiple-wikis.md`).
6. Answer in the conversation; do not write files unless asked.
7. **Capture a miss.** If the wiki could not answer, or answered only partially, and the question sits within its subject, propose recording it in `wiki/gaps.md`: append today's date to a matching gap's demand evidence, or add a new `question` entry. Record only with the user's go-ahead; a plain query writes nothing (`references/gaps.md`).

If the user asks whether the reasoning holds rather than what the wiki says, switch to Critique (`references/critical-analysis.md`).

### Crystallise (archive)

**When the user asks to save an answer to the wiki you MUST read `references/archive.md` and follow it.** The answer becomes a `type: archive` page so the exploration compounds like an ingested source.

---

## Lint

Health checks in two tiers: **deterministic problems are auto-fixed; anything needing judgement is reported, never silently rewritten.** You never rewrite article prose on your own authority. Lint checks internal consistency; to verify an article against its sources, use Audit.

**Before fixing anything you MUST read `references/lint.md` and follow it** - it enumerates every check in each tier and its fix behaviour. The bullets below index what it covers; they are not the procedure.

- **Deterministic (auto-fix):** index consistency, internal and raw links, frontmatter, See Also, log retention, the wiki skill file's links, concept-map freshness, the gap register, and the `local/` leak guard. Safe to repair without asking.
- **Heuristic (report only):** factual contradictions, supersessions never marked stale, orphan pages, missing cross-references, undocumented concepts (propose as `wanted` gaps), open gaps an article now answers, multi-concept articles, drifted archives, low-value concept maps, and a missing root `SKILL.md`, `CLAUDE.md`, or wiki `.gitignore`. Surface them; never auto-fix.

Two dependency-free read-only helpers back the deterministic tier, run with `uv`: `scripts/lint_wiki.py <project-root>` for structural findings (frontmatter, index, links, raw, the `local/` leak guard) and `scripts/lint_mermaid.py` for concept-map validity. Run them rather than improvising a shell script; without `uv`, use grep and the file tools and check mermaid by eye. The helpers detect; you apply the fixes.

### Post-lint

Log under today's date heading in `wiki/log.md`:

```
* **Lint**: <N> issues found, <M> auto-fixed.
```

---

## Audit

Verify an article's claims against the `raw/` sources it cites. Lint checks internal consistency; Audit checks external fidelity - do the cited sources actually support what the article says. Opt-in and user-invoked on a named article or topic, never automatic; it reads every cited source in full. Triggers: "audit X", "check the citations on Y", "does the wiki still match its sources".

**Before auditing you MUST read `references/audit.md` and follow it** - it carries target selection, claim extraction, the per-source sub-agent prompt, and the verdict schema.

- **Report only - never rewrite article prose on your own authority** (same boundary as Lint's heuristic tier). A failed claim is surfaced for the user to fix, supersede, or accept.
- Fan out one read-only sub-agent per cited source in parallel, then aggregate worst-first.

### Post-audit

Log under today's date heading in `wiki/log.md`:

```
* **Audit**: [<article or topic>](<path>) - <N> claims, <S> supported, <U> unsupported/partial.
```

If the user asks to keep the audit, crystallise it as a `type: archive` page citing the audited article - **read `references/archive.md` and follow it**.

---

## Critique

Examine the reasoning in a source or article and report what holds up: argument structure, hidden assumptions, logical fallacies, bias risk, internal consistency. Audit checks external fidelity against cited `raw/` sources; Critique checks internal soundness and does not fact-check empirical claims against the world. Like Audit it is opt-in, user-invoked, read-only and never rewrites prose. It runs on whatever the user points at - a `raw/` source, a `wiki/` article, or pasted content - and needs no `raw/`. Triggers: "critique X", "is this argument sound?", "what is this assuming?", "stress-test the reasoning in Y".

**Before critiquing you MUST read `references/critical-analysis.md` and follow its analysis steps and output structure - do not work from memory.** Say so plainly when the reasoning is sound; do not manufacture criticism. For many targets, fan out one read-only sub-agent per target in parallel, then present grouped weakest-first.

### Post-critique

Log under today's date heading in `wiki/log.md`:

```
* **Critique**: [<article, topic, or source>](<path>) - <overall assessment>.
```

Critique writes nothing else on its own. With the user's go-ahead it may crystallise the analysis as a `type: archive` page citing the critiqued target - **read `references/archive.md` and follow it** - or record a surfaced assumption or open question as a `question` gap in `wiki/gaps.md` (`references/gaps.md`).

---

## Optional: graphify as an external lens

If the **graphify** skill or tool is available, run it over the wiki as a disposable, read-only knowledge-graph lens: to see how articles connect, surface orphans and missing cross-references, triage a large `raw/` corpus before ingest, or answer connection-heavy questions. Markdown remains the source of truth; `graphify-out/` is generated and gitignored, never committed. Act on findings only through normal llm-wiki operations (a See Also, a `gaps.md` entry, a supersession, a Query answer), verified against the markdown first. **When you reach for graphify, read `references/graphify.md` first and follow it.**

---

## Gotchas

- **Path direction inside the wiki.** From `wiki/<topic>/`, a raw file is two levels up (`../../raw/<topic>/file.md`); a same-topic article is just its filename. A wrong `../` count is the most common broken link.
- **Keep the index prefix in step with the article.** On a supersession or archival, set or flip the `[Stale]`/`[Archived]` prefix on the index summary in the same pass, and refresh the summary if the thesis moved.
- **Long sources lose detail quietly.** Claims and exact numbers get dropped or softened when a transcript is compiled straight to prose. List the durable atoms first and re-read the source against your article before finishing (`references/high-fidelity-ingest.md`).
- **Only delete rich originals that live in `raw/`.** After extracting a binary to markdown, delete the original only when it was inside `raw/` (markdown-only) and the extraction is verified faithful. A PDF in Downloads or a temp dir is the user's: extract a markdown copy into `raw/` and leave it alone.
- **Gaps are a frontier, not a wishlist.** Record a `wanted` page or open `question` only when evidence backs it - an article references it, or a query asked it - and close gaps by resolution link rather than letting filled ones linger (`references/gaps.md`).
- **Concept maps drift silently.** When the article changes, the prose gets updated but the map can keep asserting old relationships. Recheck on cascade updates, keep the `map-sources` marker accurate, and remove the map once it no longer adds value (`references/concept-map.md`).
