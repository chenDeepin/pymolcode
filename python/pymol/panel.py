"""Qt dock-widget panel for pymolcode.

Provides the LLM chat UI that docks into PyMOL's QMainWindow.
Only import this module when running inside a Qt application.
"""

from __future__ import annotations

import asyncio
import logging
import re
import threading
from typing import Any, TYPE_CHECKING

from pymol.Qt import QtCore, QtWidgets

if TYPE_CHECKING:
    from python.agent.agent import Agent, AgentResponse

__all__ = ["PymolcodePanel", "init_plugin"]

LOGGER = logging.getLogger("pymolcode.panel")

SYSTEM_PROMPT = """\
You are pymolcode, an AI assistant for molecular visualization and drug \
discovery using PyMOL.

You have access to PyMOL tools for loading structures, changing \
representations, coloring, zooming and taking screenshots.

When the user asks you to visualize or analyze molecules:
1. Load the structure if needed
2. Apply appropriate representations
3. Color molecules to highlight important features
4. Zoom to relevant regions
5. Take screenshots if requested

Be precise with PyMOL selection syntax (e.g. 'chain A and resi 100-150').\
"""


# ---------------------------------------------------------------------------
# Lightweight message bubble
# ---------------------------------------------------------------------------


class _ChatBubble(QtWidgets.QFrame):
    _ROLE_COLORS = {
        "user": ("#2196F3", "#E3F2FD"),
        "assistant": ("#4CAF50", "#E8F5E9"),
        "system": ("#9E9E9E", "#F5F5F5"),
        "tool": ("#FF9800", "#FFF3E0"),
    }

    def __init__(self, role: str, text: str, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        fg, bg = self._ROLE_COLORS.get(role, ("#666", "#FFF"))
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(2)

        lbl_role = QtWidgets.QLabel(role.title())
        lbl_role.setStyleSheet(f"color:{fg}; font-weight:bold; font-size:11px;")
        layout.addWidget(lbl_role)

        lbl_text = QtWidgets.QLabel(text)
        lbl_text.setWordWrap(True)
        lbl_text.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        sp = lbl_text.sizePolicy()
        sp.setHorizontalPolicy(QtWidgets.QSizePolicy.Expanding)
        sp.setHeightForWidth(True)
        lbl_text.setSizePolicy(sp)
        layout.addWidget(lbl_text)

        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        self.setStyleSheet(f"QFrame{{background:{bg}; border-radius:6px;}}")


# ---------------------------------------------------------------------------
# Main panel
# ---------------------------------------------------------------------------


class PymolcodePanel(QtWidgets.QDockWidget):
    """Dock widget hosting the pymolcode LLM chat/coding UI."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__("pymolcode", parent)
        self.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea)
        self.setMinimumWidth(300)

        self._agent: Agent | None = None
        self._session_id: str | None = None
        self._busy = False
        self._pymol_cmd: Any = None

        self._build_ui()

    # -- UI construction ----------------------------------------------------

    def _build_ui(self) -> None:
        root = QtWidgets.QWidget()
        vbox = QtWidgets.QVBoxLayout(root)
        vbox.setContentsMargins(6, 6, 6, 6)
        vbox.setSpacing(6)

        # status
        self._status = QtWidgets.QLabel("Ready")
        self._status.setStyleSheet("color:#888; font-size:11px;")
        vbox.addWidget(self._status)

        # scrollable chat area
        self._scroll = QtWidgets.QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self._chat_box = QtWidgets.QWidget()
        self._chat_layout = QtWidgets.QVBoxLayout(self._chat_box)
        self._chat_layout.setAlignment(QtCore.Qt.AlignTop)
        self._chat_layout.setContentsMargins(2, 2, 2, 2)
        self._chat_layout.setSpacing(6)
        self._scroll.setWidget(self._chat_box)
        vbox.addWidget(self._scroll, stretch=1)

        # input row
        row = QtWidgets.QHBoxLayout()
        self._input = QtWidgets.QLineEdit()
        self._input.setPlaceholderText("Ask me to visualize molecules…")
        self._input.returnPressed.connect(self._on_send)
        row.addWidget(self._input, stretch=1)
        self._btn_send = QtWidgets.QPushButton("Send")
        self._btn_send.clicked.connect(self._on_send)
        row.addWidget(self._btn_send)
        vbox.addLayout(row)

        # quick-action row
        qrow = QtWidgets.QHBoxLayout()
        for label, slot in [
            ("Load PDB", self._quick_load_pdb),
            ("Clear", self._quick_clear),
            ("New session", self._quick_new_session),
        ]:
            b = QtWidgets.QPushButton(label)
            b.setStyleSheet("font-size:11px; padding:3px 6px;")
            b.clicked.connect(slot)
            qrow.addWidget(b)
        vbox.addLayout(qrow)

        self.setWidget(root)

    # -- public API ---------------------------------------------------------

    def set_pymol_cmd(self, cmd: Any) -> None:
        """Provide the ``pymol.cmd`` object so tools can drive PyMOL."""
        self._pymol_cmd = cmd
        if self._agent:
            self._wire_tools()
        
        # Also wire to REST server if it's running
        try:
            from python.bridge.gui_rest_adapter import wire_gui_cmd
            wire_gui_cmd(cmd)
        except ImportError:
            pass  # REST adapter not available

    # -- agent wiring -------------------------------------------------------

    def _ensure_agent(self) -> None:
        if self._agent is not None:
            return
        from python.agent.agent import Agent
        from python.agent.types import AgentConfig
        from python.agent.provider import resolve_provider

        provider = resolve_provider()
        if provider is None:
            raise RuntimeError(
                "No LLM provider found. Set an API key in .env or environment "
                "(e.g. ANTHROPIC_API_KEY, OPENAI_API_KEY, DEEPSEEK_API_KEY, "
                "ZAI_API_KEY, GEMINI_API_KEY)."
            )

        self._agent = Agent(
            config=AgentConfig(
                model=provider.model,
                api_key=provider.api_key,
                api_base=provider.api_base,
                system_prompt=SYSTEM_PROMPT,
            ),
        )
        self._append("system", f"Provider: {provider.provider_name}  Model: {provider.model}")
        self._wire_tools()

    def _wire_tools(self) -> None:
        if self._agent is None or self._pymol_cmd is None:
            return
        from python.agent.tools import ToolRegistry
        from python.pymol.executor import CommandExecutor

        executor = CommandExecutor(self._pymol_cmd)
        self._agent.set_tool_registry(ToolRegistry(command_executor=executor))

    # -- chat helpers -------------------------------------------------------

    def _append(self, role: str, text: str) -> None:
        self._chat_layout.addWidget(_ChatBubble(role, text))
        self._chat_box.adjustSize()
        QtCore.QTimer.singleShot(100, self._scroll_bottom)
        QtCore.QTimer.singleShot(500, self._scroll_bottom)

    def _scroll_bottom(self) -> None:
        sb = self._scroll.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        self._btn_send.setEnabled(not busy)
        self._input.setEnabled(not busy)
        self._status.setText("Processing…" if busy else "Ready")
        self._status.setStyleSheet(
            "color:#FF9800; font-size:11px;" if busy else "color:#4CAF50; font-size:11px;"
        )

    # -- slots --------------------------------------------------------------

    def _on_send(self) -> None:
        text = self._input.text().strip()
        if not text or self._busy:
            return
        self._input.clear()
        self._append("user", text)
        self._set_busy(True)

        try:
            self._ensure_agent()
        except Exception as exc:
            self._append("system", f"Agent init failed: {exc}")
            self._set_busy(False)
            return

        agent = self._agent
        sid = self._session_id

        def _work() -> None:
            loop = asyncio.new_event_loop()
            try:
                resp = loop.run_until_complete(agent.chat(text, sid))
            except Exception as exc:
                QtCore.QMetaObject.invokeMethod(
                    self,
                    "_on_error",
                    QtCore.Qt.QueuedConnection,
                    QtCore.Q_ARG(str, str(exc)),
                )
                return
            finally:
                import litellm

                loop.run_until_complete(litellm.close_litellm_async_clients())
                loop.close()
            QtCore.QMetaObject.invokeMethod(
                self,
                "_on_response",
                QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(object, resp),
            )

        threading.Thread(target=_work, daemon=True).start()

    @QtCore.Slot(object)
    def _on_response(self, resp: AgentResponse) -> None:
        self._session_id = resp.session_id
        self._append("assistant", resp.message.content)
        self._set_busy(False)

    @QtCore.Slot(str)
    def _on_error(self, msg: str) -> None:
        self._append("system", f"Error: {msg}")
        self._set_busy(False)

    # -- quick actions ------------------------------------------------------

    def _quick_load_pdb(self) -> None:
        code, ok = QtWidgets.QInputDialog.getText(
            self, "Load PDB", "PDB code:", QtWidgets.QLineEdit.Normal, ""
        )
        if ok and code:
            code = re.sub(r"[^a-zA-Z0-9]", "", code).lower()
            if len(code) == 4:
                self._input.setText(f"Load structure {code}")
                self._on_send()

    def _quick_clear(self) -> None:
        while self._chat_layout.count():
            item = self._chat_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def _quick_new_session(self) -> None:
        self._session_id = None
        self._quick_clear()
        self._append("system", "New session started.")


# ---------------------------------------------------------------------------
# Plugin entry points
# ---------------------------------------------------------------------------


def _rebrand_windows(qt_app: Any) -> None:
    """Rename all top-level windows from 'PyMOL' to 'PymolCode'."""
    for w in qt_app.topLevelWidgets():
        title = w.windowTitle()
        if title and "PyMOL" in title:
            w.setWindowTitle(title.replace("PyMOL", "PymolCode"))


def init_plugin(app: Any = None) -> PymolcodePanel | None:
    """Create and dock the panel into the active PyMOL QMainWindow.

    Called either from ``__init_plugin__`` (PyMOL's plugin system) or from
    the ``pymolcode`` CLI launcher script.
    """
    qt_app = app or QtWidgets.QApplication.instance()
    if qt_app is None:
        return None
    

    qt_app.setApplicationName("PymolCode")
    qt_app.setApplicationDisplayName("PymolCode")

    main_win = qt_app.activeWindow()
    if main_win is None:
        # Try to find the main window from topLevelWidgets
        for w in qt_app.topLevelWidgets():
            if w.windowTitle() and "PyMOL" in w.windowTitle():
                main_win = w
                break
        if main_win is None:
            return None

    main_win.setWindowTitle("PymolCode")

    panel = PymolcodePanel(main_win)
    main_win.addDockWidget(QtCore.Qt.RightDockWidgetArea, panel)

    try:
        import pymol

        if hasattr(pymol, "cmd"):
            panel.set_pymol_cmd(pymol.cmd)
    except ImportError:
        pass

    QtCore.QTimer.singleShot(500, lambda: _rebrand_windows(qt_app))
    QtCore.QTimer.singleShot(2000, lambda: _rebrand_windows(qt_app))

    LOGGER.info("pymolcode panel docked")
    return panel


def __init_plugin__(self: object | None = None) -> None:  # noqa: ARG001
    """PyMOL plugin entry point (called by PyMOL's plugin manager)."""
    init_plugin()
