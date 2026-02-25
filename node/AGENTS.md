# node/ — TypeScript Bridge Client

**TypeScript client for Python bridge server.** Communicates via JSON-RPC over stdio.

## Structure

```
node/
├── src/
│   ├── index.ts           # Public exports
│   ├── bridge-client.ts   # Main client class (470 lines)
│   ├── types.ts           # TypeScript interfaces
│   ├── config.ts          # Client configuration
│   └── tools/             # Tool definitions
│       └── registry.ts    # PyMOL tool registry
├── dist/                  # Compiled JavaScript
├── package.json           # npm config
└── tsconfig.json          # TypeScript config
```

## Exports

```typescript
// Client classes
export { BridgeClient, BridgeRpcError, BridgeTimeoutError, BridgeCancellationError }

// Types
export type { JSONRPCRequest, JSONRPCResponse, BridgeClientOptions, ... }

// Tools
export { Tool, createTool, registerPyMOLTools, PYMOL_TOOLS }
```

## Key Files

| File | Purpose |
|------|---------|
| `bridge-client.ts` | JSON-RPC client with timeout handling |
| `types.ts` | Request/response interfaces |
| `tools/registry.ts` | MCP tool schema definitions |

## Protocol

- **Transport**: stdio (stdin/stdout)
- **Framing**: Content-Length header + JSON body
- **Format**: JSON-RPC 2.0

## Usage

```typescript
import { BridgeClient } from 'pymolcode-bridge';

const client = new BridgeClient();
await client.initialize();
const result = await client.loadStructure({ source: '/path/to/file.pdb' });
```

## Build

```bash
npm install        # Install dependencies
npm run build      # Compile TypeScript to dist/
```

## Notes

- Client expects Python bridge server as subprocess
- Timeout policies per method type (configurable)
- Tool schemas mirror Python MCP tool definitions
