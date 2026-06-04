# Changelog

High-level record of functional changes to the llm-wiki skill, newest first. One line per change, pointing at the detail. Read it when someone asks what is new or changed - it is not loaded automatically. Maintainers: see `CLAUDE.md` for when and how to add an entry.

- 2026-06-04: Init now writes a root `CLAUDE.md` for the wiki repo (project memory that auto-loads by working directory): it points an agent at the wiki's SKILL.md and tells it to activate the llm-wiki skill if available. Lint offers one to wikis that predate it. See `references/wiki-claude-md-template.md`.
- 2026-06-04: Added `scripts/lint_wiki.py`, a read-only stdlib helper for the deterministic structural lint checks (frontmatter, index, links, raw, local-leak), so agents stop improvising scripts piped through the shell. See `references/lint.md`.
- 2026-06-04: Added distilled ingest for verbose external sources (transcripts, meeting notes): extract the valuable content and keep a `fidelity: distilled` raw instead of the verbatim source, gated by a critical review from a separate sub-agent, with optional `source_sha256`/`source_modified` fingerprints to detect a changed source or forgotten re-extraction. See `references/distilled-ingest.md`.
- 2026-06-04: Added optional `local/` for gitignored personal content (notes, drafts, private sources), kept in the user's clone only. See `references/local-content.md`; init now also writes a wiki `.gitignore` from `references/wiki-gitignore-template.md`.
