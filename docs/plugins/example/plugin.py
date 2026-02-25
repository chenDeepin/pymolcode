from __future__ import annotations

import importlib
from typing import Dict, Type, cast


Plugin = cast(
    Type[object],
    getattr(importlib.import_module("pymolcode.core.plugins.base"), "Plugin"),
)


class ExamplePlugin(Plugin):
    name: str = "example-plugin"
    version: str = "0.1.0"
    initialized: bool = False

    async def initialize(self) -> None:
        self.initialized = True

    async def cleanup(self) -> None:
        self.initialized = False

    async def register_tools(self) -> Dict[str, object]:
        async def echo(message: str) -> str:
            return message

        return {"example.echo": echo}

    async def register_skills(self) -> Dict[str, object]:
        return {
            "example.skill": {
                "name": "example.skill",
                "description": "Example plugin skill registration",
            }
        }
