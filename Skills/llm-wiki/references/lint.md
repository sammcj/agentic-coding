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

**Log retention** - keep `wiki/log.md` bounded, but only when the wiki is a git repo (git is then the canonical history). If the log holds more than ~12 months of entries, remove the oldest, keeping everything from the last 12 months and at least the most recent 20 entries, and leave one marker line under the `# Wiki Log` heading: `<!-- Older entries trimmed; full history in git: git log -p wiki/log.md -->`. Preserve the heading and the format comment. If the wiki is not a git repo, never trim - the log is then the only history, so report its size instead.

**Concept maps** - for `mermaid` blocks in articles (rules in `references/concept-map.md`):
- Validate syntax with the bundled validator when `uv` is available: `uv run scripts/lint_mermaid.py --require-edge-labels --max-nodes 12 <files>`. It is dependency-free. If `uv` is not installed, skip scripted validation and check the block by eye - never block the lint on a missing tool. A reported error (unbalanced brackets, unclosed label, empty block, undefined style class) means the diagram will not render or breaks a rule; fix it or report it.
- `map-sources` paths must resolve to existing articles, the same as an internal link: search for a same-named file, fix a single match, report zero or several.
- Freshness: for a map in a `current` (non-archive) article, if any `map-sources` article's `updated` is newer than the host article's `updated`, annotate the block `<!-- stale-map: <source> updated YYYY-MM-DD after host -->`. Annotate only; redrawing is judgement, left to the user. Skip `type: archive` and `status: stale` pages - their maps are snapshots.

## Heuristic checks (report only)

Rely on judgement. Report findings; do not auto-fix.

- Factual contradictions across articles that lack a conflict annotation.
- Claims a newer source has superseded but that were never marked stale.
- Orphan pages with no inbound links (no backlinks from other articles).
- Missing cross-topic references.
- Concepts mentioned often but lacking their own page.
- Articles that appear to cover more than one distinct concept (often several top-level sections that could each stand alone) - candidates for splitting into linked articles.
- Concept maps that do not earn their place: two-node, purely linear (no node gains a second inbound or outbound edge, so there is no branching or convergence), a restatement of the See Also list, or unlabelled edges. Recommend removing them - a map with no value is worse than none.
- Concept-map edges that look unsupported or contradicted by the articles they connect (verify against sources with Audit).
- Archive pages whose cited source articles have changed substantially since archival. For a deeper version of this check that reads the cited sources and verdicts each claim, see `references/audit.md`.
