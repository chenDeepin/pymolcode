"""Tool registry and execution for the agent layer."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from python.pymol.executor import CommandExecutor

__all__ = ["Tool", "ToolRegistry", "register_memory_tools"]


@dataclass(frozen=True)
class ToolSchema:
    """JSON Schema definition for a tool."""

    name: str
    description: str
    parameters: dict[str, Any]

    def to_openai_format(self) -> dict[str, Any]:
        """Convert to OpenAI function calling format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


@dataclass
class Tool:
    """A callable tool that can be invoked by the LLM."""

    schema: ToolSchema
    handler: Callable[[dict[str, Any]], str]
    is_dangerous: bool = False
    requires_confirmation: bool = False


class ToolRegistry:
    """Registry of available tools for the agent."""

    def __init__(self, command_executor: CommandExecutor | None = None) -> None:
        self._tools: dict[str, Tool] = {}
        self._command_executor = command_executor
        self._register_builtin_tools()

    def _register_builtin_tools(self) -> None:
        """Register built-in PyMOL tools."""

        # PyMOL: Load structure
        self.register(
            Tool(
                schema=ToolSchema(
                    name="pymol_load",
                    description="Load a molecular structure into PyMOL. Supports local files (PDB, SDF, MOL2) and PDB codes.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "source": {
                                "type": "string",
                                "description": "Path to structure file or PDB code (e.g., '1ubq' or '/path/to/structure.pdb')",
                            },
                            "name": {
                                "type": "string",
                                "description": "Optional name for the loaded object",
                            },
                        },
                        "required": ["source"],
                    },
                ),
                handler=self._handle_pymol_load,
            )
        )

        # PyMOL: Set representation
        self.register(
            Tool(
                schema=ToolSchema(
                    name="pymol_show",
                    description="Set the representation style for a molecular selection.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "selection": {
                                "type": "string",
                                "description": "PyMOL selection expression (e.g., 'chain A' or 'resn HEM')",
                            },
                            "representation": {
                                "type": "string",
                                "enum": [
                                    "cartoon",
                                    "surface",
                                    "sticks",
                                    "spheres",
                                    "lines",
                                    "ribbon",
                                ],
                                "description": "Representation style to apply",
                            },
                            "color": {
                                "type": "string",
                                "description": "Color to apply (e.g., 'red', 'blue', 'cyan')",
                            },
                        },
                        "required": ["selection", "representation"],
                    },
                ),
                handler=self._handle_pymol_show,
            )
        )

        # PyMOL: Color
        self.register(
            Tool(
                schema=ToolSchema(
                    name="pymol_color",
                    description="Apply color to a molecular selection.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "selection": {
                                "type": "string",
                                "description": "PyMOL selection expression",
                            },
                            "color": {
                                "type": "string",
                                "description": "Color name or hex code",
                            },
                        },
                        "required": ["selection", "color"],
                    },
                ),
                handler=self._handle_pymol_color,
            )
        )

        # PyMOL: Zoom
        self.register(
            Tool(
                schema=ToolSchema(
                    name="pymol_zoom",
                    description="Zoom the camera to a selection or all objects.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "selection": {
                                "type": "string",
                                "description": "Selection to zoom to (default: 'all')",
                            },
                        },
                    },
                ),
                handler=self._handle_pymol_zoom,
            )
        )

        # PyMOL: List objects
        self.register(
            Tool(
                schema=ToolSchema(
                    name="pymol_list",
                    description="List all loaded molecular objects in the current session.",
                    parameters={
                        "type": "object",
                        "properties": {},
                    },
                ),
                handler=self._handle_pymol_list,
            )
        )

        # PyMOL: Screenshot
        self.register(
            Tool(
                schema=ToolSchema(
                    name="pymol_screenshot",
                    description="Take a screenshot of the current PyMOL view.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "filename": {
                                "type": "string",
                                "description": "Output filename (e.g., 'scene.png')",
                            },
                            "width": {
                                "type": "integer",
                                "description": "Image width in pixels (default: 1280)",
                            },
                            "height": {
                                "type": "integer",
                                "description": "Image height in pixels (default: 720)",
                            },
                            "ray": {
                                "type": "boolean",
                                "description": "Use ray tracing for high-quality render (default: true)",
                            },
                        },
                        "required": ["filename"],
                    },
                ),
                handler=self._handle_pymol_screenshot,
                is_dangerous=True,
                requires_confirmation=True,
            )
        )

        # PyMOL: Align structures
        self.register(
            Tool(
                schema=ToolSchema(
                    name="pymol_align",
                    description="Align mobile structure to target reference structure. Returns RMSD after alignment. Use backbone atoms for best results.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "mobile": {
                                "type": "string",
                                "description": "Selection or object name for the mobile structure to align",
                            },
                            "target": {
                                "type": "string",
                                "description": "Selection or object name for the reference structure",
                            },
                            "method": {
                                "type": "string",
                                "description": "Alignment method: 'ce' (default), 'align', 'super' (see PyMOL docs)",
                            },
                            "cutoff": {
                                "type": "number",
                                "description": "RMSD cutoff for rejection (default: 1.0)",
                            },
                            "cycles": {
                                "type": "integer",
                                "description": "Number of refinement cycles (default: 0)",
                            },
                        },
                        "required": ["mobile", "target"],
                    },
                ),
                handler=self._handle_pymol_align,
            )
        )

    def _handle_pymol_align(self, args: dict[str, Any]) -> str:
        mobile = args.get("mobile", "")
        target = args.get("target", "")
        method = args.get("method", "ce")
        cutoff = args.get("cutoff", 1.0)
        cycles = args.get("cycles", 0)
        result = self._execute_pymol_command(
            "align",
            {
                "mobile": mobile,
                "target": target,
                "method": method,
                "cutoff": cutoff,
                "cycles": cycles,
            },
        )
        return json.dumps(result)

        # PyMOL: Align structures

        # PyMOL: Align structures
        self.register(
            Tool(
                schema=ToolSchema(
                    name="pymol_align",
                    description="Align mobile structure to target reference structure using backbone atoms.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "mobile": {
                                "type": "string",
                                "description": "Selection for mobile structure to align",
                            },
                            "target": {
                                "type": "string",
                                "description": "Selection for target/reference structure",
                            },
                            "method": {
                                "type": "string",
                                "enum": ["ce", "align"],
                                "description": "Alignment method: 'ce' (default) or 'align'",
                            },
                            "cutoff": {
                                "type": "number",
                                "description": "RMSD cutoff for rejection (default: 1.0)",
                            },
                        },
                        "required": ["mobile", "target"],
                    },
                ),
                handler=self._handle_pymol_align,
            )
        )

        # Python code execution (sandboxed)
        self.register(
            Tool(
                schema=ToolSchema(
                    name="python_exec",
                    description="Execute Python code in the PyMOL environment. Use for complex operations not covered by other tools.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "Python code to execute. The 'cmd' object is available for PyMOL commands.",
                            },
                        },
                        "required": ["code"],
                    },
                ),
                handler=self._handle_python_exec,
                is_dangerous=True,
                requires_confirmation=True,
            )
        )

    def register(self, tool: Tool) -> None:
        """Register a tool."""
        self._tools[tool.schema.name] = tool

    def get(self, name: str) -> Tool | None:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> list[Tool]:
        """List all registered tools."""
        return list(self._tools.values())

    def get_openai_tools(self) -> list[dict[str, Any]]:
        """Get all tools in OpenAI function calling format."""
        return [tool.schema.to_openai_format() for tool in self._tools.values()]

    def execute(self, name: str, arguments: dict[str, Any]) -> str:
        """Execute a tool and return the result."""
        tool = self.get(name)
        if tool is None:
            return json.dumps({"error": f"Unknown tool: {name}"})

        try:
            result = tool.handler(arguments)
            return result
        except Exception as exc:
            return json.dumps({"error": f"Tool execution failed: {exc}"})

    def set_command_executor(self, executor: CommandExecutor) -> None:
        """Set the command executor for PyMOL operations."""
        self._command_executor = executor

    def _execute_pymol_command(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        """Execute a PyMOL command through the executor."""
        if self._command_executor is None:
            return {"ok": False, "error": "PyMOL executor not available"}

        command = json.dumps({"method": method, "params": params})
        return self._command_executor.execute(command)

    def _handle_pymol_load(self, args: dict[str, Any]) -> str:
        source = args.get("source", "")
        name = args.get("name")
        result = self._execute_pymol_command("load_structure", {"source": source, "name": name})
        return json.dumps(result)

    def _handle_pymol_show(self, args: dict[str, Any]) -> str:
        selection = args.get("selection", "all")
        representation = args.get("representation", "cartoon")
        color = args.get("color")
        result = self._execute_pymol_command(
            "set_representation",
            {"selection": selection, "representation": representation, "color": color},
        )
        return json.dumps(result)

    def _handle_pymol_color(self, args: dict[str, Any]) -> str:
        selection = args.get("selection", "all")
        color = args.get("color", "white")
        result = self._execute_pymol_command(
            "color_object", {"selection": selection, "color": color}
        )
        return json.dumps(result)

    def _handle_pymol_zoom(self, args: dict[str, Any]) -> str:
        selection = args.get("selection", "all")
        result = self._execute_pymol_command("zoom", {"selection": selection})
        return json.dumps(result)

    def _handle_pymol_list(self, _args: dict[str, Any]) -> str:
        result = self._execute_pymol_command("list_objects", {})
        return json.dumps(result)

    def _handle_pymol_screenshot(self, args: dict[str, Any]) -> str:
        filename = args.get("filename", "screenshot.png")
        width = args.get("width", 1280)
        height = args.get("height", 720)
        ray = args.get("ray", True)
        result = self._execute_pymol_command(
            "screenshot",
            {"filename": filename, "width": width, "height": height, "ray": ray},
        )
        return json.dumps(result)

    def _handle_python_exec(self, args: dict[str, Any]) -> str:
        """Handle Python code execution through CommandExecutor."""
        code = args.get("code", "")
        if not code:
            return json.dumps({"error": "No code provided"})

        if self._command_executor is None:
            return json.dumps({"error": "PyMOL executor not available"})

        result = self._command_executor.execute_python(code)
        return json.dumps(result)

    def register_memory_tools(self, workspace_path: Path) -> None:
        """Register memory tools for persistent knowledge storage.

        Args:
            workspace_path: Base directory for memory storage
        """
        from python.memory.store import MemoryStore
        from python.memory.tools import MemoryReadTool, MemoryWriteTool

        memory_path = workspace_path / "memory" / "MEMORY.md"
        memory_store = MemoryStore(workspace_path)

        # Initialize memory files if they don't exist
        memory_store.initialize_if_missing()

        # Create tool instances
        read_tool = MemoryReadTool(memory_path=memory_path)
        write_tool = MemoryWriteTool(memory_path=memory_path)

        # Register memory_read
        self.register(
            Tool(
                schema=ToolSchema(
                    name="memory_read",
                    description=read_tool.description,
                    parameters=read_tool.get_input_schema(),
                ),
                handler=lambda args: asyncio.run(read_tool.execute(**args)),
            )
        )

        # Register memory_write
        self.register(
            Tool(
                schema=ToolSchema(
                    name="memory_write",
                    description=write_tool.description,
                    parameters=write_tool.get_input_schema(),
                ),
                handler=lambda args: asyncio.run(write_tool.execute(**args)),
            )
        )


def register_memory_tools(registry: ToolRegistry, workspace_path: Path) -> None:
    """Convenience function to register memory tools on a registry.

    Args:
        registry: ToolRegistry instance
        workspace_path: Base directory for memory storage
    """
    registry.register_memory_tools(workspace_path)
