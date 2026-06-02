---
title: Why Transformers Scale to Long Context
type: archive
topic: machine-learning
created: 2026-04-06
updated: 2026-04-06
status: current
tags: [transformers, attention, scaling]
aliases: []
---

# Why Transformers Scale to Long Context

> Sources: [Transformer Architectures](transformer-architectures.md); [Attention Efficiency](attention-efficiency.md)
> Archived: 2026-04-06

## Question

If self-attention compares every position with every other, why are long context windows practical today?

## Findings

Two separate properties combine. First, the Transformer drops recurrence, so all positions are processed in parallel and any two positions sit at constant path length, which is what makes attention good at long-range dependencies in the first place ([Transformer Architectures](transformer-architectures.md)).

Second, the memory cost that once capped sequence length was an implementation artefact, not an algorithmic limit. IO-aware methods compute exact attention in linear memory by never materialising the full score matrix ([Attention Efficiency](attention-efficiency.md)). The earlier framing that the quadratic cost was a hard ceiling has been superseded.

So the short answer: attention gives the modelling benefit, and IO-aware kernels remove the memory penalty that used to make long context impractical.

## Map

Two paths converge on practical long context; the superseded view is shown dashed and grey. (Archive snapshot, 2026-04-06; see `../../../references/concept-map.md`.)

```mermaid
flowchart LR
    arch["Transformer Architectures"]:::focus
    eff["Attention Efficiency"]:::current
    cost["Attention Memory Cost"]:::stale
    out(["Long context is practical"]):::archive

    arch -->|"enables long-range modelling"| out
    arch -->|"naive cost is quadratic"| cost
    cost -->|"superseded by"| eff
    eff -->|"removes the memory penalty"| out

    classDef focus    fill:#cfe2ff,stroke:#2f6fb0,stroke-width:2px,color:#0d2a44;
    classDef current  fill:#e8eef6,stroke:#4a5b6e,color:#16202c;
    classDef stale    fill:#ececec,stroke:#9aa0a6,stroke-dasharray:4 3,color:#5f6368;
    classDef archive  fill:#fdebcf,stroke:#c8862a,color:#5a3e12;
```

## Lessons

- A cost that looks algorithmic can turn out to be a systems problem; check where the data actually moves before treating a bound as fundamental.
- "Exact but cheaper" beats "approximate" when an implementation change can deliver it.

## See Also

- [Transformer Architectures](transformer-architectures.md)
- [Attention Efficiency](attention-efficiency.md)
