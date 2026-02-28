"""Adapter to start REST server alongside GUI mode."""

from __future__ import annotations

import asyncio
import logging
import threading
from typing import Any

LOGGER = logging.getLogger("python.bridge.gui_rest_adapter")

_rest_server: Any | None = None
_handlers: Any | None = None


def start_rest_thread(port: int = 9124, host: str = "127.0.0.1") -> None:
    """Start REST server in background thread (without PyMOL runtime)."""
    global _rest_server, _handlers

    from python.bridge.handlers import BridgeHandlers
    from python.bridge.rest_server import RestServer

    # Create handlers without executor - will be wired later
    _handlers = BridgeHandlers(command_executor=None)
    _rest_server = RestServer(_handlers, host=host, port=port)

    def run_server():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_rest_server.start())
            LOGGER.info(f"REST API running at http://{host}:{port}")
            loop.run_forever()
        except Exception as e:
            LOGGER.error(f"REST server error: {e}")

    thread = threading.Thread(target=run_server, daemon=True, name="rest-server")
    thread.start()
    LOGGER.info(f"REST server thread started on port {port}")


def wire_gui_cmd(cmd: Any) -> None:
    """Wire the GUI's PyMOL cmd object to the REST handlers."""
    global _handlers

    if _handlers is None:
        LOGGER.warning("REST handlers not initialized - call start_rest_thread first")
        return

    from python.pymol.executor import CommandExecutor
    executor = CommandExecutor(cmd)
    _handlers._command_executor = executor.execute
    LOGGER.info("REST server now connected to GUI PyMOL")
