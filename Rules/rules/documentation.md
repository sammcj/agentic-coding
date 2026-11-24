---
paths:
  - "**/*.{md,mdx,markdown,txt,rst,adoc,qmd}"
  - "**/{README,CHANGELOG,CONTRIBUTING}"
---

# Documentation

- Keep signal-to-noise ratio high - preserve domain insights, omit preamble, filler and fluff
- Match the length of written documents to what the task needs. Cover the substance, don't pad with filler sections, redundant summaries or boilerplate
- Do not split sentences across multiple lines in markdown files, this breaks readability and diffs
- Do not use tables in markdown with written content inside cells, instead prefer concise bullet points over tables for text information, tables are better suited to simple data than prose
- When using tables in markdown, do not include unwrapped content that causes the table to over-extend horizontally, do not add sentences of text inside tables, tables should be for terse, structured data, not prose
- Use _underscores_ for italics and **double asterisks** for bold in markdown files
- Configuration and examples over feature lists
- Do not manually wrap text in markdown or text files, this just makes files longer and harder to read
