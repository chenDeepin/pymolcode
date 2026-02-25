# pymolcode: LLM-Enhanced Molecular Visualization Platform

> **Vision**: Fuse OpenCode's LLM agent capabilities with PyMOL's molecular visualization to create an intelligent, dual-interface platform for structure-based drug discovery.

## Executive Summary

**pymolcode** is a next-generation molecular visualization platform that brings LLM intelligence to PyMOL's powerful visualization capabilities. It enables:
- **Conversational molecular visualization**: Natural language control of PyMOL
- **Automated drug discovery workflows**: Agent-driven structure-based design
- **Dual interface access**: Terminal (TUI) and graphical (GUI) clients
- **Extensible skill system**: Drug discovery-specific agent skills

### 0.1 Current Status Snapshot (2026-02-24)

| Area | Status | Notes |
|------|--------|-------|
| Core MCP (tools/resources/server/client) | Implemented | Functional for local PyMOL + external stubs |
| GUI/TUI parity | Implemented (baseline) | Command palette, task monitor, chat history, settings dialog present |
| Plugin SDK v1 | Implemented (baseline) | Loader/manager/config present |
| Multi-provider LLM | Implemented (API-key mode) | Zhipu/OpenAI/Anthropic/Gemini/Ollama API-key paths |
| OAuth provider auth | Missing (P0 gap) | OpenAI/Claude/Gemini OAuth broker flows not integrated |
| OpenCode + oh-my-opencode parity | Partial | Missing auth plugins, token lifecycle, capability matrix, and policy integration |
| Performance observability | Partial | Basic tests exist; no SLO dashboard, latency budget, or benchmark harness |

### 0.3 Bridge Sprint Operational Notes (2026-02-24)

- Bridge-first workflow path is now exposed via `pymolcode bridge workflow-demo`.
- Report handoff is standardized through bundle outputs (`metadata.json`, `summary.md`, `manifest.json`, plus zip archive).
- End-to-end smoke verification is available through `scripts/bridge_smoke.py` with deterministic PASS/FAIL JSON output.
- Baseline runtime remains Python 3.11+ with explicit gate behavior in CLI and test wrapper.

### 0.2 Critical Gap Statement

This architecture must support both:
1. **API-key provider access** (current baseline), and
2. **OAuth-backed provider access** (required for OpenCode/oh-my-opencode parity and practical adoption).

Without OAuth modules and provider capability governance, project usability and maintenance cost degrade rapidly.

---

## 1. Architecture Overview

### 1.1 High-Level Architecture

```
+----------------------------------------------------------------------------------+
|                                  pymolcode                                       |
+---------------------+-------------------------+----------------------------------+
| TUI Client          | GUI Client              | Python SDK / Scripting API       |
| (Textual/Rich)      | (PyMOL plugin panel)    | (notebook + automation)          |
+----------+----------+------------+------------+----------------+-----------------+
           |                        |                             |
           +------------------------+-----------------------------+
                                    |
                         +----------v-----------+
                         | Application Core     |
                         | - Session Manager    |
                         | - Command Bus        |
                         | - Agent Orchestrator |
                         | - Skill Runtime      |
                         | - Workflow Engine    |
                         +----+------------+----+
                              |            |
                  +-----------v--+      +--v---------------------+
                  | MCP Hub       |      | Molecular Bridge       |
                  | - MCP Client  |      | - PyMOL cmd adapter    |
                  | - MCP Server  |      | - Scene/object services|
                  | - Tool broker |      | - Compatibility layer  |
                  +-----+---------+      +-----------+------------+
                        |                                |
         +--------------v----------------+       +------v----------------------+
         | External MCP Tool Servers     |       | PyMOL Runtime              |
         | (docking, DB, MD, retrieval)  |       | Python API -> Executive -> |
         | PubChem/ChEMBL/DrugCLIP/etc.  |       | C++ layers                 |
         +-------------------------------+       +----------------------------+
```

### 1.2 Design Principles

1. **Shared Core + Thin Clients**: Business logic centralized, UI clients are interchangeable
2. **MCP-First Integration**: Model Context Protocol for standardized tool interoperability
3. **PyMOL Compatibility**: Full API compatibility through adapter layer
4. **Skill-Based Automation**: Drug discovery workflows as reusable, reproducible skills
5. **Type-Safe Tool Contracts**: Pydantic schemas for LLM action validation

---

## 2. Source Project Analysis

### 2.1 PyMOL Architecture (What We Adopt)

| Component | Pattern | Adoption in pymolcode |
|-----------|---------|----------------------|
| **Layer Architecture** | Python API → Executive → C++ layers | Preserve as Molecular Bridge |
| **Executive System** | Central command coordinator | Wrap in MCP Tools |
| **Command Module** (`cmd.py`) | Python API entry point | Extend with LLM-aware commands |
| **Settings System** | Hierarchical configuration | Preserve, add LLM policy settings |
| **Plugin System** | `__init_plugin__()` + `cmd.extend()` | Primary GUI integration point |
| **Skin System** | Pluggable GUI implementations | LLM chat as new skin component |

**Key PyMOL Files to Reference:**
```
modules/pymol/cmd.py          # Command API
modules/pymol/setting.py      # Settings management
modules/pmg_tk/PMGApp.py      # GUI application container
modules/pmg_qt/pymol_qt_gui.py # Qt-based GUI
layer3/Executive.h            # C++ coordinator
```

### 2.2 OpenCode Architecture (What We Adopt)

| Component | Pattern | Adoption in pymolcode |
|-----------|---------|----------------------|
| **Skills System** | Lazy-loaded skill discovery | Drug discovery skill registry |
| **Agent Coordination** | Task spawning, session continuity | Agent orchestrator module |
| **Multi-Provider LLM** | Unified provider abstraction | LiteLLM-style adapter layer |
| **Auth Plugins** | OAuth + API key hybrid auth | Provider auth broker + token store |
| **TUI Framework** | Terminal-based interface | Textual-based TUI client |
| **Plugin Architecture** | Event-driven modules | Event bus for extensions |

#### OpenCode/oh-my-opencode Operational Requirements

- Provider auth must include OAuth-capable flows for OpenAI/Claude/Gemini where available.
- Auth integration must be plugin-ready (OpenCode-style plugin hooks and provider injection).
- Provider model metadata should include capability variants (context, output limits, reasoning level, modalities).
- Local config should allow per-provider defaults and fallback chains.

### 2.3 Existing PyMOL+LLM Projects (Lessons Learned)

| Project | Approach | Strengths | Gaps pymolcode Addresses |
|---------|----------|-----------|--------------------------|
| **pymol-mcp** | Socket MCP server | Clean separation, Claude integration | No TUI, limited skills |
| **ChatMOL** | ChatGPT plugin | Multi-LLM support | No workflow automation |
| **PyMolCopilot** | Chat window | GUI integration | No skill system |
| **ReACT PyMOL** | RAG + agent | Document retrieval | Limited tool integration |

---

## 3. Core Modules Specification

### 3.1 Module Architecture

```
pymolcode/
├── interface/
│   ├── tui/                    # Terminal interface (Textual)
│   │   ├── app.py              # Main TUI application
│   │   ├── chat.py             # Chat interface
│   │   ├── commands.py         # Command palette
│   │   └── monitor.py          # Task monitor
│   └── gui/
│       ├── plugin.py           # PyMOL plugin entry
│       ├── chat_panel.py       # LLM chat panel
│       ├── skill_browser.py    # Skill browser UI
│       └── workflow_monitor.py # Workflow status
│
├── core/
│   ├── session/                # Session management
│   │   ├── manager.py          # Session lifecycle
│   │   ├── context.py          # Molecular context
│   │   └── artifacts.py        # Output management
│   ├── agent/
│   │   ├── orchestrator.py     # Agent coordination
│   │   ├── planner.py          # Action planning
│   │   └── executor.py         # Tool execution
│   ├── auth/
│   │   ├── broker.py           # OAuth/API-key broker
│   │   ├── providers.py        # Provider auth adapters
│   │   ├── tokens.py           # Token lifecycle + refresh
│   │   └── secure_store.py     # OS keyring/encrypted storage
│   ├── skills/
│   │   ├── registry.py         # Skill discovery
│   │   ├── runtime.py          # Skill execution
│   │   └── validation.py       # Dependency checks
│   └── workflows/
│       ├── engine.py           # Pipeline engine
│       ├── checkpoints.py      # State persistence
│       └── provenance.py       # Audit trail
│
├── integration/
│   ├── pymol/
│   │   ├── adapter.py          # PyMOL command wrapper
│   │   ├── objects.py          # Object services
│   │   ├── selections.py       # Selection API
│   │   └── rendering.py        # Visualization services
│   └── mcp/
│       ├── server.py           # MCP server (expose tools)
│       ├── client.py           # MCP client (consume tools)
│       ├── tools.py            # Tool definitions
│       └── resources.py        # PyMOL state as resources
│
├── platform/
│   ├── plugins/                # Plugin system
│   │   ├── loader.py           # Plugin discovery
│   │   ├── events.py           # Event bus
│   │   └── permissions.py      # Capability system
│   └── config/
│       ├── settings.py         # Configuration
│       ├── policies.py         # Safety policies
│       └── provider_matrix.py  # Provider capabilities + fallback policy
│
└── skills/                     # Built-in skills
    ├── structure_prep/         # Protein/ligand preparation
    ├── pocket_analysis/        # Binding site analysis
    ├── docking/                # Docking orchestration
    ├── interactions/           # Interaction profiling
    ├── sar/                    # SAR annotation
    └── reporting/              # Report generation
```

### 3.2 Module Responsibilities

| Module | Responsibility | Key Classes/Functions |
|--------|----------------|------------------------|
| `interface.tui` | Terminal UX | `TuiApp`, `ChatView`, `CommandPalette` |
| `interface.gui` | PyMOL panel UX | `PymolcodePlugin`, `ChatPanel`, `SkillBrowser` |
| `core.session` | State management | `SessionManager`, `MolecularContext` |
| `core.agent` | LLM orchestration | `AgentOrchestrator`, `Planner`, `Executor` |
| `core.skills` | Skill lifecycle | `SkillRegistry`, `SkillRuntime` |
| `core.workflows` | Pipeline execution | `WorkflowEngine`, `CheckpointManager` |
| `integration.pymol` | PyMOL bridge | `PymolAdapter`, `ObjectService` |
| `integration.mcp` | Tool protocol | `McpServer`, `McpClient`, `ToolRegistry` |

---

## 4. MCP Integration Design

### 4.1 MCP Server (pymolcode as Tool Provider)

Expose PyMOL capabilities as standardized MCP tools:

```python
# integration/mcp/tools.py

from mcp.server import Server
from mcp.types import Tool, TextContent
from pydantic import BaseModel

class LoadStructureInput(BaseModel):
    source: str  # PDB ID, file path, or URL
    name: str = None  # Object name in PyMOL
    format: str = "auto"  # pdb, sdf, mol2, etc.

class LoadStructureOutput(BaseModel):
    object_name: str
    atom_count: int
    chain_count: int

# MCP Tool definitions
TOOLS = [
    Tool(
        name="load_structure",
        description="Load molecular structure into PyMOL",
        inputSchema=LoadStructureInput.model_json_schema(),
    ),
    Tool(
        name="align_objects",
        description="Align molecular structures",
        inputSchema=AlignInput.model_json_schema(),
    ),
    Tool(
        name="measure_contacts",
        description="Measure intermolecular contacts",
        inputSchema=ContactsInput.model_json_schema(),
    ),
    Tool(
        name="color_by_property",
        description="Color structure by property",
        inputSchema=ColorInput.model_json_schema(),
    ),
    Tool(
        name="export_image",
        description="Export visualization as image",
        inputSchema=ExportInput.model_json_schema(),
    ),
    Tool(
        name="run_docking_workflow",
        description="Execute docking workflow skill",
        inputSchema=DockingInput.model_json_schema(),
    ),
]
```

### 4.2 MCP Resources (PyMOL State Exposure)

Expose PyMOL state for LLM context:

```python
# integration/mcp/resources.py

RESOURCES = [
    # Current scene state
    "scene://current",           # Active view, objects, selections
    "scene://objects",           # List of loaded objects
    "scene://selections",        # Active selections
    
    # Object metadata
    "object://{name}/metadata",  # Object properties
    "object://{name}/atoms",     # Atom information
    "object://{name}/bonds",     # Bond topology
    
    # Session state
    "session://history",         # Command history
    "session://artifacts",       # Generated outputs
    "session://workflow",        # Active workflow state
]
```

### 4.3 MCP Client (External Tool Integration)

Connect to external drug discovery tools:

```python
# External MCP tool servers to integrate
EXTERNAL_TOOLS = {
    "docking": [
        "gnina-mcp-server",      # GNINA docking
        "vina-mcp-server",       # AutoDock Vina
        "gold-mcp-server",       # GOLD docking
    ],
    "databases": [
        "pubchem-mcp-server",    # PubChem queries
        "chembl-mcp-server",     # ChEMBL data
        "pdb-mcp-server",        # PDB retrieval
    ],
    "analysis": [
        "drugclip-mcp-server",   # DrugCLIP screening
        "rdkit-mcp-server",      # Cheminformatics
        "mdanalysis-mcp-server", # Trajectory analysis
    ],
}
```

### 4.4 Provider Authentication Architecture (OAuth + API Key Hybrid)

Auth must support two modes per provider:

1. **API key mode** (fast path for automation and CI)
2. **OAuth mode** (OpenCode/oh-my-opencode parity for user-linked subscriptions and managed sessions)

```python
# core/auth/broker.py

class AuthMode(str, Enum):
    API_KEY = "api_key"
    OAUTH = "oauth"

class ProviderAuthBroker:
    def login(self, provider: str, mode: AuthMode) -> AuthSession: ...
    def refresh(self, provider: str) -> AuthSession: ...
    def logout(self, provider: str) -> None: ...
    def validate(self, provider: str) -> AuthHealth: ...

# core/auth/providers.py
PROVIDER_AUTH = {
    "openai": {"modes": ["api_key", "oauth"]},
    "anthropic": {"modes": ["api_key", "oauth"]},
    "gemini": {"modes": ["api_key", "oauth"]},
    "zhipuai-coding-plan": {"modes": ["api_key"]},
    "ollama": {"modes": ["api_key", "local"]},
}
```

**Acceptance Criteria (P0):**
- OpenAI/Claude/Gemini can be configured in either API-key or OAuth mode.
- Token refresh and expiry are handled without crashing active sessions.
- Secure token storage is required for OAuth sessions.
- Auth mode is visible in GUI settings and TUI status panels.

---

## 5. Skill System Design

### 5.1 Skill Package Format

```yaml
# skills/docking/skill.yaml
name: docking_workflow
version: "1.0.0"
description: Automated molecular docking workflow

# Trigger hints for LLM
triggers:
  - "dock [ligand] to [protein]"
  - "run docking for [targets]"
  - "find binding poses"

# Required MCP tools
requires_tools:
  - load_structure
  - align_objects
  - measure_contacts
  
# External tool dependencies
requires_external:
  - gnina-mcp-server | vina-mcp-server

# Input/output schema
input_schema:
  protein: str        # Protein structure
  ligands: list[str]  # Ligand structures
  pocket: str = null  # Optional pocket definition
  
output_schema:
  poses: list[dict]
  scores: list[float]
  artifacts:
    images: list[str]
    sdf_files: list[str]

# Execution graph
workflow:
  - step: precheck
    action: validate_inputs
  - step: prep_protein
    action: protein_preparation
  - step: prep_ligands
    action: ligand_preparation
  - step: run_docking
    action: execute_docking
    parallel: true
  - step: analyze
    action: interaction_analysis
  - step: rank
    action: score_ranking
  - step: summarize
    action: generate_report
  - step: persist
    action: save_artifacts
```

### 5.2 Built-in Skills

| Skill | Purpose | Workflow Steps |
|-------|---------|----------------|
| `protein_prep` | Structure preparation | Validate → Add hydrogens → Optimize → Assign charges |
| `ligand_prep` | Ligand preparation | Standardize → Generate 3D → Minimize → Enumerate states |
| `pocket_analysis` | Binding site detection | Surface → Cavity detection → Druggability scoring |
| `docking_batch` | High-throughput docking | Prepare → Dock → Score → Rank → Visualize |
| `interaction_map` | Contact analysis | Detect contacts → Classify → Visualize → Report |
| `pose_compare` | Pose comparison | Align → RMSD → Interaction fingerprint → Report |
| `hit_prioritize` | Hit ranking | Score aggregation → Property filter → Rank → Visualize |
| `session_report` | Documentation | Collect artifacts → Generate figures → Compile report |

### 5.3 Skill Execution Model

```
┌─────────────────────────────────────────────────────────────┐
│                    Skill Execution Flow                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. DISCOVERY                                                │
│     └── SkillRegistry.find(intent) → matched_skills         │
│                                                              │
│  2. VALIDATION                                               │
│     ├── Check tool dependencies                              │
│     ├── Validate input schema                                │
│     └── Confirm external services                            │
│                                                              │
│  3. EXECUTION                                                │
│     ├── WorkflowEngine.execute(skill.workflow)               │
│     │   ├── Step-by-step execution                           │
│     │   ├── Checkpoint after each step                       │
│     │   └── Retry on transient failures                       │
│     └── Emit progress events                                 │
│                                                              │
│  4. VERIFICATION                                             │
│     ├── Validate output schema                               │
│     ├── Run deterministic post-checks                        │
│     └── Generate provenance manifest                         │
│                                                              │
│  5. ARTIFACT PERSISTENCE                                     │
│     ├── Save generated files (images, SDF, logs)             │
│     ├── Record provenance (inputs, versions, params)         │
│     └── Update session artifacts index                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. Dual Interface Strategy

### 6.1 Shared Core Architecture

```python
# core/session/manager.py

class ApplicationService:
    """
    Central service that both TUI and GUI call.
    No domain logic in UI layer.
    """
    
    def __init__(self):
        self.session = SessionManager()
        self.agent = AgentOrchestrator()
        self.skills = SkillRegistry()
        self.workflows = WorkflowEngine()
        self.pymol = PymolAdapter()
        self.mcp = McpHub()
        
    # Unified API for both interfaces
    async def chat(self, message: str) -> AsyncIterator[ChatEvent]:
        """Process user message, yield streaming events."""
        
    async def execute_skill(self, skill_name: str, **params) -> SkillResult:
        """Execute a skill workflow."""
        
    async def load_structure(self, source: str) -> StructureInfo:
        """Load structure via PyMOL adapter."""
        
    async def get_scene_state(self) -> SceneState:
        """Get current PyMOL scene state."""
```

### 6.2 TUI Implementation (Textual)

```python
# interface/tui/app.py

from textual.app import App
from textual.widgets import Header, Footer

class PymolcodeTUI(App):
    """Terminal interface for pymolcode."""
    
    CSS_PATH = "styles.css"
    
    def __init__(self, core: ApplicationService):
        self.core = core
        super().__init__()
        
    def compose(self):
        yield Header()
        yield ChatView(self.core)
        yield CommandPalette(self.core)
        yield TaskMonitor(self.core)
        yield Footer()
        
    def on_chat_message(self, message: str):
        async def process():
            async for event in self.core.chat(message):
                self.handle_event(event)
        asyncio.create_task(process())
```

### 6.3 GUI Implementation (PyMOL Plugin)

```python
# interface/gui/plugin.py

from pymol.Qt import QtWidgets
from pymol import cmd

class PymolcodePlugin(QtWidgets.QDockWidget):
    """PyMOL plugin panel for pymolcode."""
    
    def __init__(self, core: ApplicationService):
        self.core = core
        super().__init__("pymolcode")
        self.setup_ui()
        
    def setup_ui(self):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        
        # Chat panel
        self.chat_panel = ChatPanel(self.core)
        layout.addWidget(self.chat_panel)
        
        # Skill browser
        self.skill_browser = SkillBrowser(self.core)
        layout.addWidget(self.skill_browser)
        
        # Workflow monitor
        self.workflow_monitor = WorkflowMonitor(self.core)
        layout.addWidget(self.workflow_monitor)
        
        self.setWidget(widget)

def __init_plugin__(app=None):
    """PyMOL plugin entry point."""
    from pymol.plugins import addmenuitemqt
    
    def show_plugin():
        core = get_application_service()  # Singleton
        plugin = PymolcodePlugin(core)
        app.root.addDockWidget(Qt.RightDockWidgetArea, plugin)
    
    addmenuitemqt('pymolcode', show_plugin)

# Register additional commands
@cmd.extend
def pymolcode_chat(message: str):
    """Send message to pymolcode from PyMOL command line."""
    core = get_application_service()
    return asyncio.run(core.chat(message))
```

### 6.4 Event Synchronization

```python
# platform/plugins/events.py

from typing import Protocol
from dataclasses import dataclass

@dataclass
class SessionEvent:
    type: str  # "molecule_loaded", "skill_started", etc.
    data: dict
    source: str  # "tui" or "gui"

class EventBus:
    """Synchronize state between TUI and GUI."""
    
    def __init__(self):
        self._subscribers: list[Callable[[SessionEvent], None]] = []
        
    def subscribe(self, handler: Callable[[SessionEvent], None]):
        self._subscribers.append(handler)
        
    def emit(self, event: SessionEvent):
        for handler in self._subscribers:
            handler(event)
            
# Usage: both TUI and GUI subscribe to events
event_bus.subscribe(tui.handle_session_event)
event_bus.subscribe(gui.handle_session_event)
```

---

## 7. Technology Stack

### 7.1 Core Dependencies

| Category | Technology | Purpose |
|----------|-----------|---------|
| **Runtime** | Python 3.11+ | Main language |
| **Async** | asyncio / AnyIO | Concurrent operations |
| **TUI** | Textual | Terminal interface |
| **GUI** | PyQt5/6 | PyMOL panel integration |
| **MCP** | mcp (official SDK) | Tool protocol |
| **LLM** | LiteLLM | Multi-provider abstraction |
| **Auth** | OAuth 2.0 + plugin adapters | Provider login/session support |
| **Secrets** | keyring/OS secure store | Token + key persistence |
| **Validation** | Pydantic v2 | Schema validation |
| **Config** | pydantic-settings | Configuration management |

### 7.2 Scientific Stack

| Category | Technology | Purpose |
|----------|-----------|---------|
| **Cheminformatics** | RDKit | Molecular operations |
| **Bioinformatics** | Biopython | Sequence/structure |
| **Trajectories** | MDAnalysis | MD simulation analysis |
| **Data** | NumPy, pandas | Data structures |
| **Visualization** | PyMOL (required) | Molecular rendering |

### 7.3 Infrastructure

| Category | Technology | Purpose |
|----------|-----------|---------|
| **API** | FastAPI | Local control plane |
| **Storage** | SQLite | Session metadata |
| **Artifacts** | Filesystem first | Output storage |
| **Logging** | structlog | Structured logging |
| **Tracing** | OpenTelemetry | Observability |

---

## 8. Implementation Phases

### Phase 0: Foundation (2 weeks)

**Goals**: Contracts, scaffolding, compatibility tests

**Deliverables**:
- [x] Project structure setup
- [x] Module boundary definitions
- [x] Tool schema specifications (Pydantic models)
- [x] Event model design
- [x] PyMOL version compatibility tests
- [x] CI/CD pipeline

**Key Files**:
```
pymolcode/
├── pyproject.toml
├── src/pymolcode/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   └── types.py          # Core type definitions
│   └── integration/
│       └── pymol/
│           └── compat.py     # PyMOL compatibility layer
└── tests/
    └── test_pymol_compat.py
```

### Phase 1: MVP (4-6 weeks)

**Goals**: Functional prototype with basic capabilities

**Deliverables**:
- [x] Shared ApplicationService core
- [x] TUI client (Textual) with chat
- [x] Minimal GUI panel (load, chat)
- [x] Single LLM provider (Anthropic)
- [x] Essential MCP tools (5-7 tools)
- [x] 3-4 core skills (protein_prep, ligand_prep, docking, interaction_map)
- [x] Basic artifact persistence

**MCP Tools (MVP)**:
1. `load_structure` - Load from file/PDB
2. `save_structure` - Export structure
3. `set_representation` - Change representation
4. `color_object` - Color molecules
5. `align_objects` - Structure alignment
6. `measure_distance` - Distance measurement
7. `export_image` - Save visualization

### Phase 2: Integration (4-6 weeks)

**Goals**: Full MCP hub, multi-provider, plugin SDK

**Deliverables**:
- [x] Complete MCP server + client
- [x] Multi-provider LLM (Anthropic, OpenAI, Gemini, Ollama) in API-key mode
- [x] Plugin SDK v1 (baseline)
- [x] External tool server integration (DrugCLIP, RDKit stubs)
- [x] MCP resource exposure
- [x] Enhanced TUI (command palette, task monitor)
- [x] Full GUI feature parity (baseline)
- [x] OAuth auth broker for OpenAI/Claude/Gemini
- [x] Provider capability matrix + fallback policy engine
- [x] Secure token storage + refresh lifecycle

### Phase 2.5: OpenCode/oh-my-opencode Parity Hardening (2-3 weeks)

**Goals**: Eliminate practical auth/integration gaps that block day-to-day usage.

**Deliverables**:
- [x] OpenCode-compatible auth plugin layer (`opencode-openai-codex-auth` class integration pattern)
- [x] Claude and Gemini OAuth adapter interfaces (provider-specific token exchange)
- [x] Unified auth broker APIs (`login`, `refresh`, `logout`, `validate`)
- [x] Capability-aware model routing (modalities/context/reasoning variants)
- [x] Policy guards for auth scopes and token storage handling
- [x] Migration guide: API-key-only -> OAuth/API-key hybrid

**External Integrations**:
- DrugCLIP MCP server (virtual screening)
- RDKit MCP server (cheminformatics)
- PubChem MCP server (database queries)

### Phase 2.6: TypeScript Control Plane Bridge (2-4 weeks)

**Goals**: Achieve OpenCode-style TypeScript-native orchestration without rewriting PyMOL runtime.

**Deliverables**:
- [ ] TS control-plane service (`opencode-bridge`) for provider routing, skill orchestration, and session policy hooks.
- [ ] Stable Python bridge service for PyMOL open-source control (JSON-RPC over stdio or local HTTP).
- [ ] Contract-first schemas for all bridge methods (`load_structure`, `align`, `measure`, `render`, `state_snapshot`).
- [ ] Cross-language session correlation IDs (TS orchestrator <-> Python worker <-> MCP tools).
- [ ] Failure policy: bridge retries, timeout budgets, and fallback to direct Python execution.

**Non-Goals (explicit)**:
- Full Python-to-TypeScript rewrite in one phase.
- Direct replacement of PyMOL Python API bindings.

**Acceptance Criteria**:
- TS orchestrator can drive at least 80% of existing PyMOL tool workflows through the bridge.
- End-to-end parity tests pass for TUI/GUI-triggered tasks through TS and Python execution modes.
- No regression in existing API-key/OAuth auth flows.

### Phase 3: Drug Discovery Features (6-8 weeks)

**Goals**: Advanced workflows, provenance, performance

**Deliverables**:
- [x] Advanced skills (docking_batch, pose_compare, hit_prioritize)
- [x] Async workflow engine with checkpoints
- [x] Provenance tracking system
- [x] Batch processing capabilities
- [x] Session persistence and recovery
- [x] Report generation skills
- [ ] Medicinal-chemistry data collector layer (ChEMBL/BindingDB/PDB) with normalized schema
- [ ] Residue-context annotation pipeline (binding-site residues, ligand-distance, interaction tags)
- [ ] Hypothesis ledger for SAR ideas (for example: phenyl-group hydrophobic affinity rationale) with validation status

**Advanced Skills**:
- `docking_batch` - High-throughput docking
- `pose_compare` - RMSD + interaction fingerprints
- `hit_prioritize` - Multi-criteria ranking
- `session_report` - Automated documentation

### Phase 4: Production Ready (4-6 weeks)

**Goals**: Hardening, distribution, documentation

**Deliverables**:
- [x] Performance optimization
- [x] Policy controls (safety, permissions)
- [x] Packaging (pip, conda)
- [x] Comprehensive documentation
- [x] Tutorial notebooks
- [x] Reproducibility benchmarks
- [x] Security audit

---

## 9. Key Design Decisions

### 9.1 Decision Matrix

| Decision | Choice | Rationale | Tradeoff |
|----------|--------|-----------|----------|
| Core architecture | Shared core + thin clients | Maintainability, consistency | IPC complexity |
| Tool protocol | MCP-first | Ecosystem leverage, standardization | Upfront schema work |
| PyMOL integration | API adapter layer | Safe upgrades, compatibility | Less raw power |
| Workflow model | Skill graphs | Reliability, reproducibility | Reduced flexibility |
| Action model | Typed + policy-guarded | Safety for scientific workflows | Extra plumbing |

### 9.2 Safety Model

```python
# platform/config/policies.py

class SafetyPolicy:
    """Define action safety levels."""
    
    READ_ONLY = "read_only"      # No side effects
    MODIFIES_STATE = "modifies"   # Changes PyMOL state
    EXTERNAL_CALL = "external"    # Calls external services
    DESTRUCTIVE = "destructive"   # Deletes data
    
TOOL_POLICIES = {
    "load_structure": SafetyPolicy.MODIFIES_STATE,
    "delete_object": SafetyPolicy.DESTRUCTIVE,
    "run_docking": SafetyPolicy.EXTERNAL_CALL,
    "get_scene_state": SafetyPolicy.READ_ONLY,
}

def check_permission(tool: str, user_confirmation: bool):
    policy = TOOL_POLICIES.get(tool)
    if policy == SafetyPolicy.DESTRUCTIVE:
        require_explicit_confirmation(user_confirmation)
    if policy == SafetyPolicy.EXTERNAL_CALL:
        log_external_call(tool)
```

---

## 10. Risk Mitigation

| Risk | Mitigation Strategy |
|------|---------------------|
| **GUI event-loop conflicts** | Dedicated background executor, thread-safe UI bridge |
| **LLM nondeterminism** | Typed tools, deterministic post-checks, provenance manifests |
| **OAuth token expiry/revocation** | Background refresh, scoped retries, forced re-auth UX |
| **Provider auth fragmentation** | Auth broker abstraction + capability matrix |
| **PyMOL version drift** | Adapter shims, CI against multiple PyMOL versions |
| **Long-running tasks** | Async job queue, checkpointing, resumable workflows |
| **Plugin security** | Capability-based permissions, signed metadata, sandboxed execution |
| **Memory leaks in C++** | Resource cleanup monitoring, session restart policies |

---

## 11. Next Steps

### Immediate Actions (Week 1-2)

1. **Setup project structure**
   ```bash
   mkdir -p pymolcode/src/pymolcode/{core,integration,interface,platform,skills}
   ```

2. **Define core types**
   ```python
   # src/pymolcode/core/types.py
   # - SessionState, MoleculeContext, SkillResult, etc.
   ```

3. **Create PyMOL compatibility tests**
   ```python
   # tests/test_pymol_compat.py
   # - Test against PyMOL 2.5, 3.0, 3.1
   ```

4. **Draft MCP tool schemas**
   ```python
   # src/pymolcode/integration/mcp/schemas.py
   # - Input/output models for all tools
   ```

5. **Start TS control-plane bridge spike**
   ```text
   Build a minimal TypeScript orchestrator that calls one Python bridge method
   (e.g., load_structure) and returns structured result + trace id.
   ```

6. **Create medicinal-chemistry data schema migration**
   ```text
   Add tables for compounds, targets, activities, residue_context, hypotheses,
   and llm_interactions with provenance fields.
   ```

### Technical Decisions Needed

1. **OAuth sequence priority**: OpenAI -> Claude -> Gemini provider adapters
2. **Token storage strategy**: OS keyring first, encrypted file fallback
3. **Capability routing policy**: strict matrix vs best-effort fallback
4. **PyMOL version support**: Minimum version 2.5+ (keep)
5. **Bridge protocol**: JSON-RPC over stdio vs local HTTP for TS<->Python boundary
6. **Execution ownership**: TS-first planning with Python execution fallback rules

### Immediate Performance/Status Checks (must track continuously)

- **Provider call latency**: p50/p95 by provider and model
- **Auth reliability**: login success rate, refresh success rate, token invalidation incidents
- **Tool execution health**: MCP tool success rate + timeout rate
- **UI responsiveness**: TUI/GUI command-to-feedback latency budget
- **Regression safety**: CI matrix for PyMOL versions + provider adapters

---

## 12. References

### Source Projects
- [PyMOL Open Source](https://github.com/schrodinger/pymol-open-source)
- [OpenCode](https://github.com/sst/opencode)
- [oh-my-opencode](https://github.com/code-yeongyu/oh-my-opencode)
- [opencode-openai-codex-auth](https://github.com/numman-ali/opencode-openai-codex-auth)
- [PyMOL Wiki - Plugin Architecture](https://pymolwiki.org/PluginArchitecture)
- [PyMOL MCP Server](https://github.com/vrtejus/pymol-mcp)
- [ChatMOL](https://github.com/ChatMol/ChatMol)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)

### Architecture References
- [PyMOL DeepWiki Architecture](https://deepwiki.com/schrodinger/pymol-open-source)
- [Anthropic MCP Course](https://anthropic.skilljar.com/introduction-to-model-context-protocol)
- [Textual Framework](https://github.com/Textualize/textual)

### Drug Discovery Integration
- [DrugCLIP](https://github.com/bowen-gao/DrugCLIP) - Virtual screening
- [RDKit](https://github.com/rdkit/rdkit) - Cheminformatics
- [BioChemAIgent](https://www.biorxiv.org/content/10.64898/2025.12.17.694892v1) - Agent framework

---

## Appendix A: MCP Tool Schemas

```python
# Complete tool definitions for Phase 1

from pydantic import BaseModel, Field
from typing import Optional, Literal
from enum import Enum

class RepresentationType(str, Enum):
    CARTOON = "cartoon"
    STICK = "stick"
    SPHERE = "sphere"
    SURFACE = "surface"
    MESH = "mesh"
    LINE = "line"

# Tool 1: Load Structure
class LoadStructureInput(BaseModel):
    source: str = Field(description="PDB ID, file path, or URL")
    name: Optional[str] = Field(default=None, description="Object name in PyMOL")
    format: str = Field(default="auto", description="File format (pdb, sdf, mol2)")

class LoadStructureOutput(BaseModel):
    object_name: str
    atom_count: int
    chain_count: Optional[int]
    title: Optional[str]

# Tool 2: Set Representation
class SetRepresentationInput(BaseModel):
    selection: str = Field(default="all", description="PyMOL selection")
    representation: RepresentationType
    color: Optional[str] = Field(default=None, description="Color name or scheme")

class SetRepresentationOutput(BaseModel):
    success: bool
    message: str

# Tool 3: Measure Contacts
class MeasureContactsInput(BaseModel):
    selection1: str
    selection2: str
    cutoff: float = Field(default=4.0, description="Distance cutoff in Angstroms")
    
class Contact(BaseModel):
    atom1: str
    atom2: str
    distance: float
    contact_type: str  # hydrogen_bond, hydrophobic, etc.

class MeasureContactsOutput(BaseModel):
    contacts: list[Contact]
    summary: dict
```

---

## Appendix B: Skill Example

```yaml
# skills/pocket_analysis/skill.yaml

name: pocket_analysis
version: "1.0.0"
description: Identify and analyze protein binding pockets

triggers:
  - "find pockets in [protein]"
  - "analyze binding sites"
  - "detect cavities"

requires_tools:
  - load_structure
  - set_representation
  - export_image

input_schema:
  protein: str
  method: str = "fpocket"  # fpocket, coot, custom
  min_volume: float = 100.0

output_schema:
  pockets:
    - id: int
      center: list[float]
      volume: float
      druggability_score: float
      residues: list[str]
  artifacts:
    images: list[str]
    data_file: str

workflow:
  - step: validate
    action: check_structure_loaded
    params:
      selection: "{protein}"
      
  - step: detect
    action: run_pocket_detection
    params:
      method: "{method}"
      protein: "{protein}"
      
  - step: filter
    action: filter_by_volume
    params:
      min_volume: "{min_volume}"
      
  - step: visualize
    action: create_pocket_visualization
    params:
      pockets: "{detected_pockets}"
      
  - step: export
    action: export_results
    params:
      format: "json"
      
  - step: summarize
    action: generate_summary
    params:
      include_images: true
```

---

*Document Version: 1.0.0*
*Last Updated: 2026-02-24*
*Authors: pymolcode planning team*
