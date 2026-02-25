# PyMOL Plugin Interface

> Integrating pymolcode into PyMOL's GUI

## Overview

pymolcode integrates into PyMOL's GUI as an LLM-powered molecular visualization interface. The plugin creates a dockable panel with a chat interface.

## Installation

### Via PyMOL Plugin Manager

1. Open PyMOL
2. Plugin → Plugin Manager → Install New Plugin
3. Select `python/pymol/panel.py` or install via pip

### Via pip

```bash
pip install pymolcode
# Plugin auto-registers via [project.entry-points."pymol.plugins"]
```

## Plugin Entry Point

Entry point defined in `pyproject.toml`:

```toml
[project.entry-points."pymol.plugins"]
pymolcode = "python.pymol.panel:__init_plugin__"
```

Implementation in `python/pymol/panel.py`:

```python
def __init_plugin__():
    """PyMOL plugin entry point for pymolcode."""
    from pymol.Qt import QtWidgets, QtCore
    from python.pymol.panel import PymolcodePanel

    app = QtWidgets.QApplication.instance()
    main_window = app.activeWindow() if app else None
    if main_window is None:
        return

    panel = PymolcodePanel(main_window)
    main_window.addDockWidget(QtCore.Qt.RightDockWidgetArea, panel)
```

## Panel Components

| Component | Description |
|-----------|-------------|
| Chat display | Message history with formatting |
| Input field | User message entry |
| Send button | Trigger agent processing |
| Quick actions | Common operations toolbar |
| Status bar | Processing state indicator |

## Protocol Methods

The following JSON-RPC methods are supported by the bridge:

| Method | Description |
| ------ | ------ |
| `initialize` | Returns protocol version and Capaabilities
| `shutdown` | Cleanly shutdown the bridge server
| `bridge.ping` | Health check and protocol metadata
| `pymol.load_structure` | Load structure from file/PDB code
| `pymol.set_representation` | Set representation style |
| `pymol.color_object` |Apply color to selection |
| `pymol.zoom` |Zoom camera |
| `pymol.list_objects` |List loaded objects |
| `pymol.screenshot` |Take screenshot |
| `agent.chat` |Send message to LLM agent |
| `agent.list_sessions` |List chat sessions |
| `skill.list` |List available skills |
| `skill.execute` |Execute a skill |
| `session.save` |Save session state |
| `session.load` |Load session |

## Tool System
The agent has access to the following PyMOL tools:
- `pymol_load` - Load structures
- `pymol_show` - Set representation
- `pymol_color` - Apply color
- `pymol_zoom` - Zoom camera
- `pymol_list` - List objects
- `pymol_screenshot` - Take screenshot
- `python_exec` - Execute Python code (disabled by default)

## Skill System
Built-in skills for drug discovery workflows:
- `structure_analysis` - Analyze molecular structures
- `binding_site_analysis` - Analyze binding sites
- `ligand_comparison` - Compare ligand structures
- `trajectory_analysis` - Analyze MD trajectories

## Future Extensions

Planned extension points:
- `python/skill/` - Domain-specific skills (docking, MD, QSAR)
- `python/bridge/` - MCP server for external tool integration
- Plugin UI for advanced features (dock widgets, dialogs)

## Testing

```bash
pytest tests/integration/ -m "not skip_pymol"
pytest tests/python/test_pymol_runtime.py
```

## See Also

- [API Reference](./api.md) - Programmatic access
- [Headless Rendering](./headless-rendering.md) - Running without GUI
