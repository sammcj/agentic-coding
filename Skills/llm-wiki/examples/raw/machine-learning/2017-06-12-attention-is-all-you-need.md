---
title: Attention Is All You Need
source: https://arxiv.org/abs/1706.03762
collected: 2026-04-03
published: 2017-06-12
type: raw
topic: machine-learning
---

# Attention Is All You Need

Vaswani et al., 2017. Introduces the Transformer, a sequence model built entirely on attention, with no recurrence and no convolution.

The core component is scaled dot-product attention: queries, keys, and values are projected, and the output is a weighted sum of the values where the weight of each value comes from the dot product of the query with the corresponding key, scaled by the square root of the key dimension. Multi-head attention runs several of these in parallel on different learned projections, then concatenates the results.

Because the model has no recurrence, position is injected through fixed sinusoidal positional encodings added to the input embeddings. The architecture is an encoder-decoder: the encoder maps the input sequence to a continuous representation, and the decoder generates the output one token at a time, attending to both the encoder output and its own previous outputs (with masking so it cannot attend to future positions).

The paper's headline result is that attention alone, without recurrence, both trains faster (it parallelises across sequence positions) and reaches higher quality than the recurrent and convolutional models that preceded it. The authors note that self-attention relates any two positions in constant path length, which helps the model learn long-range dependencies.

A known cost: self-attention compares every position with every other position, so compute and memory grow with the square of the sequence length. The paper frames this as the main scaling concern for very long sequences.
