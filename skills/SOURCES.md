# Skills Attribution & Sources

> This directory contains reference skills for AI agents, derived from various open-source projects and documentation.

## Overview

The skills in this directory are educational and reference materials designed to enhance AI agent capabilities. They are **not** part of the pymolcode core application but are included as reference implementations.

## License

Skills in this directory are licensed under:
- **Apache License 2.0** (most skills) - See individual `LICENSE.txt` files
- **MIT License** (some skills) - See SKILL.md headers

## Primary Sources

### Claude Code Skills (Anthropic)

Many skills are derived from or inspired by [Claude Code](https://github.com/anthropics/claude-code) patterns and best practices for AI-assisted development.

### OpenCode Skills

Skills adapted from [OpenCode](https://github.com/opencode-ai/opencode) agent patterns:
- `00-core/` - Core utilities and planning
- `17-agents/` - Agent orchestration patterns

### Orchestra Research Skills

Scientific and AI/ML skills from [Orchestra Research](https://github.com/orchestra-research):
- `01-scientific/` - Scientific computing skills
- `03-ai-ml/` - Machine learning and AI skills

### Trail of Bits Security Skills

Security-focused skills from [Trail of Bits](https://github.com/trailofbits):
- `07-security/` - Security analysis, fuzzing, auditing

## Category Sources

| Category | Primary Source | License |
|----------|---------------|---------|
| `00-core/` | Claude Code, OpenCode | Apache 2.0 |
| `01-scientific/` | Orchestra Research, K-Dense | Apache 2.0 |
| `02-research/` | Orchestra Research | Apache 2.0 |
| `03-ai-ml/` | Orchestra Research | MIT |
| `04-testing/` | OpenCode, Trail of Bits | Apache 2.0 |
| `05-backend/` | OpenCode | Apache 2.0 |
| `06-documentation/` | Orchestra Research | Apache 2.0 |
| `07-security/` | Trail of Bits | Apache 2.0 |
| `08-productivity/` | OpenCode | Apache 2.0 |
| `09-agents/` | OpenCode | Apache 2.0 |

## Key Projects Acknowledged

The skills reference documentation from many open-source projects. See:
- [Open Source Sponsors](./01-scientific/open-source-sponsors.md) - Comprehensive list of scientific projects
- [Scientific Skills](./01-scientific/scientific-skills.md) - Detailed database and package references

### Notable Projects

| Project | Description | License |
|---------|-------------|---------|
| [PyMOL](https://github.com/schrodinger/pymol-open-source) | Molecular visualization | BSD-3-Clause |
| [RDKit](https://github.com/rdkit/rdkit) | Cheminformatics | BSD-3-Clause |
| [HuggingFace](https://huggingface.co) | ML models & datasets | Apache 2.0 |
| [LangChain](https://github.com/langchain-ai/langchain) | LLM framework | MIT |
| [Semgrep](https://github.com/returntocorp/semgrep) | Static analysis | LGPL-2.1 |
| [CodeQL](https://github.com/github/codeql) | Code analysis | Custom |

## Usage in pymolcode

These skills are **reference materials** included for:
1. Agent capability enhancement
2. Workflow pattern examples
3. Best practice documentation

They are not executed as part of pymolcode's core functionality.

## Contributing

If you identify a missing attribution or source:
1. Open an issue with details
2. Include the skill path and original source
3. Provide license information if available

## Copyright

Individual skills retain their original copyright notices. See:
- `SKILL.md` headers for author and license info
- `LICENSE.txt` files in skill directories
- `references/` folders for detailed source documentation

---

*Last updated: February 2026*

### PyMOLWiki Scripts
- Source: https://github.com/Pymol-Scripts/Pymol-script-repo
- License: BSD-2-Clause (permissive, commercial-compatible)
- Scripts integrated: show_ligand_interactions, findseq, colorbyrmsd, extra_fit, center_of_mass, quickdisplays, findSurfaceResidues, distancetoatom, anglebetweenhelices, cgo_arrow
