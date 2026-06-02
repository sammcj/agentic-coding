---
title: Transformer Architectures
type: concept
topic: machine-learning
created: 2026-04-03
updated: 2026-04-05
status: current
superseded_by:
tags: [transformers, attention]
aliases: [Transformer]
---

# Transformer Architectures

> Sources: Vaswani et al., 2017-06-12
> Raw: [Attention Is All You Need](../../raw/machine-learning/2017-06-12-attention-is-all-you-need.md)

## Overview

The Transformer is a sequence model built entirely on attention, with no recurrence and no convolution. Removing recurrence lets the model process all positions in parallel during training, which is the main reason it trains faster than the recurrent models it replaced while reaching higher quality.

## Components

Scaled dot-product attention takes projected queries, keys, and values and returns a weighted sum of the values, where each weight is the dot product of a query with a key, scaled by the square root of the key dimension. Multi-head attention runs several of these in parallel on different learned projections and concatenates the results, so the model can attend to several kinds of relationship at once.

Because there is no recurrence, position is supplied explicitly through sinusoidal positional encodings added to the input embeddings.

## Encoder-decoder structure

The encoder maps the input sequence to a continuous representation. The decoder generates output one token at a time, attending to both the encoder output and its own previous tokens, with masking that prevents it from attending to future positions.

## Scaling characteristic

Self-attention relates any two positions in constant path length, which helps with long-range dependencies. The cost is that every position is compared with every other position, so the naive implementation grows with the square of the sequence length. Whether that quadratic cost is a hard limit is taken up in [Attention Efficiency](attention-efficiency.md).

## See Also

- [Attention Efficiency](attention-efficiency.md)
