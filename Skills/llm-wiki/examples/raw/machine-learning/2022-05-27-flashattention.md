---
title: "FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness"
source: https://arxiv.org/abs/2205.14135
collected: 2026-04-05
published: 2022-05-27
type: raw
topic: machine-learning
---

# FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness

Dao et al., 2022. Argues that the bottleneck in attention on modern GPUs is not arithmetic but memory movement between the slow high-bandwidth memory (HBM) and the fast on-chip SRAM. Standard implementations materialise the full attention matrix in HBM, which is what makes memory grow with the square of the sequence length.

FlashAttention computes the same exact attention without ever writing the full matrix to HBM. It tiles the computation, streams blocks of queries, keys, and values into SRAM, and uses the online softmax trick to combine partial results, so the output is identical to standard attention. In the backward pass it recomputes attention blocks rather than storing them, trading a little extra compute for a large reduction in memory traffic.

The result: memory use becomes linear in sequence length rather than quadratic, and wall-clock time drops because the kernel moves far less data. This makes much longer context windows practical on the same hardware.

The reframing matters as much as the numbers. The quadratic memory cost of attention had been treated as an algorithmic property of the method. FlashAttention shows it was largely an artefact of how the computation was mapped onto the memory hierarchy: an IO problem, not an inherent limit of attention.
