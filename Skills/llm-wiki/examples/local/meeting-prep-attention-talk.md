# Prep: internal talk on attention scaling

Personal notes for the team session. This file lives in `local/`, so it is gitignored and stays in this clone only. It links into the shared wiki (allowed); nothing in the wiki links back here (not allowed).

## Angle

Open with the quadratic-cost framing, then show why it stopped being the binding limit. The wiki already has the through-line:

- [Why Transformers Scale](../wiki/machine-learning/why-transformers-scale.md) - the narrative spine for the talk.
- [Attention Efficiency](../wiki/machine-learning/attention-efficiency.md) - the IO-aware result that reframed the cost.
- [Transformer Architectures](../wiki/machine-learning/transformer-architectures.md) - background for anyone new.

## To do before the session

- Pull two concrete sequence-length numbers from the FlashAttention raw source.
- Decide whether to mention the superseded [Attention Memory Cost](../wiki/machine-learning/attention-cost.md) page as a "here is how the framing shifted" aside.

If any of this hardens into something worth keeping, promote it through a normal ingest rather than leaving it here.
