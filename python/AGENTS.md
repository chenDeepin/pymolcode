# python/ — Core Python Package

**Main package for pymolcode.** Contains CLI, agent orchestration, PyMOL bridge, and skill system.

## Structure

```
python/
├── cli.py              # Main CLI entry (89 lines)
├── agent/              # LLM agent orchestration
│   ├── agent.py        # Agent core logic (241 lines)
│   ├── provider.py     # LLM provider abstraction (291 lines)
│   ├── tools.py        # Tool definitions (322 lines)
│   └── types.py        # Agent type definitions
├── bridge/             # JSON-RPC bridge server
│   ├── server.py       # Bridge server main (249 lines)
│   ├── handlers.py     # Request handlers (349 lines)
│   └── analysis.py     # Analysis utilities
├── pymol/              # PyMOL integration
│   ├── executor.py     # Command executor (319 lines)
│   ├── panel.py        # GUI panel plugin (317 lines)
│   └── runtime.py      # PyMOL runtime wrapper (284 lines)
├── session/            # Session management
│   ├── config.py       # Configuration handling
│   ├── schema.py       # Session schemas
│   └── bootstrap.py    # Session initialization
├── skill/              # Skill system
│   ├── base.py         # Skill base classes
│   ├── builtin.py      # Built-in skills (271 lines)
│   └── registry.py     # Skill registry
├── protocol/           # JSON-RPC protocol
│   ├── framing.py      # Content-Length framing
│   ├── spec.py         # Protocol specification
│   └── errors.py       # Error types
├── persistence/        # State persistence (337 lines)
└── plugins/            # Plugin loader system
```

## Entry Points

| Module | Function | Called By |
|--------|----------|-----------|
| `cli.py` | `main()` | `pymolcode` console script |
| `bridge/server.py` | `main()` | `pymolcode-bridge` console script |
| `pymol/panel.py` | `__init_plugin__()` | PyMOL plugin entry point |

## Key Files

| File | Purpose | Size |
|------|---------|------|
| `bridge/handlers.py` | JSON-RPC method implementations | 349 lines |
| `persistence/persistence.py` | State save/load logic | 337 lines |
| `agent/tools.py` | MCP tool definitions | 322 lines |
| `pymol/executor.py` | PyMOL command execution | 319 lines |
| `pymol/panel.py` | PyQt GUI panel | 317 lines |

## Conventions

- All modules use `from __future__ import annotations`
- Pydantic v2 models for all data structures
- Async functions throughout (no blocking calls)
- Structured logging via `structlog`

## Anti-Patterns

- **NO** direct `pymol.cmd` calls outside `pymol/executor.py`
- **NO** synchronous I/O in async functions
- **NO** hardcoded paths → use `session/config.py` settings
- **NO** untyped dict returns → use Pydantic models

## Testing

```bash
pytest tests/python/           # Unit tests for this package
pytest --cov=python tests/    # Coverage report
```

## Notes

- CLI spawns PyMOL subprocess with plugin injection via temp script
- Bridge uses Content-Length framed JSON-RPC over stdio
- Agent tools integrate with MCP (Model Context Protocol)
