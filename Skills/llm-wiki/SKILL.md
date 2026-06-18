---
name: llm-wiki
description: "Use when building or maintaining a self-contained personal knowledge base (an LLM wiki) as plain markdown, optionally opened as an Obsidian vault. Triggers: ingesting sources into a wiki, querying wiki knowledge, linting wiki health, auditing article claims against their sources, critiquing the reasoning in a source or article, superseding stale knowledge, 'add to wiki', or any mention of 'LLM wiki' or 'Karpathy wiki'."
argument-hint: "[ingest | query | lint | audit | critique] [input]"
---

# LLM Wiki

Build and maintain a personal knowledge base as plain markdown. You manage two directories: `raw/` (immutable source material) and `wiki/` (compiled knowledge you own). Sources land in `raw/`, you compile them into `wiki/` articles, and the wiki compounds over time. Everything is local markdown with YAML frontmatter, readable on GitHub and openable as an Obsidian vault. No servers, no databases, no embeddings.

Core idea (Karpathy): the LLM writes and maintains the wiki; the human chooses sources and asks questions. Knowledge is compiled once at ingest and kept current, not re-derived on every query. That is the difference from RAG, which retrieves raw chunks and re-synthesises on every question.

## Invocation

**Query is the default.** Ingest, Lint, Audit, and Critique are the four deliberate operations - each opted into by its verb or by a request that plainly calls for it. Anything else is a Query against the wiki: a bare question, "what do I know about X", "summarise everything on Y". You do not need a `query` keyword to query; it is what the skill does unless one of the four operations is clearly being asked for.

A leading mode argument routes straight to that operation:

- `ingest` (alias `add`) - Ingest. Any trailing text is the source: a URL, a path, or pasted content.
- `lint` - Lint. Health checks; needs no further input.
- `audit` - Audit. Trailing text names the article or topic to verify.
- `critique` (alias `scrutinise`) - Critique. Trailing text names the article, topic, or pasted content whose reasoning to examine.
- `query` (alias `ask`) - Query. Rarely needed as an explicit keyword, but it forces query handling when a question might otherwise look like one of the four operations above.

So `/llm-wiki lint` runs Lint and `/llm-wiki ingest https://...` ingests that URL. Otherwise treat the whole argument as a natural-language request: route it to Ingest, Lint, Audit, or Critique only when it clearly calls for one, and answer everything else as a Query.

### What's always required, and what's scenario-gated

Every operation, always: you act only on the user's request (never background-write); any write compiles from a source already in `raw/` (never straight from a live URL or external path), then updates `wiki/index.md` and appends `wiki/log.md`; you bump an article's `updated` whenever its content changes; and you replace outdated knowledge by superseding it, never by deleting or editing in place. These hold across all five operations.

Everything else is scenario-gated, and its detailed protocol lives in `references/` - the authoritative procedure, which SKILL.md only summarises. When the request or the situation matches one - a rich-format source, a distilled extract, a long or noisy source, a concept map, the gap register, local content, a lint, an audit, a critique - you MUST read the named reference and follow it before acting, rather than working from memory or assuming you know the format or the steps. If a section points at a reference, that pointer is an instruction to open it, not a citation to note. When unsure whether a reference applies, read it and decide; the cost of reading is small next to the cost of corrupting the wiki by guessing.

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

Three layers, all under the user's project root, plus an optional `local/` for personal content.

**raw/** - Immutable source material. You read, never modify. Organised by topic subdirectories, e.g. `raw/machine-learning/`. The source of truth.

**wiki/** - Compiled knowledge articles. You have full ownership. One level of topic subdirectories only: `wiki/<topic>/<article>.md`. Four special files:
- `wiki/README.md` - Orientation for anyone opening the wiki without this skill: what the structure is and the conventions that keep it sound. Mostly static; created at init.
- `wiki/index.md` - Global catalogue. One row per article, grouped by topic, with link, summary, and Updated date. The entry point for queries.
- `wiki/log.md` - Append-only operation log with a greppable prefix.
- `wiki/gaps.md` - Register of known unknowns: concepts the wiki references but has not written, and questions it cannot answer. "What we don't know yet" to the index's "what we know".

**local/** (optional) - Personal markdown kept out of git: meeting prep, drafts, working notes, private sources. A sibling of `raw/` and `wiki/`, excluded by the wiki `.gitignore`, present in the user's clone only. It is a scratch bench, exempt from the index, log, gaps, cascade, and audit. One rule governs it: `local/` may link into `wiki/` and `raw/`, but no committed file may ever link into `local/` (broken for other clones, and it leaks the path into git). Full rules, query behaviour, and the promotion path: `references/local-content.md`.

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

`wiki/README.md` orients a reader who has the wiki but not this skill: the raw/wiki split, the frontmatter fields, supersession-not-deletion, and what index.md, log.md, and gaps.md are, with a pointer to the skill for the full workflow. It is the GitHub landing page for the wiki directory. Keep it high-level and mostly static - it describes the format, not the catalogue, so it does not change on every ingest. Do not copy the operational procedures from this file into it; point to them. Template: `references/templates/wiki-readme-template.md`.

`wiki/index.md` is the human-readable catalogue and the agent's first read on any query. Hand-maintained. If the user has Obsidian with Dataview, parts of it can be auto-generated from frontmatter, but never depend on a plugin: the maintained index.md is canonical.

`wiki/log.md` is append-only and chronological, a convenience over git history, which holds the canonical record. Each entry starts with `## [YYYY-MM-DD] <op> | <title>` so `grep "^## \[" wiki/log.md | tail -5` returns recent activity. Keep entries lean: the header carries the signal, and a sub-item names another article touched rather than narrating the change in prose. Operations only ever append; lint prunes the oldest entries for retention when the wiki is a git repo, so the file stays bounded and git recovers the rest.

`wiki/gaps.md` is the register of known unknowns. Two kinds of entry: `wanted` (a concept articles reference but no page covers) and `question` (something a source raised or a user asked that the wiki cannot answer). Entries are grouped by topic and ranked by evidence of demand - which articles reference the gap, how often it has been asked - never by a score. Gaps are captured during ingest, query, and lint, never by a background process; they close by a resolution link rather than deletion, the same as supersession; and the file is greppable (`grep "^### \[open\]" wiki/gaps.md`). Full format, capture rules, and lifecycle: `references/gaps.md`.

### Initialisation

Triggers only on the first Ingest. Check whether `raw/` and `wiki/` exist. Create only what is missing; never overwrite existing files:

- `raw/` directory (with `.gitkeep`)
- `wiki/` directory (with `.gitkeep`)
- `wiki/README.md` - orientation doc from `references/templates/wiki-readme-template.md`
- `wiki/index.md` - heading `# Knowledge Base Index`, empty body
- `wiki/log.md` - heading `# Wiki Log`, empty body
- `wiki/gaps.md` - heading `# Knowledge Gaps`, empty body (`references/gaps.md`)
- `.gitignore` (project root) - from `references/templates/wiki-gitignore-template.md`. Excludes `local/` and per-machine editor noise so the wiki can live in git cleanly. Do not overwrite an existing one; merge in the `local/` line if missing.
- `SKILL.md` (project root) - lets the wiki load as a query-only Agent Skill, from `references/templates/wiki-skill-template.md`. See "The wiki as a skill" below.
- `CLAUDE.md` (project root) - project memory that orients any agent whose working directory is the wiki repo and tells it to activate the llm-wiki skill if present, from `references/templates/wiki-claude-md-template.md`. See "The wiki's CLAUDE.md" below.

`local/` is not created at init; it appears the first time the user stores personal content there (`references/local-content.md`).

If Query or Lint cannot find the wiki structure at the working directory, first check whether the directory instead holds several wiki subdirectories (each with its own `wiki/` and `raw/`): that is a multi-wiki setup, handled per "Working across separate wikis" above, not an uninitialised wiki. Only when neither a wiki nor sibling wikis are present, tell the user: "Run an ingest first to initialise the wiki." Do not auto-create.

### The wiki as a skill

`SKILL.md` at the project root lets an agent load the wiki as an Agent Skill and *query* it without this skill present. It is a different file from this skill's own SKILL.md: lightweight, mostly links into `wiki/index.md` and `wiki/README.md`, and read-only. Write it at init from `references/templates/wiki-skill-template.md`, which carries the exact format.

- **Name and describe it from the content.** Name it `<subject>-llm-wiki` (e.g. `ml-llm-wiki`, `team-runbook-llm-wiki`), choosing the prefix from the wiki's subject or audience, so the name signals it is an llm-wiki. A skill's name must match the directory it loads from, so tell the user to load the wiki directory under that name. Write a `description` that says what the wiki is for and names concrete trigger topics. At init the wiki may be near-empty - write your best guess from the first sources or the user's stated purpose, and refresh `name` and `description` as it grows.
- **Query only; writes go through llm-wiki.** The file routes every add, update, supersede, lint, and audit back to this skill, and reminds the user that llm-wiki is required to keep the wiki current. It must not describe a write workflow of its own. When you create it, tell the user that the llm-wiki skill must stay installed to maintain the wiki.
- Created at init, never overwritten. Lint reports a missing one and offers to add it to wikis that predate this (`references/lint.md`).

### The wiki's CLAUDE.md

`CLAUDE.md` at the project root is project memory: an agent auto-loads it whenever the wiki repo is its working directory, no skill required. It complements the root SKILL.md - SKILL.md loads by description match, CLAUDE.md by location, so it is the entry point for an agent working *inside* the wiki. Keep it tiny: state what the repo is, point the agent at the root SKILL.md to learn how to interface with the wiki, and tell it to activate the **llm-wiki** skill if available (otherwise treat the wiki as read-only and route writes through it). It defers the query steps to SKILL.md rather than repeating them. Write it at init from `references/templates/wiki-claude-md-template.md`; created once, never overwritten. Lint reports a missing one and offers to add it (`references/lint.md`).

### Working across separate wikis

A user may keep several independent wikis side by side - each a full, self-contained llm-wiki cloned wherever they like (e.g. `~/git/wikis/{ml,payments,ops}/`). The wikis do not nest and do not know about each other; there is no host wiki and no shared root inside any of them.

When your session's working directory holds more than one wiki (subdirectories that each have their own `wiki/` and `raw/`), you are in a multi-wiki setup. Two rules then apply, and the full protocol is in `references/multiple-wikis.md` - read it before querying or maintaining across wikis:

- **Catalogue them in `WIKI-INDEX.md`.** Maintain a `WIKI-INDEX.md` at that working directory (create it if missing): what each wiki is for and how to tell them apart, plus the cross-wiki rules below. If a wiki's purpose is not clear from its own README/SKILL, ask the user rather than guessing.
- **Each wiki is isolated; read its own instructions first.** Before you query or change a wiki, read that wiki's own `CLAUDE.md` and `SKILL.md` (and any skill it bundles) - they do not auto-load from a parent directory. No wiki links or refers to another. If a fact in one wiki is worth having in another, ask the user, then add a version to the target as a normal ingest (cite the true origin; never link across wikis).

---

## Ingest

Fetch a source into `raw/`, then compile it into `wiki/`. Always both steps.

### Decide how much of the source to keep

Decide this before fetching or converting; it sets what lands in `raw/`.

- **Verbatim (default)** - a faithful copy of the source, the immutable ground truth Audit checks against. Use it unless the user asks otherwise.
- **Distilled** - the high-signal content only, with filler removed. Choose it when the user asks for "the valuable content", "the high-signal parts", "the useful bits", "just the signal", "the key points", "what matters" or similar - phrasing that wants the substance, not the whole source. Follow `references/distilled-ingest.md`, which distils by *removing* filler rather than generalising specifics away, and ends in a mandatory separate-sub-agent review so nothing load-bearing is cut.

Pick one mode per source. A rich format (a docx transcript, a PDF) does not decide it: convert to markdown as an intermediate step, then keep or distil per the chosen mode. Converting a transcript and copying it in whole when the user asked for the signal is the failure to avoid. If a long, noisy source carries no instruction either way, ask rather than defaulting to a verbatim dump.

### Fetch (raw/)

1. Get the source content using whatever web or file tools your environment provides. If nothing can reach the source, ask the user to paste it directly.

2. **Filter before writing.** Strip secrets and credentials (API keys, tokens, passwords) and obvious private data (PII that is not the point of the source). If a source is mostly sensitive, flag it and ask the user before saving rather than redacting silently.

3. Pick a topic directory. Check existing `raw/` subdirectories first; reuse one if the topic is close enough. Create a new subdirectory only for genuinely distinct topics.

4. Save as `raw/<topic>/YYYY-MM-DD-descriptive-slug.md`:
   - Slug from source title, kebab-case, max 60 characters.
   - Published date unknown -> omit the date prefix from the file name. The frontmatter `published` field still appears, set to `Unknown`.
   - If a file with the same name exists, append a numeric suffix, e.g. `descriptive-slug-2.md`.
   - Include frontmatter (source, collected, published) and preserve the original text (verbatim mode; a distilled extract follows `references/distilled-ingest.md` instead). Clean formatting noise; do not rewrite opinions.

   See `references/templates/raw-template.md` for the exact format.

Tip: Use sub-agents with well defined goals, scope and context to parallelise work and reduce context rot in the main conversation.

### Rich and external sources

`raw/` holds durable markdown only. When a source is a rich format (PDF, Word, slides, images, spreadsheets), convert it to markdown before saving, following `references/rich-format-ingest.md`: it covers structure preservation, the faithfulness review, and what to do with the original file. If the user asked for the high-signal content rather than the whole source (see "Decide how much of the source to keep"), the converted markdown is an intermediate step, not the raw file you keep - distil it per `references/distilled-ingest.md`.

**Compile only from `raw/`.** Land every source as markdown in `raw/` before compiling, never straight from a live URL or an external path (a temp file vanishes, a URL changes; the Raw provenance link must persist). If a markdown file is already in `raw/`, skip the fetch and compile it directly.

Another of the user's wikis can be the origin of a source. To carry a fact across, re-land its underlying source into this wiki's `raw/` and compile it like any normal ingest, citing the true upstream origin - never a link into the other wiki. The cross-wiki rules are in `references/multiple-wikis.md`.

### Compile (wiki/)

Decide where the new content belongs:

- **Same core thesis as an existing article** -> Merge into it. Add the new source to the article's Sources/Raw lines. Update affected sections and bump `updated`.
- **New concept** -> Create a new article in the most relevant topic directory. Name the file after the concept, not the raw file. Write full frontmatter. Give it at least one inbound link from a related article (a See Also or an in-body reference), not just an `index.md` row - an article nothing links to is an orphan.
- **Spans multiple topics** -> Place in the most relevant directory; add See Also links to related articles elsewhere.

These are not exclusive: one source may merge into an existing article while also creating a new article for a distinct concept it introduces.

When a source is persuasive or argumentative rather than factual - an opinion piece, a vendor's case for its product, a strategy memo - consider a Critique pass (`references/critical-analysis.md`) before compiling it as settled knowledge, so its reasoning risks are on record. Report them and let the user decide; a common outcome is to attribute a contested claim to its source rather than assert it, or to log the open question in `gaps.md`.

**One article, one concept.** Merging keeps related knowledge together, but repeated merges can grow an article past its thesis. When an article has come to cover more than one distinct concept - typically visible as top-level sections that could each stand alone - split the secondary concept into its own article, leave a one-line summary and a See Also link in its place, and cross-link the two. Split on concept boundaries, not length: a long article on a single concept is fine. As a rough prompt to recheck scope, revisit an article that climbs past ~400-500 lines, but never split on line count alone.

**Concept maps (optional).** When several articles relate in a way prose handles poorly - branching, convergence, a supersession or causal chain - a small mermaid diagram can earn its place. Draw one only when it adds what a sentence cannot; a map that restates the See Also list or a linear `A -> B -> C` is noise, and a map with no value is worse than none. A map in a current article is load-bearing: it carries a `map-sources` marker and is maintained on cascade updates; a map in a `type: archive` page is a dated snapshot. The when/when-not test, the colour palette, the format, freshness, and how to brief a sub-agent to draw one (sub-agents propose, you embed) are in `references/concept-map.md`.

See `references/templates/article-template.md` for the format. Provenance lives in the body as clickable links:
- Sources line: author, organisation, or publication + date, semicolon-separated.
- Raw line: markdown links to `raw/` files, semicolon-separated.

### Long-form and noisy sources

Transcripts, chat logs, long articles, and interview notes carry load-bearing detail that one compile pass can silently drop or soften. When a source is long or noisy, extract the durable items (decisions, claims, numbers, named entities, open questions) as a list first, write the article from that list, then re-read the source once against the article to confirm nothing important was lost, hardened, or overstated. Keep the source's exact terms, figures, and hedging, and anchor the heaviest claims with an inline quote and a locator (the section, page, or timestamp) next to their raw link. For short, clean, single-claim sources the normal compile above is enough. Full protocol: `references/high-fidelity-ingest.md`.

### Distilling an external source

When the retention mode is distilled (see "Decide how much of the source to keep") - the user points at a verbose external source like a meeting transcript, call notes, or a long thread and wants its valuable content kept rather than the whole source - read `references/distilled-ingest.md` and follow it. The extract saved to `raw/` is marked `fidelity: distilled` (a derived artefact, not the verbatim source). The protocol distils by cutting filler and repetition without generalising away specifics - numbers, hedging, dissent, owners, conditionals, and open questions all stay - and ends in a mandatory critical review by a separate sub-agent before the source may be discarded, the guard against over-zealous cutting. This is the opposite choice from "Long-form and noisy sources" above, which keeps the verbatim source in `raw/`.

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

Update `wiki/gaps.md` if this ingest touched the frontier of what is known: record a load-bearing open question the source raised but did not answer, or a concept you forward-referenced with no page yet, as a new entry; and close (resolve-and-link) any gap a new article filled. Skip it when nothing changed. See `references/gaps.md`.

Append to `wiki/log.md`:

```
## [YYYY-MM-DD] ingest | <primary article title>
- Created: <additional new article title>
- Updated: <cascade-updated article title>
- Superseded: <old article title> -> <new article title>
```

Omit any sub-item that does not apply. The header names the primary new article; `- Created:` lists any additional articles the same source produced. Refer to articles by title, not file path, and keep each sub-item to the title alone - the article body and the git diff hold what changed, so do not restate it here.

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
5. If `local/` exists, search it too and fold in any relevant personal notes, labelling each hit clearly as `local/ (uncommitted)` so it is never mistaken for shared knowledge (`references/local-content.md`). A query runs against one wiki; never silently fold another of the user's wikis into the answer. If the question really spans wikis, say so and ask which to draw on (`references/multiple-wikis.md`).
6. Output the answer in the conversation. Do not write files unless asked.
7. **Capture a miss.** If the wiki could not answer, or answered only partially, and the question sits within the wiki's subject, propose recording it in `wiki/gaps.md`: append today's date to a matching gap's demand evidence, or add a new `question` entry. Record only with the user's go-ahead; a plain query writes nothing on its own. See `references/gaps.md`.

When the user asks not just what the wiki says but whether the reasoning behind it holds - to scrutinise or stress-test an answer or a wiki position rather than retrieve it - switch to Critique and follow `references/critical-analysis.md`.

### Crystallise (archive)

When the user asks to save the answer to the wiki, file it as a first-class page so the exploration compounds like an ingested source.

1. Write the answer as a new article with `type: archive`. See `references/templates/archive-template.md`. Convert conversation citations to file-relative paths (e.g. `wiki/topic/article.md` becomes `../topic/article.md`, or `article.md` for the same directory).
   - Sources line: markdown links to the wiki articles the answer cites.
   - No Raw line (content does not come from `raw/`).
   - Capture the question, the findings, the articles and entities involved, and any lesson worth keeping as a standalone point.
   - When the relationships are non-linear, a concept map can capture them; in an archive it is a snapshot (no `map-sources` marker, never cascade-checked). See `references/concept-map.md`.
   - File name reflects the query topic; place in the most relevant topic directory.
2. Always create a new page; never merge an archive into an existing article.
3. Update `wiki/index.md`, prefixing the summary with `[Archived]`.
4. Append to `wiki/log.md`:
   ```
   ## [YYYY-MM-DD] query | Archived: <page title>
   ```

---

## Lint

Health checks on the wiki, in two tiers with different authority. The load-bearing boundary: **deterministic problems are auto-fixed; anything needing judgement is reported, never silently rewritten.** You never rewrite article prose on your own authority. Lint checks the wiki's internal consistency; to verify an article against the sources it cites, use Audit.

**Before fixing anything you MUST read `references/lint.md` and follow it** - it enumerates every check in each tier and its exact fix behaviour. SKILL.md states only the boundary; the checks below are an index, not the procedure.

- **Deterministic (auto-fix):** index consistency, internal and raw links, frontmatter, See Also, log retention, the wiki skill file's links, concept-map freshness, the gap register, and the `local/` leak guard. Safe to repair without asking.
- **Heuristic (report only):** factual contradictions, supersessions never marked stale, orphan pages, missing cross-references, undocumented concepts (propose as `wanted` gaps), open gaps an article now answers, multi-concept articles, drifted archives, low-value concept maps, and a missing root `SKILL.md`, `CLAUDE.md`, or wiki `.gitignore`. Surface them; never auto-fix.

Two dependency-free helpers back the deterministic tier, read-only and run with `uv` when available: `scripts/lint_wiki.py <project-root>` for structural findings (frontmatter, index, links, raw, and the `local/` leak guard) and `scripts/lint_mermaid.py` for concept-map validity. Run them rather than improvising a shell script (a heredoc mangles `!`); when `uv` is absent, fall back to grep and the file tools, and check mermaid by eye. The helpers detect; you apply the fixes.

### Post-lint

Append to `wiki/log.md`:

```
## [YYYY-MM-DD] lint | <N> issues found, <M> auto-fixed
```

---

## Audit

Verify that an article's claims hold up against the `raw/` sources it cites. Where Lint checks internal consistency (links, frontmatter, index), Audit checks external fidelity: do the cited sources actually support what the article says - the verification the evidence chains imply but never enforce. Opt-in and user-invoked on a named article or topic, never automatic; it reads every cited source in full. Triggers: "audit X", "check the citations on Y", "does the wiki still match its sources".

**Before auditing you MUST read `references/audit.md` and follow it** - it carries the claim-extraction steps, the per-source sub-agent prompt, and the verdict schema. In outline: pick the target (skip `status: stale` and `type: archive` pages unless asked); list the article's provenance-bearing claims, including each labelled concept-map edge, and map each to the `raw/` file that should back it (a load-bearing claim with no cited source is itself a finding); dispatch one read-only sub-agent per source in parallel to verdict each claim - `supported`, `partial`, `unsupported`, or `source-missing` - with the passage that backs it; aggregate worst-first and report, quoting what the source actually says for anything not `supported`. Report only - never rewrite article prose on your own authority (the same boundary as Lint's heuristic tier); a failed claim is surfaced for the user to fix, supersede, or accept.

### Post-audit

Append to `wiki/log.md`:

```
## [YYYY-MM-DD] audit | <article or topic>: <N> claims, <S> supported, <U> unsupported/partial
```

If the user asks to keep the audit, crystallise it as a `type: archive` page (see Query > Crystallise), citing the audited article.

---

## Critique

Examine the reasoning in a source or article and report what holds up. Where Audit checks external fidelity (do the cited `raw/` sources support the claims), Critique checks internal soundness: argument structure, hidden assumptions, logical fallacies, bias risk, internal consistency. It deliberately does not fact-check empirical claims against the world - that is Audit's job - so the two are complementary halves of "is this knowledge trustworthy". Like Audit, it is opt-in, user-invoked, read-only, and reports its findings; it never rewrites prose. It runs on whatever the user points at - a `raw/` source, a `wiki/` article, or pasted content - and needs no `raw/` to run. Triggers: "critique X", "is this argument sound?", "what is this assuming?", "stress-test the reasoning in Y".

**Before critiquing you MUST read `references/critical-analysis.md` and follow its analysis steps and output structure - do not work from memory.** In outline: pick the target (or several); work through the reasoning - understand the argument as the author would state it, isolate the core claims, weigh the evidence, spot logical issues, surface hidden assumptions, check what is missing and whether it is internally consistent; report the four sections - Summary, Key Issues, Questions to Probe, Bottom Line. Say so plainly when the reasoning is sound; do not manufacture criticism. For many targets, fan out one read-only sub-agent per target in parallel, then present grouped weakest-first.

### Post-critique

Append to `wiki/log.md`:

```
## [YYYY-MM-DD] critique | <article, topic, or source>: <overall assessment>
```

Critique writes nothing else on its own. With the user's go-ahead it may crystallise the analysis as a `type: archive` page (see Query > Crystallise) citing the critiqued target, or record an assumption or open question it surfaced as a `question` gap in `wiki/gaps.md` (`references/gaps.md`). Full protocol, output structure, and guidelines: `references/critical-analysis.md`.

---

## Optional: graphify as an external lens

If the **graphify** skill or tool is available, you can run it over the wiki as a disposable, read-only knowledge-graph lens: to see how articles actually connect, surface orphans and missing cross-references, triage a large `raw/` corpus before ingest, or answer connection-heavy cross-document questions. The graph stays external. Markdown remains the source of truth; `graphify-out/` is generated and gitignored, never committed or treated as a parallel store; and any finding is acted on only through normal llm-wiki operations (a See Also, a `gaps.md` entry, a supersession, a Query answer), verified against the markdown first. This does not contradict the design philosophy's exclusion of a knowledge-graph database: the graph is a throwaway analysis pass, not stored wiki infrastructure. **When you reach for graphify, read `references/graphify.md` first and follow it.**

---

## Gotchas

The subtle failure points, worth checking before you finish an operation.

**Paths and consistency**

- **Path direction inside the wiki.** From `wiki/<topic>/`, a raw file is two levels up (`../../raw/<topic>/file.md`) and a same-topic article is just its filename. A wrong `../` count is the most common broken link.
- **Keep `updated` and the index in step.** Whenever an article's content changes (a cascade update or a supersession counts), bump `updated` in its frontmatter and the matching `index.md` row in the same pass. They are meant to agree, and drift between them is easy to miss.

**Ingest fidelity**

- **Ingest is fetch and compile.** A source saved to `raw/` but never compiled into `wiki/` adds nothing. Finish both, and update `index.md` and `log.md`, before treating the ingest as done.
- **Long sources lose detail quietly.** Load-bearing claims and exact numbers get dropped or softened when a transcript or chat log is compiled straight to prose. List the durable atoms first and re-read the source against your article before finishing (`references/high-fidelity-ingest.md`).
- **Extract the signal when asked; don't convert-and-dump.** When the user wants "the valuable content" or "the high-signal parts" - especially of a verbose source like a transcript - distilling is the job, not copying the whole thing in with the hellos and banter intact; a rich format (docx, PDF) is converted only as an intermediate step (`references/distilled-ingest.md`).
- **Only delete rich originals that live in `raw/`.** After extracting a binary to markdown, delete it only when it was inside `raw/` (which stays markdown-only) and the extraction is verified faithful. A PDF in the user's Downloads or a temp dir is theirs: extract a markdown copy into `raw/`, leave the original untouched, and do not link to it.

**Lifecycle and authority**

- **Replace knowledge by superseding, not by editing in place or deleting.** Write the replacement, mark the old page `status: stale` with `superseded_by` and a callout, and keep it - the history is the point. Full mechanic: Conflicts and supersession, above.
- **Auto-fix only the deterministic list.** Index, links, frontmatter, and See Also are safe to repair; surface contradictions, stale claims, and orphans for the user rather than rewriting prose on your own authority (see Lint).
- **Critique and Audit answer different questions.** Audit checks whether the cited `raw/` sources support an article's claims (external fidelity); Critique checks whether the reasoning itself holds up (internal soundness) and does not fact-check claims against the world. Both report only - neither rewrites prose on its own authority (`references/critical-analysis.md`, `references/audit.md`).
- **Gaps are a frontier, not a wishlist.** Record a `wanted` page or open `question` only when evidence backs it - an article references it, or a query asked it - and close gaps by resolution link rather than letting filled ones linger (`references/gaps.md`).

**Maps and separate wikis**

- **Concept maps drift silently.** A current-article map is load-bearing: when the article changes, the prose gets updated but the map can keep asserting the old relationships. Recheck it on cascade updates, keep its `map-sources` marker accurate, and remove it once it no longer adds value (`references/concept-map.md`).
- **Keep separate wikis separate.** When the user has several wikis side by side, each operates in isolation: read the target wiki's own `CLAUDE.md` and `SKILL.md` before touching it (they do not auto-load from a parent directory), never link or fold one wiki's content into another, and carry a fact across only by re-ingesting its source into the target with the user's go-ahead. Catalogue the wikis in a `WIKI-INDEX.md` at the directory holding them (`references/multiple-wikis.md`).

---

## Conventions

**Format, paths, and dates**

- Standard markdown throughout. YAML frontmatter on every article and raw file; relative links in bodies.
- `wiki/` supports one level of topic subdirectories only. No deeper nesting.
- Dates: today's date for log entries, `collected`, and `created`/`archived`. `updated` reflects when an article's knowledge content last changed. `published` comes from the source (`Unknown` when unavailable).
- Inside `wiki/` files use file-relative links; in conversation use project-root-relative paths.
- A distilled raw (`fidelity: distilled`, `references/distilled-ingest.md`) holds an extract of a verbose external source instead of the verbatim original. It is produced through a separate-sub-agent review gate and audited with the weaker guarantee a derived source implies.

**Supersession, gaps, maps, and critique**

- Supersession replaces deletion for outdated knowledge: mark stale, link the replacement, keep the page. Git carries the history.
- `wiki/gaps.md` registers known unknowns (`references/gaps.md`): `wanted` pages and open `question`s, grouped by topic, ranked by evidence not a score, and closed by a resolution link rather than deletion. Record only gaps with evidence behind them.
- Concept maps are optional and value-gated (`references/concept-map.md`): a current-article map is load-bearing and carries `map-sources`; an archive map is a snapshot. Validate with `scripts/lint_mermaid.py` when `uv` is available.
- Critique (`references/critical-analysis.md`) examines reasoning quality - argument structure, hidden assumptions, fallacies, bias risk, internal consistency - and is the internal-soundness counterpart to Audit's external-fidelity check. It deliberately does not fact-check claims against sources. Opt-in, read-only, reports a four-section analysis, and never rewrites prose.

**Operational behaviour**

- Ingest updates `wiki/index.md` and `wiki/log.md`, and `wiki/gaps.md` when it touches the knowledge frontier. Crystallise (from Query) updates the index and log. Lint updates `wiki/log.md`, `wiki/index.md` only when auto-fixing index entries, and `wiki/gaps.md` when closing or proposing gaps. Audit updates `wiki/log.md` only, and writes an archive page only if the user asks to keep the result. Critique updates `wiki/log.md` only, and writes an archive page or a `gaps.md` question only if the user asks to keep the result. A plain query writes nothing on its own; with the user's go-ahead it may add a missed question to `wiki/gaps.md`.
- Ensure sub-agents have clear goals and scope to understand the context of the work they're tasked with. Use forked sub-agents (if available) when sub-agent tasks require the complete conversation history.

**Repo infrastructure**

- A root `SKILL.md` (`references/templates/wiki-skill-template.md`) lets the wiki load as a query-only Agent Skill; it is created at init, named `<subject>-llm-wiki`, and routes all writes back through this skill.
- A root `CLAUDE.md` (`references/templates/wiki-claude-md-template.md`) is project memory that orients any agent whose working directory is the wiki repo and tells it to activate the llm-wiki skill if available. It loads by location where the root SKILL.md loads by description match; created at init, never overwritten.
- `local/` (`references/local-content.md`) is optional, gitignored personal content in the user's clone only, exempt from the index/log/gaps/cascade/audit machinery (Critique may still run on it when the user points at it). Local files may link into `wiki/` and `raw/`; no committed file may link into `local/`. Query scans it and labels hits `local/ (uncommitted)`. Init writes a wiki `.gitignore` (`references/templates/wiki-gitignore-template.md`) that excludes it.
- Multiple wikis (`references/multiple-wikis.md`) are independent, side-by-side llm-wikis the user clones wherever they like; they do not nest and do not reference each other. When a session's working directory holds more than one, catalogue them in a `WIKI-INDEX.md` there, read each wiki's own `CLAUDE.md`/`SKILL.md` before querying or maintaining it, and carry a fact across only by re-ingesting its source into the target wiki with the user's go-ahead - never a cross-wiki link.
- Recommend the wiki be a git repo so supersession and history have a real audit trail. Do not require it.
