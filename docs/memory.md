# Memory System

> Persistent knowledge storage for the pymolcode agent using YAML format

## Overview

The memory system allows pymolcode's agent to learn from mistakes and remember preferences across sessions. Memory is stored in YAML files for easy editing and readability.

## File Structure

```
memory/
├── memory.yaml           # Main memory (preferences, knowledge)
├── lessons.yaml          # Lessons learned from mistakes
├── now.yaml              # Active todos and priorities
└── 2026-02-26.yaml       # Daily session notes
```

## YAML File Formats

### memory.yaml - Main Memory

```yaml
metadata:
  version: "1.0"
  created: "2026-02-26T00:00:00Z"
  updated: "2026-02-26T12:00:00Z"
  scope: workspace
  owner: pymolcode-agent

preferences:
  visualization:
    theme: dark
    protein: cartoon
    ligand: sticks
    surface: transparent
  workflow:
    verify_operations: true
    honest_reporting: true

knowledge:
  cdk_inhibitors:
    target: CDK4/6
    mechanism: Cell cycle arrest in G1 phase
    clinical: [palbociclib, ribociclib, abemaciclib]
    tags: [drug-discovery, kinases]
```

### lessons.yaml - Lessons Learned

```yaml
metadata:
  version: "1.0"
  created: "2026-02-26T00:00:00Z"

lessons:
  - id: lesson-pymol-verification-001
    created: "2026-02-26T00:12:00Z"
    category: pymol
    tags: [critical, verification]
    lesson: Always verify PyMOL load operations by checking object list
    context: Agent reported successful load when pymol_load actually failed
    fix: After any pymol_load, call pymol_list to verify the object exists

  - id: lesson-honest-reporting-001
    created: "2026-02-26T00:15:00Z"
    category: general
    tags: [critical, honesty]
    lesson: Report failures honestly, never make false success claims
    context: Made excuses about PDB accessibility instead of reporting actual error
    fix: Check function results against observable evidence before reporting
```

### now.yaml - Active Todos

```yaml
metadata:
  version: "1.0"
  updated: "2026-02-26T12:00:00Z"

active_todos:
  - id: "1739877600"
    task: "Implement docking visualization"
    priority: P1
    status: pending
    tags: [feature, visualization]
    created: "2026-02-26T10:00:00Z"

  - id: "1739881200"
    task: "Fix screenshot path issue"
    priority: P2
    status: in_progress
    tags: [bug]
    created: "2026-02-26T11:00:00Z"
```

### Daily Session Notes (YYYY-MM-DD.yaml)

```yaml
metadata:
  date: "2026-02-26"
  created: "2026-02-26T09:00:00Z"

events:
  - time: "09:15"
    type: session_start
    content: "Started new session"

  - time: "10:30"
    type: user_request
    content: "Load 8P0M structure"
    metadata:
      pdb_id: 8P0M
      success: false

  - time: "10:45"
    type: lesson_learned
    content: "Recorded lesson about verifying PyMOL operations"
    metadata:
      lesson_id: lesson-pymol-verification-001
```

## Memory Tools

### memory_read

Read from persistent memory storage.

```json
{
  "section": "lessons",
  "tags": ["critical", "pymol"],
  "keywords": ["verification"],
  "limit": 20
}
```

### memory_write

Write to persistent memory storage.

```json
{
  "operation": "create",
  "section": "lessons",
  "data": {
    "lesson": "...",
    "context": "...",
    "fix": "..."
  },
  "tags": ["critical", "pymol"]
}
```

## API Reference

### MemoryStore

```python
from python.memory.store import MemoryStore
from pathlib import Path

store = MemoryStore(workspace=Path("/path/to/workspace"))
store.initialize_if_missing()

# Add a lesson
lesson_id = store.add_lesson(
    lesson="Always verify PyMOL operations",
    context="Reported success when load failed",
    fix="Check object list after load",
    tags=["critical", "pymol"],
    category="pymol"
)

# Add a todo
todo_id = store.add_todo(
    task="Implement feature X",
    priority="P1",
    tags=["feature"]
)

# Complete a todo
store.complete_todo(todo_id)

# Log today's event
store.append_today(
    event_type="user_request",
    content="Load PDB 1UBQ",
    metadata={"pdb_id": "1UBQ"}
)

# Get memory context for system prompt
context = store.get_memory_context(include_lessons=True, include_todos=False)

# Search lessons
results = store.search_lessons(query="pymol", tags=["critical"])
```

## Integration Points

### Agent System

Memory context is injected into the system prompt:

```python
if self._memory_store:
    memory_context = self._memory_store.get_memory_context()
    if memory_context:
        system_prompt = f"{system_prompt}\n\n{memory_context}"
```

### Bridge Server

Initialize memory for a workspace via JSON-RPC:

```json
{
    "jsonrpc": "2.0",
    "method": "memory.initialize",
    "params": {
        "workspace": "/path/to/workspace"
    }
}
```

## Artifact Organization

Generated files (PNG, PDB, CIF) are organized under `.pymolcode_artifacts/`:

```
.pymolcode_artifacts/
├── screenshots/
│   ├── 2026-02-26/
│   │   ├── binding_site.png
│   │   └── complex_view.png
│   └── ...
├── structures/
│   ├── downloaded/
│   │   ├── 8p0m.pdb
│   │   └── 1ubq.cif
│   └── generated/
│       └── docked_complex.pdb
└── sessions/
    └── session-20260226/
        ├── scene.pse
        ├── chat.json
        └── memory/
            ├── memory.yaml
            ├── lessons.yaml
            └── now.yaml
```

## Security

### Data Redaction

The `MemoryPolicy` class automatically redacts sensitive data:

- API keys (`sk-*`, `api_key: ...`)
- Passwords (`password: ...`)
- Tokens (`Bearer ...`)

### Limits

| Limit | Value | Purpose |
|-------|-------|---------|
| Max entry size | 10 KB | Prevent oversized entries |
| Max file size | 1 MB | Prevent memory bloat |
| Max entries per section | 100 | Encourage cleanup |

## Best Practices

### For Adding Lessons

```python
store.add_lesson(
    lesson="Clear, actionable statement",
    context="What happened and why it was wrong",
    fix="Specific action to prevent recurrence",
    tags=["category", "severity"],
    category="pymol|general|workflow"
)
```

### For Managing Todos

```python
# Priority levels: P0 (urgent), P1 (high), P2 (medium), P3 (low)
store.add_todo(task="...", priority="P2")

# Mark complete when done
store.complete_todo(todo_id)
```

### For Session Logging

```python
# Log important events
store.append_today(
    event_type="user_request|lesson_learned|error|milestone",
    content="Description of what happened",
    metadata={"key": "value"}  # Optional
)
```
