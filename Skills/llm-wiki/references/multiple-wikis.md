# Multiple wikis: several independent wikis, side by side

A user can run more than one llm-wiki at once - say one for machine-learning reading, one for a payments project, one for ops runbooks. Each is a full, self-contained wiki with its own `raw/`, `wiki/`, `index.md`, `log.md`, and its own git repo. They sit side by side, cloned wherever the user keeps them (e.g. `~/git/wikis/{ml,payments,ops}/`). They do not nest, there is no host wiki, and no wiki contains or owns another.

The whole model is isolation. Each wiki is queried and maintained on its own terms; nothing flows between them automatically. This keeps every wiki portable and correct for someone who only ever clones that one.

## Detecting a multi-wiki setup

You are in a multi-wiki setup when your session's working directory holds more than one wiki - subdirectories that each have their own `wiki/` and `raw/`. A session rooted *inside* a single wiki is the ordinary case; nothing here applies, just operate on that wiki.

When you see several wikis under the working directory, maintain a `WIKI-INDEX.md` there (the directory the user launched the session from, above the wikis - not inside any of them, so it never lands in a wiki's git history). Create it if it is missing.

## WIKI-INDEX.md

A short orientation file: what each wiki is for, how to tell them apart, and the rules for working across them. It is the first thing to read in a multi-wiki session and the map for routing a request to the right wiki.

Fill the purpose and differentiator for each wiki from its own `wiki/README.md` and root `SKILL.md` description. If a wiki's purpose is not clear from inspection, ask the user rather than guessing. Keep it current: add a row when a wiki is cloned in, drop one when it goes away.

```markdown
# Wiki Index

Independent llm-wikis kept under this directory. Each is self-contained and operates in isolation - they do not link to or reference each other.

Working rules for any agent here:
- Before querying or maintaining a wiki, read that wiki's own CLAUDE.md and SKILL.md (and any skill it bundles). They do not auto-load from this parent directory.
- A query runs against one wiki. Do not fold one wiki's content into another's answer.
- No wiki links into another. To carry a fact across, re-ingest its source into the target wiki with the user's go-ahead (see below); never add a cross-wiki link.

## Wikis

- **ml/** - Machine-learning reading: papers, model architectures, training notes. Subject-matter reference.
- **payments/** - The Payments project knowledge base: decisions, integrations, runbooks for that system.
- **ops/** - Infrastructure and on-call runbooks.
```

## Each wiki is isolated

Two rules carry the whole model.

1. **Read the target wiki's own instructions first.** Before you query or change a wiki, read its root `CLAUDE.md` and `SKILL.md`, and follow any skill it bundles (e.g. its own `.claude/skills/`). Do not assume the conventions of one wiki apply to another. This matters because of two current Claude Code behaviours: a nested `CLAUDE.md` in a subdirectory is **not** auto-loaded from a parent project root, and a nested `.claude/skills/` directory is **not** discovered recursively. So a wiki's own context is inert until you read it deliberately.
2. **No wiki references another.** No article, index, log, or any committed file in one wiki links or points into another. A cross-wiki link is broken for anyone who clones only one of the wikis, and it couples two bases that are meant to stand alone.

## Querying

A query runs against a single wiki. Pick the right one from `WIKI-INDEX.md` (or ask the user when the request is ambiguous), then query it normally. Never silently search a second wiki and blend its content into the answer - that mixes two separate bases and their provenance. If a question genuinely spans wikis, say so, answer from each separately with the wiki named, and keep the answers distinct.

## Maintaining another wiki

To maintain a wiki other than the one you are rooted in, move into its context rather than editing it from the parent directory: change the working directory to that wiki, read and follow its own `CLAUDE.md` and `SKILL.md`, and use the llm-wiki skill (or the wiki's own bundled skill) with it as the project root. The edits land in that wiki's own `raw/`, `wiki/`, index, log, and git repo. For full, automatic skill support the cleanest path is a fresh session rooted at that wiki; offer that when the user would rather not drive it through the current session.

## Carrying a fact across wikis

Wikis do not share content, but a fact that lives in one is sometimes worth having in another. This is never automatic. When you spot the opportunity, ask the user; only on a yes do you carry it across, and you do it as a normal ingest into the target wiki, not as a link or a copy of the other wiki's article.

1. **Re-ingest the underlying source, not the compiled article.** The source wiki's article cites its own `raw/` source. Re-land that underlying source into the target wiki's `raw/` as a new file, then compile it into the target `wiki/` like any normal ingest, with full provenance to the target's own `raw/` copy. Update the target's `index.md` and `log.md`.
2. **Chase the true origin.** Cite the upstream original the source wiki recorded, so the provenance chain ends at the real origin rather than at "the other wiki". Record the source wiki only as a breadcrumb in the raw file's `source` field (e.g. `via ml-wiki; original: <upstream source>`), never as a link into it. `fidelity: distilled` applies if you kept only the high-signal part (`references/distilled-ingest.md`). Format: `references/templates/raw-template.md`.

Nothing is written back into the source wiki by this; it is read only. To change the source wiki itself, maintain it directly in its own context (above).

## Setup

There is nothing to initialise. The user clones each wiki wherever they want; the wikis are ordinary, independent repos. `WIKI-INDEX.md` is created the first time a session sees more than one wiki under its working directory, and it lives above the wikis, so no wiki's `.gitignore` is involved. Because the wikis never nest, there is no leak guard to run across them - the isolation comes from their being separate repos, not from an ignore rule.
