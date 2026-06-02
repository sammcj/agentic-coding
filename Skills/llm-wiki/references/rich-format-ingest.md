# Rich-format ingest (PDF, Word, slides, images, spreadsheets)

How to bring a non-text source into `raw/` without losing structure or detail. `raw/` holds durable markdown only, so every rich source is converted before it is saved, and the markdown becomes the record you compile from.

## Convert to markdown

Use the document-extraction skill or tool available in your environment, matched to the format:

- PDF: a PDF extraction skill or tool (OCR for scanned pages).
- Word / docx: a document extraction skill.
- Slides / pptx: a slide-to-markdown skill that captures each slide and the meaning of its diagrams and screenshots, not just the title text.
- Spreadsheets / xlsx / csv: a spreadsheet skill; keep tables as markdown tables.
- Images: vision or OCR; transcribe the text and describe the load-bearing visual content.

Prefer deterministic tools over eyeballing the file: they convert the same way every time and do not quietly paraphrase.

## Preserve structure, not just text

The detail that makes a rich source worth keeping usually lives in its structure. Carry it across:

- Headings and section order.
- Tables as markdown tables, with their columns and units intact.
- Reading order. Multi-column PDFs and slide decks scramble easily; confirm the flow reads correctly.
- The meaning of figures, charts, and diagrams. A chart is a claim: write the claim it makes and keep the numbers. An image that carries information gets a short description; a purely decorative one can be dropped.

## Clean up deterministically

Strip conversion noise (page headers and footers, navigation chrome, repeated watermarks, broken ligatures, stray whitespace) without rewriting meaning or opinions. Where a script can do it reliably, prefer the script.

## Self-review against the original

Before saving, read the markdown against the source once and confirm nothing load-bearing was dropped, mangled, or reordered: every table, every figure's claim, every number, every named entity. This is the only check between a lossy conversion and the wiki, so do it honestly. If the source is also long or noisy, apply `references/high-fidelity-ingest.md` on top.

## What happens to the original

- **Original inside `raw/`** (the user dropped it there): once the self-review confirms the extraction is faithful, delete the binary so `raw/` stays markdown-only. If the content cannot survive in markdown (scanned pages, diagrams, charts the review shows it loses), keep the original and tell the user rather than deleting the only copy.
- **Original outside the wiki** (Downloads, another folder, a temp file): leave it untouched and do not link to it. The markdown saved in `raw/` is the record; its `source` frontmatter names the origin. Never delete a file the user keeps outside the wiki.

## Gotchas

- **Slides hide content in images.** Decks often carry the real point in a screenshot or diagram, not the bullet text. Capture what the visual says, or the article inherits an empty summary.
- **Tables fail quietly.** Merged cells, multi-row headers, and wrapped columns mangle on conversion. Check tables specifically in the self-review.
- **Do not delete what markdown cannot hold.** The verified-faithful gate exists for exactly this: a scanned figure or a chart with no underlying numbers is not captured by prose, so the original stays.
