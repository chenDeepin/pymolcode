from __future__ import annotations

from collections.abc import Callable


Handler = Callable[..., object]


class PluginRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Handler] = {}
        self._skills: dict[str, Handler] = {}

    def register_tool(self, name: str, handler: Handler) -> bool:
        if name in self._tools:
            return False
        self._tools[name] = handler
        return True

    def register_skill(self, name: str, handler: Handler) -> bool:
        if name in self._skills:
            return False
        self._skills[name] = handler
        return True

    def get_tool(self, name: str) -> Handler | None:
        return self._tools.get(name)

    def list_tools(self) -> list[str]:
        return sorted(self._tools)

    def unregister_tool(self, name: str, handler: Handler | None = None) -> bool:
        existing = self._tools.get(name)
        if existing is None:
            return False
        if handler is not None and existing is not handler:
            return False
        del self._tools[name]
        return True

    def unregister_skill(self, name: str, handler: Handler | None = None) -> bool:
        existing = self._skills.get(name)
        if existing is None:
            return False
        if handler is not None and existing is not handler:
            return False
        del self._skills[name]
        return True
