# PymolCode

> **LLM-Enhanced Molecular Visualization Platform for Drug Discovery**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

**PymolCode** fuses LLM agent capabilities with [PyMOL](https://github.com/schrodinger/pymol-open-source)'s molecular visualization to create an intelligent platform for structure-based drug discovery.

## Features

- 🤖 **Conversational Molecular Visualization** - Natural language control of PyMOL
- 🧠 **Persistent Memory System** - Agent learns from mistakes and remembers preferences across sessions
- 🔬 **Automated Drug Discovery Workflows** - Agent-driven structure-based design
- 💻 **Dual Interface** - CLI and PyMOL GUI plugin
- 🔧 **Extensible Skill System** - Drug discovery-specific agent skills
- 🔌 **MCP Integration** - Model Context Protocol for standardized tool interoperability
- 🛡️ **Safety Controls** - Policy-guarded actions for scientific reproducibility

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        PymolCode                            │
├────────────────┬─────────────────┬─────────────────────────┤
│   CLI Bridge   │   GUI Client    │   Python SDK            │
│  (Headless)    │ (PyMOL Plugin)  │   (Scripting API)       │
├────────────────┴─────────────────┴─────────────────────────┤
│                    Application Core                         │
│  Session │ Agent │ Skills │ Bridge │ Memory │ Protocol     │
├─────────────────────────────────────────────────────────────┤
│          MCP Hub              │      Molecular Bridge       │
│  MCP Server │ MCP Client      │  PyMOL Adapter │ Services  │
├───────────────────────────────┴─────────────────────────────┤
│           External Tools (MCP Servers)                      │
│  Docking │ Databases │ Screening │ Analysis                │
└─────────────────────────────────────────────────────────────┘
```

## Installation

### Prerequisites

- **Python 3.11+**
- **PyMOL 2.5+** (Open-source or Incentive)
  - **Open-source**: `pip install pymol-open-source` or build from [source](https://github.com/schrodinger/pymol-open-source)
  - **Incentive PyMOL**: Download from [Schrödinger](https://pymol.org/2/)
- **UV package manager** (recommended) - [Install UV](https://docs.astral.sh/uv/)

### Setup

```bash
# Clone the repository
git clone https://github.com/chenDeepin/pymolcode.git
cd pymolcode

# Create virtual environment
uv venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows

# Install dependencies
uv pip install -e ".[all]"

# (Optional) Verify installation
pymolcode --version
```

## Usage

### PyMOL GUI Plugin

```bash
# Launch PyMOL with pymolcode panel
pymolcode
```

### Headless Bridge Server

```bash
# Run bridge server (JSON-RPC over stdio)
pymolcode --headless
# or
pymolcode-bridge
```

### TypeScript Bridge Client

```bash
# Build TypeScript client
cd node
npm install
npm run build

# Use the client programmatically
# See node/src/bridge-client.ts
```

### PyMOL Plugin Installation

```python
# In PyMOL, install the plugin manually:
# Plugin → Plugin Manager → Install New Plugin → Select python/pymol/panel.py

# Then use from PyMOL command line:
pymolcode> load PDB 1UBQ and show as cartoon
pymolcode> color by secondary structure
pymolcode> find binding pockets
```

## Example Usage

### Conversational Visualization

```
User: Load the TEAD1-YAP complex (PDB 3KYS) and highlight the interface

pymolcode: I'll load the structure and identify the protein-protein interface.

[Loads 3KYS, detects interface residues, applies stick representation]

Done! I've loaded the TEAD1-YAP complex and highlighted 45 interface residues
in red (YAP) and blue (TEAD1). The interface spans ~850 Å² with key contacts
at residues YAP F96, P97, P98 and TEAD1 L381, Y382, K383.

Would you like me to analyze the interaction types or dock a potential inhibitor?
```

### Automated Workflow

```
User: Run docking for these 10 ligands against the TEAD1 pocket

pymolcode: I'll execute the docking_batch skill. This involves:

1. Preparing the protein structure
2. Generating ligand conformers  
3. Running molecular docking
4. Analyzing interactions
5. Ranking by binding score

[Workflow executes with progress updates]

Results: Top 3 hits identified:
- ligand_03: ΔG = -9.2 kcal/mol, key H-bonds with Y422, F393
- ligand_07: ΔG = -8.8 kcal/mol, hydrophobic contacts in lipophilic pocket
- ligand_01: ΔG = -8.5 kcal/mol, potential covalent warhead positioning

Visualizations saved to ./artifacts/docking_run_001/
```

## Skills

Built-in drug discovery skills:

| Skill | Description |
|-------|-------------|
| `protein_prep` | Structure preparation (protonation, optimization) |
| `ligand_prep` | Ligand preparation (standardization, 3D generation) |
| `pocket_analysis` | Binding site detection and druggability scoring |
| `docking_batch` | High-throughput molecular docking |
| `interaction_map` | Protein-ligand contact analysis |
| `pose_compare` | RMSD and interaction fingerprint comparison |
| `hit_prioritize` | Multi-criteria hit ranking |
| `session_report` | Automated documentation generation |

## Configuration

```yaml
# ~/.config/pymolcode/config.yaml

llm:
  provider: anthropic  # anthropic, openai, gemini, ollama
  model: claude-3-opus-20240229
  api_key: ${ANTHROPIC_API_KEY}

mcp:
  servers:
    - name: drugclip
      command: python -m drugclip_mcp_server
    - name: rdkit
      command: python -m rdkit_mcp_server

policies:
  destructive_actions: require_confirmation
  external_calls: log_and_notify
  max_concurrent_tasks: 4
```

## Memory System

PymolCode includes a persistent memory system that allows the LLM agent to learn from mistakes and remember preferences across sessions. The memory system uses YAML files for human-readability and easy manual inspection.

### Memory Files

```
memory/
├── memory.yaml         # General preferences and accumulated knowledge
├── lessons.yaml        # Lessons learned from mistakes (prevents repetition)
├── now.yaml            # Active tasks and priorities (P0-P3)
└── YYYY-MM-DD.yaml     # Daily session notes
```

### Memory Categories

- **Preferences**: User's preferred workflows, visualization styles, naming conventions
- **Lessons**: Documented mistakes with corrective actions (e.g., "Always verify PyMOL command success")
- **Knowledge**: Domain expertise accumulated over time (binding site patterns, common issues)
- **Active Tasks**: Current session focus and priorities

### Agent Identity

The agent's core identity and behavioral guidelines are defined in [SOUL.md](./SOUL.md), which establishes:
- Core values (accuracy, verification, transparency)
- Critical rules (never report success without verification)
- Behavioral guidelines

### Artifact Organization

Generated artifacts are organized in two locations:

**Project-local** (for session outputs):
```
.pymolcode_artifacts/
├── screenshots/        # PNG visualization exports
├── structures/         # PDB/CIF molecular structures
└── reports/            # Generated analysis reports
```

**Global** (for cached data, configurable via `~/.pymolcode/config.json`):
```
~/.pymolcode/
├── artifacts/
│   ├── pdb/            # Downloaded PDB structures (cached)
│   ├── screenshots/    # Default screenshot location
│   └── scripts/        # Generated scripts
├── sessions/           # Saved session states
└── plugins/            # Installed plugins
```

## Development

### Project Structure

```
pymolcode/
├── python/              # Main Python package
│   ├── cli.py          # CLI entry point
│   ├── agent/          # LLM agent orchestration
│   ├── bridge/         # JSON-RPC bridge server
│   ├── pymol/          # PyMOL integration
│   ├── session/        # Session management
│   ├── skill/          # Skill registry
│   ├── protocol/       # JSON-RPC protocol
│   ├── persistence/    # State persistence
│   ├── memory/         # Persistent memory system
│   └── plugins/        # Plugin loader
├── node/               # TypeScript bridge client
├── launcher/           # Bridge orchestrator
├── docs/               # Documentation
├── memory/             # YAML memory files
├── skills/             # Reference skills (not project code)
├── .pymolcode_artifacts/  # Generated artifacts (PNG, PDB, etc.)
└── tests/              # Test suites (not in git)
```

### Running Tests

> **Note**: The `tests/` directory is not included in the repository. Create tests locally for development.

```bash
# Unit tests
pytest tests/unit

# Integration tests (requires PyMOL)
pytest tests/integration

# All tests with coverage
pytest --cov=python tests/
```

### Code Quality

```bash
ruff check python/      # Lint
ruff format python/     # Format
mypy python/           # Type check
```

## Documentation

| Document | Description |
|----------|-------------|
| [API Reference](./docs/api.md) | Python SDK and JSON-RPC API |
| [PyMOL Plugin](./docs/pymol-plugin-interface.md) | GUI integration guide |
| [Skills Guide](./docs/skills.md) | Creating custom skills |
| [MCP Integration](./docs/mcp.md) | External tool integration |
| [Memory System](./docs/memory.md) | Persistent agent memory |
| [Headless Rendering](./docs/headless-rendering.md) | Running without display |
| [External MCP Servers](./docs/external-mcp-servers.md) | DrugCLIP, RDKit (planned) |
| [Documentation Index](./docs/index.md) | All documentation |
| [Skills Sources](./skills/SOURCES.md) | Skills attribution & licenses |
| [SOUL.md](./SOUL.md) | Agent identity & behavioral guidelines |
| [AGENTS.md](./AGENTS.md) | AI agent context |

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for development guidelines.

## License

MIT License - see [LICENSE](./LICENSE) for details.

## Author

- **CHENRAN JIANG** - Creator & Lead Developer

## Acknowledgments

- [PyMOL](https://github.com/schrodinger/pymol-open-source) - Molecular visualization foundation
- [OpenCode](https://github.com/opencode-ai/opencode) - LLM agent patterns
- [MCP](https://modelcontextprotocol.io) - Tool integration protocol
- [pymol-mcp](https://github.com/vrtejus/pymol-mcp) - MCP integration reference
- [ChatMOL](https://github.com/ChatMol/ChatMol) - LLM interface patterns

## Citation

If you use PymolCode in your research, please cite:

```bibtex
@software{pymolcode2026,
  title = {PymolCode: LLM-Enhanced Molecular Visualization Platform},
  author = {Jiang, Chenran},
  year = {2026},
  url = {https://github.com/chenDeepin/pymolcode}
}
```

---

*Built with ❤️ for the drug discovery community*
