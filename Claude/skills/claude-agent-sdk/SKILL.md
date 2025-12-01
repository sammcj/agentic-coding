---
name: claude-agent-sdk
description: Use when working with Anthropic Claude Agent SDK. Provides architecture guidance, implementation patterns, best practices, and common pitfalls.
# model: inherit
---

# Claude Agent SDK

## Overview

The Claude Agent SDK enables building autonomous AI agents with Claude through a feedback loop architecture. Available for Python (3.10+) and TypeScript (Node 18+).

**Repository:**
- Python: https://github.com/anthropics/claude-agent-sdk-python
- TypeScript: https://github.com/anthropics/claude-agent-sdk-typescript

**Documentation:** https://platform.claude.com/docs/en/agent-sdk/overview

## Installation

```bash
# Python
pip install claude-agent-sdk

# TypeScript
npm install @anthropic-ai/agent-sdk
```

## Core Architecture: Feedback Loop Pattern

Every agent follows this cycle:

1. **Gather Context** → filesystem navigation, subagents, tools
2. **Take Action** → tools, bash, code generation, MCP
3. **Verify Work** → rules-based, visual, LLM-as-judge
4. **Repeat** → iterate until completion

This pattern applies whether you're building a simple script or a complex multi-agent system.

## Execution Mechanisms (Priority Order)

Choose mechanisms based on task requirements:

1. **Custom Tools** → Primary workflows (appear prominently in context)
2. **Bash** → Flexible one-off operations
3. **Code Generation** → Complex, reusable outputs (prefer TypeScript for linting feedback)
4. **MCP** → Pre-built external integrations (Slack, GitHub, databases)

**Rule:** Use tools for repeatable operations, bash for exploration, code generation when you need structured output that can be validated.

## Quick Start Patterns

### Python: Basic Query

```python
from claude_agent_sdk import query

result = await query(
    model="claude-sonnet-4-5",
    system_prompt="You are a helpful coding assistant.",
    user_message="List files in current directory",
    working_dir=".",
)
print(result.final_message)
```

### TypeScript: Session Management

```typescript
import { ClaudeSdkClient } from '@anthropic-ai/agent-sdk';

const client = new ClaudeSdkClient({ apiKey: process.env.ANTHROPIC_API_KEY });

const result = await client.query({
  model: 'claude-sonnet-4-5',
  systemPrompt: 'You are a helpful coding assistant.',
  userMessage: 'List files in current directory',
  workingDir: '.',
});

console.log(result.finalMessage);
```

## Key Components

### 1. Custom Tools (SDK MCP Servers)

In-process tools with no subprocess overhead. Primary building block for agents.

**Python:**
```python
from claude_agent_sdk.mcp import tool, create_sdk_mcp_server

@tool(
    name="calculator",
    description="Perform calculations",
    input_schema={"expression": str}
)
async def calculator(args):
    result = eval(args["expression"])  # Use safe eval in production
    return {"content": [{"type": "text", "text": str(result)}]}

server = create_sdk_mcp_server(name="math", tools=[calculator])
```

**TypeScript:**
```typescript
import { createSdkMcpServer, tool } from '@anthropic-ai/agent-sdk';
import { z } from 'zod';

const calculator = tool({
  name: 'calculator',
  description: 'Perform calculations',
  inputSchema: z.object({ expression: z.string() }),
  async execute({ expression }) {
    const result = eval(expression); // Use safe eval in production
    return { content: [{ type: 'text', text: String(result) }] };
  },
});

const server = createSdkMcpServer({ name: 'math', tools: [calculator] });
```

**Benefits over external MCP:** Better performance, easier debugging, shared memory space, no IPC overhead.

### 2. Hooks (Lifecycle Callbacks)

Intercept and modify agent behaviour at specific points.

**Available hooks:**
- `PreToolUse` → Validate/modify/deny tool calls before execution
- `PostToolUse` → Process/log/modify tool results
- `Stop` → Handle completion events

**Python validation example:**
```python
async def validate_command(input_data, tool_use_id, context):
    if "rm -rf" in input_data["tool_input"].get("command", ""):
        return {
            "hookSpecificOutput": {
                "permissionDecision": "deny",
                "permissionDecisionReason": "Dangerous command blocked"
            }
        }
```

**TypeScript logging example:**
```typescript
const loggingHook = {
  matcher: (input) => input.toolName === 'bash',
  async handler(input, toolUseId, context) {
    console.log(`Executing: ${input.toolInput.command}`);
  }
};
```

### 3. Permission System

Four modes with progressively less restriction:

- `default` → Prompt for each tool use
- `plan` → Agent can read/explore freely, prompts for modifications
- `acceptEdits` → Auto-approve file edits, prompt for bash/destructive ops
- `bypassPermissions` → Fully autonomous (use carefully)

**Dynamic control with `canUseTool`:**
```python
async def permission_callback(tool_name, tool_input, context):
    if tool_name == "bash" and "git push" in tool_input.get("command", ""):
        return False  # Deny
    return True  # Allow
```

### 4. Subagents

Isolated agents with separate context windows and specialised capabilities.

**When to use:**
- Parallel processing of independent tasks
- Context isolation (prevent one task from bloating main context)
- Specialised agents with different tools/models

**Python:**
```python
from claude_agent_sdk import ClaudeAgentOptions

options = ClaudeAgentOptions(
    subagent_definitions={
        "researcher": {
            "tools": ["read", "grep", "glob"],
            "model": "claude-haiku-4",
            "description": "Fast research agent"
        }
    }
)
```

**TypeScript:**
```typescript
const options = {
  subagentDefinitions: {
    researcher: {
      tools: ['read', 'grep', 'glob'],
      model: 'claude-haiku-4',
      description: 'Fast research agent'
    }
  }
};
```

### 5. Context Management

**Agentic Search (Preferred):**
Use bash + filesystem navigation (grep, ls, tail) before reaching for semantic search. Simpler and more reliable.

**Automatic Compaction:**
SDK automatically summarises messages when approaching token limits. Transparent and automatic.

**Folder Structure as Context Engineering:**
Organise files intentionally—directory structure is visible to the agent and influences its understanding.

## Verification Patterns

### Rules-Based (Preferred)
Explicit validation enables self-correction:
```python
# In PostToolUse hook
if tool_name == "write":
    # Run linter on generated file
    lint_result = run_linter(tool_output)
    if lint_result.has_errors:
        return {"continue": True}  # Let agent fix errors
```

### Visual Feedback
For UI tasks, screenshot and re-evaluate:
```python
@tool(name="check_ui", description="Verify UI matches requirements")
async def check_ui(args):
    screenshot = take_screenshot(args["url"])
    # Return screenshot to agent for evaluation
    return {"content": [{"type": "image", "source": screenshot}]}
```

### LLM-as-Judge
Only for fuzzy criteria where rules don't work (higher latency):
```python
judge_result = await secondary_model.evaluate(
    criteria="Does output match tone guidelines?",
    output=agent_output
)
```

## Common Pitfalls & Solutions

### 1. System Prompt Not Loading
**Symptom:** CLAUDE.md ignored, custom prompts not applied
**Solution:** Set `setting_sources=["project"]` or `["user", "project"]`

```python
# Python
options = ClaudeAgentOptions(setting_sources=["project"])

# TypeScript
const options = { settingSources: ['project'] };
```

### 2. Tool Not Available
**Symptom:** "Tool not found" errors
**Solution:** Check MCP tool naming: `mcp__{server_name}__{tool_name}`

### 3. Permission Denied
**Symptom:** Agent can't access directories
**Solution:** Add directories explicitly:

```python
options = ClaudeAgentOptions(add_dirs=["/path/to/data"])
```

### 4. Python Keyword Conflicts
**Symptom:** Syntax errors with `async` or `continue` parameters
**Solution:** Use `async_` and `continue_` (SDK auto-converts)

```python
# Use async_ not async
hook_result = {"async_": True, "continue_": False}
```

### 5. Context Overflow
**Symptom:** Token limit errors
**Solution:** Use subagents for isolation or let automatic compaction handle it

### 6. Tool Execution Failures
**Symptom:** Tools fail silently or with unclear errors
**Solution:** Return structured error messages in tool responses:

```python
return {
    "content": [{
        "type": "text",
        "text": "Error: Invalid input. Expected format: ...",
        "isError": True
    }]
}
```

### 7. External MCP Server Not Connecting
**Symptom:** stdio/SSE MCP servers timeout
**Solution:** Verify server is executable and logs are accessible:

```python
# Check server stderr in context.mcp_server_logs
async def debug_hook(input_data, tool_use_id, context):
    print(context.mcp_server_logs.get("server_name"))
```

## Language-Specific Considerations

### Python vs TypeScript

| Aspect | Python | TypeScript |
|--------|--------|------------|
| **Runtime** | `anyio.run(main)` | Native async/await |
| **Min Version** | Python 3.10+ | Node.js 18+ |
| **Type Safety** | Type hints optional | Strict types with Zod |
| **Hook Fields** | `async_`, `continue_` | `async`, `continue` |
| **CLI** | Bundled (no install) | Separate install needed |
| **Tool Validation** | Dict-based schemas | Zod schemas |

### TypeScript Advantages
- Linting provides extra feedback layer for generated code
- Stronger type safety catches errors earlier
- Better IDE integration

### Python Advantages
- Simpler setup for data science workflows
- Direct integration with ML/data tools
- More concise for scripting tasks

## Decision Frameworks

### When to Use Claude Agent SDK

✅ **Use when:**
- Building autonomous agents that need computer access
- Iterative workflows with verification loops
- Multi-step tasks requiring context and tool use
- Custom tool integration requirements
- Need for permission control and safety

❌ **Don't use when:**
- Simple API calls sufficient (use Messages API)
- No tool/computer access needed
- Purely conversational applications
- Real-time streaming responses critical

### Tool vs Bash vs Code Generation

**Use Custom Tools when:**
- Operation repeats frequently
- Need structured input/output validation
- Want prominent placement in agent context
- Require error handling and retry logic

**Use Bash when:**
- One-off exploration or debugging
- System operations (git, file management)
- Flexible scripting without formal structure

**Use Code Generation when:**
- Need structured, reusable output
- Can validate with linting/compilation
- Building components or modules
- TypeScript preferred for feedback quality

### SDK MCP vs External MCP

**Use SDK MCP (in-process) when:**
- Building custom tools for your agent
- Performance matters (no subprocess overhead)
- Need shared state with main process
- Debugging tool logic

**Use External MCP (stdio/SSE) when:**
- Integrating third-party services
- Tool needs isolation
- Using pre-built MCP servers
- Cross-language tool requirements

## Session Management

### Resuming Sessions

**Python:**
```python
# First run
result1 = await query(user_message="Create a file", working_dir=".")

# Resume with new message
result2 = await query(
    user_message="Now modify it",
    working_dir=".",
    session_id=result1.session_id
)
```

**TypeScript:**
```typescript
// First run
const result1 = await client.query({ userMessage: 'Create a file' });

// Resume
const result2 = await client.query({
  userMessage: 'Now modify it',
  sessionId: result1.sessionId
});
```

### Forking Sessions

Create alternative branches from a point:

```python
# Fork for different approach
result_fork = await query(
    user_message="Try different implementation",
    session_id=original_result.session_id,
    fork_session=True
)
```

## Budget Control

Set USD spending limits:

```python
options = ClaudeAgentOptions(budget={"usd": 5.00})
```

Agent stops when budget exceeded. Useful for cost control in production.

## Testing Patterns

### Mock Tools for Testing

**Python:**
```python
import pytest
from unittest.mock import AsyncMock

@pytest.fixture
def mock_tool():
    return AsyncMock(return_value={
        "content": [{"type": "text", "text": "mocked"}]
    })

async def test_agent(mock_tool):
    server = create_sdk_mcp_server(name="test", tools=[mock_tool])
    # Test with mocked tool
```

**TypeScript:**
```typescript
import { jest } from '@jest/globals';

const mockTool = {
  name: 'test',
  execute: jest.fn().mockResolvedValue({
    content: [{ type: 'text', text: 'mocked' }]
  })
};
```

### Integration Testing

Test with real tools in isolated environment:

```python
import tempfile
import os

async def test_file_operations():
    with tempfile.TemporaryDirectory() as tmpdir:
        result = await query(
            user_message="Create test.txt with content 'hello'",
            working_dir=tmpdir,
            permission_mode="bypassPermissions"
        )
        assert os.path.exists(f"{tmpdir}/test.txt")
```

## Migration from Claude Code SDK

If migrating from the deprecated `claude-code-sdk`:

1. **Package renamed:** `claude-code-sdk` → `claude-agent-sdk`
2. **System prompt not default:** Must explicitly set or enable via `setting_sources`
3. **Type renamed (Python):** `ClaudeCodeOptions` → `ClaudeAgentOptions`
4. **Settings sources not automatic:** Must set `setting_sources=["project"]`

See migration guide: https://platform.claude.com/docs/en/agent-sdk/migration-guide

## Performance Optimisation

1. **Use Haiku for simple tasks** → 5x cheaper, faster for research/exploration
2. **SDK MCP over external** → No subprocess overhead
3. **Batch operations** → Combine file operations when possible
4. **Set turn limits** → Prevent infinite loops (`turn_limit` parameter)
5. **Monitor token usage** → Use budget controls in production

## Security Best Practices

1. **Always validate tool inputs** → Never trust unchecked input
2. **Use permission callbacks** → Deny dangerous operations dynamically
3. **Restrict filesystem access** → Use `add_dirs` to limit scope
4. **Sandbox external MCP servers** → Isolate third-party tools
5. **Set budgets** → Prevent runaway costs
6. **Log all tool uses** → Audit trail via PostToolUse hooks
7. **Never hardcode API keys** → Use environment variables

## Key Principles

1. **Folder structure is context engineering** → Organise intentionally
2. **Rules-based feedback enables self-correction** → Add linting and validation
3. **Start with agentic search** → Bash navigation before semantic search
4. **Tools are primary, bash is secondary** → Use tools for repeatable operations
5. **TypeScript for generated code** → Extra feedback layer improves quality
6. **Verification closes the loop** → Always validate agent work
7. **Use subagents for isolation** → Prevent context bloat and enable parallelism

## Additional Resources

- **API Reference (Python):** https://platform.claude.com/docs/en/agent-sdk/python
- **API Reference (TypeScript):** https://platform.claude.com/docs/en/agent-sdk/typescript
- **Examples Repository:** https://github.com/anthropics/claude-agent-sdk-demos
- **Engineering Blog:** https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk
