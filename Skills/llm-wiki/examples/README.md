# Example sample vault

An illustrative wiki in the format this skill produces. It is small and self-consistent so you can see how the pieces fit, including supersession and a crystallised query. The content is a worked example, not a real knowledge base.

Open this `examples/` directory as an Obsidian vault, or read the files directly. The relative links resolve within the tree.

## Layout

```text
examples/
├── raw/machine-learning/
│   ├── 2017-06-12-attention-is-all-you-need.md
│   └── 2022-05-27-flashattention.md
└── wiki/
    ├── index.md
    ├── log.md
    └── machine-learning/
        ├── transformer-architectures.md     (current)
        ├── attention-efficiency.md          (current, supersedes attention-cost)
        ├── attention-cost.md                (stale, superseded)
        └── why-transformers-scale.md        (archive)
```

## What each file shows

| File | What it demonstrates |
|------|----------------------|
| `raw/.../*.md` | Immutable sources with frontmatter (source, collected, published); original text preserved |
| `transformer-architectures.md` | A compiled article: frontmatter, Sources/Raw provenance lines, See Also cross-reference |
| `attention-efficiency.md` | A newer source that supersedes an older claim, with an evidence chain attributing each side |
| `attention-cost.md` | A superseded page: `status: stale`, `superseded_by`, and a supersession callout. Kept for history, not deleted |
| `why-transformers-scale.md` | A crystallised query answer: `type: archive`, with Question, Findings, and standalone Lessons |
| `index.md` | The catalogue, showing the `[Stale]` and `[Archived]` summary prefixes |
| `log.md` | The append-only log with the greppable `## [date] op | title` prefix, including a supersede entry |

## Raw vs compiled

The raw files keep the source text as collected. The wiki articles distill and reorganise that material, add provenance and cross-references, and stay current as new sources arrive. The pair `attention-cost.md` (stale) and `attention-efficiency.md` (current) shows knowledge being superseded rather than overwritten: the old page remains, marked stale and pointing at its replacement, and git carries the full history.
