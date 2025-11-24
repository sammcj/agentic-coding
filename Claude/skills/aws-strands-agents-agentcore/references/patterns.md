# Implementation Patterns & Best Practices

## Foundation Component Patterns

### Pattern 1: Base Agent Factory

Build reusable agent factories with organisational defaults:

```python
# foundation/agent_factory.py
from strands import Agent
from strands.models import BedrockModel
from strands.session import DynamoDBSessionManager
from strands.agent.conversation_manager import SlidingWindowConversationManager
import os

class BaseAgentFactory:
    """Platform standard agent factory."""

    @staticmethod
    def create_agent(
        agent_id: str,
        system_prompt: str,
        tools: list,
        session_backend: str = "dynamodb",
        enable_observability: bool = True
    ) -> Agent:
        """Create agent with organisational defaults."""

        model = BedrockModel(
            model_id=os.getenv("DEFAULT_MODEL_ID", "us.anthropic.claude-sonnet-4-5-20250929-v1:0"),
            temperature=0.7,
            region_name=os.getenv("AWS_REGION", "us-east-1")
        )

        session_manager = DynamoDBSessionManager(
            table_name=os.getenv("SESSION_TABLE"),
            region_name=os.getenv("AWS_REGION")
        ) if session_backend == "dynamodb" else None

        conversation_manager = SlidingWindowConversationManager(
            max_messages=20,
            min_messages=2
        )

        hooks = []
        if enable_observability:
            from foundation.observability import StandardObservabilityHook
            hooks.append(StandardObservabilityHook())

        return Agent(
            agent_id=agent_id,
            model=model,
            system_prompt=system_prompt,
            tools=tools,
            session_manager=session_manager,
            conversation_manager=conversation_manager,
            hooks=hooks
        )
```

**Usage by Product Teams**:
```python
from foundation.agent_factory import BaseAgentFactory

agent = BaseAgentFactory.create_agent(
    agent_id="customer-support",
    system_prompt="You are a helpful customer support agent.",
    tools=[tool1, tool2]
)
```

---

### Pattern 2: MCP Server Registry

Create a catalogue of organisation-wide MCP servers:

```python
# foundation/mcp_loader.py
from strands.tools.mcp import MCPClient
from mcp import streamablehttp_client

class MCPRegistry:
    """Load MCP servers from organisational catalogue."""

    # ECS-hosted MCP servers (always persistent)
    MCP_ENDPOINTS = {
        "database-query": "http://mcp-database.internal:8000/mcp",
        "aws-tools": "http://mcp-aws-tools.internal:8000/mcp",
        "notification": "http://mcp-notification.internal:8000/mcp"
    }

    @staticmethod
    def load_servers(server_names: list[str]) -> list:
        """Load tools from specified MCP servers."""
        all_tools = []

        for name in server_names:
            endpoint = MCPRegistry.MCP_ENDPOINTS[name]
            client = MCPClient(lambda e=endpoint: streamablehttp_client(e))

            with client:
                tools = client.list_tools_sync()
                all_tools.extend(tools)

        return all_tools

# Usage
tools = MCPRegistry.load_servers(["database-query", "aws-tools"])
agent = BaseAgentFactory.create_agent(
    agent_id="support-agent",
    system_prompt="You are helpful.",
    tools=tools
)
```

---

### Pattern 3: Semantic Tool Search (> 50 Tools)

For large tool sets, use semantic search to dynamically load relevant tools:

```python
# foundation/tool_search.py
from sentence_transformers import SentenceTransformer
import numpy as np

class DynamicToolLoader:
    """Load relevant tools based on query for large tool sets."""

    def __init__(self, all_tools: list):
        self.all_tools = all_tools
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

        # Pre-compute embeddings
        self.tool_embeddings = self.model.encode([
            tool.__doc__ for tool in all_tools
        ])

    def get_relevant_tools(self, query: str, top_k: int = 10) -> list:
        """Find top-k relevant tools for query."""
        query_embedding = self.model.encode([query])

        similarities = np.dot(self.tool_embeddings, query_embedding.T).flatten()
        top_indices = np.argsort(similarities)[-top_k:]

        return [self.all_tools[i] for i in top_indices]

# Usage with large tool sets
tool_loader = DynamicToolLoader(all_organisational_tools)  # 100+ tools

# For each agent invocation
relevant_tools = tool_loader.get_relevant_tools(user_query, top_k=10)
agent = Agent(tools=relevant_tools)  # Only 10 tools, not 100+
```

**Why This Matters**: Models struggle with > 50-100 tools. AWS internal agents with 6,000 tools use semantic search instead of describing all tools to the model.

---

## Tool Design Patterns

### Rule 1: User-Task Oriented (Not API-Oriented)

```python
# ❌ BAD: API-style granularity
@tool
def get_user_by_id(user_id: str) -> dict:
    """Get user by ID."""
    pass

@tool
def get_user_orders(user_id: str) -> list:
    """Get orders for user."""
    pass

# ✅ GOOD: Task-oriented
@tool
def get_customer_profile(customer_email: str) -> dict:
    """
    Get complete customer profile including orders, preferences, and history.

    Args:
        customer_email: Customer's email address

    Returns:
        Comprehensive customer data
    """
    user = _get_user_by_email(customer_email)
    orders = _get_user_orders(user["id"])
    preferences = _get_user_preferences(user["id"])

    return {
        "user": user,
        "orders": orders,
        "preferences": preferences
    }
```

---

### Rule 2: Structured Error Handling

**Always return structured results, never raise exceptions to the model.**

```python
# ✅ GOOD: Graceful error handling
@tool
def query_database(sql: str) -> dict:
    """Execute SQL query and return results."""
    try:
        results = database.execute(sql)
        return {
            "status": "success",
            "content": [{"text": json.dumps(results)}]
        }
    except DatabaseError as e:
        return {
            "status": "error",
            "content": [{"text": f"Query failed: {str(e)}. Check syntax and permissions."}]
        }
```

---

### Rule 3: Response Size Management

For large datasets, use pagination:

```python
@tool
def query_large_dataset(query: str, page: int = 1, page_size: int = 10) -> dict:
    """Query dataset with pagination to avoid large responses."""
    results = database.query(query, offset=(page-1)*page_size, limit=page_size)

    return {
        "status": "success",
        "content": [{"text": json.dumps(results)}],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "has_more": len(results) == page_size
        }
    }
```

---

## Security Patterns

### Tool-Level Permissions

```python
from strands import Agent, tool
from strands.hooks import BeforeToolCallEvent, HookProvider, HookRegistry

TOOL_PERMISSIONS = {
    "delete_database": "admin:delete_records",
    "send_company_email": "user:send_email",
    "query_database": "user:read_data"
}

class PermissionValidator(HookProvider):
    """Validate tool permissions before execution."""

    def __init__(self, user_permissions: list[str]):
        self.user_permissions = user_permissions

    def register_hooks(self, registry: HookRegistry, **kwargs):
        registry.add_callback(BeforeToolCallEvent, self.validate_permissions)

    def validate_permissions(self, event: BeforeToolCallEvent):
        tool_name = event.tool_use["name"]
        required_permission = TOOL_PERMISSIONS.get(tool_name)

        if required_permission and required_permission not in self.user_permissions:
            event.cancel_tool = f"Permission denied: {required_permission} required"

# Usage
agent = Agent(
    tools=[delete_database, query_database],
    hooks=[PermissionValidator(user_permissions=["user:read_data"])]
)
```

---

### Human-in-the-Loop for Sensitive Actions

```python
class ApprovalHook(HookProvider):
    """Require approval for sensitive operations."""

    SENSITIVE_TOOLS = ["delete_database", "send_company_email", "transfer_funds"]

    def register_hooks(self, registry: HookRegistry, **kwargs):
        registry.add_callback(BeforeToolCallEvent, self.require_approval)

    def require_approval(self, event: BeforeToolCallEvent):
        if event.tool_use["name"] in self.SENSITIVE_TOOLS:
            approval = event.interrupt(
                "approval-required",
                reason={
                    "action": event.tool_use["name"],
                    "params": event.tool_use["input"]
                }
            )

            if approval.lower() != "approved":
                event.cancel_tool = "Action denied by user"

agent = Agent(hooks=[ApprovalHook()], tools=[delete_database])
```

---

## Performance Optimisation

### Concurrent Tool Execution

```python
from strands.tools.executors import ConcurrentToolExecutor

# For thread-safe tools that can run in parallel
agent = Agent(
    tools=[fetch_api_data, query_database, check_cache],
    tool_executor=ConcurrentToolExecutor()
)
```

**When to Use**:
- Tools are I/O bound (API calls, database queries)
- Tools are thread-safe
- Order of execution doesn't matter

**When to Avoid**:
- Tools modify shared state
- Tools depend on each other

---

### Tool Caching Strategy

```python
from functools import lru_cache

@tool
@lru_cache(maxsize=100)
def get_product_catalogue() -> dict:
    """Get product catalogue (cached for performance)."""
    return database.get_all_products()
```

---

## Conversation Management Strategies

### For Short Sessions (< 10 Exchanges)

```python
from strands.agent.conversation_manager import SlidingWindowConversationManager

conversation_manager = SlidingWindowConversationManager(
    max_messages=15,  # Keep last 15 messages
    min_messages=2
)

agent = Agent(conversation_manager=conversation_manager)
```

---

### For Long Sessions (Need Historical Context)

```python
from strands.agent.conversation_manager import SummarizingConversationManager

conversation_manager = SummarizingConversationManager(
    max_messages=30,
    summarize_messages_count=25
)

agent = Agent(conversation_manager=conversation_manager)
```

---

## Testing Patterns

### Unit Testing Tools

```python
# test_tools.py
from myapp.tools import analyse_data

def test_analyse_data():
    """Test tool in isolation."""
    result = analyse_data(data="sample data")

    assert result["status"] == "success"
    assert "insights" in result["content"][0]["text"]
```

---

### Integration Testing Agents

```python
# test_agent.py
from foundation.agent_factory import BaseAgentFactory
from unittest.mock import Mock

def test_agent_with_mocked_tools():
    """Test agent with mocked tools."""

    mock_tool = Mock(return_value={
        "status": "success",
        "content": [{"text": "mocked result"}]
    })

    agent = BaseAgentFactory.create_agent(
        agent_id="test-agent",
        system_prompt="You are a test agent.",
        tools=[mock_tool],
        session_backend="memory"  # Use in-memory for tests
    )

    result = agent("Test query")

    assert mock_tool.called
    assert "mocked result" in str(result.message)
```

---

## Common Anti-Patterns to Avoid

### ❌ 1. Overloading Agents with Too Many Tools

**Problem**: Models struggle with > 50 tools

**Solution**: Use semantic search (Pattern 3 above)

---

### ❌ 2. Hardcoding Business Logic in System Prompts

**Problem**: Changes require code deployment

**Solution**: Store system prompts in configuration (S3, Parameter Store)

---

### ❌ 3. Ignoring Token Limits

**Problem**: Agents fail when context exceeds model limits

**Solution**: Implement conversation management (sliding window or summarisation)

---

### ❌ 4. No Timeout Configuration

**Problem**: Runaway agents consume resources indefinitely

**Solution**: Always set execution timeouts and max loop counts

```python
from strands.multiagent import GraphBuilder

builder = GraphBuilder()
# ... add nodes and edges ...
builder.set_execution_timeout(300)  # 5 minute timeout
builder.set_max_node_executions(10)  # Max 10 loops
```

---

### ❌ 5. MCP Server Deployment to Lambda

**Problem**: Connection errors, cold starts, pool failures

**Solution**: NEVER deploy MCP servers to Lambda. Use ECS/Fargate or AgentCore Runtime.

---

### ❌ 6. No Cost Monitoring

**Problem**: Unexpected bills from multi-agent token usage

**Solution**: Implement cost tracking hooks (see observability.md)

---

## Key Metrics to Track

| Metric | Threshold | Alert Condition |
|--------|-----------|-----------------|
| **Token Usage** | > 100K tokens/hour | Cost anomaly |
| **Tool Failure Rate** | > 5% | Reliability issue |
| **Agent Loop Count** | > 10 cycles | Potential runaway |
| **Response Latency** | > 30 seconds | Performance degradation |
| **Error Rate** | > 2% | System issue |

---

## Production Deployment Checklist

Before production deployment:

- [ ] Conversation management configured (SlidingWindow or Summarising)
- [ ] Observability hooks implemented
- [ ] Cost tracking enabled
- [ ] OpenTelemetry tracing configured
- [ ] Error handling in all tools
- [ ] Security permissions validated
- [ ] MCP servers deployed to ECS/Fargate (NOT Lambda)
- [ ] Timeout limits set (agents, multi-agent graphs, tools)
- [ ] Session backend configured (DynamoDB for production)
- [ ] CloudWatch dashboards created
