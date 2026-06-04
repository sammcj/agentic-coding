---
title: {Title}
source: {URL or origin description}
collected: {YYYY-MM-DD}
published: {YYYY-MM-DD or Unknown}
type: raw
topic: {topic-name}
fidelity: {verbatim | distilled}    # optional; omit or 'verbatim' for a faithful source copy. 'distilled' = an extract of a discarded verbose source (references/distilled-ingest.md)
original: {external | discarded}     # only with fidelity: distilled - what happened to the source: 'external' still exists untouched outside the wiki; 'discarded' not retained (deleted from raw/ after the review gate, or an ephemeral paste)
source_sha256: {hex digest}          # optional - hash of the source bytes at collection (e.g. shasum -a 256), so a later ingest can tell if the source changed. Omit for an ephemeral or non-persistent source. Most useful for a distilled extract, which keeps no copy to diff against.
source_modified: {YYYY-MM-DD}        # optional - the source's own last-modified or last-edited date, where the medium exposes one (file mtime, HTTP Last-Modified, a doc's edited date). A softer change signal than the hash.
---

# {Title}

{Original content below. Preserve the source text faithfully. Clean up formatting noise (extra whitespace, broken HTML artifacts, navigation chrome), but do not rewrite opinions or alter meaning. Secrets, credentials, and private data must already have been stripped during the ingest filter step.

If this is a distilled extract (`fidelity: distilled`), it is the high-signal content kept in place of a verbose external source the user did not want retained in full. It is source-shaped, not concept-shaped, and was produced and reviewed per `references/distilled-ingest.md`. Keep the source's own terms, numbers, and hedging; anchor the heaviest claims with a verbatim quote and a locator.

If this content was converted from a rich format (PDF, slides, document, image), it is the extracted markdown: preserve tables, reading order, and the meaning of figures and charts, and name the original in `source`.}
