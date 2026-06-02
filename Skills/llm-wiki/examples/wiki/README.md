# About this wiki

A personal knowledge base of plain markdown, built and maintained with the llm-wiki skill (part of https://github.com/sammcj/agentic-coding). It is meant to stay readable and editable without that skill or any other tool: every file is standard markdown with YAML frontmatter and relative links, so it renders on GitHub and opens as an Obsidian vault.

## Structure

- `raw/<topic>/` - immutable source material, one markdown file per source. Read, never edited after capture.
- `wiki/<topic>/<article>.md` - compiled articles, distilled from `raw/` and owned by whoever maintains the wiki.
- `wiki/index.md` - the catalogue: one row per article, grouped by topic. Start here.
- `wiki/log.md` - append-only history of ingests, queries, lints, and audits.

## Conventions, if you maintain this by hand

- Every article carries frontmatter: `title`, `type` (concept | entity | archive), `topic`, `created`, `updated`, `status` (current | stale), and `superseded_by`. Bump `updated` whenever an article's content changes, and keep the matching `index.md` row in step.
- Replace outdated knowledge by superseding, not deleting: set the old article's `status: stale` and `superseded_by`, add a `> [!warning] Superseded by ...` callout, and write the replacement as a new current article. Keeping the old page is the point - it explains why the current state exists.
- Cite sources, do not score them. Link the `raw/` file, and for a load-bearing claim point at the exact spot (a section, page, or timestamp), rather than attaching a confidence number a reader cannot check.
- Keep the wiki in git. History, rollback, and "how did this get here" come from version control, not from bespoke fields.

For the full ingest, query, lint, and audit workflow, use the llm-wiki skill.
