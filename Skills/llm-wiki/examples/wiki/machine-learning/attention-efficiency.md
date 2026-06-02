---
title: Attention Efficiency
type: concept
topic: machine-learning
created: 2026-04-05
updated: 2026-04-05
status: current
superseded_by:
tags: [attention, scaling, flashattention]
aliases: [FlashAttention]
---

# Attention Efficiency

> Sources: Dao et al., 2022-05-27; Vaswani et al., 2017-06-12
> Raw: [FlashAttention](../../raw/machine-learning/2022-05-27-flashattention.md); [Attention Is All You Need](../../raw/machine-learning/2017-06-12-attention-is-all-you-need.md)

## Overview

The memory cost of attention is not the hard limit it was once taken to be. Standard implementations materialise the full attention score matrix, which makes memory grow with the square of sequence length ([Attention Is All You Need](../../raw/machine-learning/2017-06-12-attention-is-all-you-need.md)). FlashAttention shows this is an artefact of how the computation is mapped onto GPU memory rather than a property of attention itself ([FlashAttention](../../raw/machine-learning/2022-05-27-flashattention.md)). This page supersedes the earlier [Attention Memory Cost](attention-cost.md).

## The IO-aware view

On modern GPUs the bottleneck is moving data between slow high-bandwidth memory and fast on-chip SRAM, not arithmetic. FlashAttention tiles the computation, streams blocks of queries, keys, and values through SRAM, and combines partial results with an online softmax, so the full matrix is never written to slow memory. The output is exact, identical to standard attention. The backward pass recomputes blocks instead of storing them, trading a little compute for a large drop in memory traffic.

## Result

Memory use becomes linear in sequence length rather than quadratic, and wall-clock time drops because far less data moves. Longer context windows become practical on the same hardware. The reframing is the durable lesson: a cost treated as algorithmic turned out to be an IO problem.

## See Also

- [Transformer Architectures](transformer-architectures.md)
- [Attention Memory Cost](attention-cost.md) (superseded)
