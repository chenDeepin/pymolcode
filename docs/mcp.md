# MCP Integration

> Model Context Protocol integration for pymolcode

## Overview

pymolcode supports MCP (Model Context Protocol) for standardized tool interoperability with external services.

## Current Status

The MCP integration is **in development**. The bridge server provides the foundation for MCP compatibility.

## Running MCP Server

```bash
# Start pymolcode bridge (JSON-RPC over stdio)
pymolcode-bridge

# The bridge speaks JSON-RPC protocol which can be adapted to MCP
```

## Architecture

```
┌─────────────────────────────────────────────────┐
│                   pymolcode                      │
├─────────────────────────────────────────────────┤
│              Bridge Server (JSON-RPC)           │
├─────────────────────────────────────────────────┤
│  Built-in Tools                                 │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐    │
│  │ pymol_load│ │pymol_show │ │pymol_zoom │    │
│  └───────────┘ └───────────┘ └───────────┘    │
├─────────────────────────────────────────────────┤
│  External MCP Servers (Planned)                 │
│  ┌───────────┐ ┌───────────┐                   │
│  │ DrugCLIP  │ │  RDKit    │                   │
│  └───────────┘ └───────────┘                   │
└─────────────────────────────────────────────────┘
```

## Configuration (Planned)

Future support for external MCP servers:

```yaml
# ~/.config/pymolcode/config.yaml (planned)
mcp:
  servers:
    - name: drugclip
      command: python -m drugclip_mcp_server
    - name: rdkit
      command: python -m rdkit_mcp_server
```

## MCP Resources (Planned)

pymolcode will expose PyMOL state as MCP resources:

| Resource URI | Description |
|--------------|-------------|
| `scene://current` | Current scene state |
| `object://{name}/metadata` | Object metadata |
| `session://state` | Session state |

## See Also

- [Model Context Protocol](https://modelcontextprotocol.io) - Official specification
- [External MCP Servers](./external-mcp-servers.md) - Planned integration guides
- [API Reference](./api.md) - JSON-RPC API documentation
