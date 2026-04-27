# DeepEval Custom Metrics Implementation Guide

## Overview

DeepEval provides extensive extensibility for creating custom evaluation metrics beyond G-Eval. You can create completely custom metrics by subclassing base metric classes, implementing your own scoring logic, and integrating with traditional NLP scoring methods or custom LLMs.

## Can You Create Custom Metrics by Subclassing?

**Yes.** DeepEval allows you to create custom metrics by inheriting from `BaseMetric` (or related base classes for different test case types). Custom metrics are automatically integrated within DeepEval's ecosystem, including CI/CD pipelines, metric caching, multi-processing, and automatic reporting to Confident AI.

## BaseMetric Class Interface

### Core Properties

```python
class BaseMetric:
    # Required properties
    threshold: float                        # Pass/fail threshold
    score: Optional[float] = None          # Calculated metric score
    success: Optional[bool] = None         # Pass/fail status
    reason: Optional[str] = None           # Explanation for score
    error: Optional[str] = None            # Error information if evaluation failed

    # Optional configuration
    evaluation_model: Optional[str] = None  # Name of evaluation model
    include_reason: bool = False           # Include reasoning in output
    strict_mode: bool = False              # Strict threshold enforcement
    async_mode: bool = True                # Enable async execution
    verbose_mode: bool = True              # Detailed logging

    # Internal tracking
    evaluation_cost: Optional[float] = None
    verbose_logs: Optional[str] = None
    score_breakdown: Dict = None
    skipped: bool = False
    requires_trace: bool = False
    model: Optional[DeepEvalBaseLLM] = None
    using_native_model: Optional[bool] = None
    _required_params: List[LLMTestCaseParams]
```

### Required Methods

#### 1. `__init__` - Initialise Properties

```python
def __init__(
    self,
    threshold: float = 0.5,
    evaluation_model: str = None,
    include_reason: bool = True,
    strict_mode: bool = False,
    async_mode: bool = True
):
    self.threshold = 1 if strict_mode else threshold
    self.evaluation_model = evaluation_model
    self.include_reason = include_reason
    self.strict_mode = strict_mode
    self.async_mode = async_mode
```

#### 2. `measure()` - Synchronous Evaluation

```python
@abstractmethod
def measure(self, test_case: LLMTestCase, *args, **kwargs) -> float:
    """
    Perform synchronous evaluation of test case.

    Must set:
    - self.score: The calculated metric score
    - self.success: Whether test passed (score >= threshold)
    - self.reason: (Optional) Explanation for the score
    - self.error: (If exception) Error message

    Returns:
        float: The calculated score
    """
    raise NotImplementedError
```

#### 3. `a_measure()` - Asynchronous Evaluation

```python
@abstractmethod
async def a_measure(self, test_case: LLMTestCase, *args, **kwargs) -> float:
    """
    Perform asynchronous evaluation of test case.

    Should implement the same scoring logic as measure() but using
    async operations where possible. If no async implementation is
    available, can simply call measure():

    async def a_measure(self, test_case: LLMTestCase) -> float:
        return self.measure(test_case)

    Returns:
        float: The calculated score
    """
    raise NotImplementedError
```

#### 4. `is_successful()` - Determine Pass/Fail Status

```python
@abstractmethod
def is_successful(self) -> bool:
    """
    Determine if the metric evaluation was successful.

    Recommended implementation:
    """
    if self.error is not None:
        self.success = False
    else:
        return self.success
    return self.success
```

#### 5. `__name__` - Metric Name Property

```python
@property
def __name__(self):
    """Return the display name for this metric"""
    return "My Custom Metric"
```

## Custom Scoring Logic Implementation

### Example 1: Simple ROUGE Metric

```python
from deepeval.scorer import Scorer
from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase

class RougeMetric(BaseMetric):
    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold
        self.scorer = Scorer()

    def measure(self, test_case: LLMTestCase) -> float:
        try:
            self.score = self.scorer.rouge_score(
                prediction=test_case.actual_output,
                target=test_case.expected_output,
                score_type="rouge1"
            )
            self.success = self.score >= self.threshold
            return self.score
        except Exception as e:
            self.error = str(e)
            raise

    async def a_measure(self, test_case: LLMTestCase) -> float:
        # ROUGE scoring is not async, so reuse sync method
        return self.measure(test_case)

    def is_successful(self) -> bool:
        if self.error is not None:
            self.success = False
        else:
            return self.success
        return self.success

    @property
    def __name__(self):
        return "Rouge Metric"
```

### Example 2: Composite Metric (Combining Multiple Metrics)

```python
from deepeval.metrics import BaseMetric, AnswerRelevancyMetric, FaithfulnessMetric
from deepeval.test_case import LLMTestCase
from typing import Optional

class FaithfulRelevancyMetric(BaseMetric):
    def __init__(
        self,
        threshold: float = 0.5,
        evaluation_model: Optional[str] = "gpt-4-turbo",
        include_reason: bool = True,
        async_mode: bool = True,
        strict_mode: bool = False,
    ):
        self.threshold = 1 if strict_mode else threshold
        self.evaluation_model = evaluation_model
        self.include_reason = include_reason
        self.async_mode = async_mode
        self.strict_mode = strict_mode

    def measure(self, test_case: LLMTestCase) -> float:
        try:
            relevancy_metric, faithfulness_metric = self.initialise_metrics()

            # Run both metrics
            relevancy_metric.measure(test_case)
            faithfulness_metric.measure(test_case)

            # Custom logic to combine scores
            self.set_score_reason_success(relevancy_metric, faithfulness_metric)
            return self.score
        except Exception as e:
            self.error = str(e)
            raise

    async def a_measure(self, test_case: LLMTestCase) -> float:
        try:
            relevancy_metric, faithfulness_metric = self.initialise_metrics()

            # Run both metrics concurrently using async
            await relevancy_metric.a_measure(test_case)
            await faithfulness_metric.a_measure(test_case)

            self.set_score_reason_success(relevancy_metric, faithfulness_metric)
            return self.score
        except Exception as e:
            self.error = str(e)
            raise

    def is_successful(self) -> bool:
        if self.error is not None:
            self.success = False
        else:
            return self.success
        return self.success

    @property
    def __name__(self):
        return "Composite Relevancy Faithfulness Metric"

    # Helper methods
    def initialise_metrics(self):
        relevancy_metric = AnswerRelevancyMetric(
            threshold=self.threshold,
            model=self.evaluation_model,
            include_reason=self.include_reason,
            async_mode=self.async_mode,
            strict_mode=self.strict_mode
        )
        faithfulness_metric = FaithfulnessMetric(
            threshold=self.threshold,
            model=self.evaluation_model,
            include_reason=self.include_reason,
            async_mode=self.async_mode,
            strict_mode=self.strict_mode
        )
        return relevancy_metric, faithfulness_metric

    def set_score_reason_success(
        self,
        relevancy_metric: BaseMetric,
        faithfulness_metric: BaseMetric
    ):
        # Take minimum of both scores for conservative evaluation
        composite_score = min(relevancy_metric.score, faithfulness_metric.score)
        self.score = 0 if self.strict_mode and composite_score < self.threshold else composite_score

        # Combine reasons from both metrics
        if self.include_reason:
            self.reason = f"{relevancy_metric.reason}\n\n{faithfulness_metric.reason}"

        # Success requires both metrics to pass
        self.success = self.score >= self.threshold
```

### Example 3: Custom LLM-Based Metric with Error Handling

```python
from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase
from deepeval.models import DeepEvalBaseLLM
from typing import Optional

class CustomLLMMetric(BaseMetric):
    def __init__(
        self,
        threshold: float = 0.5,
        model: Optional[DeepEvalBaseLLM] = None,
        include_reason: bool = True,
        async_mode: bool = True
    ):
        self.threshold = threshold
        self.model = model
        self.include_reason = include_reason
        self.async_mode = async_mode

    def measure(self, test_case: LLMTestCase) -> float:
        try:
            # Custom scoring logic using LLM
            prompt = self._generate_evaluation_prompt(test_case)
            response = self.model.generate(prompt)

            # Parse response and calculate score
            self.score = self._parse_score(response)

            if self.include_reason:
                self.reason = self._parse_reason(response)

            self.success = self.score >= self.threshold
            return self.score
        except Exception as e:
            self.error = str(e)
            self.success = False
            raise

    async def a_measure(self, test_case: LLMTestCase) -> float:
        try:
            prompt = self._generate_evaluation_prompt(test_case)
            response = await self.model.a_generate(prompt)

            self.score = self._parse_score(response)

            if self.include_reason:
                self.reason = self._parse_reason(response)

            self.success = self.score >= self.threshold
            return self.score
        except Exception as e:
            self.error = str(e)
            self.success = False
            raise

    def is_successful(self) -> bool:
        if self.error is not None:
            self.success = False
        else:
            return self.success
        return self.success

    @property
    def __name__(self):
        return "Custom LLM Metric"

    # Helper methods
    def _generate_evaluation_prompt(self, test_case: LLMTestCase) -> str:
        return f"""
        Evaluate the following LLM output.
        Input: {test_case.input}
        Output: {test_case.actual_output}

        Provide a score from 0-1 and reasoning.
        """

    def _parse_score(self, response: str) -> float:
        # Custom parsing logic
        pass

    def _parse_reason(self, response: str) -> str:
        # Custom parsing logic
        pass
```

## Available Scoring Methods via Scorer Class

DeepEval provides a `Scorer` class with traditional NLP scoring methods:

### ROUGE Score
```python
from deepeval.scorer import Scorer

scorer = Scorer()
score = scorer.rouge_score(
    target="reference text",
    prediction="generated text",
    score_type="rouge1"  # Options: 'rouge1', 'rouge2', 'rougeL'
)
```

### BLEU Score
```python
score = scorer.sentence_bleu_score(
    references="reference text",  # or List[str]
    prediction="generated text",
    bleu_type="bleu1"  # Options: 'bleu1', 'bleu2', 'bleu3', 'bleu4'
)
```

### BERTScore
```python
scores = scorer.bert_score(
    references="reference text",
    predictions="generated text",
    model="microsoft/deberta-large-mnli",
    lang="en"
)
# Returns dict with 'bert-precision', 'bert-recall', 'bert-f1'
```

### Exact Match
```python
score = scorer.exact_match_score(
    target="expected text",
    prediction="generated text"
)
# Returns 1 for exact match, 0 otherwise
```

### Neural Toxicity Score
```python
toxicity_scores = scorer.neural_toxic_score(
    prediction="text to evaluate",
    model="original"  # Options: 'original', 'unbiased', 'multilingual'
)
# Returns mean toxicity score and dict of toxicity types
```

### Hallucination Score
```python
score = scorer.hallucination_score(
    source="source document",
    prediction="generated summary",
    model=None  # Uses Vectara Hallucination Evaluation Model
)
```

### Bias Score
```python
score = scorer.neural_bias_score(
    text="text to evaluate",
    model=None
)
```

## Using Custom Metrics

### Standalone Execution
```python
from deepeval.test_case import LLMTestCase

test_case = LLMTestCase(
    input="What is machine learning?",
    actual_output="Machine learning is a subset of AI...",
    expected_output="Machine learning is an AI field..."
)

metric = RougeMetric(threshold=0.5)
metric.measure(test_case)

print(f"Score: {metric.score}")
print(f"Success: {metric.is_successful()}")
print(f"Reason: {metric.reason}")
```

### With DeepEval Test Framework
```python
from deepeval import assert_test, evaluate
from deepeval.test_case import LLMTestCase

def test_llm():
    metric = RougeMetric(threshold=0.5)
    test_case = LLMTestCase(...)
    assert_test(test_case, [metric])

# Or bulk evaluation
evaluate(test_cases=[test_case1, test_case2], metrics=[metric])
```

### Async Execution
```python
# Metrics run asynchronously by default
def test_multiple_metrics():
    test_case = LLMTestCase(...)
    metric1 = CustomMetric1()
    metric2 = CustomMetric2()

    # Both metrics run concurrently
    assert_test(test_case, [metric1, metric2], run_async=True)
```

## Custom Metric Requirements Summary

### Essential Elements
1. **Inherit from BaseMetric** (or BaseConversationalMetric, BaseMultimodalMetric, BaseArenaMetric for other test case types)
2. **Implement `__init__`** with at minimum a `threshold` parameter
3. **Implement `measure()`** with score calculation logic
4. **Implement `a_measure()`** for async support (can reuse `measure()` if no async operations)
5. **Implement `is_successful()`** to determine pass/fail status
6. **Define `__name__` property** for metric identification

### Best Practices
1. **Set self.score** in both `measure()` and `a_measure()`
2. **Set self.success** based on threshold comparison
3. **Set self.reason** if `include_reason=True`
4. **Set self.error** and re-raise exceptions in try-except blocks
5. **Use strict_mode** to enforce threshold > rather than >=
6. **Leverage async operations** in `a_measure()` for concurrent metric execution
7. **Consider test case parameter requirements** via `_required_params`

## Community Examples

### Real-World Use Cases

1. **Medical Diagnosis Faithfulness**: Custom G-Eval metric checking clinical accuracy against medical literature
2. **PII Leakage Detection**: Metric identifying personally identifiable information in outputs
3. **Action Item Accuracy**: Meeting summarisation metric validating action items
4. **Clarity Evaluation**: Assessing response clarity and directness
5. **Professionalism Assessment**: Evaluating tone and domain-appropriate formality
6. **Citation Accuracy**: Validating citations in RAG responses
7. **Summary Concision**: Checking summary focus and brevity

### Framework Statistics

DeepEval processes over 10 million G-Eval metrics monthly, with answer correctness being the most commonly used custom metric type. The framework supports three primary custom metric approaches:

1. **G-Eval**: LLM-as-a-judge with subjective criteria
2. **DAG Metric**: Deterministic LLM-powered decision trees (most powerful)
3. **BaseMetric subclassing**: Full custom implementation control

## Integration Benefits

Custom metrics inherit DeepEval's ecosystem capabilities:

- **CI/CD Integration**: Run metrics in continuous integration pipelines
- **Metric Caching**: Avoid redundant evaluations
- **Multi-processing**: Parallel metric execution for performance
- **Confident AI Platform**: Automatic result reporting and visualisation
- **Test Reports**: Detailed evaluation summaries and logs
- **Tracing Support**: Component-level evaluation with `@observe` decorator

## Additional Resources

- [Official Custom Metrics Documentation](https://deepeval.com/docs/metrics-custom)
- [Building Custom Metrics Guide](https://deepeval.com/guides/guides-building-custom-metrics)
- [G-Eval Metric Documentation](https://deepeval.com/docs/metrics-llm-evals)
- [DeepEval GitHub Repository](https://github.com/confident-ai/deepeval)
- [Scorer Class Implementation](https://github.com/confident-ai/deepeval/blob/main/deepeval/scorer/scorer.py)
- [BaseMetric Source Code](https://github.com/confident-ai/deepeval/blob/main/deepeval/metrics/base_metric.py)

---

*Research conducted: 2025-11-25*
*DeepEval Version: Latest (as of January 2025)*
