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
- OpenTelemetry tracing setup (environment variables, fluent API, code-based)
- Custom observability hooks (logging, metrics, alerting)
- CloudWatch integration (automatic metrics, custom metrics)
- Third-party platforms (Arize Phoenix, Langfuse, Jaeger)
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

## Quick Implementation Examples

### Basic Agent Creation

```python
from strands import Agent
from strands.models import BedrockModel
from strands.session import DynamoDBSessionManager
from strands.agent.conversation_manager import SlidingWindowConversationManager

agent = Agent(
    agent_id="my-agent",
    model=BedrockModel(model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0"),
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

```python
from strands.observability import StrandsTelemetry

# Development: Console output
telemetry = StrandsTelemetry().setup_console_exporter()

# Production: OTLP endpoint (reads from environment)
telemetry = StrandsTelemetry().setup_otlp_exporter()

# Both: Console + OTLP (multi-backend)
telemetry = StrandsTelemetry() \
    .setup_console_exporter() \
    .setup_otlp_exporter()
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
- [ ] Observability hooks implemented (see **[observability.md](references/observability.md)**)
- [ ] Cost tracking enabled (see **[observability.md](references/observability.md)**)
- [ ] OpenTelemetry tracing configured
- [ ] Error handling in all tools (see **[patterns.md](references/patterns.md)**)
- [ ] Security permissions validated (see **[patterns.md](references/patterns.md)**)
- [ ] MCP servers deployed to ECS/Fargate (see **[architecture.md](references/architecture.md)**)
- [ ] Timeout limits set
- [ ] Session backend configured (DynamoDB for production)
- [ ] CloudWatch dashboards created

---

## Reference Files Navigation

- **[quick-reference.md](references/quick-reference.md)** - Decision matrices, cheat sheets, common patterns, anti-patterns
- **[architecture.md](references/architecture.md)** - Deployment patterns, multi-agent orchestration, session storage, AgentCore services
- **[patterns.md](references/patterns.md)** - Foundation components, tool design, security, testing, performance optimisation
- **[limitations.md](references/limitations.md)** - Known constraints, workarounds, mitigation strategies, challenges
- **[observability.md](references/observability.md)** - OpenTelemetry setup, hooks, CloudWatch, cost tracking, monitoring

---

## Key Takeaways

1. **MCP servers MUST use streamable-http, NEVER Lambda**
2. **Use semantic search for > 15 tools** (models can't handle more)
3. **Always implement conversation management** (prevent token overflow)
4. **Multi-agent costs multiply 5-10x** (track cost from day one)
5. **Set timeout limits everywhere** (agents, graphs, tools)
6. **Error handling in tools is non-negotiable** (return errors, don't raise)
7. **Lambda for stateless, AgentCore for interactive** (streaming requires AgentCore)
8. **Observability from day one** (OpenTelemetry + cost tracking)
9. **Start simple, evolve complexity** (single agent → delegation → graph → swarm)
10. **Security by default** (permissions, approval hooks, least privilege)
11. **Separate config from code** (environment variables, prompt templates, system prompts, config files etc.)
