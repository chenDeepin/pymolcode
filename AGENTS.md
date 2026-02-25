# pymolcode

**LLM-Enhanced Molecular Visualization Platform for Drug Discovery**

> Built using PyMOL™ technology. PyMOL is a trademark of Schrödinger, LLC.

## Stack

Python 3.11+ | TypeScript | Pydantic v2 | MCP | LiteLLM | RDKit | PyMOL

## Structure

```
pymolcode/
├── python/              # Main Python package (not src/pymolcode)
│   ├── cli.py          # CLI entry point
│   ├── agent/          # LLM agent orchestration
│   ├── bridge/         # JSON-RPC bridge server
│   ├── pymol/          # PyMOL integration (executor, panel, runtime)
│   ├── session/        # Session/config management
│   ├── skill/          # Skill registry & builtins
│   ├── protocol/       # JSON-RPC framing & spec
│   ├── persistence/    # State persistence
│   └── plugins/        # Plugin loader
├── node/               # TypeScript bridge client
│   └── src/            # bridge-client.ts, types, tools
├── launcher/           # pymolcode-launcher orchestrator
├── tests/              # pytest tests (python/, integration/, unit/)
├── docs/               # Architecture & API docs
└── skills/             # Reference skills (not project code)
```

## Entry Points

| Script | Module | Purpose |
|--------|--------|---------|
| `pymolcode` | `python.cli:main` | Main CLI (PyMOL GUI + panel) |
| `pymolcode-bridge` | `python.bridge.server:main` | Headless JSON-RPC server |
| `pymolcode-launcher` | `launcher.pymolcode_launcher:main` | Bridge + node orchestrator |
| PyMOL plugin | `python.pymol.panel:__init_plugin__` | GUI panel |

**Note**: `pymolcode-tui` documented but not yet implemented.

## Commands

```bash
# Dev
uv pip install -e ".[dev]"    # Install dev deps
pytest tests/                  # Run tests
pytest --cov=python           # With coverage

# Lint/Format
ruff check python/            # Lint
ruff format python/           # Format
mypy python/                  # Type check

# Run
pymolcode                     # Launch PyMOL + panel
pymolcode --headless          # Bridge server only
```

## Conventions

| Rule | Setting |
|------|---------|
| Line length | 100 chars |
| Type checking | `strict = true` |
| Pydantic models | All data structures |
| Async | `asyncio` / `anyio` throughout |
| Linting | ruff (E, W, F, I, B, C4, UP, ARG, SIM) |

## Key Patterns

**Hexagonal Architecture**: CLI/Panel → ApplicationService → Domain → Adapters

**MCP-First**: External tools via Model Context Protocol

**Bridge Pattern**: Python bridge server ↔ TypeScript client (JSON-RPC over stdio)

**Type Safety**: All LLM actions validated via Pydantic schemas

## Where to Look

| Task | Location |
|------|----------|
| CLI implementation | `python/cli.py` |
| Agent orchestration | `python/agent/` |
| PyMOL integration | `python/pymol/executor.py`, `runtime.py` |
| JSON-RPC handlers | `python/bridge/handlers.py` |
| Session/config | `python/session/` |
| Skill registry | `python/skill/` |
| Protocol framing | `python/protocol/framing.py` |
| TS bridge client | `node/src/bridge-client.ts` |
| PyMOL GUI panel | `python/pymol/panel.py` |

## Anti-Patterns

- **NO** `as any` / type suppression (strict typing mandatory)
- **NO** direct PyMOL calls from UI → use ApplicationService
- **NO** untyped tool args → all MCP tools need Pydantic schemas
- **NO** blocking event loop → async throughout
- **NO** hardcoded paths → use `AppConfig.artifacts_dir`

## Dependencies (Key)

| Package | Purpose |
|---------|---------|
| `mcp` | Model Context Protocol SDK |
| `litellm` | Multi-provider LLM abstraction |
| `pydantic` | Data validation |
| `rdkit` | Cheminformatics |
| `structlog` | Structured logging |
| `textual` | TUI framework (planned) |

## Code Map

| Symbol | Type | Location | Role |
|--------|------|----------|------|
| `Agent` | Class | `python/agent/agent.py:40` | LLM agent orchestration |
| `BridgeServer` | Class | `python/bridge/server.py:69` | JSON-RPC server |
| `BridgeClient` | Class | `node/src/bridge-client.ts:108` | TS bridge client |
| `main` | Func | `python/cli.py:31` | CLI entry point |
| `StdoutGuard` | Class | `python/bridge/server.py:32` | Framed output control |

## Notes

- Build backend: Hatchling (not setuptools)
- PyMOL integration via adapter pattern (not embedding source)
- MCP resources expose PyMOL state: `scene://current`, `object://{name}/metadata`
- Skills defined in YAML with workflow graphs (precheck → run → validate → summarize → persist)
- Safety policies: read-only by default, write needs confirmation, destructive needs explicit flag
- CI: `.github/workflows/ci.yml` runs pytest with Python 3.11
- Tests: `tests/python/` (unit), `tests/integration/` (integration); markers: `skip_pymol`, `requires_py311`
