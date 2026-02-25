# Skills Guide

> Creating and using agent skills in pymolcode

## Overview

Skills are domain-specific agent capabilities for drug discovery workflows. Each skill is a typed, reproducible operation.

## Built-in Skills

Core skills implemented in `python/skill/builtin.py`:

| Skill | Description |
|-------|-------------|
| `structure_analysis` | Analyze molecular structure and generate comprehensive reports |
| `binding_site_analysis` | Identify and characterize potential binding sites in proteins |
| `ligand_comparison` | Compare multiple ligand structures with alignment reports |
| `trajectory_analysis` | Analyze molecular dynamics trajectories (RMSD, RMSF) |

## Skill Workflow

Each skill follows a structured workflow:

```
precheck → run → validate → summarize → persist
```

## Using Skills

### Via CLI

```bash
pymolcode skill run binding_site_analysis --object-name 3KYS
```

### Via Python API

```python
from python.skill import SkillRegistry

registry = SkillRegistry()
skill = registry.get("binding_site_analysis")
result = await skill.execute(object_name="3KYS")
```

### Via JSON-RPC

```json
{
  "jsonrpc": "2.0",
  "method": "skill.execute",
  "params": {
    "name": "binding_site_analysis",
    "args": {"object_name": "3KYS"}
  }
}
```

## Creating Custom Skills

Skills are discovered from `skills/*/SKILL.md` files with executable scripts.

### Skill Definition

```yaml
# skills/my_skill/SKILL.md
name: my_custom_skill
description: Custom analysis workflow
steps:
  - precheck: validate_inputs
  - run: execute_analysis
  - validate: check_results
  - summarize: generate_report
  - persist: save_outputs
```

## Reference Skills

The `skills/` directory contains reference skill implementations:

| Category | Description |
|----------|-------------|
| `00-core/` | Core utilities and planning |
| `01-scientific/` | Scientific computing (cheminformatics, genomics) |
| `02-research/` | Drug discovery research tools |
| `03-ai-ml/` | ML/AI integration |
| `04-testing/` | Testing patterns |
| `05-backend/` | Backend development |
| `06-documentation/` | Documentation tools |
| `07-security/` | Security analysis |

> **Note**: These are reference implementations, not core pymolcode code.
> See [skills/SOURCES.md](../skills/SOURCES.md) for attribution and license information.

## See Also

- [API Reference](./api.md) - Programmatic access
- [PyMOL Plugin](./pymol-plugin-interface.md) - GUI integration
