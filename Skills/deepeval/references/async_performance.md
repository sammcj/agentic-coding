# DeepEval Async Mode and Performance Optimisation Implementation Guide

## Overview

DeepEval provides built-in async execution and performance optimisation features for evaluating LLMs at scale. This guide covers practical implementation patterns, configuration options, and performance considerations.

## Quick Start: Async Mode

### Default Behaviour

Async mode is **enabled by default** in DeepEval metrics and evaluations:

```python
from deepeval.metrics import FaithfulnessMetric

# Async mode enabled by default
metric = FaithfulnessMetric(async_mode=True)
metric.measure(test_case)  # Blocks main thread but runs internal operations concurrently
```

### Enabling Async Evaluation

```python
from deepeval import evaluate
from deepeval.evaluate import AsyncConfig
from deepeval.metrics import AnswerRelevancyMetric

# Configure async evaluation
evaluate(
    test_cases=[test_case1, test_case2, test_case3],
    metrics=[AnswerRelevancyMetric()],
    async_config=AsyncConfig(
        run_async=True,        # Enable concurrent evaluation (default: True)
        max_concurrent=20,     # Max test cases evaluated simultaneously (default: 20)
        throttle_value=0       # Delay in seconds between test cases (default: 0)
    )
)
```

## Core Configuration Options

### AsyncConfig Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `run_async` | bool | `True` | Enables concurrent evaluation of test cases and metrics |
| `max_concurrent` | int | `20` | Maximum number of test cases running in parallel |
| `throttle_value` | int | `0` | Delay (seconds) between evaluating each test case |

**Important**: `throttle_value` and `max_concurrent` only apply when `run_async=True`.

### CacheConfig Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `use_cache` | bool | `False` | Read previously cached test results |
| `write_cache` | bool | `True` | Write test results to disk for future use |

## Performance Benefits

### 1. Concurrent Metric Evaluation

Multiple metrics on a single test case run concurrently:

```python
from deepeval import assert_test
from deepeval.metrics import (
    AnswerRelevancyMetric,
    FaithfulnessMetric,
    ContextualRelevancyMetric
)

# All three metrics run concurrently
assert_test(
    test_case,
    [
        AnswerRelevancyMetric(),
        FaithfulnessMetric(),
        ContextualRelevancyMetric()
    ],
    run_async=True  # Default
)
```

### 2. Parallel Test Case Execution

#### Using CLI

```bash
# Evaluate 4 test cases simultaneously using 4 processes
deepeval test run test_example.py -n 4
```

#### Using evaluate()

```python
from deepeval import evaluate
from deepeval.evaluate import AsyncConfig

# Process up to 10 test cases concurrently
evaluate(
    test_cases=dataset.test_cases,
    metrics=[metric],
    async_config=AsyncConfig(max_concurrent=10)
)
```

### 3. Async Metric Methods

Implement `a_measure()` for non-blocking metric execution:

```python
import asyncio
from deepeval.metrics import FaithfulnessMetric, AnswerRelevancyMetric

async def evaluate_multiple_metrics():
    # All measurements run concurrently without blocking
    await asyncio.gather(
        metric1.a_measure(test_case),
        metric2.a_measure(test_case),
        metric3.a_measure(test_case),
        metric4.a_measure(test_case)
    )
    print("Metrics finished!")

asyncio.run(evaluate_multiple_metrics())
```

## Caching Strategy

### Local Cache Usage

```python
from deepeval.evaluate import CacheConfig
from deepeval import evaluate

# Enable reading and writing cache
evaluate(
    test_cases=test_cases,
    metrics=[metric],
    cache_config=CacheConfig(
        use_cache=True,   # Read cached results
        write_cache=True  # Write new results to cache
    )
)
```

### CLI Cache Options

```bash
# Use cache for partially successful test runs
deepeval test run test_example.py -c

# Combine caching with parallel execution and error ignoring
deepeval test run test_example.py -c -n 4 -i
```

### Cache Benefits

- **Error recovery**: Rerun failed tests without re-evaluating successful ones
- **Development speed**: Iterate faster by skipping unchanged test cases
- **Cost savings**: Avoid redundant LLM API calls
- **Automatic management**: Results cached automatically when `write_cache=True`

## Handling Rate Limits

### Problem: Rate Limit Errors

When evaluating large datasets, you may encounter rate limit errors from LLM providers.

### Solution 1: Reduce Concurrency

```python
from deepeval.evaluate import AsyncConfig

# Lower max concurrent requests
evaluate(
    test_cases=large_dataset,
    metrics=[metric],
    async_config=AsyncConfig(max_concurrent=5)  # Reduced from default 20
)
```

### Solution 2: Add Throttling

```python
# Add 1-second delay between test cases
evaluate(
    test_cases=large_dataset,
    metrics=[metric],
    async_config=AsyncConfig(
        max_concurrent=10,
        throttle_value=1  # 1 second delay
    )
)
```

### Solution 3: Combined Approach

```python
# Conservative settings for strict rate limits
evaluate(
    test_cases=large_dataset,
    metrics=[metric],
    async_config=AsyncConfig(
        max_concurrent=3,   # Very conservative
        throttle_value=2    # 2 second delay
    )
)
```

### Default Retry Behaviour

DeepEval automatically handles transient errors:

- **Retry attempts**: 2 total (1 retry after initial failure)
- **Retried errors**: Network/timeout errors, 5xx server errors
- **Rate limits (429)**: Retried unless provider marks non-retryable
- **Backoff strategy**: Exponential with jitter
  - Initial delay: 1 second
  - Base multiplier: 2
  - Jitter: 2 seconds
  - Cap: 5 seconds

## Evaluation Time Considerations

### Metric Types and Speed

While specific timing benchmarks aren't published, performance varies by metric type:

**Fast metrics** (deterministic, no LLM calls):
- Exact match metrics
- String similarity metrics
- Statistical metrics

**Medium metrics** (single LLM call):
- Answer relevancy
- Faithfulness
- Contextual relevancy

**Slow metrics** (multiple LLM calls or complex reasoning):
- G-Eval (custom criteria)
- Conversational DAG metrics
- Multi-turn metrics

### Performance Optimisation Tips

1. **DAG metrics run significantly faster** than custom implementations due to automated parallel execution and caching
2. **Batch evaluation** is more efficient than individual test case evaluation
3. **Limit metric count**: Use 2-3 generic metrics + 1-2 custom metrics (max 5 total)
4. **Cache aggressively** during development and iteration

## Parallel Evaluation Patterns

### Pattern 1: CLI Parallel Execution

```bash
# Best for CI/CD pipelines
deepeval test run test_example.py -n 4 -c -i

# -n 4: Use 4 processes
# -c: Use cache
# -i: Ignore errors and continue
```

### Pattern 2: Python evaluate() Function

```python
from deepeval import evaluate
from deepeval.dataset import EvaluationDataset
from deepeval.metrics import AnswerRelevancyMetric

dataset = EvaluationDataset(goldens=[...])
for golden in dataset.goldens:
    dataset.add_test_case(...)

# Parallel execution with evaluate()
evaluate(
    dataset,
    [AnswerRelevancyMetric()],
    async_config=AsyncConfig(run_async=True)
)
```

### Pattern 3: Component-Level Async Evaluation

```python
from deepeval.tracing import observe, update_current_span
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase

@observe(metrics=[AnswerRelevancyMetric()])
def nested_component():
    update_current_span(
        test_case=LLMTestCase(input="...", actual_output="...")
    )
    pass

@observe()
async def llm_app(input: str):
    nested_component()

# Evaluates asynchronously when called
```

### Pattern 4: Manual Async Control

```python
import asyncio
from deepeval.metrics import (
    FaithfulnessMetric,
    AnswerRelevancyMetric,
    ContextualRelevancyMetric
)

async def evaluate_in_parallel():
    metrics = [
        FaithfulnessMetric(),
        AnswerRelevancyMetric(),
        ContextualRelevancyMetric()
    ]

    # All metrics evaluate concurrently
    results = await asyncio.gather(*[
        metric.a_measure(test_case) for metric in metrics
    ])

    return results
```

## Best Practices

### 1. Start with Defaults

```python
# Default settings work well for most use cases
evaluate(test_cases=test_cases, metrics=[metric])
```

### 2. Tune for Rate Limits

```python
# If hitting rate limits, gradually reduce concurrency
configs = [
    AsyncConfig(max_concurrent=20),  # Default - try first
    AsyncConfig(max_concurrent=10),  # If rate limited
    AsyncConfig(max_concurrent=5, throttle_value=1),  # Strict limits
]
```

### 3. Use Caching During Development

```python
# Enable cache to avoid redundant evaluations
evaluate(
    test_cases=test_cases,
    metrics=[metric],
    cache_config=CacheConfig(use_cache=True, write_cache=True)
)
```

### 4. Monitor Evaluation Costs

```python
# Check cost after evaluation
metric.measure(test_case)
print(f"Evaluation cost: ${metric.evaluation_cost}")
```

### 5. Implement Custom Async Metrics

```python
from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase

class CustomMetric(BaseMetric):
    def measure(self, test_case: LLMTestCase) -> float:
        # Synchronous implementation
        return score

    async def a_measure(self, test_case: LLMTestCase) -> float:
        # If no async implementation, reuse measure()
        return self.measure(test_case)
```

### 6. Combine Flags for Efficiency

```bash
# Efficient evaluation pipeline
deepeval test run test_example.py \
    -n 4 \        # Parallel processes
    -c \          # Use cache
    -i            # Ignore errors
```

## Known Issues and Workarounds

### Issue 1: Concurrent evaluate() Calls Fail

**Problem**: Multiple simultaneous `evaluate()` calls (e.g., from FastAPI endpoints) cause `AttributeError` failures.

**Cause**: Shared singleton state conflicts under concurrent access.

**Workaround**: Serialise `evaluate()` calls or use process-level isolation.

```python
import asyncio
from asyncio import Lock

eval_lock = Lock()

async def safe_evaluate(test_cases, metrics):
    async with eval_lock:
        return evaluate(test_cases=test_cases, metrics=metrics)
```

### Issue 2: async_mode=True Still Blocks

**Behaviour**: Even with `async_mode=True`, `metric.measure()` blocks the main thread.

**Explanation**: `async_mode=True` enables **internal** concurrent operations, but `measure()` is synchronous. Use `a_measure()` for non-blocking execution.

```python
# Blocks main thread (internal operations are concurrent)
metric.measure(test_case)

# Does not block main thread
await metric.a_measure(test_case)
```

### Issue 3: CancelledError in Async Mode

**Problem**: `asyncio.exceptions.CancelledError` occurs during evaluation (reported in v3.6.9+).

**Possible cause**: Race condition with large numbers of test cases.

**Workaround**: Reduce `max_concurrent` or disable async mode temporarily.

```python
# Reduce concurrency
evaluate(async_config=AsyncConfig(max_concurrent=5))

# Or disable async as last resort
evaluate(async_config=AsyncConfig(run_async=False))
```

## Performance Checklist

- [ ] Use default async settings (`run_async=True`, `max_concurrent=20`)
- [ ] Enable caching during development (`use_cache=True`, `write_cache=True`)
- [ ] Limit metrics to 5 or fewer per evaluation
- [ ] Use CLI parallel execution (`-n`) for CI/CD pipelines
- [ ] Implement `a_measure()` for custom metrics
- [ ] Monitor rate limits and adjust `max_concurrent` accordingly
- [ ] Use `throttle_value` for strict rate limit scenarios
- [ ] Combine cache (`-c`) with parallel execution (`-n`) in CLI
- [ ] Prefer `evaluate()` over individual `measure()` calls for batches
- [ ] Use DAG metrics for complex multi-step evaluations

## References

- [DeepEval Flags and Configs Documentation](https://deepeval.com/docs/evaluation-flags-and-configs)
- [Introduction to LLM Metrics](https://deepeval.com/docs/metrics-introduction)
- [Parallelization of Evaluations - GitHub Issue #500](https://github.com/confident-ai/deepeval/issues/500)
- [AsyncConfig CancelledError - GitHub Issue #2298](https://github.com/confident-ai/deepeval/issues/2298)
- [DeepEval Evaluation Introduction](https://deepeval.com/docs/evaluation-introduction)
- [DataCamp DeepEval Tutorial](https://www.datacamp.com/tutorial/deepeval)
- [GitHub Repository](https://github.com/confident-ai/deepeval)
