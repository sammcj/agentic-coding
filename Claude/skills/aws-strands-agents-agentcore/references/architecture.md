# Architecture & Deployment Patterns

## What is Strands Agents SDK?

**Open-source Python SDK** for building AI agents with minimal code using a model-driven approach.

**Core Components**:
- `Agent`: Foundational unit (model + tools + system prompt)
- `@tool`: Decorator for creating agent-callable functions
- `Multi-Agent Patterns`: Swarm, Graph, Agent-as-Tool
- `Session Management`: FileSystem, S3, DynamoDB, AgentCore Memory
- `Conversation Managers`: SlidingWindow, Summarising
- `Hooks`: Lifecycle event interception
- `Metrics`: Automatic token usage, latency, tool execution tracking

**Key Characteristic**: Framework-agnostic, model-agnostic (primarily AWS Bedrock with Anthropic Claude, also supports other providers)

---

## What is Amazon Bedrock AgentCore?

**Enterprise platform** providing production infrastructure for deploying, operating, and scaling agents.

**Relationship**:
- Strands SDK = agent development framework (can run anywhere)
- AgentCore = deployment platform (AWS-managed infrastructure)
- You can use Strands SDK WITHOUT AgentCore
- AgentCore works WITH Strands SDK (or any framework)

**AgentCore Platform Services**:

| Service              | Purpose                            | Key Features                                              |
|----------------------|------------------------------------|-----------------------------------------------------------|
| **Runtime**          | Long-running agent execution       | 8hr runtime, streaming, session isolation, no cold starts |
| **Gateway**          | Unified tool access                | MCP/Lambda/REST integration, runtime discovery            |
| **Memory**           | Persistent cross-session knowledge | Knowledge graphs, semantic retrieval                      |
| **Identity**         | Secure auth/authorisation          | IAM integration, OAuth (GitHub, Slack, etc.)              |
| **Browser**          | Managed web automation             | Headless browser, JavaScript rendering                    |
| **Code Interpreter** | Isolated Python execution          | Sandboxed environment, package installation               |
| **Observability**    | Monitoring and metrics             | CloudWatch EMF, automatic dashboards                      |

---

## Model-Driven Philosophy

**Traditional frameworks** require explicit orchestration code:
```python
# DON'T: Manual control flow
while not done:
    if needs_research:
        result = research_tool()
    elif needs_analysis:
        result = analysis_tool()
```

**Strands Agents** delegates orchestration to the model:
```python
# DO: Model decides
agent = Agent(
    system_prompt="You are a research analyst. Use tools to answer questions.",
    tools=[research_tool, analysis_tool]
)
result = agent("What are the top tech trends?")
# Model automatically decides: research_tool → analysis_tool → respond
```

---

## Deployment Architectures

### Lambda Serverless (Stateless Agents Only)

**When to Use**:
- Event-driven workloads (S3 uploads, SQS messages, EventBridge)
- Stateless request/response (< 10 minutes)
- Asynchronous background jobs
- Cost optimisation priority

**When NOT to Use**:
- Interactive chat (no streaming)
- Long-running tasks (> 15 minutes)
- **Hosting MCP servers** (stateful, need persistent connections)

**Example**:
```python
def lambda_handler(event, context):
    query = event["query"]

    # Load tools from ECS-hosted MCP servers
    tools = MCPRegistry.load_servers(["database-query", "aws-tools"])

    agent = Agent(
        agent_id=None,  # No persistent session
        system_prompt="Process this task efficiently.",
        tools=tools,
        session_backend=None  # Stateless
    )

    result = agent(query)
    return {"statusCode": 200, "body": json.dumps(result)}
```

---

### ECS/Fargate (MCP Servers)

**When to Use**:
- **Always for MCP servers** (24/7 availability)
- Connection pooling to databases, APIs
- Cost-effective persistent services

**Why Not Lambda for MCP**:
- ❌ Lambda is ephemeral (15-minute max)
- ❌ Connection pools don't persist
- ❌ Cold starts add latency
- ❌ No persistent HTTP connections

**Example**:
```python
# mcp_server.py (deployed to ECS/Fargate)
from mcp.server import FastMCP
import psycopg2.pool

# Persistent connection pool (why Lambda won't work)
db_pool = psycopg2.pool.SimpleConnectionPool(
    minconn=1, maxconn=10, host="db.internal"
)

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

# CRITICAL: streamable-http mode
if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
```

---

### AgentCore Runtime (Interactive Agents)

**When to Use**:
- Long-running tasks (up to 8 hours)
- Real-time streaming required
- Complex multi-agent orchestration
- Enterprise security requirements

**Benefits**:
- Complete session isolation
- Built-in observability via CloudWatch
- Integrated identity management
- No Lambda cold start issues

**Example**:
```python
from fastapi import FastAPI

app = FastAPI()

@app.post("/agent/invoke")
async def invoke_agent(request: dict):
    agent = Agent(
        agent_id=request["agent_id"],
        system_prompt=request["system_prompt"],
        tools=load_tools(),
        session_backend="agentcore-memory"  # Use AgentCore Memory
    )

    # AgentCore handles streaming, session isolation, observability
    result = agent(request["input"])
    return {"response": result.message["content"][0]["text"]}
```

---

### Hybrid Architecture (Recommended)

**Best Practice**: Combine Lambda agents with ECS-hosted MCP servers.

```
S3/SQS/EventBridge → Lambda Agents → HTTP → ECS MCP Servers (persistent)
API Gateway → Lambda Agents → HTTP → ECS MCP Servers (persistent)
Web Client → AgentCore Runtime → HTTP → ECS MCP Servers (persistent)
```

**Benefits**:
- ✅ Lambda for event-driven agent invocations (cost-efficient, auto-scaling)
- ✅ ECS/Fargate for stateful MCP servers (persistent, reliable)
- ✅ AgentCore Runtime for interactive experiences (streaming, long sessions)
- ✅ Clear separation of concerns
- ✅ Optimised cost and performance

---

## Agent Execution Flow

```
1. User Input → Agent
2. Agent → Model (with system prompt + tools + context)
3. Model Decision:
   - Generate Response → Return to user
   - Call Tool → Execute tool → Return result to model → Repeat from step 2
4. Final Response → User
```

**Metrics Tracked**:
- Token usage (input, output, cached, total)
- Latency (first token, total, per cycle)
- Tool statistics (calls, success rate, duration)
- Cycle count and durations

---

## Session Storage Options

| Backend | Latency | Scalability | Use Case |
|---------|---------|-------------|----------|
| **File System** | Very Low | Limited | Local dev only |
| **S3** | Medium (~50ms) | High | Serverless, simple |
| **DynamoDB** | Low (~10ms) | Very High | Production, multi-region |
| **AgentCore Memory** | Low (~50-200ms) | Very High | Cross-session intelligence, knowledge graphs |

**Decision Tree**:
```
Local dev → FileSystem
Lambda agents → S3 or DynamoDB
ECS agents → DynamoDB
Interactive chat → AgentCore Memory
Knowledge bases → AgentCore Memory
```

---

## Tool Integration Options

### Direct MCP Integration

**Use when**: Simple tool requirements, < 10 MCP servers

```python
from strands.tools.mcp import MCPClient
from mcp import streamablehttp_client

client = MCPClient(lambda: streamablehttp_client("http://mcp:8000/mcp"))
with client:
    tools = client.list_tools_sync()
agent = Agent(tools=tools)
```

### AgentCore Gateway

**Use when**: Multiple protocols, frequent tool changes, centralised governance

**Benefits**:
- Protocol abstraction (MCP + Lambda + REST)
- Runtime discovery (dynamic tool loading)
- Automatic authentication

**Limitations**:
- OpenAPI specs > 2MB cannot be loaded
- Discovery adds 50-200ms latency

---

## Multi-Agent Patterns

### Agent-as-Tool (Simple Delegation)

```python
# Create specialist agents
researcher = Agent(system_prompt="Research specialist.", tools=[web_search])
writer = Agent(system_prompt="Content writer.", tools=[grammar_check])

# Wrap as tools
@tool
def research_topic(topic: str) -> str:
    result = researcher(f"Research: {topic}")
    return result.message["content"][0]["text"]

@tool
def write_article(data: str, topic: str) -> str:
    result = writer(f"Write article about {topic} using: {data}")
    return result.message["content"][0]["text"]

# Orchestrator
orchestrator = Agent(
    system_prompt="Coordinate research and writing.",
    tools=[research_topic, write_article]
)
```

### Graph (Deterministic Workflow)

```python
from strands.multiagent import GraphBuilder

builder = GraphBuilder()
builder.add_node("collector", data_collector_agent)
builder.add_node("analyser", analyser_agent)
builder.add_node("reporter", reporter_agent)

builder.add_edge("collector", "analyser")
builder.add_edge("analyser", "reporter")

# Safety constraints
builder.set_execution_timeout(300)  # 5 minutes
builder.set_max_node_executions(10)

graph = builder.build(entry_point="collector")
result = graph.run({"task": "Analyse Q4 sales data"})
```

### Swarm (Autonomous Collaboration)

```python
from strands.multiagent import Swarm

swarm = Swarm(
    nodes=[researcher, writer, reviewer],
    entry_point=researcher,
    max_handoffs=10,  # Prevent infinite loops
    execution_timeout=300.0
)

result = swarm.run("Create and review an article")
```

---

## Regional Considerations

**Data Residency**:
- Bedrock processes data in-region (Australian data sovereignty, etc.)
- AgentCore Memory stores data in specified region
- Note: Third-party model providers may have different data locality requirements

**Best Practice**: Enforce regional processing for compliance
```python
model = BedrockModel(
    model_id="anthropic.claude-sonnet-4-5-20250929-v1:0",
    region_name="eu-west-1"  # GDPR-compliant
)
```
