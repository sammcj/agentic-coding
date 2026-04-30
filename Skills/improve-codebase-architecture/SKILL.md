---
name: improve-codebase-architecture
description: Find deepening opportunities in a codebase, informed by whatever domain language and architectural decisions are already documented in the repo. Use when the user wants to improve architecture, find refactoring opportunities, consolidate tightly-coupled modules, or make a codebase more testable and AI-navigable.
metadata:
  source: https://github.com/mattpocock/skills (adapted)
---

# Improve Codebase Architecture

Surface architectural friction and propose **deepening opportunities** - refactors that turn shallow modules into deep ones. The aim is testability and AI-navigability.

## Glossary

Use these terms exactly in every suggestion. Consistent language is the point - don't drift into "component," "service," "API," or "boundary." Full definitions in [LANGUAGE.md](LANGUAGE.md).

- **Module** - anything with an interface and an implementation (function, class, package, slice).
- **Interface** - everything a caller must know to use the module: types, invariants, error modes, ordering, config. Not just the type signature.
- **Implementation** - the code inside.
- **Depth** - leverage at the interface: a lot of behaviour behind a small interface. **Deep** = high leverage. **Shallow** = interface nearly as complex as the implementation.
- **Seam** - where an interface lives; a place behaviour can be altered without editing in place. (Use this, not "boundary.")
- **Adapter** - a concrete thing satisfying an interface at a seam.
- **Leverage** - what callers get from depth.
- **Locality** - what maintainers get from depth: change, bugs, knowledge concentrated in one place.

Key principles (see [LANGUAGE.md](LANGUAGE.md) for the full list):

- **Deletion test**: imagine deleting the module. If complexity vanishes, it was a pass-through. If complexity reappears across N callers, it was earning its keep.
- **The interface is the test surface.**
- **One adapter = hypothetical seam. Two adapters = real seam.**

This skill is _informed_ by whatever domain documentation the project already keeps. If a glossary exists, use its terms. If decision records exist, don't re-litigate them. If neither exists, that's fine - work from the code and capture anything load-bearing as it emerges.

## Process

### 1. Explore

Before exploring the code, look for any existing project documentation that names domain concepts or records architectural decisions. Common locations - check whichever apply, don't require any of them:

- A root-level glossary or context file (`CONTEXT.md`, `GLOSSARY.md`, `docs/glossary.md`, a "Domain" section in `README.md` or `CLAUDE.md`)
- Decision records (`docs/adr/`, `docs/decisions/`, `.decisions/`, `architecture/decisions/`)
- Per-package `README.md` files describing the slice's vocabulary

If you find domain documentation, read the parts relevant to the area you're touching. If you find decision records, scan titles and read any that touch the area. If neither exists, proceed without them.

Then use the Agent tool with `subagent_type=Explore` to walk the codebase. Don't follow rigid heuristics - explore organically and note where you experience friction:

- Where does understanding one concept require bouncing between many small modules?
- Where are modules **shallow** - interface nearly as complex as the implementation?
- Where have pure functions been extracted just for testability, but the real bugs hide in how they're called (no **locality**)?
- Where do tightly-coupled modules leak across their seams?
- Which parts of the codebase are untested, or hard to test through their current interface?

Apply the **deletion test** to anything you suspect is shallow: would deleting it concentrate complexity, or just move it? A "yes, concentrates" is the signal you want.

### 2. Present candidates

Present a numbered list of deepening opportunities. For each candidate:

- **Files** - which files/modules are involved
- **Problem** - why the current architecture is causing friction
- **Solution** - plain English description of what would change
- **Benefits** - explained in terms of locality and leverage, and also in how tests would improve

**Use the project's own domain vocabulary** (from whatever glossary or docs you found) **and [LANGUAGE.md](LANGUAGE.md) vocabulary for the architecture.** If the project's docs define "Order," talk about "the Order intake module" - not "the FooBarHandler," and not "the Order service." If the project has no documented vocabulary, infer the dominant terms from the code (type names, package names, table names) and use them consistently.

**Conflicts with documented decisions**: if a candidate contradicts an existing decision record, only surface it when the friction is real enough to warrant revisiting that decision. Mark it clearly (e.g. _"contradicts the decision recorded in docs/adr/0007 - but worth reopening because..."_). Don't list every theoretical refactor a prior decision forbids.

Do NOT propose interfaces yet. Ask the user: "Which of these would you like to explore?"

### 3. Grilling loop

Once the user picks a candidate, drop into a grilling conversation. Walk the design tree with them - constraints, dependencies, the shape of the deepened module, what sits behind the seam, what tests survive.

Side effects happen inline as decisions crystallise:

- **Naming a deepened module after a concept that isn't in the project's vocabulary?** Capture the term. If the project already has a glossary file, append to it in that file's existing format. If it doesn't, ask the user once whether they'd like a lightweight glossary started (e.g. `CONTEXT.md` or `GLOSSARY.md` at the root, whichever fits the repo's conventions); if yes, create it lazily with a minimal structure (term + one-line definition + aliases to avoid). Don't impose a rigid template.
- **Sharpening a fuzzy term during the conversation?** Update the glossary in place if one exists. If it doesn't and the term is genuinely load-bearing, offer to start one as above.
- **User rejects the candidate with a load-bearing reason?** Offer to record the decision so future architecture reviews don't re-suggest it. Frame it as: _"Want me to record this so future reviews don't re-suggest the same thing?"_ Only offer when all three are true:
  1. **Hard to reverse** - the cost of revisiting later is meaningful
  2. **Surprising without context** - a future reader will wonder "why did they do it this way?"
  3. **The result of a real trade-off** - there were genuine alternatives and a specific reason for the pick

  If the project already has a decision-records directory, add to it using the existing numbering and format. If it doesn't, ask once where to put it; if the user is happy to start one, create `docs/adr/0001-<slug>.md` with a simple shape (title, 1-3 sentences covering context, decision, and why). Skip ephemeral reasons ("not worth it right now") and self-evident ones.
- **Want to explore alternative interfaces for the deepened module?** See [INTERFACE-DESIGN.md](INTERFACE-DESIGN.md).
