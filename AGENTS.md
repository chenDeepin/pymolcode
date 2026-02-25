# pymolcode

**LLM-Enhanced Molecular Visualization Platform for Drug Discovery**

> Built using PyMOL™ technology. PyMOL is a trademark of Schrödinger, LLC.

## Stack

Python 3.11+ | TypeScript | Pydantic v2 | MCP | LiteLLM | RDKit | PyMOL

## Structure

```
pymolcode/
├── python/              # Main Python package (not src/pymolcode)
│   ├── cli.py          # CLI entry point (auth, ultrawork commands)
│   ├── agent/          # LLM agent orchestration
│   │   ├── agent.py    # Agent core (with memory integration)
│   │   ├── tools.py    # Tool definitions (includes memory tools)
│   │   ├── provider.py # LLM provider abstraction (OAuth + API keys)
│   │   ├── orchestrator.py  # Hephaestus orchestrator
│   │   ├── background.py    # Background agent manager
│   │   └── types.py    # Agent type definitions
│   ├── auth/           # OAuth authentication (NEW)
│   │   ├── oauth.py    # OAuth 2.0 flows (PKCE, device code)
│   │   ├── token_store.py   # Secure token storage
│   │   └── providers.py     # Provider OAuth configs
│   ├── memory/         # Memory system (YAML-based persistence)
│   ├── bridge/         # JSON-RPC bridge server
│   ├── pymol/          # PyMOL integration (executor, panel, runtime)
│   ├── session/        # Session/config management
│   ├── skill/          # Skill registry & builtins
│   │   └── bridge/     # Multi-source skill discovery (NEW)
│   │       ├── discovery.py   # Skill discovery engine
│   │       └── omo_adapter.py # Oh-My-OpenCode adapter
│   ├── protocol/       # JSON-RPC framing & spec
│   ├── persistence/    # State persistence
│   ├── workflow/       # Agentic workflows (NEW)
│   │   └── ultrawork.py    # One-command workflow execution
│   ├── validation/     # Validation utilities (NEW)
│   │   └── hash_edit.py    # Hash-anchored command validation
│   └── plugins/        # Plugin loader
├── node/               # TypeScript bridge client
│   └── src/            # bridge-client.ts, types, tools
├── launcher/           # pymolcode-launcher orchestrator
├── tests/              # pytest tests (python/, integration/, unit/)
├── docs/               # Architecture & API docs
├── memory/             # Memory YAML files (root level)
│   ├── memory.yaml     # Main memory (preferences, knowledge)
│   ├── lessons.yaml    # Lessons learned from mistakes
│   ├── now.yaml        # Active todos and priorities
│   └── YYYY-MM-DD.yaml # Daily session notes
├── skills/             # Reference skills (10 categories: 00-09)
├── .hephaestus/        # Hephaestus evidence and plans
└── SOUL.md             # Agent identity, values, and critical rules
```

## Entry Points

| Script | Module | Purpose |
|--------|--------|---------|
| `pymolcode` | `python.cli:main` | Main CLI (PyMOL GUI + panel) |
| `pymolcode-bridge` | `python.bridge.server:main` | Headless JSON-RPC server |
| `pymolcode-launcher` | `launcher.pymolcode_launcher:main` | Bridge + node orchestrator |
| PyMOL plugin | `python.pymol.panel:__init_plugin__` | GUI panel |

## Commands

```bash
# Authentication (NEW)
pymolcode auth login anthropic    # OAuth/API key login
pymolcode auth login openai       # Device code flow
pymolcode auth list               # Show stored credentials
pymolcode auth logout google      # Remove credentials

# Agentic Workflows (NEW)
pymolcode ultrawork "..."         # Full agentic workflow

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

**Hephaestus Orchestrator**: Discipline agent for autonomous deep work

## Where to Look

| Task | Location |
|------|----------|
| CLI implementation | `python/cli.py` |
| Auth commands | `python/cli.py` (auth subcommands) |
| OAuth flows | `python/auth/oauth.py` |
| Token storage | `python/auth/token_store.py` |
| Agent orchestration | `python/agent/` |
| Hephaestus orchestrator | `python/agent/orchestrator.py` |
| Background agents | `python/agent/background.py` |
| Memory system | `python/memory/` (store.py, tools.py, policy.py) |
| Soul/identity | `SOUL.md` |
| PyMOL integration | `python/pymol/executor.py`, `runtime.py` |
| JSON-RPC handlers | `python/bridge/handlers.py` |
| Session/config | `python/session/` |
| Skill registry | `python/skill/` |
| Skill bridge | `python/skill/bridge/` |
| OmO adapter | `python/skill/bridge/omo_adapter.py` |
| Ultrawork | `python/workflow/ultrawork.py` |
| Hash validation | `python/validation/hash_edit.py` |
| Protocol framing | `python/protocol/framing.py` |
| TS bridge client | `node/src/bridge-client.ts` |
| PyMOL GUI panel | `python/pymol/panel.py` |
| Memory YAML files | `memory/` directory |
| Skills library | `skills/` directory |

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
| `httpx` | HTTP client (OAuth flows) |
| `pyjwt` | JWT handling |

## Code Map

| Symbol | Type | Location | Role |
|--------|------|----------|------|
| `Agent` | Class | `python/agent/agent.py` | LLM agent orchestration |
| `Hephaestus` | Class | `python/agent/orchestrator.py` | Discipline orchestrator |
| `BackgroundAgentManager` | Class | `python/agent/background.py` | Parallel task execution |
| `OAuthManager` | Class | `python/auth/oauth.py` | OAuth 2.0 flows |
| `TokenStore` | Class | `python/auth/token_store.py` | Secure token storage |
| `SkillDiscovery` | Class | `python/skill/bridge/discovery.py` | Multi-source skill discovery |
| `OmOAdapter` | Class | `python/skill/bridge/omo_adapter.py` | Oh-My-OpenCode adapter |
| `MemoryStore` | Class | `python/memory/store.py` | YAML-based memory storage |
| `MemoryReadTool` | Class | `python/memory/tools.py` | Read from memory |
| `MemoryWriteTool` | Class | `python/memory/tools.py` | Write to memory |
| `MemoryPolicy` | Class | `python/memory/policy.py` | Security enforcement |
| `BridgeServer` | Class | `python/bridge/server.py` | JSON-RPC server |
| `BridgeClient` | Class | `node/src/bridge-client.ts` | TS bridge client |
| `main` | Func | `python/cli.py` | CLI entry point |
| `run_ultrawork` | Func | `python/workflow/ultrawork.py` | Agentic workflow execution |

## Notes

- Build backend: Hatchling (not setuptools)
- PyMOL integration via adapter pattern (not embedding source)
- MCP resources expose PyMOL state: `scene://current`, `object://{name}/metadata`
- Skills defined in YAML with workflow graphs (precheck → run → validate → summarize → persist)
- Safety policies: read-only by default, write needs confirmation, destructive needs explicit flag
- Memory system: YAML-based persistence in `memory/` directory with security policy enforcement
- Soul system: Agent identity and values defined in `SOUL.md`
- Agent learns from mistakes via memory tools (memory_read, memory_write)
- OAuth tokens stored in `~/.pymolcode/auth.json` (0o600 permissions)
- Hephaestus orchestrator: plans goals, delegates to specialists, enforces completion
- Preferred models: Claude Opus 4.6/4.5, GPT-5.3/5.2 Codex, GLM-5, Kimi K2.5
- CI: `.github/workflows/ci.yml` runs pytest with Python 3.11
- Tests: `tests/python/` (unit), `tests/integration/` (integration); markers: `skip_pymol`, `requires_py311`
