# Optional tool: graphify as an external lens

A set of conventions for using the **graphify** skill or tool, when it is available, over an llm-wiki. graphify turns a folder of files into a knowledge graph: community detection, god-node ranking, surprising connections, an HTML visualisation, and a queryable graph with an EXTRACTED/INFERRED/AMBIGUOUS audit trail. Here it is a disposable, read-only lens over the wiki, not part of it.

Use it only when graphify is present and a task genuinely calls for graph-shaped insight (how things connect, what is central, what is orphaned). Ignore it otherwise; the wiki is fully usable with index, grep, git, and the See Also web alone.

## The boundary: the graph never becomes the wiki

This does not contradict the design philosophy's exclusion of a knowledge-graph database and embeddings. The exclusion is about stored, load-bearing infrastructure. graphify here is a throwaway analysis pass, the same kind of external tool as grep, run when asked and discarded.

Keep that line clean:

- **Markdown stays the source of truth.** The graph is derived from `wiki/` and `raw/`, never the other way round. Nothing reads from the graph at query time.
- **`graphify-out/` is generated, not committed.** It is regenerable from the markdown, so add `graphify-out/` to the project `.gitignore` (alongside `local/`) and never check it in. Treat it as scratch, like a build directory.
- **Act only through normal llm-wiki operations.** A graph finding is a prompt, not an edit. Turn it into a See Also link, a `gaps.md` entry, a supersession, or a Query answer, each verified against the markdown first and applied by the usual rules. Never let the graph become a parallel store the wiki depends on.
- **Do not generate a competing Obsidian vault.** The wiki already opens as an Obsidian vault with real backlinks and a real graph view. Skip graphify's `--obsidian` and `--wiki` exports; they would shadow the canonical structure with an inferred one.

## What it is good for

**Seeing the structure.** Run graphify over `wiki/` to get a map of how articles actually connect, beyond the hand-maintained index and See Also lines:

```
/graphify wiki/
```

Read `graphify-out/GRAPH_REPORT.md`, in particular the god nodes (the most-connected concepts), the communities (clusters that often cut across topic directories), and the surprising connections (bridges between distant articles). Open `graphify-out/graph.html` for an interactive view.

**Surfacing what Lint reports by judgement.** The graph makes orphans and weak links visible, which feeds Lint's heuristic tier rather than replacing it:

- A node with no edges, or only AMBIGUOUS ones, points at an orphan page or a missing cross-reference. Confirm it in the markdown, then add a real inbound link (see Lint's See Also and orphan checks in `references/lint.md`).
- A god node that several communities lean on but no article centres on is often an undocumented concept. Record it as a `wanted` gap (`references/gaps.md`), not a new article invented on the spot.
- A surprising connection between two articles that do not link each other is a candidate cross-reference. Add the See Also only if the markdown bears it out.

**Triaging a large corpus before ingest.** When the user points at a big folder of unread sources, graphify it first to decide what is worth compiling:

```
/graphify path/to/source-folder
```

The god nodes and communities show where the substance sits, so you ingest the high-signal sources deliberately instead of compiling everything. This is a planning aid for Ingest; the actual ingest still lands each chosen source in `raw/` and compiles it per SKILL.md.

**Cross-document questions.** Once a graph exists, `graphify query` traverses it for broad, connection-heavy questions ("what links X to Y across the whole corpus"):

```
/graphify query "how does X relate to Y"
/graphify path "Concept A" "Concept B"
/graphify explain "Concept"
```

This complements wiki Query, it does not replace it. wiki Query reads the compiled articles and is the default. Reach for graphify query when the question is about structure and reach across many documents. Either way, if the user wants the answer kept, crystallise it through the normal Query archive flow (`type: archive`), citing the wiki articles it draws on, never the graph.

## Edge labels and verification

graphify labels every edge EXTRACTED (explicit in the source), INFERRED (a reasonable guess), or AMBIGUOUS (uncertain). Only EXTRACTED edges are facts. Treat INFERRED and AMBIGUOUS edges as leads to check against the markdown, never as established connections. Surprising connections in particular are designed to provoke, so verify before you act. The same evidence discipline the wiki uses for claims applies to anything the graph asserts: a link you add because of the graph still has to be true in the text.
