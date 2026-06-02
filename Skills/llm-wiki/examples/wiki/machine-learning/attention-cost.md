---
title: Attention Memory Cost
type: concept
topic: machine-learning
created: 2026-04-03
updated: 2026-04-05
status: stale
superseded_by: attention-efficiency.md
tags: [attention, scaling]
aliases: []
---

# Attention Memory Cost

> [!warning] Superseded by [Attention Efficiency](attention-efficiency.md) (2026-04-05). Kept for history.

> Sources: Vaswani et al., 2017-06-12
> Raw: [Attention Is All You Need](../../raw/machine-learning/2017-06-12-attention-is-all-you-need.md)

## Overview

This page recorded the early view that the quadratic memory cost of self-attention is an inherent property of the method and the binding limit on sequence length. That view no longer holds; see [Attention Efficiency](attention-efficiency.md). The page is kept because it explains why long-context work was framed as blocked before 2022.

## The original claim

Self-attention compares every position with every other position, so the attention score matrix has a size that grows with the square of the sequence length. The original Transformer work treated this as the main scaling concern for long sequences, with no practical workaround that preserved exact attention.

## Why it is now stale

The claim conflated an algorithmic property with an implementation detail. The quadratic term is real for the score matrix, but materialising that matrix in slow memory is a choice, not a requirement. [Attention Efficiency](attention-efficiency.md) covers the IO-aware approach that computes the same result in linear memory.
