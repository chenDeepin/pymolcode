# Attribution and Third-Party Notices

This project incorporates concepts and patterns from the following open-source projects.
This software is a separate, independent project and is not affiliated with, endorsed by,
or connected to any of the projects listed below.

---

## PyMOL Open-Source

**Project**: https://github.com/schrodinger/pymol-open-source
**License**: BSD-like (see below)
**Copyright**: Schrodinger, LLC

pymolcode integrates with PyMOL as an external dependency and uses its Python API.
PyMOL source code is NOT included in this project.

### PyMOL License Terms

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

### PyMOL Trademark Notice

PyMOL(TM) is a trademark of Schrodinger, LLC.

pymolcode is NOT a PyMOL product. pymolcode is a separate, independent software
project that integrates with PyMOL as an external dependency.

When describing this software, you may use phrases such as:
- "Built using PyMOL(TM) technology"
- "Integrates with PyMOL(TM)"
- "Compatible with PyMOL(TM)"

The notice "PyMOL is a trademark of Schrodinger, LLC" should be included in
documentation where the PyMOL trademark appears.

---

## OpenCode

**Project**: https://github.com/opencode-ai/opencode
**License**: MIT License
**Copyright**: (c) 2025 opencode

pymolcode draws architectural inspiration and design patterns from OpenCode's
agent system, skill architecture, and TUI interface design. No source code
from OpenCode is directly included in this project.

### OpenCode License Terms

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

## Other Third-Party Dependencies

pymolcode depends on numerous open-source packages. Full license information
for dependencies is available in the package metadata (via `pip show <package>`
or in the `pyproject.toml` file).

Key dependencies include:
- **mcp** - MIT License (Anthropic, PBC)
- **textual** - MIT License (Textualize)
- **pydantic** - MIT License
- **litellm** - MIT License
- **rdkit** - BSD 3-Clause License
- **biopython** - Biopython License (MIT-like)

---

## Disclaimer

pymolcode is provided "as is" without warranty of any kind, express or implied.
The authors and contributors are not responsible for any damages arising from
the use of this software.

This project is intended for research and educational purposes in drug discovery.
Users are responsible for ensuring compliance with applicable laws, regulations,
and third-party license terms when using this software.
