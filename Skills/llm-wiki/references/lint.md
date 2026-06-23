# Lint: the full check list

Health checks on the wiki, in two tiers with different authority. Deterministic problems are fixed automatically; anything needing judgement is reported, never silently rewritten. You do not rewrite article prose on your own authority. The two-tier boundary and the post-lint log entry live in SKILL.md; this file is the enumerated checks each tier runs.

## Deterministic checks (auto-fix)

Run the structural detections with the bundled helper rather than improvising a script: `uv run scripts/lint_wiki.py <project-root>` reports the `frontmatter`, `index`, `links`, `raw`, and `local` findings below (read-only; `--checks` selects a subset, `--json` for machine output, exit 1 when anything is found). It detects; you apply the fixes described here. If `uv` is unavailable, fall back to the `grep` and file-tool checks - and never heredoc a one-off script through the shell, since `!` gets backslash-escaped and corrupts the code. The other deterministic checks - See Also, log retention, the wiki skill file's links, concept-map freshness and `map-sources` resolution, and the gap register - are not scripted; do them with the file tools and grep. Concept-map mermaid syntax has its own validator (see the Concept maps check).

**Index consistency** - compare `wiki/index.md` against actual `wiki/` files (excluding README.md, index.md and log.md):
- File exists but missing from index -> add a bullet `* [Title](path) - (no summary)` under its topic section (OKF §6 form; no date column).
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

**Wiki skill file** - if a root `SKILL.md` exists (the query-only skill, `references/templates/wiki-skill-template.md`), its links into `wiki/` must resolve: a missing target gets the same fix-or-report treatment as an internal link (search `wiki/` for a same-named file, fix a single match, report zero or several). Do not touch its `name` or `description`; those are judgement (heuristic tier).

**Log retention** - keep `wiki/log.md` bounded, but only when the wiki is a git repo (git is then the canonical history). If the log holds more than ~12 months of date sections, remove the oldest whole `## YYYY-MM-DD` sections, keeping everything from the last 12 months and at least the most recent 20 date sections, and leave one marker line under the `# Wiki Log` heading: `<!-- Older entries trimmed; full history in git: git log -p wiki/log.md -->`. Preserve the heading and the format comment. If the wiki is not a git repo, never trim - the log is then the only history, so report its size instead.

**Concept maps** - for `mermaid` blocks in articles (rules in `references/concept-map.md`):
- Validate syntax with the bundled validator when `uv` is available: `uv run scripts/lint_mermaid.py --require-edge-labels --max-nodes 12 <files>`. It is dependency-free. If `uv` is not installed, skip scripted validation and check the block by eye - never block the lint on a missing tool. A reported error (unbalanced brackets, unclosed label, empty block, undefined style class) means the diagram will not render or breaks a rule; fix it or report it.
- `map-sources` paths must resolve to existing articles, the same as an internal link: search for a same-named file, fix a single match, report zero or several.
- Freshness: for a map in a `current` (non-archive) article, if any `map-sources` article's `updated` is newer than the host article's `updated`, annotate the block `<!-- stale-map: <source> updated YYYY-MM-DD after host -->`. Annotate only; redrawing is judgement, left to the user. Skip `type: archive` and `status: stale` pages - their maps are snapshots.

**Local-content leak guard** - no committed file may link into `local/` (`references/local-content.md`). Scan tracked files (`wiki/`, `raw/`, `index.md`, `log.md`, `gaps.md`, `README.md`, the root `SKILL.md` and `CLAUDE.md`) for any markdown link whose target resolves into `local/` - for example `grep -rnE '\]\(\.{0,2}/?(\.\./)*local/' wiki/ raw/ SKILL.md`. Report each as a finding (it is broken for other clones and leaks the path into git); do not rewrite the prose, since the fix - drop the link, or promote the local draft into `raw/` + `wiki/` - is judgement. `local/` itself is never scanned: its internals are exempt from every other lint check.

**Gaps register** - for `wiki/gaps.md` (format in `references/gaps.md`):
- A wiki predating this feature may have no `wiki/gaps.md`. Do not create an empty one proactively; it is created at init for new wikis, and otherwise the first time a gap needs recording (heading `# Knowledge Gaps`). Its absence is not a finding.
- Every link in a gap entry (`Raised by`, `Referenced by`, and a resolution target) must resolve, the same as an internal link: search for a same-named file, fix a single match, report zero or several.
- Auto-close fulfilled `wanted` gaps: if an `[open] wanted` gap names a concept that now has an article (a file or title match), close it - change `[open]` to `[resolved]`, drop the evidence lines, and append `-> [Article](path) (today)`. This is mechanical; closing a `question` is judgement and stays in the heuristic tier.
- Retention, only when the wiki is a git repo: prune the oldest `[resolved]` entries on the same rule as the log, keeping recent ones and leaving git to carry the rest. Never prune `[open]` entries. If the wiki is not a git repo, do not prune.

## Heuristic checks (report only)

Rely on judgement. Report findings; do not auto-fix.

- Factual contradictions across articles that lack a conflict annotation.
- Claims a newer source has superseded but that were never marked stale.
- Orphan pages with no inbound links (no backlinks from other articles). This is a connectivity gap, not a knowledge gap: the fix is a See Also, not a `gaps.md` entry. Do not record orphans in the gap register.
- Missing cross-topic references.
- Concepts mentioned often but lacking their own page. Propose each as a `wanted` gap in `wiki/gaps.md` (`references/gaps.md`); add it only with the user's go-ahead, never auto-author the article.
- Open `question` gaps in `wiki/gaps.md` that an existing article now appears to answer. Propose closing them with a resolution link; closing a `question` is judgement, so confirm rather than auto-fix.
- Articles that appear to cover more than one distinct concept (often several top-level sections that could each stand alone) - candidates for splitting into linked articles.
- Concept maps that do not earn their place: two-node, purely linear (no node gains a second inbound or outbound edge, so there is no branching or convergence), a restatement of the See Also list, or unlabelled edges. Recommend removing them - a map with no value is worse than none.
- Concept-map edges that look unsupported or contradicted by the articles they connect (verify against sources with Audit).
- Archive pages whose cited source articles have changed substantially since archival. For a deeper version of this check that reads the cited sources and verdicts each claim, see `references/audit.md`.
- No root `SKILL.md`, so the wiki cannot be loaded as a query-only skill. Report it and offer to create one from `references/templates/wiki-skill-template.md`; do not auto-create, since naming and describing it for the wiki's subject is judgement. A `SKILL.md` whose `name` or `description` is still a template placeholder, or has drifted from what the wiki now covers, is the same kind of finding: report it for the user to refine.
- No root `CLAUDE.md`, so an agent whose working directory is the wiki repo gets no project-memory orientation and may not know to read the wiki's SKILL.md or activate the llm-wiki skill. Report it and offer to create one from `references/templates/wiki-claude-md-template.md`; do not auto-create, since the subject line is judgement (the same treatment as the root SKILL.md). A `CLAUDE.md` still carrying a `{...}` template placeholder is the same kind of finding.
- No wiki `.gitignore`, or one that does not exclude `local/`, when the wiki is a git repo or `local/` exists. Offer to write or amend it from `references/templates/wiki-gitignore-template.md`; merging the single `local/` line into a user-maintained file is safe once confirmed, but do not silently rewrite the rest of their ignore rules.
