# Changelog

High-level record of functional changes to the llm-wiki skill, newest first. One line per change, pointing at the detail. Read it when someone asks what is new or changed - it is not loaded automatically. Maintainers: see `CLAUDE.md` for when and how to add an entry.

- 2026-06-04: Added distilled ingest for verbose external sources (transcripts, meeting notes): extract the valuable content and keep a `fidelity: distilled` raw instead of the verbatim source, gated by a critical review from a separate sub-agent. See `references/distilled-ingest.md`.
- 2026-06-04: Added optional `local/` for gitignored personal content (notes, drafts, private sources), kept in the user's clone only. See `references/local-content.md`; init now also writes a wiki `.gitignore` from `references/wiki-gitignore-template.md`.
