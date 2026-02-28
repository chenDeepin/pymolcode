"""Main LLM Agent implementation using LiteLLM."""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from python.agent.tools import ToolRegistry
from python.agent.types import (
    AgentConfig,
    AgentMessage,
    AgentRole,
    ChatSession,
    ToolCall,
    ToolResult,
)

if TYPE_CHECKING:
    from python.memory.store import MemoryStore

__all__ = ["Agent", "AgentResponse"]

LOGGER = logging.getLogger("pymolcode.agent")


@dataclass
class AgentResponse:
    """Response from the agent."""

    session_id: str
    message: AgentMessage
    is_complete: bool = True
    metadata: dict[str, Any] | None = None


class Agent:
    """LLM-powered agent for molecular visualization and drug discovery."""

    DEFAULT_SYSTEM_PROMPT = """\
You are pymolcode, an AI assistant for molecular visualization and drug \
discovery using PyMOL.

You have access to PyMOL tools for:
- Loading molecular structures (PDB files, local files)
- Changing representations (cartoon, surface, sticks, spheres)
- Coloring molecules
- Zooming and viewing
- Taking screenshots

You also have access to MEMORY tools for:
- Reading lessons learned from past mistakes (memory_read)
- Writing new lessons to avoid repeating errors (memory_write)

CRITICAL: You MUST learn from your mistakes. When you make an error:
1. Acknowledge the mistake honestly
2. Use memory_write to record the lesson in the 'lessons' section
3. Apply the lesson to avoid repeating the error

Example memory entry after a mistake:
{
    "operation": "create",
    "section": "lessons",
    "data": {
        "lesson": "Always verify PyMOL operations succeeded",
        "context": "Reported success when load actually failed",
        "fix": "Check object list after load operations"
    },
    "tags": ["critical", "verification", "pymol"]
}

When the user asks you to visualize or analyze molecules:
1. First load the structure if needed
2. Apply appropriate representations
3. Color molecules to highlight important features
4. Zoom to relevant regions
5. Take screenshots if requested

Always explain what you're doing and provide helpful scientific context.
Be precise with PyMOL selection syntax (e.g., 'chain A and resi 100-150').
"""

    def __init__(
        self,
        config: AgentConfig | None = None,
        tool_registry: ToolRegistry | None = None,
        memory_store: MemoryStore | None = None,
    ) -> None:
        self._config = config or AgentConfig(system_prompt=self.DEFAULT_SYSTEM_PROMPT)
        self._tools = tool_registry or ToolRegistry()
        self._sessions: dict[str, ChatSession] = {}
        self._provider_resolved = False
        self._memory_store = memory_store

    @property
    def config(self) -> AgentConfig:
        return self._config

    @property
    def tools(self) -> ToolRegistry:
        return self._tools

    @property
    def memory_store(self) -> MemoryStore | None:
        return self._memory_store

    def set_memory_store(self, store: MemoryStore) -> None:
        self._memory_store = store

    def create_session(self, metadata: dict[str, Any] | None = None) -> ChatSession:
        session_id = str(uuid.uuid4())[:8]
        session = ChatSession(id=session_id, metadata=metadata or {})
        self._sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> ChatSession | None:
        return self._sessions.get(session_id)

    def set_tool_registry(self, registry: ToolRegistry) -> None:
        self._tools = registry

    def _resolve_provider(self) -> None:
        """Auto-discover LLM provider if not explicitly configured."""
        if self._provider_resolved:
            return
        self._provider_resolved = True

        # If user already set an api_key, nothing to resolve
        if self._config.api_key:
            return

        from python.agent.provider import resolve_provider

        info = resolve_provider(
            model_override=self._config.model if self._config.model != "gpt-4o" else None,
            api_key_override=self._config.api_key,
            api_base_override=self._config.api_base,
        )
        if info is None:
            LOGGER.warning("No LLM provider found – chat will fail until a key is configured")
            return

        LOGGER.info("Using LLM provider: %s  model: %s", info.provider_name, info.model)
        self._config.model = info.model
        self._config.api_key = info.api_key
        self._config.api_base = info.api_base

    async def chat(
        self,
        message: str,
        session_id: str | None = None,
    ) -> AgentResponse:
        self._resolve_provider()

        if session_id:
            session = self._sessions.get(session_id)
            if session is None:
                session = self.create_session()
        else:
            session = self.create_session()

        user_msg = AgentMessage(role=AgentRole.USER, content=message)
        session.add_message(user_msg)

        messages = self._build_messages(session)
        response_message, tool_results = await self._run_llm_loop(messages)
        session.add_message(response_message)

        return AgentResponse(
            session_id=session.id,
            message=response_message,
            is_complete=True,
            metadata={"tool_results_count": len(tool_results)},
        )

    def _build_messages(self, session: ChatSession) -> list[dict[str, Any]]:
        messages: list[dict[str, Any]] = []
        system_prompt = self._config.system_prompt or self.DEFAULT_SYSTEM_PROMPT

        if self._memory_store:
            memory_context = self._memory_store.get_memory_context(include_lessons=True)
            if memory_context:
                system_prompt = (
                    f"{system_prompt}\n\n---\n\n# Your Persistent Memory\n\n{memory_context}"
                )

        messages.append({"role": "system", "content": system_prompt})
        for msg in session.messages:
            messages.append(msg.to_litellm_format())
        return messages

    async def _run_llm_loop(
        self,
        messages: list[dict[str, Any]],
    ) -> tuple[AgentMessage, list[ToolResult]]:
        import litellm

        iteration = 0
        all_tool_results: list[ToolResult] = []

        # Build litellm kwargs
        litellm_kw: dict[str, Any] = {
            "model": self._config.model,
            "temperature": self._config.temperature,
            "max_tokens": self._config.max_tokens,
            "timeout": self._config.timeout_seconds,
        }
        if self._config.api_key:
            litellm_kw["api_key"] = self._config.api_key
        if self._config.api_base:
            litellm_kw["api_base"] = self._config.api_base

        while iteration < self._config.max_tool_iterations:
            iteration += 1

            try:
                response = await litellm.acompletion(
                    messages=messages,
                    tools=self._tools.get_openai_tools() if self._config.enable_tools else None,
                    tool_choice=self._config.tool_choice if self._config.enable_tools else None,
                    **litellm_kw,
                )
            except Exception as exc:
                LOGGER.error("LLM call failed: %s", exc)
                return AgentMessage(
                    role=AgentRole.ASSISTANT,
                    content=f"LLM error: {exc}",
                ), all_tool_results

            choice = response.choices[0]
            assistant_msg = choice.message
            tool_calls = assistant_msg.tool_calls or []

            if not tool_calls:
                return AgentMessage(
                    role=AgentRole.ASSISTANT,
                    content=assistant_msg.content or "",
                ), all_tool_results

            agent_tool_calls: list[ToolCall] = []
            iteration_results: list[ToolResult] = []

            for tc in tool_calls:
                tool_call = ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=json.loads(tc.function.arguments),
                )
                agent_tool_calls.append(tool_call)
                LOGGER.info("Tool: %s  args: %s", tool_call.name, tool_call.arguments)

                result_str = self._tools.execute(tool_call.name, tool_call.arguments)
                result = ToolResult(tool_call_id=tc.id, content=result_str)
                iteration_results.append(result)
                all_tool_results.append(result)

            messages.append(
                {
                    "role": "assistant",
                    "content": assistant_msg.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {"name": tc.name, "arguments": json.dumps(tc.arguments)},
                        }
                        for tc in agent_tool_calls
                    ],
                }
            )
            for tr in iteration_results:
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tr.tool_call_id,
                        "content": tr.content,
                    }
                )

        return AgentMessage(
            role=AgentRole.ASSISTANT,
            content="I've completed the requested operations.",
            tool_results=all_tool_results,
        ), all_tool_results
