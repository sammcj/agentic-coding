# Lint: the full check list

Health checks in two tiers: deterministic problems are fixed automatically; anything needing judgement is reported, never silently rewritten. You do not rewrite article prose on your own authority.

## Deterministic checks (auto-fix)

Run `uv run scripts/lint_wiki.py <project-root>` for the `frontmatter`, `index`, `links`, `raw` and `local` findings below (read-only; `--checks` selects a subset, `--json` for machine output, exit 1 on any finding). It detects; you apply the fixes below. Without `uv`, fall back to `grep` and the file tools - never heredoc a one-off script through the shell: `!` gets backslash-escaped and corrupts the code. Unscripted (use the file tools and grep): See Also, log retention, the wiki skill file's links, concept-map freshness, `map-sources` resolution, the gap register.

**Index consistency** - compare `wiki/index.md` against the `wiki/` files (excluding README.md, index.md and log.md):
- File exists but missing from index -> add a bullet `* [Title](path) - (no summary)` under its topic section (no date column).
- Index entry points to a nonexistent file -> mark it `[MISSING]`. Do not delete; the user decides.

**Internal links** - for every markdown link in article bodies (including Sources lines), excluding Raw links and README.md/index.md/log.md:
- Target missing -> search `wiki/` for a file of the same name. Exactly one match: fix the path. Zero or several: report.

**Raw references** - every Raw link must point to an existing `raw/` file:
- Target missing -> search `raw/` for a file of the same name. Exactly one match: fix. Zero or several: report.

**Frontmatter** - well-formed frontmatter on every article:
- Missing required field (`title`, `type`, `topic`, `created`, `updated`, `status`) -> fill what is derivable (topic from folder, dates from file or index), report the rest.
- `status: stale` but no `superseded_by`, or no supersession callout -> report; do not guess the replacement.
- `superseded_by` points to a nonexistent file -> report.

**See Also** - within each topic directory: add missing cross-references between related articles; remove links to deleted files.

**Wiki skill file** - if a root `SKILL.md` exists (the query-only skill, `references/templates/wiki-skill-template.md`), its links into `wiki/` must resolve: a missing target gets the internal-link treatment (search `wiki/` for a same-named file, fix a single match, report zero or several). Do not touch its `name` or `description` - judgement (heuristic tier).

**Log retention** - only when the wiki is a git repo. If `wiki/log.md` holds more than ~12 months of `## YYYY-MM-DD` sections, remove the oldest whole sections, keeping everything from the last 12 months and at least the 20 most recent date sections. Preserve the `# Wiki Log` heading and format comment, and leave one marker line under the heading: `<!-- Older entries trimmed; full history in git: git log -p wiki/log.md -->`. Never trim a non-git wiki (the log is then the only history); report its size instead.

**Concept maps** - for `mermaid` blocks in articles (rules in `references/concept-map.md`):
- Validate syntax when `uv` is present: `uv run scripts/lint_mermaid.py --require-edge-labels --max-nodes 12 <files>`. Without `uv`, check the block by eye - never block the lint on a missing tool. Fix or report each reported error.
- `map-sources` paths must resolve, the same as an internal link: search for a same-named file, fix a single match, report zero or several.
- Freshness: for a map in a `current` (non-archive) article, if any `map-sources` article's `updated` is newer than the host article's `updated`, annotate the block `<!-- stale-map: <source> updated YYYY-MM-DD after host -->`. Annotate only; redrawing is judgement. Skip `type: archive` and `status: stale` pages (their maps are snapshots).

**Local-content leak guard** - no committed file may link into `local/` (`references/local-content.md`). Scan tracked files (`wiki/`, `raw/`, `index.md`, `log.md`, `gaps.md`, `README.md`, root `SKILL.md` and `CLAUDE.md`) for links resolving into `local/`, e.g. `grep -rnE '\]\(\.{0,2}/?(\.\./)*local/' wiki/ raw/ SKILL.md`. Report each; the fix (drop the link, or promote the local draft into `raw/` + `wiki/`) is judgement, so do not rewrite the prose. `local/` itself is never scanned; its internals are exempt from every lint check.

**Gaps register** - for `wiki/gaps.md` (format in `references/gaps.md`):
- A missing `wiki/gaps.md` is not a finding. Do not create an empty one proactively; it is created at init, or the first time a gap needs recording (heading `# Knowledge Gaps`).
- Every link in a gap entry (`Raised by`, `Referenced by`, and a resolution target) must resolve, the same as an internal link: search for a same-named file, fix a single match, report zero or several.
- Auto-close fulfilled `wanted` gaps: if an `[open] wanted` gap names a concept that now has an article (file or title match), change `[open]` to `[resolved]`, drop the evidence lines, and append `-> [Article](path) (today)`. Closing a `question` is judgement and stays in the heuristic tier.
- Retention: only when the wiki is a git repo, prune the oldest `[resolved]` entries on the same rule as the log. Never prune `[open]` entries, and never prune a non-git wiki.

## Heuristic checks (report only)

Report findings; do not auto-fix.

- Factual contradictions across articles that lack a conflict annotation.
- Claims a newer source has superseded but never marked stale.
- Orphan pages (no inbound links). This is a connectivity gap, not a knowledge gap: the fix is a See Also, not a `gaps.md` entry.
- Missing cross-topic references.
- Concepts mentioned often but lacking their own page. Propose each as a `wanted` gap (`references/gaps.md`); add it only with the user's go-ahead, never auto-author the article.
- Open `question` gaps that an existing article now appears to answer. Propose closing with a resolution link; confirm rather than auto-fix.
- Articles covering more than one distinct concept (several top-level sections that could each stand alone) - candidates for splitting into linked articles.
- Concept maps that do not earn their place: two-node, purely linear (no node gains a second inbound or outbound edge), a restatement of the See Also list, or unlabelled edges. Recommend removing them.
- Concept-map edges unsupported or contradicted by the articles they connect (verify against sources with Audit).
- Archive pages whose cited source articles have changed substantially since archival. Deeper version: `references/audit.md`.
- No root `SKILL.md`, so the wiki cannot be loaded as a query-only skill - or one whose `name` or `description` is still a template placeholder or has drifted from what the wiki covers. Offer to create it from `references/templates/wiki-skill-template.md`.
- No root `CLAUDE.md`, so an agent working in the wiki repo gets no project-memory orientation towards the wiki's SKILL.md or the llm-wiki skill - or one still carrying a `{...}` template placeholder. Offer to create it from `references/templates/wiki-claude-md-template.md`.

  For both files: report and offer, never auto-create - naming and describing them for the wiki's subject is judgement. **Before creating either file you MUST read `references/init.md` and follow it** - it carries the `<subject>-llm-wiki` naming rule, the describe-from-content rule, and the query-only boundary that the templates alone do not state.
- No wiki `.gitignore`, or one that does not exclude `local/`, when the wiki is a git repo or `local/` exists. Offer to write or amend from `references/templates/wiki-gitignore-template.md`; merging the single `local/` line into a user-maintained file is safe once confirmed, but leave the rest of their ignore rules alone.
