# Ingest: the full procedure

Fetch a source into `raw/`, then compile it into `wiki/`. Both steps, every time.

SKILL.md carries the parts that are decided before this procedure starts or that override it: the retention mode (verbatim vs distilled), the compile-only-from-`raw/` rule, and conflicts and supersession. This file is the procedure itself.

## Fetch (raw/)

1. Get the source content with whatever web or file tools your environment provides. If nothing can reach the source, ask the user to paste it directly.
2. **Filter before writing.** Strip secrets and credentials (API keys, tokens, passwords) and obvious private data (PII that is not the point of the source). If a source is mostly sensitive, flag it and ask the user before saving rather than redacting silently.
3. Pick a topic directory. Check existing `raw/` subdirectories first and reuse one if the topic is close enough. Create a new subdirectory only for a genuinely distinct topic.
4. Save as `raw/<topic>/YYYY-MM-DD-descriptive-slug.md`:
   - Slug from the source title, kebab-case, max 60 characters.
   - Published date unknown -> omit the date prefix from the file name. The frontmatter `published` field still appears, set to `Unknown`.
   - A file of the same name already exists -> append a numeric suffix, e.g. `descriptive-slug-2.md`.
   - Include frontmatter (source, collected, published) and preserve the original text. Clean formatting noise; do not rewrite opinions. A distilled extract follows `references/distilled-ingest.md` instead.
   - Exact format: `references/templates/raw-template.md`.

`raw/` holds durable markdown only. Convert a rich format (PDF, Word, slides, images, spreadsheets) to markdown before saving, per `references/rich-format-ingest.md`.

When the source originated in another of the user's wikis, re-land its underlying source into this wiki's `raw/` and cite the true upstream origin, never a link into the other wiki (`references/multiple-wikis.md`).

Fan the extract work out to sub-agents with defined goals, scope and context to keep the main conversation lean.

## Compile (wiki/)

Decide where the new content belongs:

- **Same core thesis as an existing article** -> merge into it. Add the new source to the article's Sources/Raw lines, update the affected sections, bump `updated`.
- **New concept** -> create an article in the most relevant topic directory. Name the file after the concept, not the raw file. Write full frontmatter. Give it at least one inbound link from a related article (a See Also or an in-body reference), not just an `index.md` row - an article nothing links to is an orphan.
- **Spans multiple topics** -> place it in the most relevant directory and add See Also links to related articles elsewhere.

These are not exclusive: one source may merge into an existing article while also creating a new article for a distinct concept it introduces.

**One article, one concept.** Repeated merges can grow an article past its thesis. When an article covers more than one distinct concept - typically visible as top-level sections that could each stand alone - split the secondary concept into its own article, leave a one-line summary and a See Also link in its place, and cross-link the two. Split on concept boundaries, not length: a long article on a single concept is fine. Revisit an article's scope once it climbs past ~400-500 lines, but never split on line count alone.

Format: `references/templates/article-template.md`. Provenance lives in the body as clickable links:

- Sources line: author, organisation, or publication + date, semicolon-separated.
- Raw line: markdown links to `raw/` files, semicolon-separated.

## Cascade updates

After the primary article, check for ripple effects:

1. Scan articles in the same topic directory for content the new source affects.
2. Scan `wiki/index.md` entries in other topics for related concepts.
3. Update every materially affected article and bump its `updated` date.

Never cascade-update `type: archive` or `status: stale` pages. Archives are snapshots; stale pages are history.

## Post-ingest

**`wiki/index.md`** - add or update an entry for every touched article. A new topic section gets a one-line description; the per-topic bullet form is in `references/templates/index-template.md`. Prefix a stale article's summary with `[Stale]`.

**`wiki/gaps.md`** - only when this ingest touched the frontier of what is known. Record a load-bearing open question the source raised but did not answer, or a concept you forward-referenced with no page yet; close (resolve-and-link) any gap a new article filled. Skip it when nothing changed. Format and lifecycle: `references/gaps.md`.

**`wiki/log.md`** - append under today's date heading:

```
* **Ingest**: compiled [<primary article>](<path>); created [<additional article>](<path>); updated [<cascade-updated article>](<path>).
* **Supersession**: [<old article>](<path>) superseded by [<new article>](<path>).
```

Drop any clause or bullet that does not apply. The **Ingest** bullet names the primary article first, then any additional articles the same source created and any cascade-updated articles; a supersession gets its own **Supersession** bullet. Link each article with the title as the link text; the article body and the git diff hold what changed, so do not restate it here.
