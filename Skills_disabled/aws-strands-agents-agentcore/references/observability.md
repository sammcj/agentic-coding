# Observability & Tracing

## Overview

Two observability approaches:

1. **AWS AgentCore Observability** - Managed service with GenAI dashboard, automatic instrumentation (for agents using AgentCore services)
2. **OpenTelemetry** - Standard OTLP configuration for self-hosted agents or third-party platforms

For quality assessment, see **[evaluations.md](evaluations.md)**.

---

## AWS AgentCore Observability

### One-Time Setup: Enable Transaction Search

**Via Console**: CloudWatch → Application Signals → Transaction Search → Enable (select 1-10% sampling)

**Via CLI**:
```bash
# Configure X-Ray → CloudWatch permissions
aws logs put-resource-policy --policy-name AgentCoreObs --policy-document '{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "xray.amazonaws.com"},
    "Action": "logs:PutLogEvents",
    "Resource": ["arn:aws:logs:REGION:ACCOUNT:log-group:aws/spans:*"]
  }]
}'

# Enable CloudWatch destination
aws xray update-trace-segment-destination --destination CloudWatchLogs
```

---

### Runtime-Hosted Agents (Automatic)

**Installation**:
```bash
pip install 'strands-agents[otel]'
echo "aws-opentelemetry-distro" >> requirements.txt
```

**Agent code** (automatic instrumentation):
```python
from strands import Agent
from strands.models import BedrockModel
from bedrock_agentcore.runtime import BedrockAgentCoreApp

app = BedrockAgentCoreApp()
agent = Agent(
    model=BedrockModel(model_id="anthropic.claude-sonnet-4-5-20250929-v1:0"),
    tools=[weather_tool],
    system_prompt="You are helpful."
)

@app.entrypoint
def handler(payload):
    return agent(payload["prompt"]).message['content'][0]['text']
```

**Deploy**:
```python
from bedrock_agentcore_starter_toolkit import Runtime
runtime = Runtime()
runtime.configure(entrypoint="agent.py", requirements_file="requirements.txt")
runtime.launch()
```

Traces appear automatically in [GenAI Observability Dashboard](https://console.aws.amazon.com/cloudwatch/home#gen-ai-observability).

---

### Non-Runtime Hosted (Self-Hosted with AgentCore Observability)

**Environment variables**:
```bash
export AGENT_OBSERVABILITY_ENABLED=true
export OTEL_PYTHON_DISTRO=aws_distro
export OTEL_PYTHON_CONFIGURATOR=aws_configurator
export OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
export OTEL_RESOURCE_ATTRIBUTES="service.name=my-agent"
```

**Run**:
```bash
pip install strands-agents[otel] aws-opentelemetry-distro
opentelemetry-instrument python agent.py
```

---

### Session Tracking

Associate traces across multi-turn conversations:

```python
from opentelemetry import baggage, context

session_id = "user-123"
ctx = baggage.set_baggage("session.id", session_id)

with context.attach(ctx):
    response = agent("First question")
    response = agent("Follow-up question")
```

---

### Viewing Data

**GenAI Dashboard**: CloudWatch → GenAI Observability → Bedrock AgentCore tab
- Agents View: All agents, metrics per agent
- Sessions View: Browse sessions, filter by agent/date
- Traces View: Inspect trajectories and timelines

**CloudWatch Logs**:
- Runtime logs: `/aws/bedrock-agentcore/runtimes/<agent_id>-<endpoint>/[runtime-logs]`
- OTEL logs: `/aws/bedrock-agentcore/runtimes/<agent_id>-<endpoint>/otel-rt-logs`

**Transaction Search**: CloudWatch → Transaction Search → `/aws/spans/default`

---

## OpenTelemetry (General)

### Setup Options

**Recommended: StrandsTelemetry Fluent API**

```python
from strands.observability import StrandsTelemetry

# Development: Console output
telemetry = StrandsTelemetry().setup_console_exporter()

# Production: OTLP endpoint (reads OTEL_EXPORTER_OTLP_ENDPOINT from env)
telemetry = StrandsTelemetry().setup_otlp_exporter()

# Both
telemetry = StrandsTelemetry() \
    .setup_console_exporter() \
    .setup_otlp_exporter() \
    .setup_meter(enable_otlp_exporter=True)
```

**Environment Variables**:
```bash
export OTEL_EXPORTER_OTLP_ENDPOINT="http://collector:4318"
export OTEL_EXPORTER_OTLP_HEADERS="x-api-key=your-key"
```

---

### Custom Attributes

```python
agent = Agent(
    system_prompt="...",
    tools=[...],
    trace_attributes={
        "environment": "production",
        "customer_tier": "enterprise",
        "region": "us-east-1"
    }
)
```

---

### Automatic Metrics

```python
result = agent("Query")
metrics = result.metrics

# Token usage
print(metrics.accumulated_usage['totalTokens'])
print(metrics.accumulated_usage['inputTokens'])
print(metrics.accumulated_usage['outputTokens'])

# Performance
print(metrics.cycle_count)
print(metrics.cycle_durations)

# Tool usage
for tool_name, data in metrics.tool_metrics.items():
    print(f"{tool_name}: {data['call_count']} calls")
    print(f"  Success: {data['success_count'] / data['call_count']:.1%}")
    print(f"  Avg duration: {data['total_duration'] / data['call_count']:.2f}s")
```

---

## Custom Observability Hooks

### Production Hook Pattern

```python
from strands.hooks import HookProvider, HookRegistry
from strands.hooks.events import BeforeToolCallEvent, AfterToolCallEvent, AfterInvocationEvent
import logging, time

class ObservabilityHook(HookProvider):
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.logger = logging.getLogger(f"agent.{agent_name}")
        self.tool_timings = {}

    def register_hooks(self, registry: HookRegistry, **kwargs):
        registry.add_callback(BeforeToolCallEvent, self.before_tool)
        registry.add_callback(AfterToolCallEvent, self.after_tool)
        registry.add_callback(AfterInvocationEvent, self.log_completion)

    def before_tool(self, event: BeforeToolCallEvent):
        tool_id = event.tool_use["toolUseId"]
        self.tool_timings[tool_id] = time.time()
        self.logger.info("Tool invoked", extra={
            "tool": event.tool_use["name"],
            "input": event.tool_use["input"]
        })

    def after_tool(self, event: AfterToolCallEvent):
        tool_id = event.tool_use["toolUseId"]
        duration = time.time() - self.tool_timings[tool_id]

        self.logger.info("Tool completed", extra={
            "tool": event.tool_use["name"],
            "duration_ms": duration * 1000,
            "status": event.result.get("status")
        })

        if duration > 5.0:
            self.logger.warning(f"Slow tool: {event.tool_use['name']} took {duration:.2f}s")

    def log_completion(self, event: AfterInvocationEvent):
        metrics = event.result.metrics.get_summary()
        self.logger.info("Agent completed", extra={
            "cycles": metrics["total_cycles"],
            "tokens": metrics["accumulated_usage"]["totalTokens"]
        })

# Usage
agent = Agent(hooks=[ObservabilityHook("my-agent")])
```

---

### Cost Tracking Hook

```python
from strands.hooks import HookProvider
from strands.hooks.events import AfterInvocationEvent
import boto3

PRICING = {"input": 0.003 / 1000, "output": 0.015 / 1000}

class CostTrackingHook(HookProvider):
    def __init__(self, budget_limit: float = 100.0):
        self.budget_limit = budget_limit
        self.total_cost = 0.0
        self.cloudwatch = boto3.client('cloudwatch')

    def register_hooks(self, registry, **kwargs):
        registry.add_callback(AfterInvocationEvent, self.track_cost)

    def track_cost(self, event):
        usage = event.result.metrics.accumulated_usage
        cost = (usage["inputTokens"] * PRICING["input"] +
                usage["outputTokens"] * PRICING["output"])
        self.total_cost += cost

        self.cloudwatch.put_metric_data(
            Namespace='AgentCosts',
            MetricData=[{
                'MetricName': 'InvocationCost',
                'Value': cost,
                'Unit': 'None'
            }]
        )

        if self.total_cost > self.budget_limit * 0.9:
            logger.warning(f"Budget: ${self.total_cost:.2f} of ${self.budget_limit:.2f}")

agent = Agent(hooks=[CostTrackingHook(budget_limit=100.0)])
```

---

## Third-Party Platforms

### Arize Phoenix

```python
import phoenix as px
from phoenix.trace.opentelemetry import OpenInferenceTracer

session = px.launch_app()
tracer = OpenInferenceTracer()

from strands.observability import StrandsTelemetry
telemetry = StrandsTelemetry(tracer_provider=tracer.tracer_provider)
# View at http://localhost:6006
```

### Langfuse

```python
from langfuse.opentelemetry import LangfuseSpanExporter
from opentelemetry.sdk.trace import TracerProvider, SimpleSpanProcessor

exporter = LangfuseSpanExporter(
    public_key="pk-xxx",
    secret_key="sk-xxx",
    host="https://cloud.langfuse.com"
)
provider = TracerProvider()
provider.add_span_processor(SimpleSpanProcessor(exporter))

from strands.observability import StrandsTelemetry
telemetry = StrandsTelemetry(tracer_provider=provider)
```

---

## Production Checklist

### AgentCore Platform
- [ ] Transaction Search enabled
- [ ] ADOT installed (`aws-opentelemetry-distro`)
- [ ] Session tracking enabled
- [ ] Sampling configured (1-10%)

### Essential
- [ ] OpenTelemetry tracing enabled
- [ ] Cost tracking implemented
- [ ] CloudWatch dashboards created
- [ ] Error alerting configured

### Metrics
- [ ] Latency tracked (p50, p90, p99)
- [ ] Token usage monitored
- [ ] Tool success rate tracked
- [ ] Error rate alerts (> 2%)

### Security
- [ ] Sensitive data redacted from traces
- [ ] Access logs enabled
- [ ] Retention policies configured
