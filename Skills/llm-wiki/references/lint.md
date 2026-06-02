# Lint: the full check list

Health checks on the wiki, in two tiers with different authority. Deterministic problems are fixed automatically; anything needing judgement is reported, never silently rewritten. You do not rewrite article prose on your own authority. The two-tier boundary and the post-lint log entry live in SKILL.md; this file is the enumerated checks each tier runs.

## Deterministic checks (auto-fix)

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

## Heuristic checks (report only)

Rely on judgement. Report findings; do not auto-fix.

- Factual contradictions across articles that lack a conflict annotation.
- Claims a newer source has superseded but that were never marked stale.
- Orphan pages with no inbound links (no backlinks from other articles).
- Missing cross-topic references.
- Concepts mentioned often but lacking their own page.
- Archive pages whose cited source articles have changed substantially since archival. For a deeper version of this check that reads the cited sources and verdicts each claim, see `references/audit.md`.
