# DeepEval Dataset Management Implementation Guide

## Overview

DeepEval provides dataset management capabilities through the `EvaluationDataset` class and synthetic data generation through the `Synthesizer` class. This guide covers practical workflows for creating, loading, managing, and versioning evaluation datasets.

## Core Concepts

### Golden vs Test Case

- **Golden**: A precursor to a test case containing input data and expected results. Goldens exist within an `EvaluationDataset` and lack `actual_output` at creation time.
- **Test Case**: Generated from a golden at evaluation time by adding the `actual_output` from your LLM application.

### Dataset Types

- **Single-Turn**: Contains `Golden` objects with `input` field for single interaction scenarios
- **Multi-Turn**: Contains `ConversationalGolden` objects with `scenario` and `expected_outcome` fields for conversational AI evaluation

**Important**: A dataset's type (`_multi_turn`) is immutable once the first golden is added.

## EvaluationDataset API

### Initialisation

```python
from deepeval.dataset import EvaluationDataset, Golden, ConversationalGolden

# Empty dataset
dataset = EvaluationDataset()

# Single-turn dataset
dataset = EvaluationDataset(goldens=[
    Golden(input="What is your name?"),
    Golden(input="Choose a number between 1 to 100")
])

# Multi-turn dataset
dataset = EvaluationDataset(goldens=[
    ConversationalGolden(
        scenario="User frustrated about delayed order",
        expected_outcome="Redirected to human agent",
        user_description="Returning customer with history of issues"
    )
])
```

### Golden Object Structure

#### Single-Turn Golden

```python
from deepeval.dataset import Golden

golden = Golden(
    input="What is your refund policy?",  # Required
    expected_output="We offer a 30-day full refund",  # Optional
    context=["Refund policy: 30 days, full refund"],  # Optional list of strings
    expected_tools=[],  # Optional list of ToolCall objects

    # Metadata fields
    additional_metadata={"source": "customer_faq"},  # Optional dict
    comments="Edge case for international orders",  # Optional string
    custom_column_key_values={"priority": "high"}  # Optional dict
)
```

#### Multi-Turn ConversationalGolden

```python
from deepeval.dataset import ConversationalGolden

conversational_golden = ConversationalGolden(
    scenario="Andy Byron wants to purchase VIP tickets to a Coldplay concert",
    expected_outcome="Successful purchase of two tickets",
    user_description="Andy Byron is the CEO of Astronomer"
)
```

### Adding Data to Datasets

#### Adding Individual Goldens

```python
# Add to single-turn dataset
dataset.add_golden(Golden(input="What are your business hours?"))

# Add to multi-turn dataset
dataset.add_golden(ConversationalGolden(
    scenario="User expressing gratitude",
    expected_outcome="Acknowledges appreciation"
))
```

#### Adding Test Cases

```python
from deepeval.test_case import LLMTestCase

# Generate test cases from goldens
for golden in dataset.goldens:
    test_case = LLMTestCase(
        input=golden.input,
        actual_output=your_llm_app(golden.input),
        expected_output=golden.expected_output,
        retrieval_context=golden.context
    )
    dataset.add_test_case(test_case)
```

### Loading Datasets from Files

#### From JSON

```python
from deepeval.dataset import EvaluationDataset

dataset = EvaluationDataset()

# Load goldens with default key mapping
dataset.add_goldens_from_json_file(
    file_path="/path/to/goldens.json"
)

# Load goldens with custom key mapping
dataset.add_goldens_from_json_file(
    file_path="/path/to/goldens.json",
    input_key_name="query",
    expected_output_key_name="ideal_response",
    context_key_name="knowledge_chunks"
)

# Load complete test cases
dataset.add_test_cases_from_json_file(
    file_path="/path/to/test_cases.json",
    input_key_name="query",
    actual_output_key_name="model_response",
    expected_output_key_name="ideal_response",
    context_key_name="context",
    retrieval_context_key_name="retrieved_chunks"
)
```

**JSON Format Example**:
```json
[
  {
    "input": "What is your refund policy?",
    "expected_output": "We offer a 30-day full refund",
    "context": ["Refund policy: 30 days, full refund, no questions asked"]
  },
  {
    "input": "Do you ship internationally?",
    "expected_output": "Yes, we ship to over 50 countries",
    "context": ["International shipping available to 50+ countries"]
  }
]
```

#### From CSV

```python
dataset = EvaluationDataset()

# Load goldens with default column mapping
dataset.add_goldens_from_csv_file(
    file_path="/path/to/goldens.csv"
)

# Load goldens with custom column mapping and delimiter
dataset.add_goldens_from_csv_file(
    file_path="/path/to/goldens.csv",
    input_col_name="query",
    expected_output_col_name="ideal_response",
    context_col_name="knowledge_base",
    context_col_delimiter=";"  # Split context strings into lists
)

# Load complete test cases
dataset.add_test_cases_from_csv_file(
    file_path="/path/to/test_cases.csv",
    input_col_name="query",
    actual_output_col_name="model_response",
    expected_output_col_name="ideal_response",
    context_col_name="context",
    context_col_delimiter=";",
    retrieval_context_col_name="retrieved_chunks",
    retrieval_context_col_delimiter=";"
)
```

**CSV Format Example**:
```csv
input,expected_output,context
"What is your refund policy?","We offer a 30-day full refund","Refund policy: 30 days;Full refund;No questions asked"
"Do you ship internationally?","Yes, we ship to over 50 countries","International shipping;50+ countries"
```

### Saving Datasets

#### Local Storage

```python
# Save as JSON
dataset.save_as(
    file_type="json",
    directory="/path/to/datasets",
    file_name="my_evaluation_dataset",  # Optional, defaults to timestamp
    include_test_cases=True  # Include both goldens and test cases
)

# Save as CSV
dataset.save_as(
    file_type="csv",
    directory="/path/to/datasets",
    file_name="my_evaluation_dataset",
    include_test_cases=False  # Save only goldens
)
```

#### Cloud Storage (Confident AI)

```python
# Push to Confident AI
dataset.push(
    alias="Production Evaluation Dataset v2",
    finalized=True  # Set to False for draft datasets
)

# Overwrite existing dataset
dataset.push(
    alias="Production Evaluation Dataset v2",
    overwrite=True
)
```

### Loading Datasets from Cloud

```python
dataset = EvaluationDataset()

# Pull from Confident AI
dataset.pull(alias="Production Evaluation Dataset v2")

# Pull public dataset
dataset.pull(alias="health_rag_queries", public=True)

# Access the loaded goldens
print(f"Loaded {len(dataset.goldens)} goldens")
for golden in dataset.goldens:
    print(f"Input: {golden.input[:50]}...")
```

### Dataset Properties and Methods

```python
# Access goldens
print(dataset.goldens)  # List of Golden or ConversationalGolden objects

# Access test cases
print(dataset.test_cases)  # List of LLMTestCase objects

# Check dataset type
print(dataset._multi_turn)  # True or False

# Iterate for evaluation
for golden in dataset.evals_iterator():
    response = your_llm_app(golden.input)
    # Process response
```

## Synthetic Dataset Generation with Synthesizer

### Synthesizer Initialisation

```python
from deepeval.synthesizer import Synthesizer
from deepeval.synthesizer.config import (
    FiltrationConfig,
    EvolutionConfig,
    StylingConfig,
    Evolution
)

# Basic initialisation
synthesizer = Synthesizer()

# Advanced configuration
synthesizer = Synthesizer(
    model="gpt-4o",  # or custom DeepEvalBaseLLM instance
    async_mode=True,  # Enable concurrent generation
    max_concurrent=50,  # Control parallelism
    cost_tracking=True,  # Display LLM API costs

    # Quality control
    filtration_config=FiltrationConfig(
        synthetic_input_quality_threshold=0.7,  # 0-1 scale
        max_quality_retries=5
    ),

    # Complexity configuration
    evolution_config=EvolutionConfig(
        num_evolutions=2,  # Evolution steps per input
        evolutions={
            Evolution.REASONING: 0.3,
            Evolution.MULTICONTEXT: 0.2,
            Evolution.CONCRETISING: 0.2,
            Evolution.COMPARATIVE: 0.15,
            Evolution.HYPOTHETICAL: 0.15
        }
    ),

    # Output styling
    styling_config=StylingConfig(
        input_format="Question format with specific technical context",
        expected_output_format="Concise answer with code examples",
        task="Technical documentation Q&A",
        scenario="Developer onboarding to API"
    )
)
```

### Generation Methods

#### From Documents

```python
# Generate single-turn goldens
goldens = synthesizer.generate_goldens_from_docs(
    document_paths=[
        "/path/to/docs/api_guide.txt",
        "/path/to/docs/user_manual.pdf",
        "/path/to/docs/faq.docx",
        "/path/to/docs/readme.md"
    ],
    include_expected_output=True,
    max_goldens_per_document=10,
    chunk_size=1024,  # Tokens per chunk
    chunk_overlap=128  # Overlap between chunks
)

# Generate multi-turn conversational goldens
conversational_goldens = synthesizer.generate_conversational_goldens_from_docs(
    document_paths=["/path/to/chatbot_scenarios.txt"],
    include_expected_outcome=True,
    max_goldens_per_document=5
)

# Access generated goldens
print(f"Generated {len(synthesizer.synthetic_goldens)} goldens")
```

#### From Prepared Contexts

```python
# Define context groups (each group = list of related text chunks)
contexts = [
    [
        "Our refund policy allows returns within 30 days.",
        "Refunds are processed within 5-7 business days.",
        "Original shipping costs are non-refundable unless item is defective."
    ],
    [
        "We accept Visa, Mastercard, American Express, and PayPal.",
        "All transactions use 256-bit SSL encryption.",
        "Payment methods can be saved for future purchases."
    ],
    [
        "Standard shipping takes 3-5 business days.",
        "Express shipping (1-2 days) available for additional fee.",
        "Free shipping on orders over $50."
    ]
]

# Generate single-turn goldens
goldens = synthesizer.generate_goldens_from_contexts(
    contexts=contexts,
    include_expected_output=True,
    max_goldens_per_context=3,
    source_files=["refund_policy.txt", "payment_info.txt", "shipping_guide.txt"]
)

# Generate multi-turn goldens
conversational_goldens = synthesizer.generate_conversational_goldens_from_contexts(
    contexts=contexts,
    include_expected_outcome=True,
    max_goldens_per_context=2
)
```

#### From Scratch

```python
# Generate goldens without source documents
goldens = synthesizer.generate_goldens_from_scratch(
    num_goldens=25,
    include_expected_output=True
)

conversational_goldens = synthesizer.generate_conversational_goldens_from_scratch(
    num_goldens=15,
    include_expected_outcome=True
)
```

#### From Existing Goldens (Evolution)

```python
# Expand existing dataset with variations
existing_goldens = [
    Golden(input="What is your refund policy?"),
    Golden(input="How do I track my order?")
]

expanded_goldens = synthesizer.generate_goldens_from_goldens(
    goldens=existing_goldens,
    num_goldens=10,  # Total goldens to generate
    include_expected_output=True
)
```

### Synthetic Data Pipeline

The generation process follows four stages:

1. **Input Generation**: Creates synthetic inputs with or without provided contexts
2. **Filtration**: Filters inputs based on quality criteria:
   - Self-containment (input is complete without external context)
   - Clarity (intent is clearly conveyed)
   - Quality scores range from 0-1
3. **Evolution**: Rewrites inputs to increase complexity using evolution techniques
4. **Styling**: Applies output format preferences

### Evolution Techniques

```python
from deepeval.synthesizer.config import Evolution

# Available evolution types
evolutions = {
    Evolution.REASONING: 0.25,      # Multi-step logical thinking
    Evolution.MULTICONTEXT: 0.20,   # Utilises all context information
    Evolution.CONCRETISING: 0.15,   # Makes abstract concepts concrete
    Evolution.CONSTRAINED: 0.10,    # Adds specific constraints
    Evolution.COMPARATIVE: 0.15,    # Requires comparisons
    Evolution.HYPOTHETICAL: 0.10,   # Introduces hypothetical scenarios
    Evolution.IN_BREADTH: 0.05      # Broadens scope
}

synthesizer = Synthesizer(
    evolution_config=EvolutionConfig(
        num_evolutions=2,  # Each input evolved twice
        evolutions=evolutions
    )
)
```

### Accessing Generation Metadata

```python
# Convert to DataFrame for analysis
import pandas as pd

df = synthesizer.to_pandas()
print(df.head())

# Access quality scores
for golden in synthesizer.synthetic_goldens:
    input_quality = golden.additional_metadata.get("synthetic_input_quality")
    context_quality = golden.additional_metadata.get("context_quality")
    evolutions = golden.additional_metadata.get("evolutions")

    print(f"Input Quality: {input_quality}")
    print(f"Context Quality: {context_quality}")
    print(f"Evolution Applied: {evolutions}")
```

### Saving Synthetic Datasets

```python
from deepeval.dataset import EvaluationDataset

# Create dataset from synthetic goldens
dataset = EvaluationDataset(goldens=synthesizer.synthetic_goldens)

# Save locally
dataset.save_as(
    file_type="json",
    directory="/path/to/synthetic_datasets"
)

# Push to Confident AI
dataset.push(alias="Synthetic QA Dataset v1")
```

## Confident AI Cloud Integration

### Authentication

```python
from deepeval import login

# Interactive login (opens browser)
login()

# Or set API key in environment
# export CONFIDENT_API_KEY="your-api-key"
```

### Cloud Dataset Management

#### Pushing Datasets

```python
dataset = EvaluationDataset(goldens=goldens)

# Push finalised dataset
dataset.push(
    alias="Customer Support QA v2.1",
    finalized=True
)

# Push draft dataset (won't be pulled until finalised)
dataset.push(
    alias="Customer Support QA Draft",
    finalized=False
)

# Overwrite existing dataset
dataset.push(
    alias="Customer Support QA v2.1",
    overwrite=True
)
```

#### Pulling Datasets

```python
# Pull from cloud
dataset = EvaluationDataset()
dataset.pull(alias="Customer Support QA v2.1")

# Pull public dataset
dataset.pull(alias="topic_agent_queries", public=True)

# List available datasets
available_datasets = EvaluationDataset.list_datasets()
for ds in available_datasets:
    print(f"Dataset: {ds['alias']}, ID: {ds['id']}, Size: {ds['size']}")
```

#### Updating Cloud Datasets

```python
# Pull existing dataset
dataset = EvaluationDataset()
dataset.pull(alias="Customer Support QA v2.1")

# Add new goldens
dataset.add_golden(Golden(
    input="What is your international shipping policy?",
    expected_output="We ship to 50+ countries with tracking"
))

# Push updates
dataset.push(alias="Customer Support QA v2.1", overwrite=True)
```

#### Versioning Strategy

```python
# Version naming convention
dataset.push(alias="Customer Support QA v1.0")
dataset.push(alias="Customer Support QA v1.1")
dataset.push(alias="Customer Support QA v2.0")

# Or use descriptive names
dataset.push(alias="Customer Support QA - Production")
dataset.push(alias="Customer Support QA - Staging")
dataset.push(alias="Customer Support QA - Development")
```

## Practical Workflows

### Workflow 1: Creating Dataset from CSV Files

```python
from deepeval.dataset import EvaluationDataset

# Load from CSV
dataset = EvaluationDataset()
dataset.add_goldens_from_csv_file(
    file_path="/data/customer_queries.csv",
    input_col_name="question",
    expected_output_col_name="answer",
    context_col_name="relevant_docs",
    context_col_delimiter="|"
)

# Validate
print(f"Loaded {len(dataset.goldens)} goldens")

# Save to cloud
dataset.push(alias="Customer Queries v1.0")
```

### Workflow 2: Synthetic Dataset Generation

```python
from deepeval.synthesizer import Synthesizer
from deepeval.dataset import EvaluationDataset

# Initialise synthesizer
synthesizer = Synthesizer(model="gpt-4o", cost_tracking=True)

# Generate from documents
synthesizer.generate_goldens_from_docs(
    document_paths=[
        "/docs/api_reference.md",
        "/docs/user_guide.pdf",
        "/docs/troubleshooting.txt"
    ],
    include_expected_output=True,
    max_goldens_per_document=15,
    chunk_size=1024
)

# Review quality
df = synthesizer.to_pandas()
high_quality = df[df['synthetic_input_quality'] > 0.7]
print(f"High quality goldens: {len(high_quality)}")

# Create and save dataset
dataset = EvaluationDataset(goldens=synthesizer.synthetic_goldens)
dataset.push(alias="Synthetic API Documentation Dataset")
```

### Workflow 3: Hybrid Dataset (Manual + Synthetic)

```python
from deepeval.dataset import EvaluationDataset, Golden
from deepeval.synthesizer import Synthesizer

# Start with manual goldens
manual_goldens = [
    Golden(
        input="How do I reset my password?",
        expected_output="Click 'Forgot Password' on the login page",
        context=["Password reset instructions in user guide"]
    ),
    Golden(
        input="What are your support hours?",
        expected_output="24/7 support available",
        context=["Support information from FAQ"]
    )
]

# Generate variations
synthesizer = Synthesizer()
synthetic_goldens = synthesizer.generate_goldens_from_goldens(
    goldens=manual_goldens,
    num_goldens=20,
    include_expected_output=True
)

# Combine datasets
all_goldens = manual_goldens + synthesizer.synthetic_goldens
dataset = EvaluationDataset(goldens=all_goldens)

# Save
dataset.save_as(file_type="json", directory="/datasets")
dataset.push(alias="Hybrid Support Dataset v1")
```

### Workflow 4: Dataset-Based Evaluation

```python
from deepeval.dataset import EvaluationDataset
from deepeval.test_case import LLMTestCase
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric
from deepeval import evaluate

# Load dataset
dataset = EvaluationDataset()
dataset.pull(alias="Customer Support QA v2.1")

# Generate test cases
for golden in dataset.goldens:
    test_case = LLMTestCase(
        input=golden.input,
        actual_output=your_llm_app(golden.input),
        expected_output=golden.expected_output,
        retrieval_context=golden.context
    )
    dataset.add_test_case(test_case)

# Evaluate
metrics = [
    AnswerRelevancyMetric(threshold=0.7),
    FaithfulnessMetric(threshold=0.8)
]
evaluate(dataset, metrics=metrics)
```

### Workflow 5: CI/CD Integration with Pytest

```python
import pytest
from deepeval import assert_test
from deepeval.dataset import EvaluationDataset
from deepeval.test_case import LLMTestCase
from deepeval.metrics import AnswerRelevancyMetric

# Load dataset
dataset = EvaluationDataset()
dataset.pull(alias="Production Eval Dataset")

# Generate test cases
for golden in dataset.goldens:
    test_case = LLMTestCase(
        input=golden.input,
        actual_output=your_llm_app(golden.input),
        expected_output=golden.expected_output
    )
    dataset.add_test_case(test_case)

# Pytest parametrisation
@pytest.mark.parametrize("test_case", dataset.test_cases)
def test_llm_application(test_case: LLMTestCase):
    metric = AnswerRelevancyMetric(threshold=0.7)
    assert_test(test_case, [metric])
```

### Workflow 6: Multi-Turn Conversation Evaluation

```python
from deepeval.dataset import EvaluationDataset, ConversationalGolden
from deepeval.test_case import ConversationalTestCase

# Create conversational dataset
goldens = [
    ConversationalGolden(
        scenario="User frustrated about delayed shipment",
        expected_outcome="Issue resolved or escalated to human agent",
        user_description="Premium customer with order history"
    ),
    ConversationalGolden(
        scenario="User requesting product recommendation",
        expected_outcome="Relevant products suggested based on preferences",
        user_description="First-time visitor interested in electronics"
    )
]

dataset = EvaluationDataset(goldens=goldens)

# Generate conversation turns (implement your conversation simulator)
for golden in dataset.goldens:
    turns = generate_conversation_turns(golden.scenario)
    test_case = ConversationalTestCase(
        scenario=golden.scenario,
        turns=turns
    )
    dataset.add_test_case(test_case)

# Save
dataset.push(alias="Chatbot Conversations v1")
```

## CLI Commands

```bash
# Create dataset interactively
deepeval dataset create

# List available datasets
deepeval dataset list

# Pull dataset from cloud
deepeval dataset pull "Customer Support QA v2.1"

# Push dataset to cloud
deepeval dataset push --file dataset.json --alias "Customer Support QA v2.1"

# Generate synthetic dataset
deepeval dataset generate \
  --contexts contexts.txt \
  --num-goldens 50 \
  --output synthetic_dataset.json
```

## Best Practises

### Dataset Design

1. **Start Small**: Begin with 10-20 high-quality manual goldens
2. **Diverse Coverage**: Ensure goldens cover different intents, edge cases, and complexity levels
3. **Context Quality**: Provide relevant, concise context for retrieval-based systems
4. **Version Control**: Use semantic versioning for dataset aliases (v1.0, v1.1, v2.0)

### Synthetic Generation

1. **Document Chunking**: Match chunk_size to your retrieval system's chunk size
2. **Quality Threshold**: Start with 0.5, increase to 0.7+ for production datasets
3. **Evolution Balance**: Distribute evolution types based on your use case
4. **Review Generated Data**: Always manually review a sample of synthetic goldens

### Cloud Management

1. **Draft vs Finalised**: Use draft mode during dataset development
2. **Naming Conventions**: Use descriptive aliases with version numbers
3. **Regular Updates**: Update cloud datasets as your application evolves
4. **Team Collaboration**: Use Confident AI for team-based dataset management

### Evaluation Workflows

1. **Separate Datasets**: Maintain separate datasets for development, staging, and production
2. **Metadata Usage**: Leverage `additional_metadata` for filtering and analysis
3. **Test Case Generation**: Generate `actual_output` at evaluation time, not during dataset creation
4. **Metric Selection**: Choose metrics appropriate for your dataset type (single vs multi-turn)

## Common Patterns

### Pattern 1: Load or Generate

```python
from deepeval.dataset import EvaluationDataset

try:
    dataset = EvaluationDataset()
    dataset.pull(alias="My Dataset")
    print(f"Loaded {len(dataset.goldens)} goldens from cloud")
except Exception:
    # Generate if not found
    from deepeval.synthesizer import Synthesizer
    synthesizer = Synthesizer()
    goldens = synthesizer.generate_goldens_from_docs(
        document_paths=["docs.txt"]
    )
    dataset = EvaluationDataset(goldens=synthesizer.synthetic_goldens)
    dataset.push(alias="My Dataset")
```

### Pattern 2: Incremental Dataset Building

```python
dataset = EvaluationDataset()

# Load existing
dataset.pull(alias="Evolving Dataset")

# Add new goldens
new_goldens = [
    Golden(input="New query 1"),
    Golden(input="New query 2")
]
for golden in new_goldens:
    dataset.add_golden(golden)

# Save back
dataset.push(alias="Evolving Dataset", overwrite=True)
```

### Pattern 3: Dataset Splitting

```python
# Load full dataset
full_dataset = EvaluationDataset()
full_dataset.pull(alias="Full Dataset")

# Split into train/test
import random
random.shuffle(full_dataset.goldens)
split_point = int(len(full_dataset.goldens) * 0.8)

train_goldens = full_dataset.goldens[:split_point]
test_goldens = full_dataset.goldens[split_point:]

train_dataset = EvaluationDataset(goldens=train_goldens)
test_dataset = EvaluationDataset(goldens=test_goldens)

train_dataset.push(alias="Train Dataset")
test_dataset.push(alias="Test Dataset")
```

## Troubleshooting

### Issue: Context not loading as list

**Solution**: Specify delimiter when loading from CSV:
```python
dataset.add_goldens_from_csv_file(
    file_path="data.csv",
    context_col_name="context",
    context_col_delimiter=";"  # or "|", ",", etc.
)
```

### Issue: Dataset type mismatch

**Solution**: Ensure all goldens are same type before adding:
```python
# Check before adding
print(dataset._multi_turn)  # True = ConversationalGolden only, False = Golden only
```

### Issue: Synthetic generation quality too low

**Solution**: Adjust filtration threshold and evolution config:
```python
from deepeval.synthesizer.config import FiltrationConfig, EvolutionConfig

synthesizer = Synthesizer(
    filtration_config=FiltrationConfig(
        synthetic_input_quality_threshold=0.7,  # Increase from default 0.5
        max_quality_retries=5
    ),
    evolution_config=EvolutionConfig(
        num_evolutions=2  # More evolutions = more complex inputs
    )
)
```

### Issue: Cloud dataset not pulling

**Solution**: Verify authentication and finalisation status:
```bash
# Check login
deepeval login

# Verify dataset is finalised on Confident AI platform
# Or pull with finalized=False option
```

## Sources

- [Datasets | DeepEval Documentation](https://deepeval.com/docs/evaluation-datasets)
- [Introduction to Synthetic Data | DeepEval](https://deepeval.com/docs/synthesizer-introduction)
- [Generate From Goldens | DeepEval](https://deepeval.com/docs/synthesizer-generate-from-goldens)
- [Generate Goldens From Contexts | DeepEval](https://deepeval.com/docs/synthesizer-generate-from-contexts)
- [Using Datasets | DeepEval - Confident AI](https://docs.confident-ai.com/confident-ai/confident-ai-evaluation-dataset-evaluation)
- [Curating Datasets | DeepEval - Confident AI](https://docs.confident-ai.com/confident-ai/confident-ai-evaluation-dataset-management)
- [Test Cases, Goldens, and Datasets | Confident AI Docs](https://www.confident-ai.com/docs/llm-evaluation/core-concepts/test-cases-goldens-datasets)
- [Chatbot Evaluation | DeepEval](https://deepeval.com/docs/getting-started-chatbots)
- [Conversation Simulator | DeepEval](https://deepeval.com/docs/conversation-simulator)
- [GitHub - confident-ai/deepeval](https://github.com/confident-ai/deepeval)
- [Introduction | Confident AI Platform](https://documentation.confident-ai.com/dataset-editor/introduction)
- [Prompt Versioning | DeepEval](https://docs.confident-ai.com/confident-ai/confident-ai-hyperparameters-prompt-versioning)
