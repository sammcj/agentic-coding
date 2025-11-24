# Observability & Tracing

## OpenTelemetry Distributed Tracing

Strands Agents provides comprehensive observability built on OpenTelemetry standards.

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

## AgentCore CloudWatch Integration

### Automatic Metrics (No Configuration Required)

AgentCore automatically emits using Enhanced Metric Format (EMF):

**Runtime Metrics**:
- `SessionCount`: Active agent sessions
- `InvocationCount`: Total invocations
- `Latency`: Request latency (p50, p90, p99)
- `TokenUsage`: Input, output, total tokens
- `ErrorRate`: Failed invocations percentage

**Gateway Metrics**:
- `ToolInvocationCount`: Tool calls per tool
- `ToolLatency`: Tool execution latency
- `ToolErrorRate`: Tool failure rate

**Memory Metrics**:
- `MemoryQueryCount`: Memory query invocations
- `MemoryQueryLatency`: Retrieval latency

---

### Custom CloudWatch Metrics

```python
import boto3
from datetime import datetime

cloudwatch = boto3.client('cloudwatch')

def publish_custom_metric(metric_name: str, value: float, unit: str = "Count"):
    cloudwatch.put_metric_data(
        Namespace='CustomAgentMetrics',
        MetricData=[{
            'MetricName': metric_name,
            'Value': value,
            'Unit': unit,
            'Timestamp': datetime.utcnow(),
            'Dimensions': [
                {'Name': 'AgentName', 'Value': 'support-agent'},
                {'Name': 'Environment', 'Value': 'production'}
            ]
        }]
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

### Essential

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
