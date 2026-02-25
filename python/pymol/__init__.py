"""PyMOL integration layer for pymolcode.

This package provides:
- CommandExecutor: typed dispatch of PyMOL commands
- PyMOLRuntime: headless PyMOL process management
- panel / __init_plugin__: Qt dock-widget plugin (imported lazily to avoid Qt dep at import time)
"""

from __future__ import annotations

from python.pymol.executor import CommandExecutor
from python.pymol.runtime import PyMOLRuntime

__all__ = [
    "CommandExecutor",
    "PyMOLRuntime",
]
