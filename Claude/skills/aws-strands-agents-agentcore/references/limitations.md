# Limitations & Considerations

## MCP Server Requirements

### ✅ HTTP Streaming IS Supported

AgentCore fully supports streamable HTTP transport for MCP servers.

**Requirements**:
1. **Transport**: MUST use `streamable-http` mode (NOT `stdio`)
2. **Endpoint**: MUST be at `0.0.0.0:8000/mcp`
3. **Headers**: Must accept `application/json` and `text/event-stream`
4. **Session**: Uses `MCP-Session-Id` header for isolation

**FastMCP Configuration**:
```python
from mcp.server import FastMCP

mcp = FastMCP("My Server")

@mcp.tool()
def my_tool(param: str) -> str:
    return f"Result: {param}"

# ✅ Correct: streamable-http mode
mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)

# ❌ Wrong: stdio mode doesn't work with HTTP
mcp.run(transport="stdio")
```

**Deployment Constraints**:
- **NEVER** deploy to Lambda (stateful, need persistent connections)
- **ALWAYS** deploy to ECS/Fargate or AgentCore Runtime
- Reason: Connection pools, 24/7 availability, stateful resources

---

## Strands Agents SDK Limitations

### 1. Tool Selection at Scale

**Issue**: Models struggle with > 50-100 tools

**Impact**: Wrong tool selection, decreased accuracy

**Solution**: Semantic search for dynamic tool loading (see patterns.md)

**Example**: AWS internal agent with 6,000 tools uses semantic search, not full tool descriptions

---

### 2. Token Context Windows

**Issue**: Long conversations exceed model limits

**Limits**:
- Claude 4.5: 200K tokens (use ~180K max)
- Nova Pro: 300K tokens (use ~250K max)

**Impact**: Truncated history, "forgotten" context

**Solution**: Conversation managers (SlidingWindow or Summarising)

```python
from strands.agent.conversation_manager import SlidingWindowConversationManager

manager = SlidingWindowConversationManager(max_messages=20, min_messages=2)
agent = Agent(conversation_manager=manager)
```

---

### 3. Lambda Streaming

**Issue**: Lambda doesn't support HTTP response streaming

**Impact**: No real-time responses, long wait times

**Solution**: Use AgentCore Runtime for streaming, or implement polling pattern

---

### 4. Multi-Agent Cost

**Issue**: Each agent call consumes tokens

**Multiplier**:
- Agent-as-Tool: 2-3x
- Graph: 3-5x
- Swarm: 5-8x

**Impact**: Unexpected bills at scale

**Solution**: Cost tracking hooks, budget alerts, model selection (Haiku for simple tasks)

---

### 5. Bedrock API Throttling

**Issue**: ConverseStream API has rate limits

**Default**: 50-100 TPS (varies by region/account)

**Impact**: ThrottlingException errors

**Solution**:
1. Request quota increases
2. Exponential backoff retry:

```python
def invoke_agent_with_retry(agent: Agent, query: str, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            return agent(query)
        except ClientError as e:
            if e.response['Error']['Code'] == 'ThrottlingException':
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(wait_time)
            else:
                raise
    raise Exception("Max retries exceeded")
```

---

## AgentCore Platform Limitations

### 1. Runtime Constraints

| Limit               | Value        | Mitigation                        |
|---------------------|--------------|-----------------------------------|
| **Max Runtime**     | 8 hours      | Break tasks into resumable chunks |
| **Session Timeout** | Configurable | Balance resource usage vs UX      |

---

### 2. Gateway Limitations

**API Spec Size**: OpenAPI specs > 2MB cannot be loaded

**Workaround**:
- Split into multiple registrations
- Create facade APIs with only agent-relevant operations

**Tool Discovery**: Large catalogues (> 50 tools) slow initialisation

**Latency**: 50-200ms added for discovery

---

### 3. Browser Tool Issues

**CAPTCHA Blocking**: Cannot automate Google, LinkedIn, banking sites

**Solution**:
- Use official APIs instead of browser automation
- Human-in-the-loop for CAPTCHA sites
- Enterprise API partnerships

**CORS Errors**: Web applications calling AgentCore encounter CORS errors

**Solution**:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
```

---

### 4. Memory Service Limitations

**Scale Limits**: > 100K graph entries degrade performance

**Query Latency**: 50-200ms per retrieval

**Consistency**: Eventual, not transactional

**Best Practice**: Use for high-value data, not transactional state

**Fallback**: Use DynamoDB for critical transactional data

---

## Multi-Agent System Challenges

### 1. Swarm Pattern Unpredictability

**Issue**: Swarm agents make autonomous handoff decisions

**Symptoms**:
- Agents loop unnecessarily
- Handoffs don't follow expected paths
- Difficult to debug

**Mitigation**:
```python
from strands.multiagent import Swarm

swarm = Swarm(
    nodes=[researcher, writer, reviewer],
    entry_point=researcher,
    max_handoffs=10,  # Prevent infinite loops
    execution_timeout=300.0  # 5 minute timeout
)
```

---

### 2. Graph Pattern Complexity

**Issue**: Complex graphs become difficult to maintain

**Best Practice**:
- Keep graphs simple (< 10 nodes)
- Document with diagrams
- Use sub-graphs for complex workflows

---

### 3. Cost Accumulation

**Example**:
| Pattern | LLM Calls | Cost Multiplier |
|---------|-----------|-----------------|
| Single Agent | 1-3 | 1x |
| Agent as Tool | 4-6 | 2-3x |
| Swarm | 10-15 | 5-8x |
| Graph | 5-10 | 3-5x |

**Solution**: Cost monitoring (see observability.md)

---

## Production Deployment Challenges

### 1. Cold Start Latency

**Issue**: 30-60 seconds for first invocation

**Causes**:
- Model loading
- MCP client initialisation
- Dependencies

**Solutions**:
1. **Warm Agent Pools**:
```python
class AgentPool:
    def __init__(self, pool_size: int = 5):
        self.agents = queue.Queue(maxsize=pool_size)
        for _ in range(pool_size):
            agent = BaseAgentFactory.create_agent(...)
            self.agents.put(agent)

    def get_agent(self) -> Agent:
        return self.agents.get()

    def return_agent(self, agent: Agent):
        agent.clear_messages()
        self.agents.put(agent)
```

2. **Lambda Provisioned Concurrency**
3. **AgentCore Runtime** (eliminates cold starts)

---

### 2. State Management Complexity

**Challenges**:
- Concurrent access to shared sessions
- Race conditions
- State corruption

**Solution**: DynamoDB with optimistic locking
```python
from strands.session import DynamoDBSessionManager

session_manager = DynamoDBSessionManager(
    table_name="agent-sessions",
    region_name="us-east-1",
    use_optimistic_locking=True  # Prevent race conditions
)
```

---

### 3. Observability Gaps

**Common Gaps**:
- Why did agent choose specific tool?
- What was the model's reasoning?
- Why did multi-agent handoff occur?

**Solutions**:
1. **Structured Logging** (see observability.md)
2. **Model Reasoning Traces** (for Claude 4):
```python
model = BedrockModel(
    model_id="anthropic.claude-4-20250228-v1:0",
    enable_thinking=True  # Model explains reasoning
)
```
3. **AgentCore Observability** (automatic metrics)

---

## Security Considerations

### 1. Tool Permission Management

**Risk**: Agents with broad permissions, hallucinations cause unintended actions

**Mitigation**: Principle of least privilege

```python
# Define tool-specific IAM roles
@tool
def query_database(sql: str) -> dict:
    # Assume read-only role before executing
    assume_role("arn:aws:iam::account:role/ReadOnlyDatabaseRole")
    # Execute query
```

---

### 2. Data Residency and Compliance

**Consideration**: LLM providers process data in different regions (GDPR, HIPAA)

**Solution**: Enforce regional processing
```python
model = BedrockModel(
    model_id="anthropic.claude-sonnet-4-5-20250929-v1:0",
    region_name="eu-west-1"  # GDPR-compliant region
)

session_manager = DynamoDBSessionManager(
    table_name="agent-sessions",
    region_name="eu-west-1"
)
```

---

## Integration Challenges

### 1. Legacy System Integration

**Common Issues**:
- APIs lack semantic descriptions
- Complex multi-step authentication
- Non-standard data formats

**Pattern**: Facade for legacy APIs
```python
@tool
def get_customer_data(customer_email: str) -> dict:
    """
    Get customer data from legacy CRM.

    Internally handles:
    - Session token acquisition
    - Multi-step API calls
    - Data format transformation
    """
    session = legacy_crm.authenticate()
    customer = legacy_crm.find_customer(session, email=customer_email)
    orders = legacy_crm.get_orders(session, customer.id)

    return {
        "status": "success",
        "content": [{"text": json.dumps({
            "name": customer.name,
            "orders": [order.to_dict() for order in orders]
        })}]
    }
```

---

### 2. Real-Time Requirements

**Limitation**: Agents have inherent latency (1-10 seconds)

**Not Suitable For**:
- High-frequency trading
- Real-time control systems
- Sub-second response requirements

**Suitable For**:
- Customer support
- Content generation
- Data analysis
- Workflow automation

---

## Summary: Must Address vs Nice to Have

### Must Address

1. **Tool Discovery at Scale**: Semantic search for > 50 tools
2. **Cost Monitoring**: Cost tracking from day one
3. **Observability**: Logging, metrics, tracing
4. **Security**: Tool-level permissions, human-in-the-loop
5. **MCP Servers**: Deploy in streamable-http mode, NOT Lambda

### Nice to Have

1. **Warm Agent Pools**: Reduce cold starts
2. **Response Caching**: Avoid duplicate LLM calls
3. **Multi-Region**: Deploy close to users

### Can Defer

1. **Advanced Multi-Agent**: Start single agents first
2. **Custom Models**: Use Bedrock initially
3. **Complex Graphs**: Begin with linear workflows
