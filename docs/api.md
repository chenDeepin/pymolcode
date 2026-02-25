# API Reference

> Python SDK for pymolcode integration

## Installation

```bash
pip install pymolcode
# or with all extras
pip install "pymolcode[all]"
```

## Core Modules

| Module | Description |
|--------|-------------|
| `python.cli` | CLI entry point |
| `python.agent` | LLM agent orchestration |
| `python.bridge` | JSON-RPC bridge server |
| `python.pymol` | PyMOL integration layer |
| `python.session` | Session management |
| `python.skill` | Skill registry & execution |
| `python.protocol` | JSON-RPC protocol types |

## Bridge Server API

Start the bridge server:

```bash
pymolcode --headless           # Headless JSON-RPC server
pymolcode-bridge               # Alternative entry point
```

### JSON-RPC Methods

| Method | Description |
|--------|-------------|
| `initialize` | Get protocol version & capabilities |
| `shutdown` | Graceful shutdown |
| `bridge.ping` | Health check and protocol metadata |
| `pymol.load_structure` | Load from file/PDB code |
| `pymol.set_representation` | Set representation style |
| `pymol.color_object` | Apply color to selection |
| `pymol.zoom` | Zoom camera |
| `pymol.list_objects` | List loaded objects |
| `pymol.screenshot` | Capture image |
| `agent.chat` | Send message to LLM agent |
| `skill.list` | List available skills |
| `skill.execute` | Execute a skill |
| `session.save` | Save session state |
| `session.load` | Load session |

## TypeScript Client

```typescript
import { BridgeClient } from 'pymolcode-bridge';

const client = new BridgeClient();
await client.initialize();
const result = await client.loadStructure({ 
  source: '/path/to/structure.pdb' 
});
```

## Agent Tools

Built-in PyMOL tools available to the agent:

| Tool | Description |
|------|-------------|
| `pymol_load` | Load structures |
| `pymol_show` | Set representation |
| `pymol_color` | Apply color |
| `pymol_zoom` | Zoom camera |
| `pymol_list` | List objects |
| `pymol_screenshot` | Take screenshot |

## See Also

- [MCP Integration](./mcp.md) - External tool integration
- [PyMOL Plugin](./pymol-plugin-interface.md) - GUI integration
- [Skills Guide](./skills.md) - Custom skill development
