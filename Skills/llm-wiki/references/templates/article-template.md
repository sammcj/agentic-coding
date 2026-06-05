---
title: {Title}
type: concept            # concept | entity | archive
topic: {topic-name}
created: {YYYY-MM-DD}
updated: {YYYY-MM-DD}
status: current          # current | stale
superseded_by:           # relative path to replacement, set only when status: stale
tags: []
aliases: []
---

# {Title}

{OPTIONAL - include only when this article has been superseded:}
> [!warning] Superseded by [{Replacement}](replacement.md) ({YYYY-MM-DD}). Kept for history.

> Sources: {Author1, YYYY-MM-DD; Author2, YYYY-MM-DD}
> Raw: [{source1}](../../raw/{topic1}/{filename1}.md); [{source2}](../../raw/{topic2}/{filename2}.md)

## Overview

{One paragraph summarising the key points of this article.}

## {Body Sections}

{Synthesise a coherent structure from the source material. Do not copy source text verbatim; distill and reorganise. Use blockquotes sparingly for particularly important original phrasing; for a load-bearing claim from a long or noisy source, pair the quote with its raw link and a locator (section, page, or timestamp) so it stays checkable, e.g. `> "exact sentence" ([Source](../../raw/topic/file.md) §4.2)`.

Where sources disagree, annotate the conflict inline with an evidence chain that attributes each side, e.g. "Uses Redis for caching ([Source A](...), [Source B](...)); [Source C](...) reports Memcached." Never resolve a conflict with a numeric confidence score.}

{OPTIONAL - include this section only when cross-references exist:}

## See Also

{Cross-references to related wiki articles, maintained during lint. Plain or typed links both work:
- Same topic: [Other Article](other-article.md)
- Different topic: [Other Article](../other-topic/other-article.md)
- Typed (optional): Depends on [Other Article](../other-topic/other-article.md)}
