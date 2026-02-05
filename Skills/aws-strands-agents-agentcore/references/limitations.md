# Limitations & Considerations

### 1. Tool Selection at Scale

**Issue**: Models struggle with > 50-100 tools

**Impact**: Wrong tool selection, decreased accuracy

**Solution**: Semantic search for dynamic tool loading (see patterns.md)

**Example**: AWS internal agent with 6,000 tools uses semantic search

---

### 2. Token Context Windows

**Issue**: Long conversations exceed model limits

**Limits**:
- Claude 4.5: 200K tokens (use ~180K max)
- Nova Pro: 300K tokens (use ~250K max)

**Impact**: Truncated history, "forgotten" context

**Solution**:
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

**Solution**: Request quota increases, exponential backoff retry:

```python
def invoke_with_retry(agent: Agent, query: str, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            return agent(query)
        except ClientError as e:
            if e.response['Error']['Code'] == 'ThrottlingException':
                wait = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(wait)
            else:
                raise
    raise Exception("Max retries exceeded")
```

---

## AgentCore Platform Limitations

### Runtime Constraints

| Limit               | Value        | Mitigation                        |
|---------------------|--------------|-----------------------------------|
| **Max Runtime**     | 8 hours      | Break tasks into resumable chunks |
| **Session Timeout** | Configurable | Balance resource usage vs UX      |

---

### Gateway Limitations

**API Spec Size**: OpenAPI specs > 2MB cannot be loaded

**Workaround**: Split into multiple registrations or create facade APIs with only agent-relevant operations

**Tool Discovery**: Large catalogues (> 50 tools) slow initialisation

**Latency**: 50-200ms added for discovery

---

### Browser Tool Issues

**CAPTCHA Blocking**: Cannot automate Google, LinkedIn, banking sites

**Solution**: Use official APIs instead, human-in-the-loop for CAPTCHA sites, or enterprise API partnerships

**CORS Errors**: Web applications calling AgentCore encounter CORS errors

**Solution**:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
```

---

### Memory Service Limitations

**Scale Limits**: > 100K graph entries degrade performance

**Query Latency**: 50-200ms per retrieval

**Consistency**: Eventual, not transactional

**Best Practice**: Use for high-value data, not transactional state. Use DynamoDB for critical transactional data.

---

## Multi-Agent System Challenges

### Swarm Pattern Unpredictability

**Issue**: Swarm agents make autonomous handoff decisions

**Symptoms**: Agents loop unnecessarily, handoffs don't follow expected paths

**Mitigation**:
```python
from strands.multiagent import Swarm

swarm = Swarm(
    nodes=[researcher, writer, reviewer],
    entry_point=researcher,
    max_handoffs=10,  # Prevent infinite loops
    execution_timeout=300.0
)
```

---

### Graph Pattern Complexity

**Issue**: Complex graphs become difficult to maintain

**Best Practice**: Keep graphs simple (< 10 nodes), document with diagrams, use sub-graphs for complex workflows

---

### Cost Accumulation

| Pattern | LLM Calls | Cost Multiplier |
|---------|-----------|-----------------|
| Single Agent | 1-3 | 1x |
| Agent as Tool | 4-6 | 2-3x |
| Swarm | 10-15 | 5-8x |
| Graph | 5-10 | 3-5x |

---

## Production Deployment Challenges

### Cold Start Latency

**Issue**: 30-60 seconds for first invocation

**Causes**: Model loading, MCP client initialisation, dependencies

**Solutions**:

1. **Warm Agent Pools**:
```python
class AgentPool:
    def __init__(self, pool_size: int = 5):
        self.agents = queue.Queue(maxsize=pool_size)
        for _ in range(pool_size):
            self.agents.put(BaseAgentFactory.create_agent(...))

    def get_agent(self) -> Agent:
        return self.agents.get()

    def return_agent(self, agent: Agent):
        agent.clear_messages()
        self.agents.put(agent)
```

2. Lambda Provisioned Concurrency
3. AgentCore Runtime (eliminates cold starts)

---

### State Management Complexity

**Challenges**: Concurrent access to shared sessions, race conditions, state corruption

**Solution**: DynamoDB with optimistic locking
```python
from strands.session import DynamoDBSessionManager

session_manager = DynamoDBSessionManager(
    table_name="agent-sessions",
    region_name="us-east-1",
    use_optimistic_locking=True
)
```

---

### Observability Gaps

**Common Gaps**: Why did agent choose specific tool? What was the model's reasoning? Why did multi-agent handoff occur?

**Solutions**:
1. Structured Logging (see observability.md)
2. **Model Reasoning Traces** (Claude 4):
```python
model = BedrockModel(
    model_id="anthropic.claude-4-20250228-v1:0",
    enable_thinking=True
)
```
3. AgentCore Observability (automatic metrics)

---

## Security Considerations

### Tool Permission Management

**Risk**: Agents with broad permissions, hallucinations cause unintended actions

**Mitigation**: Principle of least privilege

```python
@tool
def query_database(sql: str) -> dict:
    # Assume read-only role before executing
    assume_role("arn:aws:iam::account:role/ReadOnlyDatabaseRole")
    # Execute query
```

---

### Data Residency and Compliance

**Consideration**: LLM providers process data in different regions (GDPR, HIPAA)

**Solution**: Enforce regional processing
```python
model = BedrockModel(
    model_id="anthropic.claude-sonnet-4-5-20250929-v1:0",
    region_name="eu-west-1"  # GDPR-compliant
)

session_manager = DynamoDBSessionManager(
    table_name="agent-sessions",
    region_name="eu-west-1"
)
```

---

## Integration Challenges

### Legacy System Integration

**Common Issues**: APIs lack semantic descriptions, complex multi-step authentication, non-standard data formats

**Pattern**: Facade for legacy APIs
```python
@tool
def get_customer_data(customer_email: str) -> dict:
    """
    Get customer data from legacy CRM.

    Internally handles session tokens, multi-step API calls, and data transformation.
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

### Real-Time Requirements

**Limitation**: Agents have inherent latency (1-10 seconds)

**Not Suitable For**: High-frequency trading, real-time control systems, sub-second response requirements

**Suitable For**: Customer support, content generation, data analysis, workflow automation

---

## Summary: Priorities

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
