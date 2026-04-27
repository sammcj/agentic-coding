# DeepEval LLM Provider Support Implementation Guide

## Overview

DeepEval is a flexible LLM evaluation framework that supports ANY LLM provider through multiple configuration approaches. The framework allows you to use various providers including OpenAI, Azure OpenAI, Anthropic Claude, Google Gemini, AWS Bedrock, Ollama (local models), and more through direct integrations or the LiteLLM proxy.

## Supported LLM Providers

DeepEval provides first-class support for the following providers:

### Cloud Providers
- **OpenAI**: GPT-3.5, GPT-4, GPT-4.1, GPT-5, o1, o3-mini, o4-mini models
- **Azure OpenAI**: All OpenAI models through Azure endpoints
- **Anthropic**: Claude 3, Claude 3.5, Claude 3.7, Claude 4 (Opus, Sonnet, Haiku)
- **Google**: Gemini models via Vertex AI or Google AI
- **AWS Bedrock**: Claude, Titan, and complete Bedrock model lineup
- **DeepSeek**: DeepSeek models
- **Grok**: xAI Grok models
- **Kimi**: Moonshot AI models

### Local/Self-Hosted
- **Ollama**: Run any Ollama-supported model locally
- **LocalModel**: Custom local model implementations
- **LiteLLM**: Proxy to 100+ LLM providers with unified interface

### Key Characteristics
- DeepEval treats the evaluation LLM as a configurable component
- Default evaluation model: `gpt-4.1`
- Each metric instance can use a different LLM provider
- All LLM-as-Judge metrics support custom model configuration

---

## Configuration Methods

DeepEval offers two primary configuration approaches:

### 1. CLI Configuration (Global Default)

Sets the default LLM provider for all metrics unless overridden in code.

#### OpenAI
```bash
deepeval set-openai --model=gpt-4.1
```

#### Azure OpenAI
```bash
deepeval set-azure-openai \
    --openai-endpoint=https://example-resource.azure.openai.com/ \
    --openai-api-key=<api_key> \
    --openai-model-name=gpt-4.1 \
    --deployment-name=my-deployment \
    --openai-api-version=2025-01-01-preview
```

To switch providers:
```bash
deepeval unset-azure-openai
```

#### Ollama
```bash
deepeval set-ollama deepseek-r1:1.5b --base-url="http://localhost:11434"
```

#### Gemini (Vertex AI)
```bash
deepeval set-gemini \
    --model-name=gemini-2.0-flash-001 \
    --project-id=<project_id> \
    --location=us-central1
```

Optional: Persist settings with `--save` flag.

### 2. Python Configuration (Per-Metric)

Specify custom LLM models directly in your code for fine-grained control.

---

## Provider-Specific Configuration

### OpenAI

**Default Model**: `gpt-4.1`

**Installation**:
```bash
pip install deepeval
```

**Environment Setup**:
```bash
export OPENAI_API_KEY="sk-..."
```

**Configuration**:
```python
from deepeval.models import GPTModel
from deepeval.metrics import AnswerRelevancyMetric

# Basic configuration
model = GPTModel(model="gpt-4.1")

# Advanced configuration
model = GPTModel(
    model="gpt-4o",
    temperature=0,
    cost_per_input_token=0.000002,
    cost_per_output_token=0.000008,
    generation_kwargs={
        "max_tokens": 1000,
        "top_p": 0.95
    }
)

# Use with metrics
metric = AnswerRelevancyMetric(model=model, threshold=0.7)
```

**Supported Models**:
- Latest: `gpt-5`, `gpt-5-mini`, `gpt-5-nano`
- Reasoning: `o1`, `o1-pro`, `o1-mini`, `o3-mini`, `o4-mini`
- Standard: `gpt-4.1`, `gpt-4.1-mini`, `gpt-4.1-nano`, `gpt-4o`, `gpt-4o-mini`
- Legacy: `gpt-3.5-turbo`, `gpt-4-turbo`

**Pricing** (per 1M tokens):
| Model | Input Cost | Output Cost |
|-------|-----------|-------------|
| gpt-4.1 | $2.00 | $8.00 |
| gpt-4o | $2.50 | $10.00 |
| gpt-4o-mini | $0.15 | $0.60 |
| o3-mini | $1.10 | $4.40 |
| gpt-5 | $1.25 | $10.00 |

**Special Considerations**:
- Reasoning models (`o1`, `o3-mini`, `o4-mini`, `gpt-5`) require `temperature=1` (auto-adjusted)
- Structured output support for newer models (`gpt-4o`, `gpt-4.1`, `o1`, `gpt-5`)
- JSON mode for older models (`gpt-3.5-turbo`, `gpt-4-turbo`)
- Log probabilities unsupported on reasoning models

---

### Azure OpenAI

**Configuration**:
```python
from deepeval.models import AzureOpenAIModel

model = AzureOpenAIModel(
    model_name="gpt-4.1",
    deployment_name="my-gpt4-deployment",
    azure_openai_api_key="<your-key>",
    openai_api_version="2025-01-01-preview",
    azure_endpoint="https://example-resource.azure.openai.com/",
    temperature=0,
    generation_kwargs={"max_tokens": 1500}
)
```

**Required Parameters**:
- `model_name`: Azure model identifier
- `deployment_name`: Your deployment name
- `azure_openai_api_key`: Authentication credential
- `openai_api_version`: API version (e.g., "2025-01-01-preview")
- `azure_endpoint`: Resource endpoint URL

**Optional Parameters**:
- `temperature`: Defaults to 0
- `generation_kwargs`: Additional model-specific settings

**Supported Models**: All OpenAI models available through Azure deployments

**Considerations**:
- Ensure your Azure deployment matches the model version
- API versions may affect available features
- Use Azure Key Vault for production credential management

---

### Anthropic Claude

**Installation**:
```bash
pip install deepeval anthropic
```

**Environment Setup**:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

**Configuration**:
```python
from deepeval.models import AnthropicModel

model = AnthropicModel(
    model="claude-3-7-sonnet-latest",
    temperature=0,
    generation_kwargs={"max_tokens": 1024}
)
```

**Supported Models**:
- `claude-opus-4-20250514` - Most capable
- `claude-sonnet-4-20250514` - Balanced performance
- `claude-3-7-sonnet-latest` - Latest Claude 3.7
- `claude-3-5-sonnet-latest` - Claude 3.5 Sonnet
- `claude-3-5-haiku-latest` - Fast and efficient
- `claude-3-opus-latest` - Claude 3 Opus
- `claude-instant-1.2` - Legacy fast model

**Pricing** (per 1M tokens):
| Model | Input Cost | Output Cost |
|-------|-----------|-------------|
| claude-opus-4 | $15.00 | $75.00 |
| claude-sonnet-4 | $3.00 | $15.00 |
| claude-3-7-sonnet | $3.00 | $15.00 |
| claude-3-5-haiku | $0.80 | $4.00 |

**Integration Methods**:

1. **Standalone Evaluation**:
```python
from deepeval.anthropic import Anthropic
from deepeval.metrics import AnswerRelevancyMetric

client = Anthropic()

with trace(metrics=[AnswerRelevancyMetric(model=model)]):
    response = client.messages.create(
        model="claude-sonnet-4-5",
        messages=[{"role": "user", "content": "What is DeepEval?"}]
    )
```

2. **Component-Level Evaluation**:
```python
from deepeval.tracing import observe
from deepeval.anthropic import Anthropic

@observe(metrics=[AnswerRelevancyMetric()])
def llm_component():
    client = Anthropic()
    response = client.messages.create(
        model="claude-3-7-sonnet-latest",
        messages=[{"role": "user", "content": "Explain RAG"}]
    )
    return response
```

**Considerations**:
- DeepEval's Anthropic integration provides automatic tracing
- Supports both `deepeval.anthropic.Anthropic` and `deepeval.anthropic.AsyncAnthropic`
- Can evaluate Claude responses in production with Confident AI integration

---

### Google Gemini (Vertex AI)

**Installation**:
```bash
pip install deepeval google-cloud-aiplatform
```

**Authentication**:
```bash
gcloud auth application-default login
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
```

**Configuration**:
```python
from deepeval.models import GeminiModel

model = GeminiModel(
    model_name="gemini-2.0-flash-001",
    project="your-project-id",
    location="us-central1",
    temperature=0
)
```

**Required Parameters**:
- `model_name`: Gemini model identifier
- `project`: Google Cloud project ID
- `location`: Google Cloud location

**Supported Models**:
- `gemini-2.0-flash-001` - Latest fast model
- `gemini-1.5-pro` - High capability
- `gemini-1.5-flash` - Balanced performance

**Usage Example**:
```python
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams

eval_model = GeminiModel(
    model_name="gemini-1.5-pro",
    project="genai-project",
    location="us-central1"
)

metric = GEval(
    name="Correctness",
    model=eval_model,
    criteria="Determine if the actual output is correct",
    evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
    threshold=0.7
)
```

**Considerations**:
- Requires Google Cloud project with Vertex AI API enabled
- Safety settings may block some evaluation outputs - configure appropriately
- DeepEval supports both Vertex AI and Google AI SDK
- Recommended to use `HarmBlockThreshold.BLOCK_NONE` for evaluation contexts

---

### AWS Bedrock

**Installation**:
```bash
pip install deepeval boto3
```

**Authentication**:
```bash
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_REGION="us-east-1"
```

**Configuration**:
```python
from deepeval.models import AmazonBedrockModel

model = AmazonBedrockModel(
    model_id="anthropic.claude-3-opus-20240229-v1:0",
    region_name="us-east-1",
    aws_access_key_id="<optional>",
    aws_secret_access_key="<optional>",
    input_token_cost=0.000015,  # Optional
    output_token_cost=0.000075,  # Optional
    generation_kwargs={
        "temperature": 0,
        "topP": 0.9
    }
)
```

**Required Parameters**:
- `model_id`: Bedrock model identifier
- `region_name`: AWS region hosting your Bedrock endpoint

**Optional Parameters**:
- `aws_access_key_id` / `aws_secret_access_key`: Falls back to AWS credentials chain if omitted
- `input_token_cost` / `output_token_cost`: Per-token costs in USD (defaults to 0)
- `generation_kwargs`: Model-specific parameters

**Supported Model IDs**:
- Anthropic Claude: `anthropic.claude-3-opus-20240229-v1:0`, `anthropic.claude-3-sonnet-20240229-v1:0`, `anthropic.claude-3-haiku-20240307-v1:0`
- Amazon Titan: `amazon.titan-text-express-v1`, `amazon.titan-text-lite-v1`
- Other Bedrock models as available in your region

**Usage Example**:
```python
from deepeval.metrics import AnswerRelevancyMetric

bedrock_model = AmazonBedrockModel(
    model_id="anthropic.claude-3-sonnet-20240229-v1:0",
    region_name="us-west-2"
)

metric = AnswerRelevancyMetric(model=bedrock_model, threshold=0.8)
```

**Considerations**:
- Requires AWS account with Bedrock model access
- Model availability varies by region
- Bedrock provides access to multiple foundation model providers
- IAM permissions required: `bedrock:InvokeModel`

---

### Ollama (Local Models)

**Installation**:
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull deepseek-r1:1.5b

# Install DeepEval
pip install deepeval
```

**Configuration**:
```python
from deepeval.models import OllamaModel

model = OllamaModel(
    model="deepseek-r1:1.5b",
    base_url="http://localhost:11434",
    temperature=0,
    generation_kwargs={"num_ctx": 4096}
)
```

**Parameters**:
- `model`: Ollama model name (required)
- `base_url`: Ollama server URL (defaults to `http://localhost:11434`)
- `temperature`: Sampling temperature (defaults to 0)
- `generation_kwargs`: Additional Ollama parameters

**Supported Models**: Any model available through Ollama including:
- `llama3.2`, `llama3.1`, `llama2`
- `mistral`, `mixtral`
- `deepseek-r1`, `deepseek-coder`
- `qwen2.5`, `gemma2`
- `phi3`, `phi4`

**Usage Example**:
```python
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCaseParams

local_model = OllamaModel(model="llama3.1:8b")

metric = GEval(
    name="Relevance",
    model=local_model,
    criteria="Assess answer relevance to the question",
    evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
    threshold=0.5
)
```

**Considerations**:
- **Zero API costs** - runs entirely locally
- **Data privacy** - no data sent to external services
- **Performance** - dependent on local hardware (GPU recommended)
- **Model capability** - local models may not match GPT-4/Claude quality
- **JSON formatting** - some local models struggle with structured outputs
- **Evaluation reliability** - DeepEval cannot guarantee evaluation quality with custom models
- **Resource requirements** - larger models (70B+) require significant RAM/VRAM

---

### LiteLLM Proxy (100+ Providers)

LiteLLM provides a unified interface to route requests across 100+ LLM providers with a single configuration.

**Installation**:
```bash
pip install deepeval litellm
```

**Configuration**:
```python
from deepeval.models import LiteLLMModel

# OpenAI via LiteLLM
model = LiteLLMModel(
    model="gpt-4o",
    api_key="sk-...",
    temperature=0
)

# Anthropic via LiteLLM
model = LiteLLMModel(
    model="claude-3-7-sonnet-latest",
    api_key="sk-ant-...",
    temperature=0
)

# Local Ollama via LiteLLM
model = LiteLLMModel(
    model="ollama/llama3.1",
    api_base="http://localhost:11434",
    temperature=0
)
```

**Supported Providers** (via LiteLLM):
- OpenAI, Azure OpenAI
- Anthropic, AWS Bedrock
- Google Vertex AI, Google AI
- Mistral, Groq, Together AI
- Fireworks AI, Replicate
- Ollama, Hugging Face
- And 90+ more

**Environment Variables**:
```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export MISTRAL_API_KEY="..."
```

**Usage Example**:
```python
from deepeval.metrics import AnswerRelevancyMetric

# Multiple providers in same evaluation
openai_model = LiteLLMModel(model="gpt-4o")
claude_model = LiteLLMModel(model="claude-3-sonnet-20240229")

metric1 = AnswerRelevancyMetric(model=openai_model)
metric2 = AnswerRelevancyMetric(model=claude_model)
```

**Considerations**:
- Seamless provider switching with consistent interface
- Load balancing and failover capabilities
- Cost tracking across providers
- Single integration point for multiple LLMs
- Useful for A/B testing different providers

---

## Custom LLM Implementation

For providers not directly supported, implement the `DeepEvalBaseLLM` interface.

**Implementation**:
```python
from deepeval.models import DeepEvalBaseLLM
from pydantic import BaseModel
from typing import Optional, Tuple, Union, Dict

class CustomLLM(DeepEvalBaseLLM):
    def __init__(self, model_name: str, api_key: str, **kwargs):
        self.api_key = api_key
        self.kwargs = kwargs
        super().__init__(model_name)

    def load_model(self):
        # Initialise your model client
        return self.model

    def generate(self, prompt: str, schema: Optional[BaseModel] = None) -> Tuple[Union[str, Dict], float]:
        # Synchronous generation
        # Return (response, cost)
        response = "Generated response"
        cost = 0.001
        return response, cost

    async def a_generate(self, prompt: str, schema: Optional[BaseModel] = None) -> Tuple[Union[str, Dict], float]:
        # Asynchronous generation
        return self.generate(prompt, schema)

    def get_model_name(self) -> str:
        return self.model_name
```

**Required Methods**:
- `load_model()`: Initialise and return model client
- `generate(prompt, schema)`: Synchronous generation with optional Pydantic schema
- `a_generate(prompt, schema)`: Asynchronous generation
- `get_model_name()`: Return model identifier

**Optional Schema Support**:

For models that struggle with JSON output, accept Pydantic schemas:

```python
def generate(self, prompt: str, schema: BaseModel) -> BaseModel:
    # Use instructor or lm-format-enforcer for JSON confinement
    from instructor import from_openai

    client = from_openai(self.client)
    response = client.chat.completions.create(
        model=self.model_name,
        messages=[{"role": "user", "content": prompt}],
        response_model=schema
    )
    return response, 0.0
```

**JSON Confinement Libraries**:

1. **lm-format-enforcer**: For transformer-based models
```bash
pip install lm-format-enforcer
```

2. **Instructor**: Language-agnostic, works with most providers
```bash
pip install instructor
```

**Usage**:
```python
custom_model = CustomLLM(model_name="my-model", api_key="...")
metric = AnswerRelevancyMetric(model=custom_model)
```

---

## Cost Considerations

### OpenAI Cost Analysis

Based on a 50 Q&A evaluation dataset:
- **LLM Calls**: 290 total
- **Tokens Generated**: 425,086
- **Cost**: $1.13 per evaluation run (using GPT-4o)

**Cost Extrapolation**:
- 10 evaluation runs: ~$11.30
- 100 runs (typical project): ~$113
- 1,000 runs (large-scale): ~$1,130

### Provider Cost Comparison

**High-End Models** (per 1M tokens input/output):
| Provider | Model | Input | Output | Total* |
|----------|-------|-------|--------|--------|
| OpenAI | gpt-4o | $2.50 | $10.00 | $12.50 |
| Anthropic | claude-opus-4 | $15.00 | $75.00 | $90.00 |
| OpenAI | o1 | $15.00 | $60.00 | $75.00 |

**Mid-Tier Models**:
| Provider | Model | Input | Output | Total* |
|----------|-------|-------|--------|--------|
| OpenAI | gpt-4.1 | $2.00 | $8.00 | $10.00 |
| Anthropic | claude-sonnet-4 | $3.00 | $15.00 | $18.00 |
| OpenAI | gpt-4-turbo | $10.00 | $30.00 | $40.00 |

**Budget Models**:
| Provider | Model | Input | Output | Total* |
|----------|-------|-------|--------|--------|
| OpenAI | gpt-4o-mini | $0.15 | $0.60 | $0.75 |
| OpenAI | gpt-4.1-nano | $0.10 | $0.40 | $0.50 |
| Anthropic | claude-3-5-haiku | $0.80 | $4.00 | $4.80 |
| OpenAI | o3-mini | $1.10 | $4.40 | $5.50 |

*Total = Input + Output cost estimate for 1M total tokens

### Local Model Economics

**Initial Claims**: "Locally hosted models are cheaper"

**Reality**: Total cost of ownership (TCO) considerations:

1. **Hardware Costs**:
   - GPU: $1,500-$5,000+ for capable inference
   - RAM: 64GB+ recommended for larger models
   - Storage: Fast NVMe for model loading

2. **Operational Costs**:
   - Electricity: ~$0.10-0.30/hour for GPU operation
   - Maintenance: Time and expertise
   - Model updates: Ongoing

3. **Performance Trade-offs**:
   - Inference speed: Typically slower than cloud APIs
   - Model quality: May not match GPT-4/Claude reasoning
   - JSON reliability: Local models often struggle with structured output

**Break-Even Analysis**:

Assuming $2,000 GPU + $0.20/hour electricity:
- Cloud API costs: $0.01/evaluation (GPT-4o-mini)
- Local costs: $2,000 upfront + $0.20/hour

Break-even: ~200,000 evaluations (or 20,000 hours of operation)

**When Local Models Make Sense**:
- Very high evaluation volumes (10,000+ per month)
- Strict data privacy requirements
- Long-term continuous evaluation
- Experimentation and model fine-tuning

**When Cloud Models Make Sense**:
- Getting started (<1,000 evals/month)
- Need highest quality evaluations
- Variable evaluation workloads
- Limited GPU infrastructure

### Cost Optimisation Strategies

1. **Model Selection**:
   - Use `gpt-4o-mini` or `gpt-4.1-nano` for simple metrics
   - Reserve `gpt-4.1` or `claude-sonnet-4` for complex reasoning
   - Consider `o3-mini` for balanced reasoning tasks

2. **Metric Optimisation**:
   - Not all metrics require powerful models
   - Statistical metrics (BLEU, ROUGE) have zero LLM cost
   - NLP-based metrics (toxicity, bias) run locally

3. **Batch Processing**:
   - Evaluate in batches to reduce overhead
   - Use DeepEval's parallel execution
   - Cache evaluation results

4. **Sampling Strategies**:
   - Evaluate representative subset during development
   - Full evaluation in CI/CD and production monitoring

---

## Provider Limitations and Considerations

### OpenAI

**Limitations**:
- API rate limits vary by tier
- Reasoning models (`o1`, `gpt-5`) don't support log probabilities
- Temperature must be 1 for reasoning models
- Structured output limited to newer models

**Best For**:
- General-purpose evaluation
- Structured output requirements
- Wide model selection

### Azure OpenAI

**Limitations**:
- Model availability varies by region
- Deployment configuration required
- API versions change feature availability
- Quota management needed

**Best For**:
- Enterprise compliance requirements
- Existing Azure infrastructure
- Data residency requirements

### Anthropic Claude

**Limitations**:
- Max output tokens: 1024 (configurable)
- No native structured output (requires JSON parsing)
- Pricing higher than GPT-4o

**Best For**:
- Long context evaluation
- Nuanced reasoning tasks
- Ethical/safety-focused evaluation

### Google Gemini

**Limitations**:
- Requires Google Cloud project setup
- Safety filters may block evaluation outputs
- API surface differs from OpenAI

**Best For**:
- Google Cloud ecosystem
- Multimodal evaluation capabilities
- Cost-effective with Gemini Flash

### AWS Bedrock

**Limitations**:
- Model availability by region
- IAM permissions setup required
- Variable pricing across foundation models

**Best For**:
- AWS ecosystem integration
- Access to multiple foundation models
- Enterprise AWS customers

### Ollama (Local)

**Limitations**:
- Hardware requirements significant for large models
- Evaluation quality varies widely by model
- JSON output reliability issues
- No cost tracking (returns $0)
- Slower inference than cloud APIs

**Best For**:
- Data privacy requirements
- High-volume evaluation (cost savings)
- Experimentation with open models
- Offline/air-gapped environments

### LiteLLM

**Limitations**:
- Requires understanding of underlying provider limits
- Adds small latency overhead
- Debugging can be complex with proxy layer

**Best For**:
- Multi-provider evaluation
- Easy provider switching
- Load balancing needs
- Cost tracking across providers

---

## Retry and Error Handling

DeepEval implements automatic retry logic for transient failures.

### Default Retry Behaviour

**Retried Errors**:
- Network/timeout errors
- 5xx server errors
- 429 rate limits (unless marked non-retryable)

**Non-Retried Errors**:
- 4xx client errors (except 429)
- `insufficient_quota` errors from OpenAI
- Authentication failures

**Retry Configuration**:
- Default attempts: 2 (1 initial + 1 retry)
- Backoff: Exponential with jitter
- Initial delay: 1s
- Base: 2
- Jitter: 2s
- Cap: 5s

### Environment Flags

Configure retry behaviour via environment variables:

```bash
# Timeout per attempt (seconds)
export DEEPEVAL_PER_ATTEMPT_TIMEOUT_SECONDS=30

# Disable retries for specific providers
export DEEPEVAL_SDK_RETRY_PROVIDERS=""

# Enable SDK retries (default: use DeepEval retries)
export DEEPEVAL_SDK_RETRY_PROVIDERS="openai,anthropic"
```

### Handling Evaluation Timeouts

If evaluations appear "stuck":

1. Check rate limits and quotas
2. Verify API credentials
3. Increase timeout:
```bash
export DEEPEVAL_PER_ATTEMPT_TIMEOUT_SECONDS=60
```
4. Review provider status pages

---

## Configuration Best Practises

### Environment Variables

DeepEval auto-loads `.env.local` then `.env` from the current working directory.

**Precedence**: Process env → `.env.local` → `.env`

**Setup**:
```bash
cp .env.example .env.local
# Edit .env.local with your API keys
```

**.env.local Example**:
```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
DEEPEVAL_PER_ATTEMPT_TIMEOUT_SECONDS=30
```

**Opt-out**:
```bash
export DEEPEVAL_DISABLE_DOTENV=1
```

## Selection Strategy

**Development Phase**:
- Use cheaper models (`gpt-4o-mini`, `claude-haiku`) for rapid iteration
- Experiment with local Ollama models
- Focus on metric selection and threshold tuning

**Testing/CI Phase**:
- Mid-tier models (`gpt-4.1`, `claude-sonnet-4`) for balanced quality/cost
- Consistent model across test runs
- Cache evaluation results where possible

**Production Monitoring**:
- High-quality models for critical metrics
- Budget models for high-volume metrics
- Consider latency requirements

### Per-Metric Configuration

Different metrics may benefit from different models:

```python
from deepeval.models import GPTModel, AnthropicModel
from deepeval.metrics import AnswerRelevancyMetric, GEval

# Fast, cheap model for simple metrics
fast_model = GPTModel(model="gpt-4o-mini")
relevancy_metric = AnswerRelevancyMetric(model=fast_model)

# Powerful model for complex reasoning
reasoning_model = AnthropicModel(model="claude-opus-4-20250514")
correctness_metric = GEval(
    name="Correctness",
    model=reasoning_model,
    criteria="Evaluate technical accuracy and completeness",
    evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT]
)
```

### Security Considerations

1. **Never commit API keys** to version control
2. **Use environment variables** for credentials
3. **Rotate keys regularly** per provider best practises
4. **Implement least-privilege IAM** for cloud providers
5. **Monitor API usage** for anomalies
6. **Use secret management** in production (AWS Secrets Manager, HashiCorp Vault, etc.)

---

## Troubleshooting

### Common Issues

**Issue**: "Evaluation getting stuck"
- **Cause**: Rate limits, insufficient quota, or network issues
- **Solution**:
  - Check provider rate limits
  - Verify API key has sufficient quota
  - Increase timeout: `export DEEPEVAL_PER_ATTEMPT_TIMEOUT_SECONDS=60`
  - Review retry configuration

**Issue**: "Invalid JSON output from local model"
- **Cause**: Local models struggle with structured output
- **Solution**:
  - Use JSON confinement libraries (instructor, lm-format-enforcer)
  - Implement schema validation in custom model
  - Consider using more capable local model
  - Fall back to cloud provider for JSON-heavy metrics

**Issue**: "Azure OpenAI authentication failed"
- **Cause**: Incorrect endpoint, API key, or API version
- **Solution**:
  - Verify all five required parameters
  - Check deployment name matches Azure portal
  - Ensure API version is supported
  - Test credentials with Azure CLI first

**Issue**: "Gemini safety filter blocking evaluation"
- **Cause**: Google's safety filters triggering on evaluation prompts
- **Solution**:
  - Configure `HarmBlockThreshold.BLOCK_NONE` for evaluation contexts
  - Review and adjust evaluation prompts
  - Use different provider for sensitive content evaluation

**Issue**: "High costs with frequent evaluations"
- **Cause**: Using expensive models for all metrics
- **Solution**:
  - Implement tiered model strategy
  - Use statistical metrics where possible
  - Sample evaluations during development
  - Consider local models for high-volume scenarios

---

## Example: Multi-Provider Evaluation

```python
from deepeval import evaluate
from deepeval.models import GPTModel, AnthropicModel, OllamaModel
from deepeval.metrics import AnswerRelevancyMetric, GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from deepeval.dataset import EvaluationDataset, Golden

# Configure multiple providers
openai_model = GPTModel(model="gpt-4o")
claude_model = AnthropicModel(model="claude-3-7-sonnet-latest")
local_model = OllamaModel(model="llama3.1:8b")

# Create metrics with different models
relevancy = AnswerRelevancyMetric(
    model=local_model,  # Fast local model for simple metric
    threshold=0.7
)

correctness = GEval(
    name="Correctness",
    model=claude_model,  # Claude for nuanced reasoning
    criteria="Evaluate technical accuracy",
    evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
    threshold=0.8
)

consistency = GEval(
    name="Consistency",
    model=openai_model,  # GPT-4o for balanced performance
    criteria="Evaluate response consistency",
    evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
    threshold=0.7
)

# Create test cases
dataset = EvaluationDataset(
    goldens=[
        Golden(
            input="What is RAG?",
            expected_output="Retrieval-Augmented Generation (RAG) is a technique..."
        )
    ]
)

# Run evaluation
for golden in dataset.goldens:
    test_case = LLMTestCase(
        input=golden.input,
        actual_output=your_llm_app(golden.input),
        expected_output=golden.expected_output
    )
    dataset.add_test_case(test_case)

# Evaluate with all metrics
evaluate(dataset, [relevancy, correctness, consistency])
```

---

## References

### Official Documentation
- [Using Custom LLMs | DeepEval](https://deepeval.com/guides/guides-using-custom-llms)
- [Azure OpenAI | DeepEval](https://deepeval.com/integrations/models/azure-openai)
- [Anthropic | DeepEval](https://deepeval.com/integrations/frameworks/anthropic)
- [Ollama | DeepEval](https://deepeval.com/integrations/models/ollama)
- [Amazon Bedrock | DeepEval](https://deepeval.com/integrations/models/amazon-bedrock)
- [Vertex AI | DeepEval](https://www.deepeval.com/integrations/models/vertex-ai)
- [Introduction to LLM Metrics | DeepEval](https://deepeval.com/docs/metrics-introduction)

### Articles and Guides
- [A Guide on Effective LLM Assessment with DeepEval](https://www.analyticsvidhya.com/blog/2025/01/llm-assessment-with-deepeval/)
- [Elevating LLM Evaluation with DeepEval with Native Amazon Bedrock Support](https://dev.to/makawtharani/elevating-llm-evaluation-with-deepeval-with-native-aws-bedrock-support-155h)
- [How to use DeepEval with custom LLM like Bedrock](https://medium.com/@pedroazevedo6/how-to-use-deepeval-with-custom-llm-like-bedrock-c8c0c583abeb)
- [Evaluate 100+ LLMs with DeepEval + LiteLLM](https://ps2programming.medium.com/evaluate-100-llms-with-deepeval-litellm-c20277c9184c)
- [Leveraging Open Source Models for AI Evaluation with DeepEval](https://christophergs.com/blog/ai-engineering-evaluation-with-deepeval-and-open-source-models)
- [DeepEval adds native support for Gemini as an LLM Judge](https://medium.com/google-cloud/deepeval-adds-native-support-for-gemini-as-an-llm-judge-e0d7f4bf888d)

### Community and Support
- [DeepEval GitHub Repository](https://github.com/confident-ai/deepeval)
- [DeepEval Discord Community](https://discord.gg/3SEyvpgu2f)
- [Confident AI Platform](https://confident-ai.com)

---

**Document Version**: 1.0
**Last Updated**: 2025-11-25
**DeepEval Version**: Latest (as of January 2025)
