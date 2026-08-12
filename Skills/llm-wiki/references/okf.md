# Open Knowledge Format (OKF) compatibility

Read this when creating or migrating `type` fields, when settling the form of `index.md` or `log.md`, or when a Lint or Ingest runs into a wiki in an older format.

## The bundle

Treat `wiki/` as the OKF bundle root; `raw/`, `local/`, and the root `SKILL.md`/`CLAUDE.md` sit outside it. Inside `wiki/`, the format is a superset of an OKF v0.1 bundle:

- Every non-reserved file carries a non-empty `type` - articles, plus `README.md` as `Reference` and `gaps.md` as `Gap Register`.
- `index.md` and `log.md` are OKF's reserved filenames and carry no frontmatter.
- Cross-links are plain markdown.
- `resource` carries OKF's meaning: the canonical URI of the asset an `entity` article describes.
- `index.md` follows OKF's index form; `log.md` follows its update-log form.

So an llm-wiki is consumable by generic OKF tooling (a static graph viewer, say) with no export step and no typeless files. The wiki extends OKF with the `raw/` provenance layer, supersession (`status`/`superseded_by`), the `gaps.md` frontier register, and evidence chains; an OKF consumer ignores those extra frontmatter keys, which it is required to tolerate.

Maintaining the wiki still goes through the llm-wiki skill. OKF compatibility governs who can *read* a bundle, not a second way to write one.

## Migrating an older wiki

A wiki that predates these alignments shows one or more of: no `type` on `README.md`/`gaps.md`, a table-form `index.md`, or per-operation `## [date] op | title` log entries. Offer to migrate it to the current OKF-conformant format; do not migrate silently.
