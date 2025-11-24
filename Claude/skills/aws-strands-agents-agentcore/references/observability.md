# Observability & Tracing

## Overview

Strands Agents provides observability through two approaches:

1. **AWS AgentCore Observability Platform** - Enterprise observability service with GenAI dashboard, automatic instrumentation, and CloudWatch integration (for agents deployed to AgentCore)
2. **General OpenTelemetry Setup** - Standard OTLP configuration for self-hosted agents or third-party platforms

---

## AWS AgentCore Observability Platform

AWS AgentCore Observability is a managed observability service that provides trace visualisations, GenAI-specific dashboards, session tracking, and automatic instrumentation for agents deployed to AgentCore Runtime or using AgentCore services.

### Key Features

- **GenAI Observability Dashboard** in CloudWatch console
- **Automatic instrumentation** for AgentCore Runtime-hosted agents
- **Session, trace, and span hierarchy** for multi-turn conversations
- **Service-provided metrics** for runtime, memory, gateway, tools, and identity
- **CloudWatch Transaction Search** for span/trace exploration
- **AWS Distro for OpenTelemetry (ADOT)** integration
- **X-Ray distributed tracing** support

### Prerequisites (One-Time Setup)

Before using AgentCore Observability, enable CloudWatch Transaction Search:

#### Option 1: CloudWatch Console

1. Open [CloudWatch Console](https://console.aws.amazon.com/cloudwatch/)
2. Navigate to **Application Signals (APM)** → **Transaction Search**
3. Choose **Enable Transaction Search**
4. Select checkbox to ingest spans as structured logs
5. Set sampling percentage (1% free tier, adjust as needed)
6. Choose **Save**

#### Option 2: AWS CLI

```bash
# 1. Configure permissions for X-Ray to write to CloudWatch Logs
aws logs put-resource-policy --policy-name AgentCoreObservability --policy-document '{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "TransactionSearchXRayAccess",
    "Effect": "Allow",
    "Principal": {"Service": "xray.amazonaws.com"},
    "Action": "logs:PutLogEvents",
    "Resource": [
      "arn:aws:logs:REGION:ACCOUNT_ID:log-group:aws/spans:*",
      "arn:aws:logs:REGION:ACCOUNT_ID:log-group:/aws/application-signals/data:*"
    ],
    "Condition": {
      "ArnLike": {"aws:SourceArn": "arn:aws:xray:REGION:ACCOUNT_ID:*"},
      "StringEquals": {"aws:SourceAccount": "ACCOUNT_ID"}
    }
  }]
}'

# 2. Configure trace destination
aws xray update-trace-segment-destination --destination CloudWatchLogs

# 3. Configure sampling percentage (optional)
aws xray update-indexing-rule --name "Default" \
  --rule '{"Probabilistic": {"DesiredSamplingPercentage": 10}}'
```

---

### AgentCore Runtime-Hosted Agents (Automatic Instrumentation)

Agents deployed to AgentCore Runtime get automatic OTEL instrumentation with minimal configuration.

#### Installation

```bash
# Install Strands with OTEL support
pip install 'strands-agents[otel]'

# Ensure ADOT is in requirements.txt
echo "aws-opentelemetry-distro" >> requirements.txt
```

#### Agent Code

```python
# strands_agent.py
from strands import Agent, tool
from strands.models import BedrockModel
from bedrock_agentcore.runtime import BedrockAgentCoreApp

app = BedrockAgentCoreApp()

@tool
def weather() -> str:
    """Get current weather."""
    return "sunny"

model = BedrockModel(model_id="anthropic.claude-sonnet-4-5-20250929-v1:0")
agent = Agent(
    model=model,
    tools=[weather],
    system_prompt="You are a helpful assistant."
)

@app.entrypoint
def handler(payload):
    user_input = payload.get("prompt")
    response = agent(user_input)
    return response.message['content'][0]['text']

if __name__ == "__main__":
    app.run()
```

#### Deploy to AgentCore Runtime

```python
from bedrock_agentcore_starter_toolkit import Runtime
from boto3.session import Session

boto_session = Session()
agentcore_runtime = Runtime()

# Deploy with automatic OTEL instrumentation
response = agentcore_runtime.configure(
    entrypoint="strands_agent.py",
    auto_create_execution_role=True,
    auto_create_ecr=True,
    requirements_file="requirements.txt",  # Must include aws-opentelemetry-distro
    region=boto_session.region_name,
    agent_name="my-agent"
)

launch_result = agentcore_runtime.launch()

# Invoke - traces automatically appear in GenAI Observability Dashboard
response = agentcore_runtime.invoke({"prompt": "What's the weather?"})
```

**View traces**: Open [GenAI Observability Dashboard](https://console.aws.amazon.com/cloudwatch/home#gen-ai-observability)

---

### Non-Runtime Hosted Agents (Self-Hosted with AgentCore Observability)

For agents running outside AgentCore Runtime (Lambda, ECS, local), configure ADOT environment variables.

#### Environment Variables

```bash
# AWS credentials
export AWS_ACCOUNT_ID=123456789012
export AWS_DEFAULT_REGION=us-east-1
export AWS_REGION=us-east-1
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret

# Create CloudWatch log group/stream first
export LOG_GROUP=/aws/agents/my-agent
export LOG_STREAM=instance-1

# AgentCore Observability configuration
export AGENT_OBSERVABILITY_ENABLED=true
export OTEL_PYTHON_DISTRO=aws_distro
export OTEL_PYTHON_CONFIGURATOR=aws_configurator
export OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
export OTEL_EXPORTER_OTLP_LOGS_HEADERS="x-aws-log-group=${LOG_GROUP},x-aws-log-stream=${LOG_STREAM},x-aws-metric-namespace=CustomAgents"
export OTEL_RESOURCE_ATTRIBUTES="service.name=my-agent"
```

#### Agent Code

```python
# agent.py
from strands import Agent
from strands_tools import http_request
from strands.models import BedrockModel

model = BedrockModel(model_id="anthropic.claude-sonnet-4-5-20250929-v1:0")

agent = Agent(
    system_prompt="You are a helpful assistant.",
    model=model,
    tools=[http_request]
)

response = agent("What's the weather in Seattle?")
print(response)
```

#### Run with Automatic Instrumentation

```bash
# Install dependencies
pip install strands-agents[otel] aws-opentelemetry-distro

# Run with ADOT auto-instrumentation
opentelemetry-instrument python agent.py
```

**View traces**: Open [GenAI Observability Dashboard](https://console.aws.amazon.com/cloudwatch/home#gen-ai-observability) and find your agent by service name.

---

### Session Tracking

Associate traces across multi-turn conversations using OpenTelemetry baggage:

```python
from opentelemetry import baggage, context
from strands import Agent

agent = Agent(...)

# Set session ID for correlation
session_id = "user-session-123"
ctx = baggage.set_baggage("session.id", session_id)

# All traces within this context include session.id
with context.attach(ctx):
    response = agent("First question")
    response = agent("Follow-up question")
```

Run with session tracking:

```bash
opentelemetry-instrument python agent_with_session.py --session-id "user-123"
```

---

### Custom Headers for Distributed Tracing

When invoking agents via HTTP, propagate trace context using standard headers:

#### X-Ray Format (AWS Native)

```python
import requests

headers = {
    "X-Amzn-Trace-Id": "Root=1-5759e988-bd862e3fe1be46a994272793;Parent=53995c3f42cd8ad8;Sampled=1"
}

response = requests.post(
    "https://runtime.bedrock-agentcore.amazonaws.com/invoke",
    json={"prompt": "Hello"},
    headers=headers
)
```

#### W3C Format (Standard)

```python
headers = {
    "traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
}
```

---

### Viewing AgentCore Observability Data

#### GenAI Observability Dashboard

1. Open [GenAI Observability Console](https://console.aws.amazon.com/cloudwatch/home#gen-ai-observability)
2. Navigate to **Bedrock AgentCore** tab
3. Explore three views:
   - **Agents View**: List all agents (runtime and non-runtime), view metrics per agent
   - **Sessions View**: Browse all sessions, filter by agent or date
   - **Traces View**: Inspect individual traces, explore trajectory and timeline

#### CloudWatch Logs

**Standard logs** (stdout/stderr):
- Location: `/aws/bedrock-agentcore/runtimes/<agent_id>-<endpoint_name>/[runtime-logs] <UUID>`
- Contains: print statements, application logs, debugging output

**OTEL structured logs** (detailed operations):
- Location: `/aws/bedrock-agentcore/runtimes/<agent_id>-<endpoint_name>/otel-rt-logs`
- Contains: Execution details, error tracking, performance data
- Automatic: Generated by ADOT instrumentation

#### Transaction Search (Spans)

1. Open [CloudWatch Console](https://console.aws.amazon.com/cloudwatch/)
2. Navigate to **Transaction Search**
3. Location: `/aws/spans/default`
4. Filter by service name, trace ID, or custom attributes
5. Select trace to view execution graph

#### CloudWatch Metrics

1. Open [CloudWatch Console](https://console.aws.amazon.com/cloudwatch/)
2. Navigate to **Metrics**
3. Browse to `bedrock-agentcore` namespace
4. Available metrics:
   - Session count, invocation count, latency (p50, p90, p99)
   - Token usage (input, output, total)
   - Error rate, throttling
   - Tool invocation metrics
   - Memory query metrics

---

### Service-Provided Observability

AgentCore automatically emits observability data for:

| Resource Type    | Metrics | Spans | Logs | Enablement Required |
|------------------|---------|-------|------|---------------------|
| **Runtime**      | ✅      | ✅    | ✅   | Automatic           |
| **Memory**       | ✅      | ✅    | ✅   | Enable on creation  |
| **Gateway**      | ✅      | ❌    | ❌   | Automatic           |
| **Built-in Tools** | ✅    | ❌    | ❌   | Automatic           |
| **Identity**     | ✅      | ❌    | ❌   | Automatic           |

To enable memory observability:

```python
from bedrock_agentcore import BedrockAgentCoreMemory

memory = BedrockAgentCoreMemory(
    memory_id="my-memory",
    enable_observability=True  # Enables spans and logs
)
```

---

### AgentCore Observability Best Practices

1. **Start simple** - Default observability captures most critical metrics automatically
2. **Use consistent naming** - Set meaningful `service.name` in `OTEL_RESOURCE_ATTRIBUTES`
3. **Configure sampling** - Start with 1% sampling (free tier), increase based on needs
4. **Filter sensitive data** - Prevent exposure of PII in trace attributes
5. **Set up CloudWatch alarms** - Alert on error rate > 2%, latency > 10s
6. **Use session IDs** - Enable session tracking for multi-turn conversations
7. **Monitor token usage** - Track costs per agent/session using CloudWatch metrics
8. **Propagate trace context** - Use X-Amzn-Trace-Id headers for distributed tracing

---

## OpenTelemetry Distributed Tracing (General)

Strands Agents provides observability built on OpenTelemetry standards for self-hosted deployments.

### Trace Hierarchy

```
Agent Span (top-level)
├─ Cycle 1 Span (reasoning loop)
│  ├─ LLM Span (model invocation)
│  └─ Tool Span (tool execution)
├─ Cycle 2 Span
│  ├─ LLM Span
│  └─ Tool Span
└─ Cycle N Span
   └─ LLM Span
```

### Span Attributes

**Agent Span** captures:
- `agent.id`: Agent identifier
- `user.message`: User input
- `assistant.response`: Final response
- `model.id`: LLM model used
- `token.usage.total`: Total tokens
- `duration`: Total time

**LLM Span** captures:
- `model.id`: Specific model
- `model.temperature`: Temperature setting
- `token.usage.prompt`: Input tokens
- `token.usage.completion`: Output tokens
- `latency.first_token`: Time to first token
- `latency.total`: Total generation time

**Tool Span** captures:
- `tool.name`: Tool invoked
- `tool.input`: Parameters
- `tool.output`: Return value
- `tool.status`: success or error
- `duration`: Execution time

---

## Setting Up OpenTelemetry

### Option 1: Environment Variables (Recommended for Production)

```bash
# Set OTLP endpoint
export OTEL_EXPORTER_OTLP_ENDPOINT="http://collector.example.com:4318"

# Optional: Add headers for authentication
export OTEL_EXPORTER_OTLP_HEADERS="x-api-key=your-key"

# Optional: Configure sampling (10% of traces)
export OTEL_TRACES_SAMPLER="traceidratio"
export OTEL_TRACES_SAMPLER_ARG="0.1"
```

```python
from strands import Agent

# Traces automatically sent to configured endpoint
agent = Agent(system_prompt="You are helpful.", tools=[...])
result = agent("Hello!")
```

---

### Option 2: StrandsTelemetry Fluent API (Recommended)

```python
from strands.observability import StrandsTelemetry

# Development: Console output
telemetry = StrandsTelemetry().setup_console_exporter()

# Production: OTLP endpoint
telemetry = StrandsTelemetry().setup_otlp_exporter()

# Both: Console + OTLP (multi-backend)
telemetry = StrandsTelemetry() \
    .setup_console_exporter() \
    .setup_otlp_exporter()

# With metrics collection
telemetry = StrandsTelemetry() \
    .setup_otlp_exporter() \
    .setup_meter(enable_otlp_exporter=True)
```

**Key Features**:
- Method chaining for fluent configuration
- `BatchSpanProcessor` for OTLP (efficient batching)
- `SimpleSpanProcessor` for console (immediate output)
- Reads `OTEL_EXPORTER_OTLP_ENDPOINT` and `OTEL_EXPORTER_OTLP_HEADERS` from environment

---

### Option 3: Code-Based Configuration

```python
from strands.observability import StrandsTelemetry
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Configure OTLP exporter
otlp_exporter = OTLPSpanExporter(
    endpoint="http://collector.example.com:4318/v1/traces",
    headers={"x-api-key": "your-key"}
)

# Set up tracer provider
tracer_provider = TracerProvider()
tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

# Initialise Strands telemetry
telemetry = StrandsTelemetry(tracer_provider=tracer_provider)
```

---

### Custom Trace Attributes

Add metadata for filtering and analysis:

```python
from strands import Agent

agent = Agent(
    system_prompt="You are helpful.",
    tools=[...],
    trace_attributes={
        "environment": "production",
        "customer_tier": "enterprise",
        "region": "us-east-1",
        "version": "2.1.4"
    }
)
```

**Use Cases**:
- Filter traces by customer tier
- Compare performance across regions
- Track issues to deployment versions
- Segment by environment

---

## Automatic Metrics Collection

Every agent invocation automatically collects:

```python
from strands import Agent

agent = Agent(tools=[calculator, websearch])
result = agent("What is 25 * 48?")

# Access metrics
metrics = result.metrics

# Token usage
print(f"Total tokens: {metrics.accumulated_usage['totalTokens']}")
print(f"Input tokens: {metrics.accumulated_usage['inputTokens']}")
print(f"Output tokens: {metrics.accumulated_usage['outputTokens']}")

# Performance
print(f"Total cycles: {metrics.cycle_count}")
print(f"Cycle durations: {metrics.cycle_durations}")

# Tool usage
for tool_name, tool_data in metrics.tool_metrics.items():
    print(f"Tool: {tool_name}")
    print(f"  Calls: {tool_data['call_count']}")
    print(f"  Success rate: {tool_data['success_count'] / tool_data['call_count']:.1%}")
    print(f"  Avg duration: {tool_data['total_duration'] / tool_data['call_count']:.2f}s")
```

---

## Custom Observability with Hooks

### Production Observability Hook

```python
from strands.hooks import HookProvider, HookRegistry
from strands.hooks.events import (
    BeforeToolCallEvent,
    AfterToolCallEvent,
    AfterInvocationEvent
)
import logging
from datetime import datetime

class ProductionObservabilityHook(HookProvider):
    """Comprehensive observability for production agents."""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.logger = logging.getLogger(f"agent.{agent_name}")
        self.tool_timings = {}

    def register_hooks(self, registry: HookRegistry, **kwargs):
        registry.add_callback(BeforeToolCallEvent, self.before_tool_call)
        registry.add_callback(AfterToolCallEvent, self.after_tool_call)
        registry.add_callback(AfterInvocationEvent, self.log_completion)

    def before_tool_call(self, event: BeforeToolCallEvent):
        tool_name = event.tool_use["name"]
        tool_id = event.tool_use["toolUseId"]

        self.tool_timings[tool_id] = time.time()

        self.logger.info(
            "Tool invoked",
            extra={
                "agent": self.agent_name,
                "tool_name": tool_name,
                "input": event.tool_use["input"],
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    def after_tool_call(self, event: AfterToolCallEvent):
        tool_name = event.tool_use["name"]
        tool_id = event.tool_use["toolUseId"]
        duration = time.time() - self.tool_timings[tool_id]

        self.logger.info(
            "Tool completed",
            extra={
                "tool_name": tool_name,
                "status": event.result.get("status"),
                "duration_ms": duration * 1000,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        # Alert on slow tools (> 5 seconds)
        if duration > 5.0:
            self.logger.warning(f"Slow tool: {tool_name} took {duration:.2f}s")

    def log_completion(self, event: AfterInvocationEvent):
        metrics = event.result.metrics.get_summary()

        self.logger.info(
            "Agent completed",
            extra={
                "total_cycles": metrics["total_cycles"],
                "total_tokens": metrics["accumulated_usage"]["totalTokens"],
                "tool_calls": sum(
                    t["execution_stats"]["call_count"]
                    for t in metrics["tool_usage"].values()
                )
            }
        )

# Usage
agent = Agent(
    agent_id="support-agent",
    hooks=[ProductionObservabilityHook("support-agent")]
)
```

---

## Third-Party Observability Platforms

### Arize Phoenix

```python
import phoenix as px
from phoenix.trace.opentelemetry import OpenInferenceTracer

# Start Phoenix server
session = px.launch_app()

# Configure Phoenix tracer
tracer = OpenInferenceTracer()

from strands.observability import StrandsTelemetry
telemetry = StrandsTelemetry(tracer_provider=tracer.tracer_provider)

# View traces at http://localhost:6006
```

---

### Langfuse

```python
from langfuse.opentelemetry import LangfuseSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

langfuse_exporter = LangfuseSpanExporter(
    public_key="your-public-key",
    secret_key="your-secret-key",
    host="https://cloud.langfuse.com"
)

tracer_provider = TracerProvider()
tracer_provider.add_span_processor(SimpleSpanProcessor(langfuse_exporter))

from strands.observability import StrandsTelemetry
telemetry = StrandsTelemetry(tracer_provider=tracer_provider)
```

---

## Production Observability Patterns

### Pattern 1: Multi-Backend Telemetry

Send to multiple backends simultaneously:

```python
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

# CloudWatch for operations
cloudwatch_exporter = OTLPSpanExporter(
    endpoint="http://adot-collector:4318/v1/traces"
)

# Phoenix for evaluation
phoenix_exporter = OTLPSpanExporter(
    endpoint="http://phoenix:6006/v1/traces"
)

tracer_provider = TracerProvider()
tracer_provider.add_span_processor(BatchSpanProcessor(cloudwatch_exporter))
tracer_provider.add_span_processor(BatchSpanProcessor(phoenix_exporter))

from strands.observability import StrandsTelemetry
telemetry = StrandsTelemetry(tracer_provider=tracer_provider)
```

---

### Pattern 2: Cost Tracking Hook

```python
from strands.hooks import HookProvider, HookRegistry
from strands.hooks.events import AfterInvocationEvent
import boto3

# Model pricing (Claude 4.5 Sonnet)
PRICING = {
    "input_token": 0.003 / 1000,
    "output_token": 0.015 / 1000,
}

class CostTrackingHook(HookProvider):
    def __init__(self, budget_limit: float = 100.0):
        self.budget_limit = budget_limit
        self.total_cost = 0.0
        self.cloudwatch = boto3.client('cloudwatch')

    def register_hooks(self, registry: HookRegistry, **kwargs):
        registry.add_callback(AfterInvocationEvent, self.track_cost)

    def track_cost(self, event: AfterInvocationEvent):
        usage = event.result.metrics.accumulated_usage

        # Calculate cost
        input_cost = usage["inputTokens"] * PRICING["input_token"]
        output_cost = usage["outputTokens"] * PRICING["output_token"]
        invocation_cost = input_cost + output_cost

        self.total_cost += invocation_cost

        # Publish to CloudWatch
        self.cloudwatch.put_metric_data(
            Namespace='AgentCosts',
            MetricData=[
                {
                    'MetricName': 'InvocationCost',
                    'Value': invocation_cost,
                    'Unit': 'None'
                },
                {
                    'MetricName': 'CumulativeCost',
                    'Value': self.total_cost,
                    'Unit': 'None'
                }
            ]
        )

        # Alert if approaching budget
        if self.total_cost > self.budget_limit * 0.9:
            logger.warning(
                f"Budget alert: ${self.total_cost:.2f} of ${self.budget_limit:.2f}"
            )

agent = Agent(hooks=[CostTrackingHook(budget_limit=100.0)])
```

---

### Pattern 3: Error Alerting Hook

```python
from strands.hooks import HookProvider, HookRegistry
from strands.hooks.events import AfterToolCallEvent
import boto3

sns = boto3.client('sns')

class ErrorAlertingHook(HookProvider):
    def __init__(self, sns_topic_arn: str, error_threshold: int = 3):
        self.sns_topic_arn = sns_topic_arn
        self.error_threshold = error_threshold
        self.error_count = 0

    def register_hooks(self, registry: HookRegistry, **kwargs):
        registry.add_callback(AfterToolCallEvent, self.check_errors)

    def check_errors(self, event: AfterToolCallEvent):
        if event.result.get("status") == "error":
            self.error_count += 1

            if self.error_count >= self.error_threshold:
                self.send_alert(event)
                self.error_count = 0

    def send_alert(self, event: AfterToolCallEvent):
        message = f"""
        Agent Error Alert

        Tool: {event.tool_use['name']}
        Error: {event.result.get('error', 'Unknown')}
        Agent: {event.agent.agent_id}
        Count: {self.error_count}
        """

        sns.publish(
            TopicArn=self.sns_topic_arn,
            Subject="Agent Error Alert",
            Message=message
        )
```

---

## Observability Checklist

### AgentCore Platform (If Using)

- [ ] CloudWatch Transaction Search enabled (one-time setup)
- [ ] ADOT (`aws-opentelemetry-distro`) installed
- [ ] Runtime-hosted: `strands-agents[otel]` in requirements.txt
- [ ] Non-runtime hosted: Environment variables configured
- [ ] GenAI Observability Dashboard accessible
- [ ] Session tracking enabled for multi-turn conversations
- [ ] Sampling percentage configured (start with 1-10%)

### Essential (All Deployments)

- [ ] OpenTelemetry tracing enabled
- [ ] Metrics collection configured
- [ ] CloudWatch dashboards created
- [ ] Error alerting configured
- [ ] Cost tracking implemented
- [ ] Logging level set (INFO for production)

### Performance

- [ ] Latency metrics tracked (p50, p90, p99)
- [ ] Token usage monitored
- [ ] Tool execution time measured
- [ ] Slow query alerts (> 10s)

### Quality

- [ ] Tool success rate monitored
- [ ] Error rate alerts (> 2%)
- [ ] Conversation length tracking

### Cost Control

- [ ] Token usage per user/session tracked
- [ ] Budget alerts configured
- [ ] Cost attribution by team/project
- [ ] Model cost comparison

### Security

- [ ] Sensitive data redacted from traces
- [ ] Access logs enabled
- [ ] Audit trail for tool invocations
- [ ] Retention policies configured
