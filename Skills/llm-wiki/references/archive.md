# Crystallise: saving an answer into the wiki as an archive page

Read this when the user asks to save a query answer, an audit, or a critique to the wiki. File it as a first-class page so the exploration compounds like an ingested source.

1. Write the answer as a new article with `type: archive`. Format: `references/templates/archive-template.md`. Convert conversation citations to file-relative paths (`wiki/topic/article.md` becomes `../topic/article.md`, or `article.md` for the same directory).
   - Sources line: markdown links to the wiki articles the answer cites. An archived audit or critique cites the target it examined.
   - No Raw line - the content does not come from `raw/`.
   - Capture the question, the findings, the articles and entities involved, and any lesson worth keeping as a standalone point.
   - When the relationships are non-linear, a concept map can capture them; in an archive it is a snapshot (no `map-sources` marker, never cascade-checked). See `references/concept-map.md`.
   - File name reflects the query topic; place it in the most relevant topic directory.
2. Always create a new page; never merge an archive into an existing article.
3. Update `wiki/index.md`, prefixing the summary with `[Archived]`.
4. Append to `wiki/log.md` under today's date heading:

   ```
   * **Query**: archived [<page title>](<path>).
   ```

   An archived audit or critique logs under its own operation word (`**Audit**`, `**Critique**`) alongside that operation's normal entry.

Archives are point-in-time: they are never cascade-updated when a cited article later changes. Lint reports an archive whose sources have drifted; Audit verdicts its claims.
