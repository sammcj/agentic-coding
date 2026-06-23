# Knowledge Base Index

## machine-learning

How sequence models work and what governs their cost and scaling.

* [Transformer Architectures](machine-learning/transformer-architectures.md) - Attention-only sequence model: scaled dot-product and multi-head attention, positional encoding, encoder-decoder
* [Attention Efficiency](machine-learning/attention-efficiency.md) - IO-aware exact attention computes the same result in linear memory; quadratic cost was an implementation artefact
* [Attention Memory Cost](machine-learning/attention-cost.md) - [Stale] Early view that attention's quadratic memory cost was a hard limit; superseded by Attention Efficiency
* [Why Transformers Scale to Long Context](machine-learning/why-transformers-scale.md) - [Archived] Why long context is practical: parallel attention for modelling, IO-aware kernels for memory
