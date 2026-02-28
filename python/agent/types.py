"""Core type definitions for the agent layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class AgentRole(StrEnum):
    """Role of a message in the conversation."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass(frozen=True)
class ToolCall:
    """A request from the LLM to invoke a tool."""

    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class ToolResult:
    """The result of a tool execution."""

    tool_call_id: str
    content: str
    is_error: bool = False


@dataclass
class AgentMessage:
    """A message in the agent conversation."""

    role: AgentRole
    content: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_results: list[ToolResult] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_litellm_format(self) -> dict[str, Any]:
        """Convert to LiteLLM message format."""
        msg: dict[str, Any] = {"role": self.role.value, "content": self.content}
        if self.tool_calls:
            msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.name, "arguments": tc.arguments},
                }
                for tc in self.tool_calls
            ]
        if self.tool_results:
            msg["tool_call_id"] = self.tool_results[0].tool_call_id
        return msg


@dataclass
class ChatSession:
    """A chat session with message history."""

    id: str
    messages: list[AgentMessage] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_message(self, message: AgentMessage) -> None:
        """Add a message to the session."""
        self.messages.append(message)
        self.updated_at = datetime.utcnow()

    def get_context_for_llm(self, max_messages: int = 50) -> list[dict[str, Any]]:
        """Get message history in LiteLLM format."""
        recent = self.messages[-max_messages:] if len(self.messages) > max_messages else self.messages
        return [msg.to_litellm_format() for msg in recent]


@dataclass
class AgentConfig:
    """Configuration for the LLM agent."""

    model: str = "gpt-4o"
    system_prompt: str = ""
    temperature: float = 0.7
    max_tokens: int = 4096
    enable_tools: bool = True
    tool_choice: str = "auto"
    max_tool_iterations: int = 10
    timeout_seconds: float = 120.0

    # Model provider settings
    api_base: str | None = None
    api_key: str | None = None

    def to_litellm_params(self) -> dict[str, Any]:
        """Convert to LiteLLM completion parameters."""
        params: dict[str, Any] = {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if self.api_base:
            params["api_base"] = self.api_base
        if self.api_key:
            params["api_key"] = self.api_key
        return params
