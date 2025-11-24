# Quick Reference: AWS Strands Agents & AgentCore

## Model Selection

**Primary Provider**: Anthropic Claude on AWS Bedrock

**Model ID Format**: `anthropic.claude-{model}-{version}`

**Current Models** (January 2025):
- Sonnet 4.5: `anthropic.claude-sonnet-4-5-20250929-v1:0`
- Haiku 4.5: `anthropic.claude-haiku-4-5-20251001-v1:0`
- Opus 4.5: `anthropic.claude-opus-4-5-20250514-v1:0`

**IMPORTANT**: Always check for latest versions when implementing:
```bash
aws bedrock list-foundation-models --by-provider anthropic
```

---

## Deployment Decision Matrix

| Component | Lambda | ECS/Fargate | AgentCore Runtime |
|-----------|--------|-------------|-------------------|
| **Stateless Agents** | ✅ Perfect | ❌ Overkill | ❌ Overkill |
| **Interactive Agents** | ❌ No streaming | ⚠️ Possible | ✅ Ideal |
| **MCP Servers** | ❌ NEVER | ✅ Standard | ✅ With features |
| **Duration** | < 15 minutes | Unlimited | Up to 8 hours |
| **Cold Starts** | Yes (30-60s) | No | No |

### Critical Rule

**Never deploy MCP servers to Lambda** - they're stateful and need persistent connections.

---

## Multi-Agent Pattern Selection

| Pattern | Complexity | Predictability | Cost | Use Case |
|---------|-----------|----------------|------|----------|
| **Single Agent** | Low | High | 1x | Most tasks |
| **Agent as Tool** | Low | High | 2-3x | Simple delegation to specialists |
| **Graph** | High | Very High | 3-5x | Deterministic workflows with dependencies |
| **Swarm** | Medium | Low | 5-8x | Autonomous collaboration |

**Recommendation**: Start with single agents, evolve to multi-agent as needed.

---

## Session Storage Selection

```
Local dev         → FileSystem
Lambda agents     → S3 or DynamoDB
ECS agents        → DynamoDB
Interactive chat  → AgentCore Memory
Knowledge bases   → AgentCore Memory
```

---

## Model Selection Guide

| Model | Input Cost | Output Cost | Use Case |
|-------|-----------|-------------|----------|
| Claude 4.5 Sonnet | $0.003/1K | $0.015/1K | Complex reasoning, primary agent |
| Claude 4.5 Haiku | $0.0008/1K | $0.004/1K | Simple tasks, formatting, routing |
| Nova Pro | $0.0008/1K | $0.0032/1K | Cost-sensitive, 300K context |

**Strategy**: Use Haiku for simple tasks, Sonnet for complex reasoning.

---

## Critical Constraints

### MCP Server Requirements

1. **Transport**: MUST use `streamable-http` (NOT `stdio`)
2. **Endpoint**: MUST be at `0.0.0.0:8000/mcp`
3. **Deployment**: MUST be ECS/Fargate or AgentCore Runtime
4. **Headers**: Must accept `application/json` and `text/event-stream`

### Tool Count Limits

- Models struggle with > 50-100 tools
- Implement semantic search for > 50 tools
- Use dynamic tool loading based on query context

### Token Management

- Claude 4.5: 200K context (use ~180K max)
- Long conversations REQUIRE conversation managers
- Multi-agent costs multiply 5-10x

---

## Common Patterns Quick Reference

### Base Agent Creation

```python
from strands import Agent
from strands.models import BedrockModel
from strands.session import DynamoDBSessionManager
from strands.agent.conversation_manager import SlidingWindowConversationManager

agent = Agent(
    agent_id="my-agent",
    model=BedrockModel(model_id="anthropic.claude-sonnet-4-5-20250929-v1:0"),
    system_prompt="You are a helpful assistant.",
    tools=[tool1, tool2],
    session_manager=DynamoDBSessionManager(table_name="sessions"),
    conversation_manager=SlidingWindowConversationManager(max_messages=20)
)
```

### MCP Server (ECS/Fargate)

```python
from mcp.server import FastMCP

mcp = FastMCP("My Server")

@mcp.tool()
def my_tool(param: str) -> dict:
    return {"status": "success", "content": [{"text": f"Result: {param}"}]}

# CRITICAL: streamable-http mode
if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
```

### Tool Error Handling

```python
from strands import tool

@tool
def safe_tool(param: str) -> dict:
    """Always return structured results, never raise exceptions."""
    try:
        result = operation(param)
        return {"status": "success", "content": [{"text": str(result)}]}
    except Exception as e:
        return {"status": "error", "content": [{"text": f"Failed: {str(e)}"}]}
```

---

## Performance Thresholds

| Metric | Threshold | Action |
|--------|-----------|--------|
| Tool execution | > 5s | Add progress feedback |
| Agent latency | > 30s | Investigate bottlenecks |
| Token usage | > 100K | Review conversation management |
| Tool failure rate | > 5% | Review error handling |
| Error rate | > 2% | Investigate root cause |

---

## When to Use Each Service

### Strands SDK Only (No AgentCore)

Use when:
- Building simple, stateless agents
- Tight cost control required
- No need for enterprise features
- Want maximum deployment flexibility

### Strands SDK + AgentCore Platform

Use when:
- Need 8-hour runtime support
- Streaming responses required
- Enterprise security/compliance needed
- Cross-session intelligence required
- Want managed infrastructure

---

## Conversation Management

**Short Sessions (< 10 exchanges)**:
```python
SlidingWindowConversationManager(max_messages=15, min_messages=2)
```

**Long Sessions (need history)**:
```python
SummarizingConversationManager(max_messages=30, summarize_messages_count=25)
```

---

## Observability Quick Start

### Development

```python
from strands.observability import StrandsTelemetry

telemetry = StrandsTelemetry().setup_console_exporter()
```

### Production

```python
telemetry = StrandsTelemetry().setup_otlp_exporter()
# Reads OTEL_EXPORTER_OTLP_ENDPOINT from environment
```

### Both (Console + OTLP)

```python
telemetry = StrandsTelemetry() \
    .setup_console_exporter() \
    .setup_otlp_exporter()
```

---

## Common Anti-Patterns to Avoid

1. ❌ **Overloading agents with > 50 tools** → Use semantic search
2. ❌ **No conversation management** → Implement SlidingWindow or Summarising
3. ❌ **Deploying MCP servers to Lambda** → Use ECS/Fargate
4. ❌ **No timeout configuration** → Set execution limits everywhere
5. ❌ **Ignoring token limits** → Implement conversation managers
6. ❌ **No cost monitoring** → Implement cost tracking hooks from day one
