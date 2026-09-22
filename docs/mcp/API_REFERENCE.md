# W-bridge MCP API Reference

This document describes the MCP interface exposed by this service.

- Transport endpoint: `POST /mcp`
- Protocol style: JSON-RPC 2.0 over HTTP
- Protocol version returned by `initialize`: `2024-11-05`
- Server info name/version: `w-bridge-mcp` / `1.0.0`

## Transport Endpoint

### `POST /mcp`

Accepts a JSON-RPC request object.

Base request shape:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {}
}
```

Notes:

- `method` is required and must be a string.
- `params` is optional; when present it must be an object.
- If the body is not valid JSON, HTTP `400` is returned with a JSON-RPC parse error.
- For valid JSON-RPC requests, HTTP `200` is returned (including JSON-RPC errors).
- Notifications (no `id`) may return no body with HTTP `204` for notification-only methods.

## Supported MCP Methods

### 1. `initialize`

Initial handshake. Returns protocol version, capabilities, and server info.

Request:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {}
}
```

Response:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "tools": {}
    },
    "serverInfo": {
      "name": "w-bridge-mcp",
      "version": "1.0.0"
    }
  }
}
```

### 2. `notifications/initialized`

Client notification after initialization.

Behavior:

- If sent as a notification (no `id`): no response body (`204`).
- If sent with an `id`: returns empty result `{}`.

### 3. `initialized`

Alias of `notifications/initialized`.

Behavior:

- If sent as a notification (no `id`): no response body (`204`).
- If sent with an `id`: returns empty result `{}`.

### 4. `ping`

Health-style protocol ping.

Request:

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "ping",
  "params": {}
}
```

Response:

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {}
}
```

### 5. `tools/list`

Returns all registered MCP tools.

Request:

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/list",
  "params": {}
}
```

Response shape:

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "tools": [
      {
        "name": "hello",
        "description": "Say hello to a given name or the world",
        "inputSchema": {
          "type": "object",
          "properties": {
            "name": {
              "type": "string",
              "description": "The name to greet",
              "default": "World"
            }
          }
        }
      }
    ]
  }
}
```

### 6. `tools/call`

Invokes one MCP tool by name.

Request:

```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "tools/call",
  "params": {
    "name": "hello",
    "arguments": {
      "name": "Bob"
    }
  }
}
```

Response shape:

```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Hello, Bob!"
      }
    ],
    "isError": false
  }
}
```

Behavior:

- `params.name` is required and must be a string.
- `params.arguments` is optional; when present it must be an object.
- If the tool name is unknown, the method still returns `result` with `isError: true`.
- Tool exceptions are caught and returned in `result.content[0].text` with `isError: true`.

## Tool Endpoint Coverage

Tool names are exposed dynamically through `tools/list`. They include:

- Company Home tools (attention items and their create/update actions)
- Company Status tools
- Project Overview and Project Status tools
- Project All Hands tools
- Project Knowledge tools
- Room tools (message/action/decision helpers)
- Approval Request tools
- AI Config tools (profiles, settings, MCP servers, tools, skills, and profile assignments)
- Alias names (PascalCase and compatibility aliases)

To stay accurate with code changes, always use `tools/list` at runtime instead of hard-coding tool names.

## JSON-RPC Error Cases

### Parse error (invalid JSON)

HTTP status: `400`

```json
{
  "jsonrpc": "2.0",
  "id": null,
  "error": {
    "code": -32700,
    "message": "Parse error: invalid JSON"
  }
}
```

### Invalid request payload

When request is not an object, `method` is missing/invalid, or `params` is not an object:

- HTTP status: `200`
- JSON-RPC error codes used:
  - `-32600` for invalid request
  - `-32602` for invalid params

### Method not found

Unknown JSON-RPC methods return:

- HTTP status: `200`
- JSON-RPC error code: `-32601`

## Quick cURL Examples

Initialize:

```bash
curl -sS -X POST http://localhost:80/mcp \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'
```

List tools:

```bash
curl -sS -X POST http://localhost:80/mcp \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

Call a tool:

```bash
curl -sS -X POST http://localhost:80/mcp \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"hello","arguments":{"name":"World"}}}'
```
