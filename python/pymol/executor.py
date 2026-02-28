from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Final, Protocol, cast, final

JsonObject = dict[str, object]


class _CmdProtocol(Protocol):
    def load(self, source: str, name: str) -> object: ...
    def show(self, representation: str, selection: str) -> object: ...
    def color(self, color: str, selection: str) -> object: ...
    def png(self, filename: str, *, width: int, height: int, ray: int) -> object: ...
    def zoom(self, selection: str, buffer: float, complete: int) -> object: ...
    def get_object_list(self) -> list[str]: ...
    def select(self, name: str, selection: str) -> object: ...
    def get_distance(self, atom1: str, atom2: str) -> float: ...
    def count_atoms(self, selection: str) -> int: ...
    def delete(self, name: str) -> object: ...
    def get_view(self) -> tuple[float, ...]: ...
    def set_view(self, view: tuple[float, ...]) -> object: ...
    def get(self, setting: str, selection: str) -> object: ...
    def get_object_setting(self, setting: str, object_name: str) -> object: ...
    def align(self, mobile: str, target: str, cutoff: float, cycles: int) -> float: ...
    def cealign(
        self, target: str, mobile: str, d0: float, d1: float, window: int, transform: int
    ) -> float: ...


def _as_json_object(value: object, message: str) -> JsonObject:
    if not isinstance(value, Mapping):
        raise ValueError(message)
    mapping = cast(Mapping[object, object], value)
    return {str(key): item for key, item in mapping.items()}


@final
class CommandExecutor:
    _ALLOWED_METHODS: Final[frozenset[str]] = frozenset(
        {
            "load_structure",
            "set_representation",
            "color_object",
            "screenshot",
            "zoom",
            "list_objects",
            "select_atoms",
            "measure_distance",
            "get_scene_state",
            "get_object_info",
            "execute_python",
            "align",
        }
    )

    def __init__(self, cmd: _CmdProtocol) -> None:
        self._cmd: _CmdProtocol = cmd
        self._render_capability: JsonObject = {
            "supported": True,
            "mode": "unknown",
            "message": "Render capability has not been checked.",
        }

    def set_render_capability(self, capability: JsonObject) -> None:
        self._render_capability = dict(capability)

    def execute(self, command: str) -> JsonObject:
        try:
            payload_raw = cast(object, json.loads(command))
            payload = _as_json_object(payload_raw, "Command payload must be a JSON object")

            method = payload.get("method")
            params = _as_json_object(payload.get("params", {}), "'params' must be a JSON object")
            if not isinstance(method, str) or not method:
                raise ValueError("Command must include a non-empty 'method'")

            if method not in self._ALLOWED_METHODS:
                raise ValueError(f"Method '{method}' is not allowed")

            result = self._dispatch(method, params)
            return {
                "ok": True,
                "method": method,
                "result": result,
            }
        except Exception as exc:
            return {
                "ok": False,
                "error": {
                    "type": type(exc).__name__,
                    "message": str(exc),
                },
            }

    def _dispatch(self, method: str, params: JsonObject) -> JsonObject:
        if method == "load_structure":
            source = self._required_string(params, "source")
            name = self._optional_string(params, "name")
            return self.load_structure(source=source, name=name)
        if method == "set_representation":
            selection = self._required_string(params, "selection")
            representation = self._required_string(params, "representation")
            color = self._optional_string(params, "color")
            return self.set_representation(
                selection=selection,
                representation=representation,
                color=color,
            )
        if method == "color_object":
            selection = self._required_string(params, "selection")
            color = self._required_string(params, "color")
            return self.color_object(selection=selection, color=color)
        if method == "screenshot":
            filename = self._required_string(params, "filename")
            width = self._optional_int(params, "width", 1280)
            height = self._optional_int(params, "height", 720)
            ray = self._optional_bool(params, "ray", True)
            return self.screenshot(filename=filename, width=width, height=height, ray=ray)
        if method == "zoom":
            selection = self._optional_string(params, "selection") or "all"
            buffer = self._optional_float(params, "buffer", 0.0)
            complete = self._optional_bool(params, "complete", False)
            return self.zoom(selection=selection, buffer=buffer, complete=complete)
        if method == "list_objects":
            return self.list_objects()
        if method == "select_atoms":
            name = self._required_string(params, "name")
            selection = self._required_string(params, "selection")
            return self.select_atoms(name=name, selection=selection)
        if method == "measure_distance":
            atom1 = self._required_string(params, "atom1")
            atom2 = self._required_string(params, "atom2")
            return self.measure_distance(atom1=atom1, atom2=atom2)
        if method == "get_scene_state":
            return self.get_scene_state()
        if method == "get_object_info":
            object_name = self._required_string(params, "object")
            return self.get_object_info(object_name=object_name)
        if method == "execute_python":
            code = self._required_string(params, "code")
            return self.execute_python(code=code)
        if method == "align":
            mobile = self._required_string(params, "mobile")
            target = self._required_string(params, "target")
            method_name = self._optional_string(params, "method") or "ce"
            cutoff = self._optional_float(params, "cutoff", 1.0)
            cycles = self._optional_int(params, "cycles", 0)
            return self.align(
                mobile=mobile,
                target=target,
                method=method_name,
                cutoff=cutoff,
                cycles=cycles,
            )
        raise ValueError(f"Unknown method: {method}")

    @staticmethod
    def _required_string(params: JsonObject, key: str) -> str:
        value = params.get(key)
        if not isinstance(value, str) or not value:
            raise ValueError(f"'{key}' is required")
        return value

    @staticmethod
    def _optional_string(params: JsonObject, key: str) -> str | None:
        value = params.get(key)
        if value is None:
            return None
        if isinstance(value, str):
            return value
        raise ValueError(f"'{key}' must be a string")

    @staticmethod
    def _optional_int(params: JsonObject, key: str, default: int) -> int:
        value = params.get(key)
        if value is None:
            return default
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"'{key}' must be an integer")
        return value

    @staticmethod
    def _optional_float(params: JsonObject, key: str, default: float) -> float:
        value = params.get(key)
        if value is None:
            return default
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"'{key}' must be a number")
        return float(value)

    @staticmethod
    def _optional_bool(params: JsonObject, key: str, default: bool) -> bool:
        value = params.get(key)
        if value is None:
            return default
        if not isinstance(value, bool):
            raise ValueError(f"'{key}' must be a boolean")
        return value

    def load_structure(self, source: str, name: str | None = None) -> JsonObject:
        if not source:
            raise ValueError("'source' is required")
        object_name = name or Path(source).stem or "object"
        _ = self._cmd.load(source, object_name)
        return {
            "source": source,
            "object": object_name,
            "loaded": True,
        }

    def set_representation(
        self,
        selection: str,
        representation: str,
        color: str | None = None,
    ) -> JsonObject:
        if not selection:
            raise ValueError("'selection' is required")
        if not representation:
            raise ValueError("'representation' is required")
        _ = self._cmd.show(representation, selection)
        if color:
            _ = self._cmd.color(color, selection)
        return {
            "selection": selection,
            "representation": representation,
            "color": color,
            "applied": True,
        }

    def color_object(self, selection: str, color: str) -> JsonObject:
        if not selection:
            raise ValueError("'selection' is required")
        if not color:
            raise ValueError("'color' is required")
        _ = self._cmd.color(color, selection)
        return {
            "selection": selection,
            "color": color,
            "applied": True,
        }

    def screenshot(
        self,
        filename: str,
        width: int = 1280,
        height: int = 720,
        ray: bool = True,
    ) -> JsonObject:
        if not filename:
            raise ValueError("'filename' is required")

        supported = self._render_capability.get("supported")
        if not isinstance(supported, bool):
            supported = False

        if not supported:
            message = self._render_capability.get("message")
            if not isinstance(message, str) or not message:
                message = "Rendering is unavailable for screenshot generation."
            raise RuntimeError(message)

        _ = self._cmd.png(filename, width=width, height=height, ray=int(ray))
        return {
            "filename": filename,
            "width": width,
            "height": height,
            "ray": ray,
            "saved": True,
            "render_mode": self._render_capability.get("mode"),
        }

    def zoom(
        self,
        selection: str = "all",
        buffer: float = 0.0,
        complete: bool = False,
    ) -> JsonObject:
        _ = self._cmd.zoom(selection, buffer, int(complete))
        return {
            "selection": selection,
            "buffer": buffer,
            "complete": complete,
            "applied": True,
        }

    def list_objects(self) -> JsonObject:
        objects = self._cmd.get_object_list()
        return {
            "objects": objects,
            "count": len(objects),
        }

    def select_atoms(self, name: str, selection: str) -> JsonObject:
        if not name:
            raise ValueError("'name' is required")
        if not selection:
            raise ValueError("'selection' is required")
        _ = self._cmd.select(name, selection)
        atom_count = self._cmd.count_atoms(name)
        return {
            "name": name,
            "selection": selection,
            "atom_count": atom_count,
            "created": True,
        }

    def measure_distance(self, atom1: str, atom2: str) -> JsonObject:
        if not atom1:
            raise ValueError("'atom1' is required")
        if not atom2:
            raise ValueError("'atom2' is required")
        distance = self._cmd.get_distance(atom1, atom2)
        return {
            "atom1": atom1,
            "atom2": atom2,
            "distance_angstroms": distance,
            "unit": "angstrom",
        }

    def get_scene_state(self) -> JsonObject:
        view = self._cmd.get_view()
        return {
            "view": list(view),
            "object_count": len(self._cmd.get_object_list()),
        }

    def get_object_info(self, object_name: str) -> JsonObject:
        if not object_name:
            raise ValueError("'object' is required")
        atom_count = self._cmd.count_atoms(object_name)
        objects = self._cmd.get_object_list()
        exists = object_name in objects
        return {
            "object": object_name,
            "exists": exists,
            "atom_count": atom_count if exists else 0,
        }

    def align(
        self,
        mobile: str,
        target: str,
        method: str = "ce",
        cutoff: float = 1.0,
        cycles: int = 0,
    ) -> JsonObject:
        if not mobile:
            raise ValueError("'mobile' is required")
        if not target:
            raise ValueError("'target' is required")
        if method == "ce":
            rmsd = self._cmd.cealign(
                mobile=mobile,
                target=target,
                d0=cutoff,
                d1=cutoff,
                window=8,
                transform=1,
            )
        else:
            rmsd = self._cmd.align(
                mobile,
                target,
                cutoff=cutoff,
                cycles=cycles,
            )
        return {
            "mobile": mobile,
            "target": target,
            "method": method,
            "rmsd": rmsd,
            "aligned": True,
        }

    def execute_python(self, code: str) -> JsonObject:
        if not code:
            raise ValueError("'code' is required")
        local_vars = {"cmd": self._cmd}
        exec(code, {"__builtins__": __builtins__}, local_vars)
        return {
            "code": code,
            "executed": True,
        }
