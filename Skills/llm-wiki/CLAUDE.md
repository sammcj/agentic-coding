# Working on the llm-wiki skill

This repo is both a distributable Agent Skill. That dual role explains things pure skill-authoring guidance would flag: `README.md`, `LICENSE`, `CHANGELOG.md`, and `examples/` are intentional and stay. Don't strip them as "skill clutter".

## Update the changelog

When you change what the skill does or how it is used, append one line to `CHANGELOG.md` (newest first): `- YYYY-MM-DD: <what changed>, see references/<doc>.md`. Keep it terse and high-level - one functional change per line, pointing at the detail doc. Skip pure copy-edits, refactors, and internal tidy-ups; the changelog is "what's new for a user of the skill", not a git log. Do not link it from `SKILL.md` - it must stay out of the skill's loaded context, read only when asked.

## Keep the three format definitions in sync

The file format is defined in three coupled places. Change a detail in one, update all three in the same pass:

- `SKILL.md` - the spec and workflow (source of truth)
- `references/*.md` - the fill-in templates (authoritative for exact format)
- `examples/` - a self-consistent sample vault that must conform to the spec

The examples are validated against the spec, not decorative. After any format change, re-check that example frontmatter, links, the supersession pair, and the index/log still match SKILL.md and the templates. The structural linter must stay clean on the sample vault: `uv run scripts/lint_wiki.py examples` reports no issues.

Concept maps add a fourth coupling: the palette and rules in `references/concept-map.md`, the worked map in `examples/wiki/machine-learning/why-transformers-scale.md`, and the checks in `references/lint.md` must agree, and the validator must stay green on the samples: `uv run scripts/lint_mermaid.py --require-edge-labels --max-nodes 12 examples/ references/`.

## Don't re-add what the design omits

The skill deliberately excludes embeddings and vector search, a knowledge-graph database, numeric confidence scores, decay/forgetting curves, autonomous background writes, and multi-agent sync (see "Design philosophy" in SKILL.md). These omissions are the design, not gaps. It stays self-contained: plain markdown, relative links, git, and stdlib-only helper scripts that are read-only and write no artefacts. `scripts/` holds exactly two, both run via `uv` when available and both intentional (don't strip them as clutter, the way `README.md` and `examples/` are): `lint_mermaid.py` validates concept-map mermaid, and `lint_wiki.py` reports the deterministic structural lint checks. They detect only - the agent applies fixes - so neither mutates the wiki. A new script must keep that contract (stdlib, read-only, no artefacts) or it doesn't belong. No databases, servers, embeddings, or third-party packages.

## Editing SKILL.md

- Keep it lean (aim under ~4k tokens); move detailed protocol into `references/` and point to it, as the bulk-ingest protocol does.
- The skill `name` must match the directory name (`llm-wiki`); the spec validator enforces this.
- Validate after changes with the skill-creator-primer `validate_skill.py`. Its sibling `quick_validate.py` wrongly rejects valid Claude Code frontmatter extensions, so trust the spec validator.

## Commits and style

- Commit with the GitHub noreply alias (e.g. `<username>@users.noreply.github.com`), never a personal email.
- Match the repo's prose: Australian English, plain ASCII punctuation (straight quotes, single hyphens), and no marketing language.
