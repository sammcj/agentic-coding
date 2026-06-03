# Local content: personal notes kept out of git

An optional `local/` directory at the project root holds personal markdown that lives in your clone only and never reaches the remote: meeting prep, half-formed ideas, drafts, working notes, and private sources you cannot or do not want to commit. It is a sibling of `raw/` and `wiki/`, and the wiki `.gitignore` excludes it (`references/wiki-gitignore-template.md`).

`local/` is a scratch bench, not part of the compiled knowledge base. It carries none of the raw->wiki discipline: no required frontmatter, no index row, no log entry, no supersession. Write whatever you like, however you like.

## The one rule: link direction

This is the whole safety story, so it is the rule to get right.

- **`local/` may link into `wiki/` and `raw/`.** Those files exist in every clone, so the link always resolves. A local note that references shared articles is the normal, intended case.
- **No committed file may link into `local/`.** A `wiki/` article, the index, the log, `gaps.md`, the README, or the root `SKILL.md` pointing at `local/...` is a broken link for anyone else who clones the repo, and it leaks the path and filename into git history. Lint flags any such link (the leak guard, `references/lint.md`).

Put differently: shared content must read as complete and correct to someone who has never seen your `local/` directory, because most people who clone the wiki never will.

Obsidian backlinks are fine here. When a local note links to a wiki article, Obsidian shows that backlink while you view the article, but it is computed live and never written into the committed file, so nothing leaks.

## Structure

Start flat and freeform: any subdirectories and filenames you like under `local/`. There is no enforced layout.

If you want the same discipline the wiki uses (a private source compiling into a private article with provenance), you can mirror the split inside `local/` as `local/raw/` and `local/wiki/` and follow the normal ingest format by hand. That is an option for people who want it, not the default. Everything stays inside `local/` and inside your clone either way.

## How the operations treat `local/`

- **Exempt from the managed machinery.** `local/` is outside `index.md`, `log.md`, `gaps.md`, cascade updates, and audit. None of those scan it or record it.
- **Query** scans `local/` when it exists, alongside the wiki, and labels any hit clearly as `local/ (uncommitted)` so a personal note is never mistaken for shared knowledge.
- **Ingest** does not touch `local/` by default. Personal notes are something you write, not something the skill compiles.
- **Lint** ignores the internals of `local/` (no orphan, frontmatter, or link checks in there), but runs the leak guard over committed files and offers a wiki `.gitignore` if one is missing.

## Promotion path

`local/` is the drafting bench; `wiki/` is the committed record. When a local note matures into knowledge worth sharing, promote it: run it through a normal ingest so a real source lands in `raw/` and a compiled article in `wiki/`, with provenance and an index entry. Do not link the wiki to the local draft; rewrite it across the boundary. Keep or delete the local copy as you like once it is promoted.

## Setup

`local/` is created the first time you store something there, not at init, so empty wikis stay empty. The exclusion comes from the wiki `.gitignore` written at init (`references/wiki-gitignore-template.md`). For a wiki that predates this, add `local/` to its `.gitignore` (lint offers to write the template if there is none), then confirm with `git status` that `local/` shows nothing before you trust it. If the wiki is not in git, `local/` is moot - nothing is committed anyway - but the same link-direction rule still keeps shared articles self-contained.
