# PymolCode

> **LLM-Enhanced Molecular Visualization Platform for Drug Discovery**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

**PymolCode** fuses LLM agent capabilities with [PyMOL](https://github.com/schrodinger/pymol-open-source)'s molecular visualization to create an intelligent platform for structure-based drug discovery.

## Features

- 🤖 **Conversational Molecular Visualization** - Natural language control of PyMOL
- 🧠 **Persistent Memory System** - Agent learns from mistakes and remembers preferences across sessions
- ⚡ **Hephaestus Orchestrator** - Autonomous deep work with two-stage review (spec + quality)
- 🔐 **OAuth Authentication** - Secure login for OpenAI, Google, GitHub Copilot, Anthropic
- 🚀 **Ultrawork Command** - One-command agentic workflow execution
- 🔬 **Automated Drug Discovery Workflows** - Agent-driven structure-based design
- 💻 **Dual Interface** - CLI and PyMOL GUI plugin
- 🔧 **Extensible Skill System** - Drug discovery-specific agent skills with Oh-My-OpenCode integration
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
│  Session │ Agent │ Skills │ Bridge │ Memory │ Auth │ Hephaestus │
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

# Install PyMOL (required for GUI mode)
pip install pymol-open-source

# (Optional) Verify installation
pymolcode --version
```

### OAuth Configuration (Optional)

For OAuth-based authentication with LLM providers, set these environment variables:

```bash
# OpenAI (ChatGPT Plus/Pro device code flow)
export OPENAI_CLIENT_ID="your-client-id"

# Google Gemini (OAuth device code flow)
export GOOGLE_CLIENT_ID="your-client-id"
export GOOGLE_CLIENT_SECRET="your-client-secret"

# GitHub Copilot (device code flow)
export GITHUB_COPILOT_CLIENT_ID="your-client-id"
```

> **Note**: OAuth is optional. You can also use API keys directly with `pymolcode auth login <provider>`.

> **Security**: Never commit client IDs or secrets to version control. For GitHub upload, all OAuth client IDs are read from environment variables.

## Usage

### Authentication

```bash
# Login with OAuth (recommended)
pymolcode auth login openai       # Device code flow for ChatGPT Plus/Pro
pymolcode auth login google       # OAuth for Gemini
pymolcode auth login github-copilot  # GitHub Copilot
pymolcode auth login anthropic    # API key for Claude

# List stored credentials
pymolcode auth list

# Remove credentials
pymolcode auth logout openai
```

### Agentic Workflows

```bash
# One-command workflow execution
pymolcode ultrawork "analyze TEAD1 binding pocket and dock 10 ligands"
```

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

### Ultrawork Example

```bash
$ pymolcode ultrawork "Load 3KYS, identify binding pockets, and generate a report"

  pymolcode ultrawork
  Goal: Load 3KYS, identify binding pockets, and generate a report

  Hephaestus crafting plan...
  4 steps identified:

    1. [structure] Load PDB structure 3KYS
    2. [analysis] Identify binding pockets using Fpocket
    3. [analysis] Calculate pocket druggability scores
    4. [visualization] Generate pocket visualization and report

  Forging...

  Results: 4/4 completed

    [+] Load PDB structure 3KYS
    [+] Identify binding pockets using Fpocket
    [+] Calculate pocket druggability scores
    [+] Generate pocket visualization and report
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
# ~/.pymolcode/config.json
{
  "llm": {
    "provider": "anthropic",
    "model": "claude-opus-4-6",
    "auth_type": "oauth"
  },
  "auth": {
    "providers": {
      "anthropic": {"type": "oauth", "refresh_on_expiry": true},
      "openai": {"type": "oauth"},
      "google": {"type": "oauth"}
    }
  },
  "agents": {
    "hephaestus": {
      "model": "claude-opus-4-6",
      "parallel_limit": 5
    }
  },
  "skills": {
    "discovery_sources": [
      "local://~/.pymolcode/skills",
      "omo://code-yeongyu/oh-my-opencode"
    ]
  }
}
```

## Hephaestus Orchestrator

Hephaestus is the discipline orchestrator for autonomous deep work:

- **Planning**: Decomposes goals into concrete implementation steps
- **Delegation**: Dispatches tasks to category-specific specialists
- **Review Gates**: Two-stage review (spec compliance + code quality)
- **Completion Enforcement**: Drives all tasks to completion

**Preferred Models**:
- Claude Opus 4.6 / 4.5
- GPT-5.3 / 5.2 Codex
- GLM-5 (Zhipu AI)
- Kimi K2.5

## Memory System

PymolCode includes a persistent memory system that allows the LLM agent to learn from mistakes and remember preferences across sessions.

### Memory Files

```
memory/
├── memory.yaml         # General preferences and accumulated knowledge
├── lessons.yaml        # Lessons learned from mistakes (prevents repetition)
├── now.yaml            # Active tasks and priorities (P0-P3)
└── YYYY-MM-DD.yaml     # Daily session notes
```

### Artifact Organization

```
~/.pymolcode/
├── auth.json           # OAuth tokens (0o600 permissions)
├── artifacts/
│   ├── pdb/            # Downloaded PDB structures (cached)
│   ├── screenshots/    # Default screenshot location
│   └── scripts/        # Generated scripts
├── sessions/           # Saved session states
├── plugins/            # Installed plugins
└── skills/             # User-installed skills
```

## Development

### Project Structure

```
pymolcode/
├── python/              # Main Python package
│   ├── cli.py          # CLI entry point
│   ├── agent/          # LLM agent orchestration
│   ├── auth/           # OAuth authentication
│   ├── bridge/         # JSON-RPC bridge server
│   ├── pymol/          # PyMOL integration
│   ├── session/        # Session management
│   ├── skill/          # Skill registry & bridge
│   ├── workflow/       # Ultrawork command
│   ├── validation/     # Hash validation
│   ├── memory/         # Persistent memory system
│   └── plugins/        # Plugin loader
├── node/               # TypeScript bridge client
├── launcher/           # Bridge orchestrator
├── docs/               # Documentation
├── memory/             # YAML memory files
├── skills/             # Reference skills (10 categories)
└── tests/              # Test suites
```

### Running Tests

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
- [OpenCode](https://github.com/sst/opencode) - LLM agent patterns
- [oh-my-opencode](https://github.com/code-yeongyu/oh-my-opencode) - Hephaestus orchestrator patterns
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
