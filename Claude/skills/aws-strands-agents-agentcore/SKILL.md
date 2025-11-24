---
name: aws-strands-agents-agentcore
description: Use when working with AWS Strands Agents SDK or Amazon Bedrock AgentCore platform for building AI agents. Provides architecture guidance, implementation patterns, deployment strategies, observability setup, multi-agent orchestration, and MCP server integration.
---

# AWS Strands Agents & AgentCore

## Overview

**AWS Strands Agents SDK**: Open-source Python framework for building AI agents with model-driven orchestration (minimal code, model decides tool usage)

**Amazon Bedrock AgentCore**: Enterprise platform for deploying, operating, and scaling agents in production

**Relationship**: Strands SDK can run standalone OR with AgentCore platform services. AgentCore is optional but provides enterprise features (8hr runtime, streaming, memory, identity, observability).

---

## Quick Start Decision Tree

### 1. What are you building?

**Single-purpose agent (one task)**:
- Event-driven (S3, SQS, scheduled) → See **[architecture.md](references/architecture.md)** for Lambda deployment
- Interactive with streaming → See **[architecture.md](references/architecture.md)** for AgentCore Runtime
- API endpoint (stateless) → See **[architecture.md](references/architecture.md)** for Lambda

**Multi-agent system**:
- Deterministic workflow → See **[architecture.md](references/architecture.md)** for Graph Pattern
- Autonomous collaboration → See **[architecture.md](references/architecture.md)** for Swarm Pattern
- Simple delegation → See **[architecture.md](references/architecture.md)** for Agent-as-Tool Pattern

**Tool/Integration Server (MCP)**:
- **ALWAYS** → See **[architecture.md](references/architecture.md)** for ECS/Fargate or AgentCore Runtime deployment
- **NEVER Lambda** (stateful, need persistent connections)

---

## Critical Constraints (MUST KNOW)

### MCP Server Requirements

1. **Transport**: MUST use `streamable-http` (NOT `stdio`)
2. **Endpoint**: MUST be at `0.0.0.0:8000/mcp`
3. **Deployment**: MUST be ECS/Fargate or AgentCore Runtime (NEVER Lambda)
4. **Headers**: Must accept `application/json` and `text/event-stream`

**Why**: MCP servers are stateful and need persistent connections. Lambda is ephemeral and unsuitable.

See **[limitations.md](references/limitations.md)** for detailed MCP requirements and workarounds.

---

### Tool Count Limits

- Models struggle with > 50-100 tools
- **Solution**: Implement semantic search for dynamic tool loading

See **[patterns.md](references/patterns.md)** for semantic tool search implementation.

---

### Token Management

- Claude 4.5: 200K context (use ~180K max to allow for response)
- Long conversations REQUIRE conversation managers
- Multi-agent costs multiply 5-10x (implement cost tracking)

See **[limitations.md](references/limitations.md)** for token management strategies.

---

## Deployment Decision Matrix

| Component              | Lambda         | ECS/Fargate | AgentCore Runtime |
|------------------------|----------------|-------------|-------------------|
| **Stateless Agents**   | ✅ Perfect      | ❌ Overkill  | ❌ Overkill        |
| **Interactive Agents** | ❌ No streaming | ⚠️ Possible  | ✅ Ideal           |
| **MCP Servers**        | ❌ NEVER        | ✅ Standard  | ✅ With features   |
| **Duration**           | < 15 minutes   | Unlimited   | Up to 8 hours     |
| **Cold Starts**        | Yes (30-60s)   | No          | No                |

**For detailed deployment patterns and examples**, see **[architecture.md](references/architecture.md)**.

---

## Multi-Agent Pattern Selection

| Pattern           | Complexity | Predictability | Cost | Use Case                 |
|-------------------|------------|----------------|------|--------------------------|
| **Single Agent**  | Low        | High           | 1x   | Most tasks               |
| **Agent as Tool** | Low        | High           | 2-3x | Simple delegation        |
| **Graph**         | High       | Very High      | 3-5x | Deterministic workflows  |
| **Swarm**         | Medium     | Low            | 5-8x | Autonomous collaboration |

**Recommendation**: Start with single agents, evolve to multi-agent as needed.

**For implementation examples**, see **[architecture.md](references/architecture.md)**.

---

## Common Implementation Patterns

### When to Read [patterns.md](references/patterns.md)

Read when you need:
- Base agent factory patterns (reusable components for platform teams)
- MCP server registry patterns (organisational tool catalogues)
- Semantic tool search (for > 50 tools)
- Tool design best practices (granularity, error handling, response size)
- Security patterns (permissions, human-in-the-loop)
- Testing patterns (unit tests, integration tests)

### When to Read [observability.md](references/observability.md)

Read when you need:
- **AWS AgentCore Observability Platform** setup (Transaction Search, GenAI dashboard, ADOT)
- Runtime-hosted vs non-runtime hosted observability configuration
- Session tracking for multi-turn conversations
- X-Ray distributed tracing with custom headers
- Service-provided metrics for runtime, memory, gateway, tools
- OpenTelemetry tracing setup (environment variables, fluent API, code-based)
- Custom observability hooks (logging, metrics, alerting)
- Third-party platforms (Arize Phoenix, Langfuse)
- Cost tracking hooks
- Production observability patterns

### When to Read [limitations.md](references/limitations.md)

Read when you encounter:
- MCP server deployment issues
- Tool selection problems (> 50 tools)
- Token context window overflow
- Lambda streaming limitations
- Multi-agent cost concerns
- Throttling errors (Bedrock API)
- AgentCore platform constraints
- Cold start latency issues

### When to Read [quick-reference.md](references/quick-reference.md)

Read for:
- Quick decision matrices (deployment, multi-agent, session storage)
- Model selection guide (cost comparison)
- Common code patterns (agent creation, MCP servers, tool handling)
- Performance thresholds (tool execution, latency, token usage)
- Anti-patterns to avoid
- Conversation management strategies

---

## Model-Driven Philosophy

**Key Concept**: Strands Agents delegates orchestration to the model rather than requiring explicit control flow code.

```python
# Traditional: Manual orchestration (avoid)
while not done:
    if needs_research:
        result = research_tool()
    elif needs_analysis:
        result = analysis_tool()

# Strands: Model decides (prefer)
agent = Agent(
    system_prompt="You are a research analyst. Use tools to answer questions.",
    tools=[research_tool, analysis_tool]
)
result = agent("What are the top tech trends?")
# Model automatically orchestrates: research_tool → analysis_tool → respond
```

**Benefits**: Less code, more adaptable, fewer bugs, leverages model intelligence.

---

## Model Selection

**Primary Provider**: Anthropic Claude via AWS Bedrock

**Model ID Format**: `anthropic.claude-{model}-{version}`

**Current Recommended Models** (as of January 2025):
- `anthropic.claude-sonnet-4-5-20250929-v1:0` - Production (balanced performance/cost)
- `anthropic.claude-haiku-4-5-20251001-v1:0` - Fast/economical tasks
- `anthropic.claude-opus-4-5-20250514-v1:0` - Complex reasoning (when available)

**IMPORTANT**: Always verify the latest available Anthropic model versions on AWS Bedrock when implementing or documenting systems. Model versions are updated regularly with performance improvements.

**Check Latest Models**:
```bash
aws bedrock list-foundation-models --by-provider anthropic \
  --query 'modelSummaries[*].[modelId,modelName]' --output table
```

**Note**: While Strands SDK supports other providers (OpenAI, Azure, Ollama), this skill focuses on AWS Bedrock deployment patterns as the primary use case.

---

## Quick Implementation Examples

### Basic Agent Creation

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

result = agent("Process this request")
```

**For base agent factory patterns**, see **[patterns.md](references/patterns.md)**.

---

### MCP Server (ECS/Fargate Deployment)

```python
from mcp.server import FastMCP
import psycopg2.pool

# Persistent connection pool (why Lambda won't work)
db_pool = psycopg2.pool.SimpleConnectionPool(minconn=1, maxconn=10, host="db.internal")

mcp = FastMCP("Database Tools")

@mcp.tool()
def query_database(sql: str) -> dict:
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        return {"status": "success", "rows": cursor.fetchall()}
    finally:
        db_pool.putconn(conn)

# CRITICAL: streamable-http mode for AgentCore compatibility
if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
```

**For deployment architecture details**, see **[architecture.md](references/architecture.md)**.

---

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

**For comprehensive tool design patterns**, see **[patterns.md](references/patterns.md)**.

---

### Observability Setup

**AgentCore Runtime (Automatic)**:
```python
# Install with OTEL support
# pip install 'strands-agents[otel]'
# Add 'aws-opentelemetry-distro' to requirements.txt

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent

app = BedrockAgentCoreApp()
agent = Agent(...)  # Automatically instrumented

@app.entrypoint
def handler(payload):
    return agent(payload["prompt"])
```

**Self-Hosted (Environment Variables)**:
```bash
export AGENT_OBSERVABILITY_ENABLED=true
export OTEL_PYTHON_DISTRO=aws_distro
export OTEL_RESOURCE_ATTRIBUTES="service.name=my-agent"

# Run with auto-instrumentation
opentelemetry-instrument python agent.py
```

**General OpenTelemetry**:
```python
from strands.observability import StrandsTelemetry

# Development: Console output
telemetry = StrandsTelemetry().setup_console_exporter()

# Production: OTLP endpoint
telemetry = StrandsTelemetry().setup_otlp_exporter()
```

**For detailed observability patterns**, see **[observability.md](references/observability.md)**.

---

## Session Storage Selection

```
Local dev         → FileSystem
Lambda agents     → S3 or DynamoDB
ECS agents        → DynamoDB
Interactive chat  → AgentCore Memory
Knowledge bases   → AgentCore Memory
```

**For storage backend comparison and examples**, see **[architecture.md](references/architecture.md)**.

---

## When to Use AgentCore Platform vs Strands SDK Only

### Use Strands SDK Only (Deploy to Lambda/ECS)

When:
- Building simple, stateless agents
- Tight cost control required
- No need for enterprise features (identity, memory)
- Want maximum deployment flexibility

### Use Strands SDK + AgentCore Platform

When:
- Need 8-hour runtime support
- Streaming responses required
- Enterprise security/compliance (identity, audit)
- Cross-session intelligence needed (memory graphs)
- Want managed infrastructure
- Multi-agent workflows with session isolation

**For AgentCore platform service details**, see **[architecture.md](references/architecture.md)**.

---

## Common Anti-Patterns

1. ❌ **Overloading agents with > 50 tools** → Use semantic search
2. ❌ **No conversation management** → Implement SlidingWindow or Summarising
3. ❌ **Deploying MCP servers to Lambda** → Use ECS/Fargate
4. ❌ **No timeout configuration** → Set execution limits everywhere
5. ❌ **Ignoring token limits** → Implement conversation managers
6. ❌ **No cost monitoring** → Implement cost tracking from day one

**For detailed anti-patterns and solutions**, see **[patterns.md](references/patterns.md)** and **[limitations.md](references/limitations.md)**.

---

## Production Deployment Checklist

Before deploying to production:

- [ ] Conversation management configured
- [ ] **AgentCore Observability enabled** (Transaction Search, GenAI dashboard) or OpenTelemetry configured
- [ ] Observability hooks implemented (see **[observability.md](references/observability.md)**)
- [ ] Cost tracking enabled (see **[observability.md](references/observability.md)**)
- [ ] Error handling in all tools (see **[patterns.md](references/patterns.md)**)
- [ ] Security permissions validated (see **[patterns.md](references/patterns.md)**)
- [ ] MCP servers deployed to ECS/Fargate (see **[architecture.md](references/architecture.md)**)
- [ ] Timeout limits set
- [ ] Session backend configured (DynamoDB for production)
- [ ] CloudWatch alarms configured (error rate, latency, token usage)

---

## Reference Files Navigation

- **[quick-reference.md](references/quick-reference.md)** - Decision matrices, cheat sheets, common patterns, anti-patterns
- **[architecture.md](references/architecture.md)** - Deployment patterns, multi-agent orchestration, session storage, AgentCore services
- **[patterns.md](references/patterns.md)** - Foundation components, tool design, security, testing, performance optimisation
- **[limitations.md](references/limitations.md)** - Known constraints, workarounds, mitigation strategies, challenges
- **[observability.md](references/observability.md)** - AgentCore Observability platform, ADOT, GenAI dashboard, OpenTelemetry, hooks, cost tracking

---

## Key Takeaways

1. **MCP servers MUST use streamable-http, NEVER Lambda**
2. **Use semantic search for > 15 tools** (models can't handle more)
3. **Always implement conversation management** (prevent token overflow)
4. **Multi-agent costs multiply 5-10x** (track cost from day one)
5. **Set timeout limits everywhere** (agents, graphs, tools)
6. **Error handling in tools is non-negotiable** (return errors, don't raise)
7. **Lambda for stateless, AgentCore for interactive** (streaming requires AgentCore)
8. **AgentCore Observability for production** (GenAI dashboard, automatic instrumentation, session tracking)
9. **Start simple, evolve complexity** (single agent → delegation → graph → swarm)
10. **Security by default** (permissions, approval hooks, least privilege)
11. **Separate config from code** (environment variables, prompt templates, system prompts, config files etc.)
