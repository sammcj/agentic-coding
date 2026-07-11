# Building wisdom into an ebook

Bind the whole corpus into a single EPUB 3 ebook: one chapter per entry, newest first, grouped into year "parts" with divider pages, a generated gradient cover, and a nested navigation document (the ePub table of contents, which readers render as a clickable index) plus a readable index chapter:

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/wisdom.py epub --kindle  #  writes <base>/Wisdom-Library.epub & a Kindle .azw3
```

Flags: `--title` sets the book title, `--output` the destination path, `--descriptions` adds a preview paragraph under each index entry (off by default, for a denser contents list), and `--kindle` also produces a native Kindle `.azw3` via calibre's `ebook-convert` (auto-detected on PATH or in `/Applications/calibre.app`; prints an install hint if calibre is absent).

Graphviz diagrams render to PNG in the ebook (Kindle handles SVG unreliably); the PDF path keeps SVG. The build re-renders every diagram, so mermaid diagrams (network-bound via mermaid.ink) make it slow on a large corpus, which is why it stays a manual step. To rebuild the ebook automatically on each `index` refresh, set `EXTRACT_WISDOM_CREATE_EPUB=true` (off by default).

Output is EPUB 3.3 conformant.
