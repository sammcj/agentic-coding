---
name: llm-wiki
description: "Use when building or maintaining a self-contained personal knowledge base (an LLM wiki) as plain markdown, optionally opened as an Obsidian vault. Triggers: ingesting sources into a wiki, querying wiki knowledge, linting wiki health, auditing article claims against their sources, superseding stale knowledge, 'add to wiki', or any mention of 'LLM wiki' or 'Karpathy wiki'."
---

# LLM Wiki

Build and maintain a personal knowledge base as plain markdown. You manage two directories: `raw/` (immutable source material) and `wiki/` (compiled knowledge you own). Sources land in `raw/`, you compile them into `wiki/` articles, and the wiki compounds over time. Everything is local markdown with YAML frontmatter, readable on GitHub and openable as an Obsidian vault. No servers, no databases, no embeddings.

Core idea (Karpathy): the LLM writes and maintains the wiki; the human chooses sources and asks questions. Knowledge is compiled once at ingest and kept current, not re-derived on every query. That is the difference from RAG, which retrieves raw chunks and re-synthesises on every question.

## Design philosophy

These principles decide what the wiki does and, just as much, what it leaves out. Follow them when a situation is not covered explicitly below.

- **Filter at ingest, not in retention.** Decide what is worth keeping, and strip secrets, when a source arrives. A clean ingest avoids most cleanup later.
- **Supersession, not decay.** Knowledge does not expire on a timer. When new information replaces old, mark the old article stale and point it at the replacement. Keep it. An old bug report or a superseded decision still explains why the current state exists.
- **Evidence, not confidence scores.** Never attach a number like `0.85` to a claim. State the support instead: which sources confirm it, which contradict it, when it was last confirmed. A reader can check links; they cannot check a float.
- **Git is the audit trail.** History, rollback, and "how did this get here" come from version control, not from bespoke versioning fields. Recommend the wiki live in a git repo.
- **Invocation-driven, human in the loop.** You act when the user asks. Do not set up background automation that writes to the wiki unsupervised. The user curates and directs; you do the bookkeeping.
- **Text-only and self-contained.** Plain markdown, relative links, YAML frontmatter. Readily available tools (grep, git, the agent's own file and web tools) are fine. External servers, vector stores, and embedding pipelines are not.

Deliberately excluded, and why: embedding or vector search and knowledge-graph databases (infrastructure the personal scale does not need; index plus grep covers it); numeric confidence scores (false precision); automatic forgetting or decay curves (they bury exactly the errors and superseded decisions you most need to remember); autonomous background writes (an unreviewed LLM corrupts the base silently); multi-agent sync and governance layers (out of scope for a personal wiki).

## Architecture

Three layers, all under the user's project root.

**raw/** - Immutable source material. You read, never modify. Organised by topic subdirectories, e.g. `raw/machine-learning/`. The source of truth.

**wiki/** - Compiled knowledge articles. You have full ownership. One level of topic subdirectories only: `wiki/<topic>/<article>.md`. Three special files:
- `wiki/README.md` - Orientation for anyone opening the wiki without this skill: what the structure is and the conventions that keep it sound. Mostly static; created at init.
- `wiki/index.md` - Global catalogue. One row per article, grouped by topic, with link, summary, and Updated date. The entry point for queries.
- `wiki/log.md` - Append-only operation log with a greppable prefix.

**SKILL.md** (this file) - The schema layer. Defines structure, format, and workflow. This is the most important file in the system: it is what makes a disciplined wiki maintainer rather than a generic chatbot. Templates live in `references/` relative to this file; read them when you need the exact format.

### File format

Every article and raw file starts with YAML frontmatter, then standard markdown. Frontmatter is machine-readable (the agent parses it; Obsidian shows it as Properties; the Dataview plugin can query it). The body uses standard markdown links so it renders everywhere, including GitHub, and still populates Obsidian's graph and backlinks panel.

Article frontmatter:

```yaml
---
title: Transformer Architectures
type: concept          # concept | entity | archive
topic: machine-learning
created: 2026-04-03
updated: 2026-04-03
status: current        # current | stale
superseded_by:         # relative path to replacement, set only when status: stale
tags: [transformers, attention]
aliases: []
---
```

- `updated` is the canonical "knowledge last changed" date. The index mirrors it; lint reads it. It changes when the article's content changes, not when the file is touched.
- `type: archive` marks crystallised query answers (see Query). Archives are point-in-time and are never cascade-updated.
- `status` and `superseded_by` drive supersession (see below). Leave `superseded_by` empty for current articles.
- `tags` and `aliases` are optional and exist for Obsidian and Dataview; the agent does not depend on them.

### Links and paths

Inside `wiki/` files, all links are relative to the current file:
- Same topic: `[Other Article](other-article.md)`
- Different topic: `[Other Article](../other-topic/other-article.md)`
- Raw file: `[Source](../../raw/topic/file.md)` (two levels up to project root)

In conversation output, use project-root-relative paths, e.g. `wiki/topic/article.md`. `superseded_by` in frontmatter uses the same file-relative path form as body links.

### Special files

`wiki/README.md` orients a reader who has the wiki but not this skill: the raw/wiki split, the frontmatter fields, supersession-not-deletion, and what index.md and log.md are, with a pointer to the skill for the full workflow. It is the GitHub landing page for the wiki directory. Keep it high-level and mostly static - it describes the format, not the catalogue, so it does not change on every ingest. Do not copy the operational procedures from this file into it; point to them. Template: `references/wiki-readme-template.md`.

`wiki/index.md` is the human-readable catalogue and the agent's first read on any query. Hand-maintained. If the user has Obsidian with Dataview, parts of it can be auto-generated from frontmatter, but never depend on a plugin: the maintained index.md is canonical.

`wiki/log.md` is chronological and append-only. Each entry starts with `## [YYYY-MM-DD] <op> | <title>` so `grep "^## \[" wiki/log.md | tail -5` returns recent activity.

### Initialization

Triggers only on the first Ingest. Check whether `raw/` and `wiki/` exist. Create only what is missing; never overwrite existing files:

- `raw/` directory (with `.gitkeep`)
- `wiki/` directory (with `.gitkeep`)
- `wiki/README.md` - orientation doc from `references/wiki-readme-template.md`
- `wiki/index.md` - heading `# Knowledge Base Index`, empty body
- `wiki/log.md` - heading `# Wiki Log`, empty body

If Query or Lint cannot find the wiki structure, tell the user: "Run an ingest first to initialize the wiki." Do not auto-create.

---

## Ingest

Fetch a source into `raw/`, then compile it into `wiki/`. Always both steps.

### Fetch (raw/)

1. Get the source content using whatever web or file tools your environment provides. If nothing can reach the source, ask the user to paste it directly.

2. **Filter before writing.** Strip secrets and credentials (API keys, tokens, passwords) and obvious private data (PII that is not the point of the source). If a source is mostly sensitive, flag it and ask the user before saving rather than redacting silently.

3. Pick a topic directory. Check existing `raw/` subdirectories first; reuse one if the topic is close enough. Create a new subdirectory only for genuinely distinct topics.

4. Save as `raw/<topic>/YYYY-MM-DD-descriptive-slug.md`:
   - Slug from source title, kebab-case, max 60 characters.
   - Published date unknown -> omit the date prefix from the file name. The frontmatter `published` field still appears, set to `Unknown`.
   - If a file with the same name exists, append a numeric suffix, e.g. `descriptive-slug-2.md`.
   - Include frontmatter (source, collected, published) and preserve the original text. Clean formatting noise; do not rewrite opinions.

   See `references/raw-template.md` for the exact format.

### Rich and external sources

`raw/` holds durable markdown only. When a source is a rich format (PDF, Word, slides, images, spreadsheets), convert it to markdown before saving, following `references/rich-format-ingest.md`: it covers structure preservation, the faithfulness review, and what to do with the original file.

**Compile only from `raw/`.** Land every source as markdown in `raw/` before compiling, never straight from a live URL or an external path (a temp file vanishes, a URL changes; the Raw provenance link must persist). If a markdown file is already in `raw/`, skip the fetch and compile it directly.

### Compile (wiki/)

Decide where the new content belongs:

- **Same core thesis as an existing article** -> Merge into it. Add the new source to the article's Sources/Raw lines. Update affected sections and bump `updated`.
- **New concept** -> Create a new article in the most relevant topic directory. Name the file after the concept, not the raw file. Write full frontmatter.
- **Spans multiple topics** -> Place in the most relevant directory; add See Also links to related articles elsewhere.

These are not exclusive: one source may merge into an existing article while also creating a new article for a distinct concept it introduces.

See `references/article-template.md` for the format. Provenance lives in the body as clickable links:
- Sources line: author, organisation, or publication + date, semicolon-separated.
- Raw line: markdown links to `raw/` files, semicolon-separated.

### Long-form and noisy sources

Transcripts, chat logs, long articles, and interview notes carry load-bearing detail that one compile pass can silently drop or soften. When a source is long or noisy, extract the durable items (decisions, claims, numbers, named entities, open questions) as a list first, write the article from that list, then re-read the source once against the article to confirm nothing important was lost, hardened, or overstated. Keep the source's exact terms, figures, and hedging, and anchor the heaviest claims with an inline quote and a locator (the section, page, or timestamp) next to their raw link. For short, clean, single-claim sources the normal compile above is enough. Full protocol: `references/high-fidelity-ingest.md`.

### Conflicts and supersession

Check whether the new source disagrees with existing content.

- **Disagreement, both views still plausible** -> Annotate the conflict inline with an evidence chain, attributing each side: "Uses Redis for caching ([Source A](...), [Source B](...)); [Source C](...) reports Memcached." Do not pick a winner with a number. If the conflicting claims live in separate articles, note it in both and cross-link them.

- **New source clearly replaces old knowledge** -> Supersede, do not delete. On the old article: set `status: stale` and `superseded_by:` to the replacement's path, and add a callout directly under the title:
  ```
  > [!warning] Superseded by [New Article](new-article.md) (2026-04-03). Kept for history.
  ```
  Create or update the replacement article as a normal `current` article, mentioning in prose what it replaces. Git history preserves the rest; no decay, no deletion.

### Cascade updates

After the primary article, check for ripple effects:

1. Scan articles in the same topic directory for content affected by the new source.
2. Scan `wiki/index.md` entries in other topics for related concepts.
3. Update every materially affected article and bump its `updated` date.

Never cascade-update `type: archive` pages or `status: stale` pages. Archives are snapshots; stale pages are history.

### Post-ingest

Update `wiki/index.md`: add or update entries for every touched article, with the `updated` date from frontmatter. When adding a new topic section, include a one-line description. Prefix a stale article's summary with `[Stale]`.

Append to `wiki/log.md`:

```
## [YYYY-MM-DD] ingest | <primary article title>
- Created: <additional new article title>
- Updated: <cascade-updated article title>
- Superseded: <old article title> -> <new article title>
```

Omit any sub-item that does not apply. The header names the primary new article; `- Created:` lists any additional articles the same source produced. Refer to articles by title, not file path.

### Bulk and parallel ingest

For many sources at once (a folder of meeting transcripts, a backlog import) or when a single pass would exhaust context, split the work: parallelise the extract, keep the compile serial. The full protocol and the ingest-proposal schema are in `references/bulk-ingest.md`.

These rules keep a parallel batch from corrupting the wiki:

- **Pre-assign the topics before fan-out.** Read the existing `raw/` and `wiki/` topics, fix the topic set for the batch, and hand it to every sub-agent so they cannot invent divergent names for the same thing.
- **Sub-agents extract; they do not compile.** Each writes its sources only under `raw/<assigned-topic>/` and returns a structured proposal. They never touch `wiki/`, `index.md`, or `log.md`, so there are no write races.
- **The orchestrator is the sole writer to `wiki/`, `index.md`, and `log.md`.** It merges proposals against one consistent view: combine same-concept proposals into a single article with a shared evidence chain, apply in source-date order so supersession resolves newest-first, then cascade and update the index and log once.
- **Checkpoint before committing.** Present a digest (created, merged, superseded, conflicts surfaced) and wait for the user before the batch `git commit`. Favour quality over volume: ten well-supported articles beat fifty thin ones, and this checkpoint is where that gets enforced.

### Documenting a codebase

When the wiki's subject is a codebase rather than external reading, the core workflow is unchanged but a few conventions help: topic directories and slug prefixes that fit source code, a rule for where the wiki ends and the repo's own README begins, and how to record decisions reconstructed from code and git history. Optional recipe: `references/codebase-wiki.md`.

---

## Query

Search the wiki and answer questions. Triggers: "What do I know about X?", "Summarise everything on Y", "Compare A and B from my wiki".

### Steps

1. Read `wiki/index.md` to locate relevant articles.
2. Read those articles. To find connections the index misses, follow body links and use backlinks: `grep -rl "article-name.md" wiki/` lists pages that link to a given article. (In Obsidian, the graph view and backlinks panel show the same structure.)
3. Synthesise an answer. Prefer wiki content over your own training knowledge. Cite with markdown links: `[Article Title](wiki/topic/article.md)` (project-root-relative in conversation).
4. Note when a cited article is `status: stale`, and point to its replacement.
5. Output the answer in the conversation. Do not write files unless asked.

### Crystallize (archive)

When the user asks to save the answer to the wiki, file it as a first-class page so the exploration compounds like an ingested source.

1. Write the answer as a new article with `type: archive`. See `references/archive-template.md`. Convert conversation citations to file-relative paths (e.g. `wiki/topic/article.md` becomes `../topic/article.md`, or `article.md` for the same directory).
   - Sources line: markdown links to the wiki articles the answer cites.
   - No Raw line (content does not come from `raw/`).
   - Capture the question, the findings, the articles and entities involved, and any lesson worth keeping as a standalone point.
   - File name reflects the query topic; place in the most relevant topic directory.
2. Always create a new page; never merge an archive into an existing article.
3. Update `wiki/index.md`, prefixing the summary with `[Archived]`.
4. Append to `wiki/log.md`:
   ```
   ## [YYYY-MM-DD] query | Archived: <page title>
   ```

---

## Lint

Health checks on the wiki. Two tiers with different authority. The boundary is deliberate: deterministic problems are fixed automatically; anything needing judgement is reported, never silently rewritten. You do not rewrite article prose on your own authority. Lint checks the wiki's internal consistency; to verify an article against the sources it cites, see Audit.

### Deterministic checks (auto-fix)

**Index consistency** - compare `wiki/index.md` against actual `wiki/` files (excluding README.md, index.md and log.md):
- File exists but missing from index -> add an entry with `(no summary)`. Use the frontmatter `updated` date if present, otherwise the file's last modified date.
- Index entry points to a nonexistent file -> mark it `[MISSING]`. Do not delete; let the user decide.

**Internal links** - for every markdown link in article bodies (including Sources lines), excluding Raw links and README.md/index.md/log.md:
- Target missing -> search `wiki/` for a file of the same name. Exactly one match: fix the path. Zero or several: report.

**Raw references** - every Raw link must point to an existing `raw/` file:
- Target missing -> search `raw/` for a file of the same name. Exactly one match: fix. Zero or several: report.

**Frontmatter** - every article must have well-formed frontmatter:
- Missing required field (`title`, `type`, `topic`, `created`, `updated`, `status`) -> fill what is derivable (topic from folder, dates from file or index), report the rest.
- `status: stale` but no `superseded_by`, or no supersession callout -> report (do not guess the replacement).
- `superseded_by` points to a nonexistent file -> report.

**See Also** - within each topic directory: add obviously missing cross-references between related articles; remove links to deleted files.

### Heuristic checks (report only)

Rely on judgement. Report findings; do not auto-fix.

- Factual contradictions across articles that lack a conflict annotation.
- Claims a newer source has superseded but that were never marked stale.
- Orphan pages with no inbound links (no backlinks from other articles).
- Missing cross-topic references.
- Concepts mentioned often but lacking their own page.
- Archive pages whose cited source articles have changed substantially since archival.

### Post-lint

Append to `wiki/log.md`:

```
## [YYYY-MM-DD] lint | <N> issues found, <M> auto-fixed
```

---

## Audit

Verify that an article's claims hold up against the `raw/` sources it cites. Where Lint checks the wiki's internal consistency (links, frontmatter, index), Audit checks its external fidelity: do the cited sources actually support what the article says. This is the verification the evidence chains imply but never enforce. It is opt-in and user-invoked on a named article or a topic, never automatic, and it reads every cited source in full. Triggers: "audit X", "check the citations on Y", "does the wiki still match its sources".

### Steps

1. Pick the target: one article, or every current article in a topic. Skip `status: stale` and `type: archive` pages unless asked; history and snapshots are not cascade-checked.
2. From the target's Raw line and any inline raw links, list the cited `raw/` files and the claims each is meant to support. A load-bearing claim with no cited source is itself a finding.
3. For each cited raw source, dispatch a sub-agent in parallel. Give it that one source and the claims that cite it. It reads the source and returns, per claim, one verdict - `supported`, `partial`, `unsupported`, or `source-missing` - with the passage that backs it or a note that none does. Sub-agents read only; they never edit the wiki.
4. Aggregate the verdicts and report in conversation, grouped by article, worst verdicts first. For anything not `supported`, quote what the source actually says so the user can act.
5. Report only; do not rewrite article prose on your own authority (the same boundary as Lint's heuristic tier). An unsupported claim is surfaced for the user to fix, supersede, or accept.

Full protocol, the per-source sub-agent prompt, and the verdict schema: `references/audit.md`.

### Post-audit

Append to `wiki/log.md`:

```
## [YYYY-MM-DD] audit | <article or topic>: <N> claims, <S> supported, <U> unsupported/partial
```

If the user asks to keep the audit, crystallise it as a `type: archive` page (see Query > Crystallize), citing the audited article.

---

## Gotchas

The subtle failure points, worth checking before you finish an operation.

- **Path direction inside the wiki.** From `wiki/<topic>/`, a raw file is two levels up (`../../raw/<topic>/file.md`) and a same-topic article is just its filename. A wrong `../` count is the most common broken link.
- **Keep `updated` and the index in step.** Whenever an article's content changes (a cascade update or a supersession counts), bump `updated` in its frontmatter and the matching `index.md` row in the same pass. They are meant to agree, and drift between them is easy to miss.
- **Replace knowledge by superseding, not by editing in place or deleting.** When a new source overturns an old claim, write the replacement and mark the old page `status: stale` with `superseded_by` and a callout. The history is the point; preserve it rather than overwriting.
- **Auto-fix only the deterministic list.** Index, links, frontmatter, and See Also are safe to repair. For contradictions, stale claims, and orphans, surface them for the user instead of rewriting prose on your own authority.
- **Ingest is fetch and compile.** A source saved to `raw/` but never compiled into `wiki/` adds nothing. Finish both, and update `index.md` and `log.md`, before treating the ingest as done.
- **Long sources lose detail quietly.** Compiling a transcript or chat log straight to prose is where load-bearing claims and exact numbers get dropped or softened. For long or noisy sources, list the durable atoms first and re-read the source against your article before finishing (`references/high-fidelity-ingest.md`).
- **Only delete rich originals that live in `raw/`.** After extracting a binary to markdown, delete it only when it was inside `raw/` (which stays markdown-only) and the extraction is verified faithful. A PDF in the user's Downloads or a temp dir is theirs: extract a markdown copy into `raw/`, leave the original untouched, and do not link to it.

---

## Conventions

- Standard markdown throughout. YAML frontmatter on every article and raw file; relative links in bodies.
- `wiki/` supports one level of topic subdirectories only. No deeper nesting.
- Dates: today's date for log entries, `collected`, and `created`/`archived`. `updated` reflects when an article's knowledge content last changed. `published` comes from the source (`Unknown` when unavailable).
- Inside `wiki/` files use file-relative links; in conversation use project-root-relative paths.
- Supersession replaces deletion for outdated knowledge: mark stale, link the replacement, keep the page. Git carries the history.
- Ingest updates `wiki/index.md` and `wiki/log.md`. Crystallize (from Query) updates both. Lint updates `wiki/log.md`, and `wiki/index.md` only when auto-fixing index entries. Audit updates `wiki/log.md` only, and writes an archive page only if the user asks to keep the result. Plain queries write nothing.
- Recommend the wiki be a git repo so supersession and history have a real audit trail. Do not require it.
