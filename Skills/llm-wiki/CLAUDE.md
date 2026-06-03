# Working on the llm-wiki skill

This repo is both a distributable Agent Skill. That dual role explains things pure skill-authoring guidance would flag: `README.md`, `LICENSE`, `CHANGELOG.md`, and `examples/` are intentional and stay. Don't strip them as "skill clutter".

## Update the changelog

When you change what the skill does or how it is used, append one line to `CHANGELOG.md` (newest first): `- YYYY-MM-DD: <what changed>, see references/<doc>.md`. Keep it terse and high-level - one functional change per line, pointing at the detail doc. Skip pure copy-edits, refactors, and internal tidy-ups; the changelog is "what's new for a user of the skill", not a git log. Do not link it from `SKILL.md` - it must stay out of the skill's loaded context, read only when asked.

## Keep the three format definitions in sync

The file format is defined in three coupled places. Change a detail in one, update all three in the same pass:

- `SKILL.md` - the spec and workflow (source of truth)
- `references/*.md` - the fill-in templates (authoritative for exact format)
- `examples/` - a self-consistent sample vault that must conform to the spec

The examples are validated against the spec, not decorative. After any format change, re-check that example frontmatter, links, the supersession pair, and the index/log still match SKILL.md and the templates.

Concept maps add a fourth coupling: the palette and rules in `references/concept-map.md`, the worked map in `examples/wiki/machine-learning/why-transformers-scale.md`, and the checks in `references/lint.md` must agree, and the validator must stay green on the samples: `uv run scripts/lint_mermaid.py --require-edge-labels --max-nodes 12 examples/ references/`.

## Don't re-add what the design omits

The skill deliberately excludes embeddings and vector search, a knowledge-graph database, numeric confidence scores, decay/forgetting curves, autonomous background writes, and multi-agent sync (see "Design philosophy" in SKILL.md). These omissions are the design, not gaps. It stays self-contained: plain markdown, relative links, git, and at most a stdlib-only helper script that writes no artefacts. `scripts/lint_mermaid.py` (a mermaid validator the agent runs via `uv` when available) is the only script and is intentional - don't strip it as clutter, the way `README.md` and `examples/` are also intentional. No databases, servers, embeddings, or third-party packages.

## Editing SKILL.md

- Keep it lean (aim under ~4k tokens); move detailed protocol into `references/` and point to it, as the bulk-ingest protocol does.
- The skill `name` must match the directory name (`llm-wiki`); the spec validator enforces this.
- Validate after changes with the skill-creator-primer `validate_skill.py`. Its sibling `quick_validate.py` wrongly rejects valid Claude Code frontmatter extensions, so trust the spec validator.

## Commits and style

- Commit with the GitHub noreply alias (`<username>@users.noreply.github.com`), never a personal email.
- Match the repo's prose: Australian English, plain ASCII punctuation (straight quotes, single hyphens), and no marketing language.
