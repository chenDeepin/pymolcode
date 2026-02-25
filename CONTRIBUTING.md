# Contributing to pymolcode

Thank you for your interest in contributing to pymolcode! This document provides guidelines for development.

## Development Setup

### Prerequisites

- Python 3.11+
- UV package manager (recommended)
- PyMOL 2.5+ (for integration testing)

### Installation

```bash
# Clone the repository
git clone https://github.com/chenDeepin/pymolcode.git
cd pymolcode

# Create virtual environment
uv venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows

# Install with dev dependencies
uv pip install -e ".[dev]"
```

## Project Structure

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
│   └── plugins/        # Plugin loader
├── node/               # TypeScript bridge client
├── launcher/           # Bridge orchestrator
├── docs/               # Documentation
├── skills/             # Reference skills (not project code)
└── tests/              # Test suites (not in git)
```

## Code Style

### Python

- **Line length**: 100 characters max
- **Type checking**: `strict = true` (mypy)
- **Linting**: ruff (E, W, F, I, B, C4, UP, ARG, SIM)
- **Formatting**: ruff format

```bash
# Check and fix
ruff check python/ --fix
ruff format python/

# Type check
mypy python/
```

### TypeScript

```bash
cd node
npm run build
```

## Testing

> **Note**: The `tests/` directory is excluded from git. Create and run tests locally.

### Run Tests

```bash
# Unit tests
pytest tests/unit

# Integration tests (requires PyMOL)
pytest tests/integration

# All tests with coverage
pytest --cov=python tests/
```

### Writing Tests

- Place unit tests in `tests/unit/`
- Place integration tests in `tests/integration/`
- Use pytest markers for PyMOL-dependent tests:
  ```python
  import pytest
  
  @pytest.mark.skip_pymol
  def test_without_pymol():
      ...
  ```

## Pull Request Process

1. **Fork and branch**: Create a feature branch from `main`
2. **Write tests**: Add tests for new functionality
3. **Run checks**: Ensure all tests pass and code is linted
4. **Update docs**: Update relevant documentation
5. **Submit PR**: Open a pull request with a clear description

### PR Checklist

- [ ] Code passes `ruff check` and `mypy`
- [ ] Tests pass (`pytest tests/`)
- [ ] Documentation updated if needed
- [ ] PR description explains the change

## Adding Skills

Skills are domain-specific agent capabilities. To add a new skill:

1. Create directory in `skills/` (these are reference implementations)
2. Add `SKILL.md` with skill definition
3. Add executable scripts in `scripts/` subdirectory
4. Document the skill in `docs/skills.md`

## Architecture Notes

### Key Patterns

- **Hexagonal Architecture**: CLI/Panel → ApplicationService → Domain → Adapters
- **MCP-First**: External tools via Model Context Protocol
- **Bridge Pattern**: Python server ↔ TypeScript client (JSON-RPC over stdio)
- **Type Safety**: All LLM actions validated via Pydantic schemas

### Anti-Patterns (DO NOT)

- `as any` or type suppression
- Direct PyMOL calls from UI layer
- Untyped tool arguments
- Blocking the event loop
- Hardcoded file paths

## Questions?

Open an issue for bugs, feature requests, or questions.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
