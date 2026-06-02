# Working on the llm-wiki skill

This repo is both a distributable Agent Skill and a public repo (it lives in sammcj/agentic-coding). That dual role explains things pure skill-authoring guidance would flag: `README.md`, `LICENSE`, and `examples/` are intentional and stay. Don't strip them as "skill clutter".

## Keep the three format definitions in sync

The file format is defined in three coupled places. Change a detail in one, update all three in the same pass:

- `SKILL.md` - the spec and workflow (source of truth)
- `references/*.md` - the fill-in templates (authoritative for exact format)
- `examples/` - a self-consistent sample vault that must conform to the spec

The examples are validated against the spec, not decorative. After any format change, re-check that example frontmatter, links, the supersession pair, and the index/log still match SKILL.md and the templates.

## Don't re-add what the design omits

The skill deliberately excludes embeddings and vector search, a knowledge-graph database, numeric confidence scores, decay/forgetting curves, autonomous background writes, and multi-agent sync (see "Design philosophy" in SKILL.md). These omissions are the design, not gaps. Keep it self-contained: plain markdown, relative links, grep and git only.

## Editing SKILL.md

- Keep it lean (aim under ~4k tokens); move detailed protocol into `references/` and point to it, as the bulk-ingest protocol does.
- The skill `name` must match the directory name (`llm-wiki`); the spec validator enforces this.
- Validate after changes with the skill-creator-primer `validate_skill.py`. Its sibling `quick_validate.py` wrongly rejects valid Claude Code frontmatter extensions, so trust the spec validator.

## Commits and style

- Commit with the GitHub noreply alias (`<username>@users.noreply.github.com`), never a personal email.
- Match the repo's prose: Australian English, plain ASCII punctuation (straight quotes, single hyphens), and no marketing language.
