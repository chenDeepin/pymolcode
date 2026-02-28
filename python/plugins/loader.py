from __future__ import annotations

import hashlib
import importlib.util
import json
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import TypedDict, cast

from .registry import PluginRegistry

Handler = Callable[..., object]


class PluginManifest(TypedDict):
    name: str
    module: str
    tools: dict[str, str]
    skills: dict[str, str]


class LoadedPlugin(TypedDict):
    name: str
    tools: dict[str, Handler]
    skills: dict[str, Handler]


class PluginLoader:
    def __init__(
        self,
        registry: PluginRegistry | None = None,
        plugin_root: Path | None = None,
    ) -> None:
        self.registry: PluginRegistry = registry or PluginRegistry()
        self.plugin_root: Path = (plugin_root or (Path.home() / ".pymolcode" / "plugins")).resolve()
        self._loaded_plugins: dict[str, LoadedPlugin] = {}

    def discover_plugins(self, plugin_dir: Path | None = None) -> list[Path]:
        base_dir = (plugin_dir or self.plugin_root).resolve()
        if not base_dir.exists() or not base_dir.is_dir():
            return []

        discovered: list[Path] = []
        for candidate in sorted(base_dir.iterdir()):
            if candidate.is_dir() and (candidate / "plugin.json").is_file():
                discovered.append(candidate.resolve())
        return discovered

    def load_plugin(self, path: Path) -> LoadedPlugin:
        plugin_path = path.resolve()
        if not self.validate_plugin(plugin_path):
            raise ValueError(f"Invalid plugin manifest: {plugin_path}")

        manifest = self._read_manifest(plugin_path)
        plugin_name = manifest["name"]
        if plugin_name in self._loaded_plugins:
            raise ValueError(f"Plugin already loaded: {plugin_name}")

        module = self._import_module(plugin_name, self._module_path(plugin_path, manifest))
        tools = self._resolve_handlers(module, manifest["tools"], category="tool")
        skills = self._resolve_handlers(module, manifest["skills"], category="skill")

        registered_tools: list[str] = []
        registered_skills: list[str] = []

        try:
            for tool_name in sorted(tools):
                if not self.registry.register_tool(tool_name, tools[tool_name]):
                    raise ValueError(f"Tool collision: {tool_name}")
                registered_tools.append(tool_name)

            for skill_name in sorted(skills):
                if not self.registry.register_skill(skill_name, skills[skill_name]):
                    raise ValueError(f"Skill collision: {skill_name}")
                registered_skills.append(skill_name)
        except Exception:
            for skill_name in reversed(registered_skills):
                _ = self.registry.unregister_skill(skill_name)
            for tool_name in reversed(registered_tools):
                _ = self.registry.unregister_tool(tool_name)
            raise

        loaded: LoadedPlugin = {
            "name": plugin_name,
            "tools": dict(tools),
            "skills": dict(skills),
        }
        self._loaded_plugins[plugin_name] = loaded
        return loaded

    def unload_plugin(self, name: str) -> bool:
        loaded = self._loaded_plugins.pop(name, None)
        if loaded is None:
            return False

        for tool_name, handler in loaded["tools"].items():
            _ = self.registry.unregister_tool(tool_name, handler)
        for skill_name, handler in loaded["skills"].items():
            _ = self.registry.unregister_skill(skill_name, handler)
        return True

    def validate_plugin(self, path: Path) -> bool:
        try:
            plugin_path = path.resolve()
            manifest = self._read_manifest(plugin_path)
            module_path = self._module_path(plugin_path, manifest)
            return module_path.exists() and module_path.is_file()
        except (OSError, ValueError, json.JSONDecodeError):
            return False

    def list_tools(self) -> list[str]:
        return self.registry.list_tools()

    def _read_manifest(self, plugin_path: Path) -> PluginManifest:
        if not plugin_path.exists() or not plugin_path.is_dir():
            raise ValueError(f"Invalid plugin path: {plugin_path}")

        manifest_path = plugin_path / "plugin.json"
        if not manifest_path.exists() or not manifest_path.is_file():
            raise ValueError(f"Missing plugin manifest: {manifest_path}")

        payload = cast(object, json.loads(manifest_path.read_text(encoding="utf-8")))
        if not isinstance(payload, dict):
            raise ValueError(f"Invalid manifest payload: {manifest_path}")

        payload_map = cast(dict[object, object], payload)
        raw_name = payload_map.get("name")
        raw_module = payload_map.get("module", "plugin")
        raw_tools = payload_map.get("tools", {})
        raw_skills = payload_map.get("skills", {})

        if not isinstance(raw_name, str) or not raw_name.strip():
            raise ValueError("Manifest requires non-empty 'name'")
        if not isinstance(raw_module, str) or not raw_module.strip():
            raise ValueError("Manifest requires non-empty 'module'")
        if not isinstance(raw_tools, dict):
            raise ValueError("Manifest requires 'tools' as object")
        if not isinstance(raw_skills, dict):
            raise ValueError("Manifest requires 'skills' as object")

        return {
            "name": raw_name.strip(),
            "module": raw_module.strip(),
            "tools": self._normalize_mapping(cast(dict[object, object], raw_tools), "tools"),
            "skills": self._normalize_mapping(cast(dict[object, object], raw_skills), "skills"),
        }

    def _module_path(self, plugin_path: Path, manifest: PluginManifest) -> Path:
        module_name = manifest["module"]
        if module_name.endswith(".py"):
            return (plugin_path / module_name).resolve()
        return (plugin_path / f"{module_name}.py").resolve()

    def _import_module(self, plugin_name: str, module_path: Path) -> ModuleType:
        digest = hashlib.sha1(str(module_path).encode("utf-8"), usedforsecurity=False).hexdigest()
        module_key = f"pymolcode_plugin_{plugin_name}_{digest[:12]}"
        spec = importlib.util.spec_from_file_location(module_key, module_path)
        if spec is None or spec.loader is None:
            raise ValueError(f"Unable to import plugin module: {module_path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _resolve_handlers(
        self,
        module: ModuleType,
        mapping: dict[str, str],
        *,
        category: str,
    ) -> dict[str, Handler]:
        handlers: dict[str, Handler] = {}
        for public_name in sorted(mapping):
            attribute_name = mapping[public_name]
            attribute = getattr(module, attribute_name, None)
            if not callable(attribute):
                raise ValueError(
                    f"Invalid {category} handler '{attribute_name}' for '{public_name}'"
                )
            handlers[public_name] = attribute
        return handlers

    def _normalize_mapping(self, value: dict[object, object], field_name: str) -> dict[str, str]:
        normalized: dict[str, str] = {}
        for key, entry_value in value.items():
            if not isinstance(key, str) or not key.strip():
                raise ValueError(f"Manifest field '{field_name}' has invalid key")
            if not isinstance(entry_value, str) or not entry_value.strip():
                raise ValueError(f"Manifest field '{field_name}' has invalid handler name")
            normalized[key.strip()] = entry_value.strip()
        return normalized
