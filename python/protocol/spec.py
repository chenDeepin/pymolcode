"""Protocol specification for pymolcode JSON-RPC bridge."""

from __future__ import annotations

from collections.abc import Mapping

JSONRPC_VERSION = "2.0"
PROTOCOL_NAME = "pymolcode-jsonrpc"
PROTOCOL_VERSION = "2.0.0"

CONTENT_LENGTH_HEADER = "Content-Length"
HEADER_ENCODING = "ascii"
BODY_ENCODING = "utf-8"
HEADER_TERMINATOR = b"\r\n\r\n"

SERVER_ERROR_MIN = -32099
SERVER_ERROR_MAX = -32000

METHOD_CATALOG: dict[str, str] = {
    # Bridge / protocol
    "bridge.ping": "Health check and protocol metadata.",
    # PyMOL control
    "pymol.load_structure": "Load a structure into PyMOL from file or PDB code.",
    "pymol.set_representation": "Set representation style (cartoon, surface, etc.) with optional color.",
    "pymol.color_object": "Apply color to a selection.",
    "pymol.align_objects": "Align mobile selection against target selection.",
    "pymol.export_image": "Export current scene as an image artifact.",
    "pymol.zoom": "Zoom camera to selection.",
    "pymol.list_objects": "List all loaded objects.",
    "pymol.select_atoms": "Create a named selection.",
    "pymol.measure_distance": "Measure distance between two atoms.",
    "pymol.get_scene_state": "Get current camera view and object count.",
    "pymol.get_object_info": "Get information about a specific object.",
    # Agent methods (LLM integration)
    "agent.chat": "Send a message to the LLM agent and get a response.",
    "agent.list_sessions": "List all active chat sessions.",
    "agent.get_session": "Get details of a specific chat session.",
    # Skill methods (drug discovery workflows)
    "skill.list": "List all available skills with their schemas.",
    "skill.execute": "Execute a skill with parameters.",
    # Session methods
    "session.save": "Save current session state to a file.",
    "session.load": "Load a previously saved session from a file.",
}

EXAMPLE_REQUEST: dict[str, object] = {
    "jsonrpc": JSONRPC_VERSION,
    "id": 1,
    "method": "bridge.ping",
    "params": {},
}

EXAMPLE_SUCCESS_RESPONSE: dict[str, object] = {
    "jsonrpc": JSONRPC_VERSION,
    "id": 1,
    "result": {
        "protocol": PROTOCOL_NAME,
        "protocol_version": PROTOCOL_VERSION,
        "methods": sorted(METHOD_CATALOG),
    },
}

EXAMPLE_ERROR_RESPONSE: dict[str, object] = {
    "jsonrpc": JSONRPC_VERSION,
    "id": 1,
    "error": {
        "code": -32601,
        "message": "Method not found",
    },
}

# Example agent.chat request
EXAMPLE_AGENT_CHAT_REQUEST: dict[str, object] = {
    "jsonrpc": JSONRPC_VERSION,
    "id": 1,
    "method": "agent.chat",
    "params": {
        "message": "Load structure 1ubq and show it as cartoon in cyan",
        "session_id": None,  # Optional: creates new session if None
    },
}

# Example skill.execute request
EXAMPLE_SKILL_EXECUTE_REQUEST: dict[str, object] = {
    "jsonrpc": JSONRPC_VERSION,
    "id": 2,
    "method": "skill.execute",
    "params": {
        "skill": "structure_analysis",
        "params": {
            "object_name": "protein",
            "include_binding_sites": True,
        },
        "session_id": "default",
    },
}


def protocol_metadata() -> dict[str, object]:
    """Get protocol metadata."""
    return {
        "protocol": PROTOCOL_NAME,
        "protocol_version": PROTOCOL_VERSION,
        "jsonrpc_version": JSONRPC_VERSION,
        "transport": "content-length",
        "methods": sorted(METHOD_CATALOG),
        "method_catalog": METHOD_CATALOG.copy(),
    }


def is_jsonrpc_message(payload: Mapping[str, object]) -> bool:
    """Check if a payload is a valid JSON-RPC message."""
    return payload.get("jsonrpc") == JSONRPC_VERSION
