from __future__ import annotations

import importlib
import os
import queue
import threading
from dataclasses import dataclass
from types import ModuleType
from typing import Callable, Final, Protocol, cast, final

from python.pymol.executor import CommandExecutor


JsonObject = dict[str, object]


class _PyMOLCmd(Protocol):
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


class _PyMOLInstance(Protocol):
    @property
    def cmd(self) -> _PyMOLCmd: ...

    def start(self, args: list[str] | None = None) -> object: ...

    def stop(self) -> object: ...

    def quit(self) -> object: ...


@dataclass
class _CommandTask:
    command: str
    result_queue: queue.Queue[JsonObject]


@final
class PyMOLRuntime:
    def __init__(
        self,
        *,
        headless: bool = True,
        command_timeout: float = 30.0,
        pymol_factory: Callable[[], _PyMOLInstance] | None = None,
        executor_factory: Callable[[_PyMOLCmd], CommandExecutor] = CommandExecutor,
    ) -> None:
        self._headless: bool = headless
        self._command_timeout: float = command_timeout
        self._pymol_factory: Callable[[], _PyMOLInstance] | None = pymol_factory
        self._executor_factory: Callable[[_PyMOLCmd], CommandExecutor] = executor_factory
        self._pymol: _PyMOLInstance | None = None
        self._executor: CommandExecutor | None = None
        self._thread: threading.Thread | None = None
        self._queue: queue.Queue[_CommandTask | None] = queue.Queue()
        self._state_lock: Final[threading.Lock] = threading.Lock()
        self._running: bool = False

    @staticmethod
    def _is_truthy_env(value: str | None) -> bool:
        if value is None:
            return False
        normalized = value.strip().lower()
        return normalized not in {"", "0", "false", "no", "off"}

    @classmethod
    def check_render_capability(cls, *, headless: bool) -> JsonObject:
        display_raw = os.environ.get("DISPLAY")
        display = display_raw.strip() if isinstance(display_raw, str) else ""
        display_available = bool(display)
        software_fallback = cls._is_truthy_env(os.environ.get("PYMOL_NO_OPENGL"))

        glx_available = False
        glx_error: str | None = None
        try:
            _ = importlib.import_module("OpenGL")
            _ = importlib.import_module("OpenGL.GLX")
            glx_available = True
        except Exception as exc:
            glx_error = str(exc)

        if headless and software_fallback:
            return {
                "supported": True,
                "mode": "headless-software",
                "headless": True,
                "display": display or None,
                "display_available": display_available,
                "hardware_acceleration": glx_available,
                "software_rendering": True,
                "message": "Headless rendering enabled via PYMOL_NO_OPENGL software fallback.",
            }

        if not headless and display_available and glx_available:
            return {
                "supported": True,
                "mode": "interactive-hardware",
                "headless": False,
                "display": display,
                "display_available": True,
                "hardware_acceleration": True,
                "software_rendering": False,
                "message": "Interactive rendering available with DISPLAY and GLX.",
            }

        if headless and display_available and glx_available:
            return {
                "supported": True,
                "mode": "headless-hardware",
                "headless": True,
                "display": display,
                "display_available": True,
                "hardware_acceleration": True,
                "software_rendering": False,
                "message": "Headless rendering available with DISPLAY and GLX.",
            }

        if headless:
            message = (
                "Rendering is unavailable in headless mode. Start a virtual display (for example: "
                "xvfb-run -a ...) and ensure GLX is available, or set PYMOL_NO_OPENGL=1 "
                "to force software rendering."
            )
        else:
            message = (
                "Rendering is unavailable in interactive mode. Set DISPLAY to a valid X server "
                "and ensure GLX is available."
            )

        capability: JsonObject = {
            "supported": False,
            "mode": "unsupported",
            "headless": headless,
            "display": display or None,
            "display_available": display_available,
            "hardware_acceleration": glx_available,
            "software_rendering": software_fallback,
            "message": message,
        }

        if glx_error:
            capability["glx_error"] = glx_error

        return capability

    def start(self) -> None:
        with self._state_lock:
            if self._running:
                return

            pymol_instance = self._create_pymol_instance()
            self._start_embedded_instance(pymol_instance)

            self._pymol = pymol_instance
            capability = self.check_render_capability(headless=self._headless)
            self._executor = self._executor_factory(pymol_instance.cmd)
            self._executor.set_render_capability(capability)
            self._running = True
            self._thread = threading.Thread(
                target=self._executor_loop,
                name="pymol-runtime-executor",
                daemon=True,
            )
            self._thread.start()

    def shutdown(self) -> None:
        with self._state_lock:
            if not self._running:
                return
            self._running = False
            self._queue.put(None)
            thread = self._thread

        if thread is not None:
            thread.join(timeout=5.0)

        pymol_instance = self._pymol
        self._thread = None
        self._executor = None
        self._pymol = None

        if pymol_instance is not None:
            self._stop_embedded_instance(pymol_instance)

    def execute(self, command: str) -> JsonObject:
        if not self._running:
            return {
                "ok": False,
                "error": {
                    "type": "RuntimeError",
                    "message": "PyMOL runtime is not running",
                },
            }

        result_queue: queue.Queue[JsonObject] = queue.Queue(maxsize=1)
        self._queue.put(_CommandTask(command=command, result_queue=result_queue))

        try:
            return result_queue.get(timeout=self._command_timeout)
        except queue.Empty:
            return {
                "ok": False,
                "error": {
                    "type": "TimeoutError",
                    "message": f"Command timed out after {self._command_timeout}s",
                },
            }

    def _create_pymol_instance(self) -> _PyMOLInstance:
        if self._pymol_factory is not None:
            return self._pymol_factory()

        pymol2_module: ModuleType = importlib.import_module("pymol2")
        pymol_cls = cast(type[_PyMOLInstance], getattr(pymol2_module, "PyMOL"))
        return pymol_cls()

    def _start_embedded_instance(self, pymol_instance: _PyMOLInstance) -> None:
        launch_args = ["pymol", "-qc"] if self._headless else ["pymol"]
        try:
            _ = pymol_instance.start(launch_args)
        except TypeError:
            _ = pymol_instance.start()

    @staticmethod
    def _stop_embedded_instance(pymol_instance: _PyMOLInstance) -> None:
        try:
            _ = pymol_instance.stop()
            return
        except AttributeError:
            pass

        try:
            _ = pymol_instance.quit()
        except AttributeError:
            return

    def _executor_loop(self) -> None:
        while True:
            task = self._queue.get()
            if task is None:
                break

            executor = self._executor
            if executor is None:
                task.result_queue.put(
                    {
                        "ok": False,
                        "error": {
                            "type": "RuntimeError",
                            "message": "Command executor is unavailable",
                        },
                    }
                )
                continue

            try:
                result: JsonObject = executor.execute(task.command)
            except Exception as exc:
                result = {
                    "ok": False,
                    "error": {
                        "type": type(exc).__name__,
                        "message": str(exc),
                    },
                }

            task.result_queue.put(result)

    @property
    def is_running(self) -> bool:
        return self._running
