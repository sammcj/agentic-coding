# Scoping a new wiki

What an llm-wiki is good for, what it is not, and how to settle a new wiki's scope before creating any files. Run this at init; it decides what goes in the wiki's `CLAUDE.md` scope block, which every later operation is bound by.

The failure this prevents is a wiki that quietly becomes the wrong thing: a scratch space for one project turning into the organisation's knowledge store, with people relying on it who cannot query it and no one owning what is in it.

## Two modes

**Personal / solo.** One person, their own sources, their own questions. Long-running is fine - a solo wiki can accumulate for years, because the person who compiled it is the person reading it, and they know what is in there and how it got there.

**Work / team.** Several people, shared subject matter, work output. Best suited to short and medium term scopes: a project, an initiative, a discovery, a migration, a piece of research. Longer-term team use is not forbidden, but it needs to be thought through rather than drifted into - see the horizon test below.

Infer the mode from what the user is doing and the sources they bring. Ask only when you genuinely cannot tell. No keyword or marker decides it.

## Good, maybe, no-go

**Good**

- A project or initiative wiki that runs for the life of that work.
- A solo wiki on a subject the user is learning or tracking.
- A discovery or research phase, where sources arrive fast and need compiling into something answerable.
- A codebase or system wiki scoped to one system (`references/codebase-wiki.md`).

**Maybe - think it through first**

- Insight over time from a repeating input, e.g. team retros or planning sessions, where the value is the pattern across many sessions rather than any one of them. This is a legitimate long-running team wiki, but it only works if the scope stays that narrow input and someone owns it.

**No-go**

- A long-term store of knowledge spanning multiple products or teams. That is a wiki platform's job. An llm-wiki has no access control, no multi-writer story, and every write goes through one agent at one person's direction.
- Anything external stakeholders are expected to interface with. You can generate outputs *from* the wiki for them - a summary, a report, a document - and that is the right pattern. Do not build something that assumes they will query it, which would mean giving them access and expecting them to run Claude.

The test for that last one: if someone who will not run Claude needs to read this, the deliverable is a document, and the wiki is at most where it gets generated from.

## The horizon test (team wikis)

For a work wiki, settle the horizon before creating files. Ask what ends it or what triggers a review - the completion of the project, the close of the initiative, a date. Plain prose is fine (`until the platform migration ships`, `review 2026-12`); it does not need a formal marker. A solo wiki's horizon is `ongoing`.

The horizon is not a deletion timer. It is the point at which someone asks whether the wiki is still the right shape, which is the only thing that catches the slow drift from "our project's knowledge" to "our organisation's knowledge".

If the user cannot name any horizon for a team wiki, that is the signal to check they are not in no-go territory before proceeding.

## The scope block

The answers go in the wiki's root `CLAUDE.md`, which an agent auto-loads whenever the repo is its working directory, so it binds every later operation. Fields in `references/templates/wiki-claude-md-template.md`:

- `Mode` - personal or team.
- `Purpose` - one line on what this wiki is for.
- `In scope` / `Out of scope` - the boundary, in the user's own terms. Out of scope is the one that does work later, when an ingest arrives that does not belong.
- `Horizon` - `ongoing` for solo; the end point or review trigger for a team wiki.

Write it once, at init. Nothing else restates it: `wiki/README.md` and the root `SKILL.md` point at it. Lint reports a wiki missing the block, and reports drift past a declared horizon (`references/lint.md`).

A team wiki also carries the PII rule from the template: no personal information about people outside the organisation - customers, candidates, members of the public - lands in `raw/` or `wiki/`. This is stricter than the ordinary filter step in `references/ingest.md`, and it applies at ingest, not in review.

## At init

Before creating anything (`references/init.md` step 0):

1. Determine the mode. Infer it; ask only if unclear.
2. **Solo** - confirm purpose and boundary in a sentence, then proceed.
3. **Team** - point the user at the llm-wiki README's "Intended use and scope" section before creating files, summarise the no-go list in a line or two, and get purpose, boundary and horizon confirmed. Do not create files on an unanswered scoping question.
4. Write the confirmed answers into the `CLAUDE.md` scope block as init creates it.
