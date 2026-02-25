# Attribution and Third-Party Notices

This project incorporates concepts, patterns, and code from the following open-source projects.
This software is a separate, independent project and is not affiliated with, endorsed by,
or connected to any of the projects listed below.

---

## Embedded Third-Party Code

### PyMOL Open-Source (Included)

**Project**: https://github.com/schrodinger/pymol-open-source
**License**: BSD-like (see below)
**Copyright**: Schrodinger, LLC
**Location**: `third-party/pymol-open-source-master/`

pymolcode includes a copy of the PyMOL open-source source code in the `third-party/` directory
for reference and development purposes. This embedded copy is subject to the PyMOL license terms
and trademark restrictions below.

#### PyMOL License Terms

```
Open-Source PyMOL is Copyright (C) Schrodinger, LLC.

All Rights Reserved

Permission to use, copy, modify, distribute, and distribute modified
versions of this software and its built-in documentation for any
purpose and without fee is hereby granted, provided that the above
copyright notice appears in all copies and that both the copyright
notice and this permission notice appear in supporting documentation,
and that the name of Schrodinger, LLC not be used in advertising or
publicity pertaining to distribution of the software without specific,
written prior permission.

SCHRODINGER, LLC DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE,
INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN
NO EVENT SHALL SCHRODINGER, LLC BE LIABLE FOR ANY SPECIAL, INDIRECT OR
CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS
OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE
OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE
USE OR PERFORMANCE OF THIS SOFTWARE.
```

#### PyMOL Trademark Notice

PyMOL(TM) is a trademark of Schrodinger, LLC.

pymolcode is NOT a PyMOL product. pymolcode is a separate, independent software
project that includes PyMOL source code and integrates with PyMOL as an external dependency.

When describing this software, you may use phrases such as:
- "Built using PyMOL(TM) technology"
- "Integrates with PyMOL(TM)"
- "Compatible with PyMOL(TM)"
- "Contains PyMOL(TM) source code"

The notice "PyMOL is a trademark of Schrodinger, LLC" should be included in
documentation where the PyMOL trademark appears.

---

## Architectural Inspiration

### OpenCode

**Project**: https://github.com/opencode-ai/opencode
**License**: MIT License
**Copyright**: (c) 2025 opencode

pymolcode draws architectural inspiration and design patterns from OpenCode's
agent system, skill architecture, and TUI interface design. No source code
from OpenCode is directly included in this project.

#### OpenCode License Terms

```
MIT License

Copyright (c) 2025 opencode

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## Reference Skills (skills/ directory)

The `skills/` directory contains reference skills for AI agents, derived from
various open-source projects. These are **reference materials** and not part of
the pymolcode core application.

For detailed attributions and licenses, see [skills/SOURCES.md](skills/SOURCES.md).

**Primary sources include:**
- [Claude Code](https://github.com/anthropics/claude-code) (Anthropic)
- [OpenCode](https://github.com/opencode-ai/opencode) agent patterns
- [Orchestra Research](https://github.com/orchestra-research) scientific skills
- [Trail of Bits](https://github.com/trailofbits) security skills

---

## Python Dependencies

pymolcode depends on the following Python packages. Full license information
is available in the package metadata (via `pip show <package>`).

### Core Dependencies

| Package | License | Purpose |
|---------|---------|---------|
| pydantic | MIT | Data validation |
| pydantic-settings | MIT | Configuration management |
| anyio | MIT | Async compatibility |
| pyyaml | MIT | YAML parsing |
| mcp | MIT | Model Context Protocol SDK |
| litellm | MIT | Multi-provider LLM abstraction |
| click | BSD-3-Clause | CLI framework |
| textual | MIT | TUI framework |
| rich | MIT | Terminal formatting |
| structlog | MIT | Structured logging |
| httpx | BSD-3-Clause | HTTP client |
| numpy | BSD-3-Clause | Numerical computing |
| pandas | BSD-3-Clause | Data analysis |
| rdkit | BSD-3-Clause | Cheminformatics |
| biopython | Biopython (MIT-like) | Bioinformatics |

### Optional Dependencies

| Package | License | Purpose | Note |
|---------|---------|---------|------|
| PyQt5 | GPL-3.0 | GUI toolkit | Optional (`[gui]`) |
| PyQt6 | GPL-3.0 | GUI toolkit | Optional (`[gui]`) |
| MDAnalysis | GPL-2.0 | Molecular dynamics | Optional (`[analysis]`) |
| mdtraj | LGPL-2.1 | Trajectory analysis | Optional (`[analysis]`) |

### Development Dependencies

| Package | License | Purpose |
|---------|---------|---------|
| pytest | MIT | Testing framework |
| pytest-cov | MIT | Coverage reporting |
| pytest-asyncio | MIT | Async test support |
| ruff | MIT | Linting & formatting |
| mypy | MIT | Type checking |
| black | MIT | Code formatting |

---

## Node.js Dependencies (node/ directory)

The TypeScript bridge client uses minimal dependencies:

| Package | License | Purpose |
|---------|---------|---------|
| @types/node | MIT | TypeScript type definitions |
| typescript | Apache-2.0 | TypeScript compiler |
| bun-types | MIT | Bun runtime types |

---

## Acknowledgments

This project builds upon the work of many open-source contributors:

- [PyMOL](https://github.com/schrodinger/pymol-open-source) - Molecular visualization foundation
- [OpenCode](https://github.com/opencode-ai/opencode) - LLM agent patterns
- [MCP](https://modelcontextprotocol.io) - Model Context Protocol
- [pymol-mcp](https://github.com/vrtejus/pymol-mcp) - MCP integration reference
- [ChatMOL](https://github.com/ChatMol/ChatMol) - LLM interface patterns
- [RDKit](https://github.com/rdkit/rdkit) - Cheminformatics toolkit

---

## Disclaimer

pymolcode is provided "as is" without warranty of any kind, express or implied.
The authors and contributors are not responsible for any damages arising from
the use of this software.

This project is intended for research and educational purposes in drug discovery.
Users are responsible for ensuring compliance with applicable laws, regulations,
and third-party license terms when using this software.

---

*Last updated: February 2026*
