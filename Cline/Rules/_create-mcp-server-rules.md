# MCP Server Development Guidelines

## Overview

This document provides comprehensive guidelines for AI coding agents to correctly build Model Context Protocol (MCP) servers following the official specifications and best practices.

## Core Principles

1. **Transport Selection**: Default to SSE (Server-Sent Events) transport over stdio for better debugging and flexibility
2. **Security First**: Never log to stdout/stderr in stdio servers, implement proper auth for HTTP transports
3. **Specification Compliance**: Strictly follow the MCP specification for message formats and lifecycle
4. **Error Handling**: Use proper MCP error responses, not transport-level errors

Although there is no official Golang SDK, Go makes an excellent choice for building MCP servers due to its performance and concurrency model. The [mcp-go](https://github.com/mark3labs/mcp-go/) package provides a solid foundation for building MCP servers in Go.

## Transport Implementation

### SSE Transport (Recommended)

```typescript
// TypeScript Example
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";

const server = new Server({
  name: "my-server",
  version: "1.0.0"
}, {
  capabilities: {
    tools: {},
    resources: {},
    prompts: {}
  }
});

const transport = new SSEServerTransport("/message", response);
await server.connect(transport);
```

```python
# Python Example
from mcp.server import Server
from mcp.server.sse import SseServerTransport

server = Server("my-server")

async with SseServerTransport().connect_sse(scope, receive, send) as transport:
    await server.run(transport)
```

### Stdio Transport

**⚠️ CRITICAL**: When using stdio transport:
- **NEVER** use `console.log()`, `print()`, or write to stdout
- **NEVER** use `console.error()` or write to stderr for debugging
- Use the MCP logging system or file-based logging only

```typescript
// TypeScript - Stdio
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

const transport = new StdioServerTransport();
await server.connect(transport);
```

## Implementation Guidelines

### 1. Server Initialization

Always implement proper capability declaration:

```typescript
const server = new Server({
  name: "server-name",
  version: "1.0.0"
}, {
  capabilities: {
    tools: {},      // Only if implementing tools
    resources: {    // Only if implementing resources
      subscribe: true,
      listChanged: true
    },
    prompts: {      // Only if implementing prompts
      listChanged: true
    },
    logging: {}     // Enable structured logging
  }
});
```

### 2. Tool Implementation

Tools must follow this pattern:

```typescript
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    // Tool implementation
    return {
      content: [
        {
          type: "text",
          text: "Result"
        }
      ]
    };
  } catch (error) {
    // Return tool error, not protocol error
    return {
      content: [
        {
          type: "text",
          text: `Error: ${error.message}`
        }
      ],
      isError: true
    };
  }
});
```

### 3. Resource Implementation

Resources require proper URI handling:

```typescript
server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  const { uri } = request.params;

  // Validate URI format
  if (!uri.startsWith("myscheme://")) {
    throw new Error("Invalid URI scheme");
  }

  return {
    contents: [
      {
        uri,
        mimeType: "text/plain",
        text: "Content"
      }
    ]
  };
});
```

### 4. Error Handling

Use proper JSON-RPC error codes:

```typescript
// Common error codes
const ErrorCodes = {
  ParseError: -32700,
  InvalidRequest: -32600,
  MethodNotFound: -32601,
  InvalidParams: -32602,
  InternalError: -32603
};

// Resource not found (MCP specific)
const ResourceNotFound = -32002;
```

### 5. Logging Best Practices

For stdio servers, use MCP's logging system:

```typescript
server.sendLoggingMessage({
  level: "info",
  data: "Log message"
});
```

For SSE servers, you can use console methods safely.

## Security Requirements

### HTTP/SSE Servers

1. **Validate Origin Headers**: Prevent DNS rebinding attacks
   ```typescript
   if (request.headers.origin && !isAllowedOrigin(request.headers.origin)) {
     return new Response("Forbidden", { status: 403 });
   }
   ```

2. **Bind to Localhost**: For local servers
   ```typescript
   server.listen(3000, '127.0.0.1'); // NOT 0.0.0.0
   ```

3. **Implement Authentication**: For production servers
   ```typescript
   // Follow OAuth 2.1 specification for HTTP transports
   ```

### Input Validation

Always validate:
- Tool arguments against schemas
- Resource URIs for path traversal
- Request parameters for injection attacks

## Language-Specific Guidelines

### TypeScript/Node.js

```json
{
  "name": "mcp-server-example",
  "version": "1.0.0",
  "type": "module",
  "dependencies": {
    "@modelcontextprotocol/sdk": "latest"
  }
}
```

### Python

```python
# Use FastMCP for simpler implementation
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("server-name")

@mcp.tool()
async def my_tool(param: str) -> str:
    """Tool description"""
    return f"Result: {param}"
```

### Go (using mcp-go)

```go
import "github.com/mark3labs/mcp-go/server"

s := server.NewServer("server-name", "1.0.0")
s.AddTool(server.Tool{
    Name: "my-tool",
    Description: "Tool description",
    InputSchema: schema,
    Handler: toolHandler,
})
```

## Common Pitfalls to Avoid

1. **Don't use console/print in stdio servers** - This breaks the protocol
2. **Don't return HTML/non-JSON from SSE endpoints** - Must return proper SSE format
3. **Don't mix transport types** - Choose one and stick with it
4. **Don't expose sensitive data** - Implement proper access controls
5. **Don't ignore capability negotiation** - Respect client capabilities
6. **Don't use synchronous operations** - MCP is async by design
7. **Don't cache indefinitely** - Implement proper cache invalidation

## Testing Checklist

- [ ] Server initializes without errors
- [ ] Tools execute with valid inputs
- [ ] Tools handle errors gracefully
- [ ] Resources return correct MIME types
- [ ] Subscriptions work (if implemented)
- [ ] No stdout/stderr output in stdio mode
- [ ] Origin validation works (SSE)
- [ ] Authentication works (if required)
- [ ] Works with MCP Inspector tool

## Configuration Examples

### Claude Desktop (stdio)

```json
{
  "mcpServers": {
    "my-server": {
      "command": "node",
      "args": ["/absolute/path/to/server.js"]
    }
  }
}
```

### HTTP/SSE Client

```typescript
const transport = new SSEClientTransport(
  new URL("http://localhost:3000/sse")
);
await client.connect(transport);
```



## Environment Configuration

### Secrets Management

```typescript
// NEVER hardcode secrets
// BAD
const API_KEY = "sk-abc123...";

// GOOD - Use environment variables
const API_KEY = process.env.API_KEY;
if (!API_KEY) {
  throw new Error("API_KEY environment variable is required");
}

// For Claude Desktop users, use env in config:
{
  "mcpServers": {
    "my-server": {
      "command": "node",
      "args": ["server.js"],
      "env": {
        "API_KEY": "sk-abc123..."
      }
    }
  }
}
```

### Configuration Patterns

```typescript
// Support multiple configuration sources
const config = {
  apiKey: process.env.API_KEY,
  database: process.env.DATABASE_URL || 'sqlite:./local.db',
  maxRetries: parseInt(process.env.MAX_RETRIES || '3'),
  debug: process.env.DEBUG === 'true'
};
```

## Performance & Scalability

### Pagination Implementation

```typescript
server.setRequestHandler(ListResourcesRequestSchema, async (request) => {
  const { cursor } = request.params;
  const pageSize = 100;

  const { resources, nextCursor } = await getResourcesPage(cursor, pageSize);

  return {
    resources,
    nextCursor // Include only if more results exist
  };
});
```

### Long-Running Operations

```typescript
// Use progress notifications
server.setRequestHandler(CallToolRequestSchema, async (request, { progressToken }) => {
  if (progressToken) {
    // Send progress updates
    await server.sendProgress({
      progressToken,
      progress: 0,
      total: 100,
      message: "Starting operation..."
    });
  }

  // Perform operation with progress updates
  for (let i = 0; i < 100; i += 10) {
    await doWork();
    if (progressToken) {
      await server.sendProgress({
        progressToken,
        progress: i,
        total: 100,
        message: `Processing... ${i}%`
      });
    }
  }

  return { content: [{ type: "text", text: "Complete!" }] };
});
```

### Resource Caching

```typescript
class CachedResourceProvider {
  private cache = new Map<string, { data: any, timestamp: number }>();
  private ttl = 5 * 60 * 1000; // 5 minutes

  async getResource(uri: string) {
    const cached = this.cache.get(uri);
    if (cached && Date.now() - cached.timestamp < this.ttl) {
      return cached.data;
    }

    const data = await fetchResource(uri);
    this.cache.set(uri, { data, timestamp: Date.now() });
    return data;
  }
}
```

## Testing Strategies

### Unit Testing Example

```typescript
// test/tools.test.ts
import { describe, it, expect } from 'vitest';
import { createTestServer } from './helpers';

describe('Calculator Tool', () => {
  it('should add numbers correctly', async () => {
    const server = createTestServer();
    const result = await server.callTool('add', { a: 2, b: 3 });

    expect(result.content[0].text).toBe('5');
    expect(result.isError).toBe(false);
  });

  it('should handle invalid input', async () => {
    const server = createTestServer();
    const result = await server.callTool('add', { a: 'invalid' });

    expect(result.isError).toBe(true);
    expect(result.content[0].text).toContain('Error');
  });
});
```

### Integration Testing

```python
# test_integration.py
import pytest
from mcp.client import ClientSession
from mcp.client.stdio import stdio_client

@pytest.mark.asyncio
async def test_server_integration():
    async with stdio_client(
        ServerParameters(command="python", args=["server.py"])
    ) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize
            await session.initialize()

            # Test tool
            result = await session.call_tool("my-tool", {"param": "value"})
            assert result.content[0].text == "Expected result"
```

## Resource Design Patterns

### URI Scheme Design

```typescript
// Good URI scheme design
const URI_PATTERNS = {
  // Hierarchical resources
  database: 'db://database/table/record',

  // Query parameters for filters
  search: 'search://products?category=electronics&limit=10',

  // Versioned APIs
  api: 'api://v1/users/123',

  // Composite resources
  dashboard: 'dashboard://metrics/sales/2024-01'
};

// URI validation
function validateUri(uri: string): boolean {
  const url = new URL(uri);
  return ALLOWED_SCHEMES.includes(url.protocol.slice(0, -1));
}
```

### Binary Resource Handling

```typescript
server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  const { uri } = request.params;

  if (isBinaryResource(uri)) {
    const buffer = await readBinaryFile(uri);
    return {
      contents: [{
        uri,
        mimeType: getMimeType(uri),
        blob: buffer.toString('base64')
      }]
    };
  }

  // Text resource handling...
});
```

## Production Deployment

### Docker Configuration

```dockerfile
FROM node:20-slim
WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy server code
COPY . .

# Don't run as root
USER node

# For SSE servers
EXPOSE 3000
CMD ["node", "server.js"]

# For stdio servers
CMD ["node", "stdio-server.js"]
```

### Health Checks

```typescript
// For SSE servers
app.get('/health', (req, res) => {
  const health = {
    status: 'ok',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    memory: process.memoryUsage(),
    version: packageJson.version
  };

  res.json(health);
});
```

### Process Management

```yaml
# ecosystem.config.js for PM2
module.exports = {
  apps: [{
    name: 'mcp-server',
    script: './server.js',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'production',
      PORT: 3000
    },
    error_file: 'logs/err.log',
    out_file: 'logs/out.log',
    log_file: 'logs/combined.log',
    time: true
  }]
};
```

## Monitoring & Observability

### Structured Logging

```typescript
class Logger {
  log(level: string, message: string, metadata?: any) {
    const entry = {
      timestamp: new Date().toISOString(),
      level,
      message,
      ...metadata,
      // Add trace ID for request correlation
      traceId: AsyncLocalStorage.getStore()?.traceId
    };

    // For SSE servers - can use console
    if (transport === 'sse') {
      console.log(JSON.stringify(entry));
    } else {
      // For stdio - write to file
      fs.appendFileSync('/tmp/mcp-server.log',
        JSON.stringify(entry) + '\n'
      );
    }
  }
}
```

### Metrics Collection

```typescript
// Prometheus-style metrics
class Metrics {
  private counters = new Map<string, number>();
  private histograms = new Map<string, number[]>();

  incrementCounter(name: string, labels?: Record<string, string>) {
    const key = this.getKey(name, labels);
    this.counters.set(key, (this.counters.get(key) || 0) + 1);
  }

  recordHistogram(name: string, value: number, labels?: Record<string, string>) {
    const key = this.getKey(name, labels);
    const values = this.histograms.get(key) || [];
    values.push(value);
    this.histograms.set(key, values);
  }

  // Expose metrics endpoint for SSE servers
  getMetrics() {
    return {
      counters: Object.fromEntries(this.counters),
      histograms: Object.fromEntries(
        Array.from(this.histograms.entries()).map(([k, v]) => [
          k,
          { count: v.length, sum: v.reduce((a, b) => a + b, 0) }
        ])
      )
    };
  }
}
```

## Schema Validation Examples

### Tool Input Schema

```typescript
// Use JSON Schema for complex tool inputs
const searchToolSchema = {
  type: "object",
  properties: {
    query: {
      type: "string",
      description: "Search query",
      minLength: 1,
      maxLength: 200
    },
    filters: {
      type: "object",
      properties: {
        category: {
          type: "string",
          enum: ["electronics", "books", "clothing"]
        },
        priceRange: {
          type: "object",
          properties: {
            min: { type: "number", minimum: 0 },
            max: { type: "number", minimum: 0 }
          }
        }
      }
    },
    limit: {
      type: "integer",
      minimum: 1,
      maximum: 100,
      default: 10
    }
  },
  required: ["query"]
};
```

## Debugging Tips

1. **For stdio servers**:
   - Write logs to a file, ensuring the log level is configurable
   - Use MCP Inspector with file path argument

2. **For SSE servers**:
   - Use browser DevTools Network tab
   - Check SSE event format
   - Validate CORS headers

3. **General debugging**:
   - Start with minimal implementation
   - Offer to test with MCP Inspector first
   - Add features incrementally

### Common Issues and Solutions

## Stdio Server Not Responding
- Check: No console.log/print statements
- Check: Server process is running
- Check: Absolute paths in configuration
- Debug: Write logs to file with timestamps

## SSE Connection Drops
- Check: CORS headers are correct
- Check: Keep-alive is configured
- Check: No proxy timeout issues
- Debug: Monitor network tab in browser

## Tool Execution Timeouts
- Check: Implement progress notifications
- Check: Set appropriate timeout values
- Check: Handle cancellation requests
- Debug: Add timing logs

## Memory Leaks
- Check: Clean up event listeners
- Check: Clear caches periodically
- Check: Close database connections
- Debug: Monitor memory usage over time

## References

- [MCP Specification](https://modelcontextprotocol.io/specification)
- [MCP TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [mcp-go Package](https://github.com/mark3labs/mcp-go/)
- [MCP Inspector](https://modelcontextprotocol.io/docs/tools/inspector)
