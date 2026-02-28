"""Bridge handlers for JSON-RPC method dispatch."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable, Mapping
from concurrent import futures
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from python.protocol.spec import protocol_metadata

if TYPE_CHECKING:
    from python.memory.store import MemoryStore

JSONRPC_VERSION = "2.0"
PROTOCOL_VERSION = "2026-02-25"
DEFAULT_CAPABILITIES = ["initialize", "shutdown"]


class JsonRpcError(Exception):
    """JSON-RPC error."""

    code: int
    message: str

    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class HandlerOutcome:
    """Result of handling a JSON-RPC request."""

    result: dict[str, Any]
    should_shutdown: bool = False


def _get_default_render_capability() -> dict[str, Any]:
    """Get default render capability (lazy import)."""
    try:
        from python.pymol.runtime import PyMOLRuntime

        return PyMOLRuntime.check_render_capability(headless=True)
    except ImportError:
        return {
            "supported": False,
            "mode": "unavailable",
            "message": "PyMOL runtime not available",
        }


class BridgeHandlers:
    """Registry of JSON-RPC method handlers."""

    def __init__(
        self,
        capabilities: list[str] | None = None,
        protocol_version: str = PROTOCOL_VERSION,
        render_capability: dict[str, Any] | None = None,
        command_executor: Callable[[str], dict[str, Any]] | None = None,
        agent: Any | None = None,
        skill_registry: Any | None = None,
        memory_store: MemoryStore | None = None,
        workspace_path: Path | None = None,
    ) -> None:
        self._capabilities: list[str] = list(capabilities or DEFAULT_CAPABILITIES)
        self._protocol_version: str = protocol_version
        self._render_capability: dict[str, Any] = (
            render_capability or _get_default_render_capability()
        )
        self._command_executor: Callable[[str], dict[str, Any]] | None = command_executor
        self._agent = agent
        self._skill_registry = skill_registry
        self._memory_store: MemoryStore | None = memory_store
        self._workspace_path: Path | None = workspace_path

        # Extend capabilities
        self._capabilities.extend(
            [
                "bridge.ping",
                "agent.chat",
                "agent.list_sessions",
                "agent.get_session",
                "skill.list",
                "skill.execute",
                "session.save",
                "session.load",
                "memory.read",
                "memory.write",
                "memory.initialize",
            ]
        )

    def set_agent(self, agent: Any) -> None:
        """Set the agent instance."""
        self._agent = agent

    def set_skill_registry(self, registry: Any) -> None:
        """Set the skill registry."""
        self._skill_registry = registry

    def set_memory_store(self, store: MemoryStore) -> None:
        """Set the memory store."""
        self._memory_store = store
        if self._agent:
            self._agent.set_memory_store(store)

    def initialize_memory(self, workspace_path: Path) -> MemoryStore:
        """Initialize memory system for the workspace."""
        from python.agent.tools import register_memory_tools
        from python.memory.store import MemoryStore

        self._workspace_path = workspace_path
        self._memory_store = MemoryStore(workspace_path)
        self._memory_store.initialize_if_missing()

        if self._agent and hasattr(self._agent, "_tools"):
            register_memory_tools(self._agent._tools, workspace_path)
            self._agent.set_memory_store(self._memory_store)

        return self._memory_store

    def handle(self, method: str, params: object) -> HandlerOutcome:
        """Handle a JSON-RPC method call."""
        if params is not None and not isinstance(params, dict):
            raise JsonRpcError(-32602, "Invalid params")

        params_dict = cast(dict[str, Any], params or {})

        # Core methods
        if method == "initialize":
            return HandlerOutcome(
                result={
                    "protocolVersion": self._protocol_version,
                    "capabilities": self._capabilities,
                    "render_capability": self._render_capability,
                }
            )

        if method == "shutdown":
            return HandlerOutcome(result={"ok": True}, should_shutdown=True)

        if method == "bridge.ping":
            return HandlerOutcome(result=protocol_metadata())

        # PyMOL methods
        if method.startswith("pymol."):
            return self._handle_pymol_method(method, params_dict)

        # Agent methods
        if method.startswith("agent."):
            return self._handle_agent_method(method, params_dict)

        # Skill methods
        if method.startswith("skill."):
            return self._handle_skill_method(method, params_dict)

        # Session methods
        if method.startswith("session."):
            return self._handle_session_method(method, params_dict)

        # Memory methods
        if method.startswith("memory."):
            return self._handle_memory_method(method, params_dict)

        raise JsonRpcError(-32601, "Method not found")

    def _handle_pymol_method(self, method: str, params: dict[str, Any]) -> HandlerOutcome:
        """Handle pymol.* methods."""
        if self._command_executor is None:
            raise JsonRpcError(-32601, "Method not found: PyMOL executor not available")

        executor_payload = {
            "method": method.removeprefix("pymol."),
            "params": params,
        }
        execution = self._command_executor(json.dumps(executor_payload))

        if execution.get("ok") is not True:
            error = execution.get("error")
            if isinstance(error, Mapping):
                error_map = cast(Mapping[str, Any], error)
                message = error_map.get("message")
                if isinstance(message, str) and message:
                    raise JsonRpcError(-32000, message)
            raise JsonRpcError(-32000, "Command execution failed")

        result = execution.get("result")
        if not isinstance(result, Mapping):
            raise JsonRpcError(-32000, "Command result must be an object")
        result_map = cast(Mapping[str, Any], result)
        return HandlerOutcome(result={key: value for key, value in result_map.items()})

    def _handle_agent_method(self, method: str, params: dict[str, Any]) -> HandlerOutcome:
        """Handle agent.* methods."""
        if self._agent is None:
            raise JsonRpcError(-32601, "Method not found: Agent not available")

        if method == "agent.chat":
            return self._handle_agent_chat(params)
        elif method == "agent.list_sessions":
            return self._handle_agent_list_sessions()
        elif method == "agent.get_session":
            return self._handle_agent_get_session(params)

        raise JsonRpcError(-32601, f"Unknown agent method: {method}")

    def _handle_agent_chat(self, params: dict[str, Any]) -> HandlerOutcome:
        """Handle agent.chat method (synchronous wrapper for async agent)."""
        message = params.get("message", "")
        session_id = params.get("session_id")

        if not message:
            raise JsonRpcError(-32602, "message is required")

        try:
            # Run async chat in separate thread with its own event loop
            with futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    self._run_agent_chat_sync,
                    message,
                    session_id,
                )
                response = future.result(timeout=120)
        except futures.TimeoutError:
            raise JsonRpcError(-32000, "Agent chat timed out")
        except Exception as exc:
            raise JsonRpcError(-32000, f"Agent chat failed: {exc}")

        return HandlerOutcome(
            result={
                "session_id": response.session_id,
                "content": response.message.content,
                "tool_results_count": response.metadata.get("tool_results_count", 0)
                if response.metadata
                else 0,
            }
        )

    def _run_agent_chat_sync(self, message: str, session_id: str | None) -> Any:
        """Run agent chat in a synchronous context with a new event loop."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self._agent.chat(message, session_id))
        finally:
            loop.close()

    def _handle_agent_list_sessions(self) -> HandlerOutcome:
        """Handle agent.list_sessions method."""
        sessions = []
        if self._agent:
            for session_id, session in self._agent._sessions.items():
                sessions.append(
                    {
                        "id": session_id,
                        "message_count": len(session.messages),
                        "created_at": session.created_at.isoformat(),
                    }
                )

        return HandlerOutcome(result={"sessions": sessions})

    def _handle_agent_get_session(self, params: dict[str, Any]) -> HandlerOutcome:
        """Handle agent.get_session method."""
        session_id = params.get("session_id")
        if not session_id:
            raise JsonRpcError(-32602, "session_id is required")

        if not self._agent:
            raise JsonRpcError(-32000, "Agent not available")

        session = self._agent.get_session(session_id)
        if session is None:
            raise JsonRpcError(-32000, f"Session not found: {session_id}")

        return HandlerOutcome(
            result={
                "id": session.id,
                "messages": [msg.to_litellm_format() for msg in session.messages],
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
            }
        )

    def _handle_skill_method(self, method: str, params: dict[str, Any]) -> HandlerOutcome:
        """Handle skill.* methods."""
        if self._skill_registry is None:
            raise JsonRpcError(-32601, "Method not found: Skill registry not available")

        if method == "skill.list":
            return HandlerOutcome(result={"skills": self._skill_registry.get_schemas()})

        if method == "skill.execute":
            return self._handle_skill_execute(params)

        raise JsonRpcError(-32601, f"Unknown skill method: {method}")

    def _handle_skill_execute(self, params: dict[str, Any]) -> HandlerOutcome:
        """Handle skill.execute method."""
        skill_name = params.get("skill")
        skill_params = params.get("params", {})
        session_id = params.get("session_id", "default")

        if not skill_name:
            raise JsonRpcError(-32602, "skill is required")

        # Create skill context
        from python.skill.base import SkillContext

        context = SkillContext(
            session_id=session_id,
            working_dir=".",
            artifacts_dir=".pymolcode_artifacts",
            pymol_executor=None,  # Will be set externally if needed
        )

        try:
            # Run async skill execution
            with futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    self._run_skill_execute_sync,
                    skill_name,
                    skill_params,
                    context,
                )
                result = future.result(timeout=300)
        except futures.TimeoutError:
            raise JsonRpcError(-32000, "Skill execution timed out")
        except Exception as exc:
            raise JsonRpcError(-32000, f"Skill execution failed: {exc}")

        return HandlerOutcome(
            result={
                "skill": result.skill_name,
                "status": result.status.value,
                "output": result.output,
                "artifacts": result.artifacts,
                "error": result.error,
            }
        )

    def _run_skill_execute_sync(
        self,
        skill_name: str,
        params: dict[str, Any],
        context: Any,
    ) -> Any:
        """Run skill execution in a synchronous context."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._skill_registry.execute(skill_name, params, context)
            )
        finally:
            loop.close()

    def _handle_session_method(self, method: str, params: dict[str, Any]) -> HandlerOutcome:
        """Handle session.* methods."""
        if method == "session.save":
            return self._handle_session_save(params)
        elif method == "session.load":
            return self._handle_session_load(params)

        raise JsonRpcError(-32601, f"Unknown session method: {method}")

    def _handle_session_save(self, params: dict[str, Any]) -> HandlerOutcome:
        """Handle session.save method."""
        path = params.get("path", "session.json")
        return HandlerOutcome(
            result={
                "saved": True,
                "path": path,
                "message": "Session save is a placeholder",
            }
        )

    def _handle_session_load(self, params: dict[str, Any]) -> HandlerOutcome:
        """Handle session.load method."""
        path = params.get("path", "session.json")
        return HandlerOutcome(
            result={
                "loaded": True,
                "path": path,
                "message": "Session load is a placeholder",
            }
        )

    def _handle_memory_method(self, method: str, params: dict[str, Any]) -> HandlerOutcome:
        """Handle memory.* methods."""
        if method == "memory.initialize":
            return self._handle_memory_initialize(params)
        elif method == "memory.read":
            return self._handle_memory_read(params)
        elif method == "memory.write":
            return self._handle_memory_write(params)

        raise JsonRpcError(-32601, f"Unknown memory method: {method}")

    def _handle_memory_initialize(self, params: dict[str, Any]) -> HandlerOutcome:
        """Handle memory.initialize method."""
        workspace = params.get("workspace", ".")
        workspace_path = Path(workspace).resolve()

        try:
            store = self.initialize_memory(workspace_path)
            return HandlerOutcome(
                result={
                    "initialized": True,
                    "workspace": str(workspace_path),
                    "memory_file": str(store.memory_file),
                }
            )
        except Exception as exc:
            raise JsonRpcError(-32000, f"Memory initialization failed: {exc}")

    def _handle_memory_read(self, params: dict[str, Any]) -> HandlerOutcome:
        """Handle memory.read method."""
        if self._memory_store is None:
            raise JsonRpcError(-32000, "Memory store not initialized")

        section = params.get("section")
        tags = params.get("tags")
        keywords = params.get("keywords")
        limit = params.get("limit", 20)

        context = self._memory_store.get_memory_context(
            include_lessons=bool(section == "lessons" or not section),
            include_todos=bool(section == "todos"),
        )

        if tags or keywords:
            if keywords and isinstance(keywords, list):
                lessons = self._memory_store.search_lessons(query=" ".join(keywords), tags=tags)
                if lessons:
                    context += "\n\n## Search Results\n"
                    for lesson in lessons[:limit]:
                        context += f"- {lesson.get('lesson', '')}\n"

        return HandlerOutcome(
            result={
                "content": context[: limit * 500],
                "section": section,
                "truncated": len(context) > limit * 500,
            }
        )

    def _handle_memory_write(self, params: dict[str, Any]) -> HandlerOutcome:
        """Handle memory.write method."""
        if self._memory_store is None:
            raise JsonRpcError(-32000, "Memory store not initialized")

        content = params.get("content", "")
        section = params.get("section", "knowledge")
        event_type = params.get("event_type", "note")

        if not content:
            raise JsonRpcError(-32602, "content is required")

        try:
            self._memory_store.append_today(
                event_type=event_type, content=content, metadata={"section": section}
            )
            return HandlerOutcome(
                result={
                    "written": True,
                    "section": section,
                }
            )
        except Exception as exc:
            raise JsonRpcError(-32000, f"Memory write failed: {exc}")
