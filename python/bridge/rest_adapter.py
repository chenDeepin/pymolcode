"""REST server adapter for easy instantiation and lifecycle management."""

from __future__ import annotations

import asyncio
import logging
import signal
from typing import Optional

from python.bridge.handlers import BridgeHandlers
from python.bridge.rest_server import RestServer

LOGGER = logging.getLogger("python.bridge.rest_adapter")


def create_rest_server(
    handlers: BridgeHandlers,
    host: str = "127.0.0.1",
    port: int = 9124,
    token: Optional[str] = None,
) -> RestServer:
    """Create a RestServer instance with the given configuration.

    Args:
        handlers: BridgeHandlers instance for handling JSON-RPC methods
        host: Host address to bind to (default: 127.0.0.1)
        port: Port to listen on (default: 9124)
        token: Optional Bearer token for authentication

    Returns:
        Configured RestServer instance (not yet started)
    """
    return RestServer(
        handlers=handlers,
        host=host,
        port=port,
        token=token,
    )


async def run_rest_server(
    handlers: BridgeHandlers,
    host: str = "127.0.0.1",
    port: int = 9124,
    token: Optional[str] = None,
) -> None:
    """Run the REST server until SIGINT/SIGTERM.

    This function blocks until a shutdown signal is received or
    the server is stopped programmatically.

    Args:
        handlers: BridgeHandlers instance for handling JSON-RPC methods
        host: Host address to bind to (default: 127.0.0.1)
        port: Port to listen on (default: 9124)
        token: Optional Bearer token for authentication
    """
    server = create_rest_server(handlers, host, port, token)
    
    # Setup signal handlers for graceful shutdown
    loop = asyncio.get_running_loop()
    shutdown_event = asyncio.Event()
    
    def signal_handler() -> None:
        LOGGER.info("Received shutdown signal")
        shutdown_event.set()
    
    # Register signal handlers
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, signal_handler)
        except NotImplementedError:
            # Signal handlers not supported on Windows
            pass
    
    try:
        await server.start()
        
        LOGGER.info(
            "REST server running at %s",
            server.url,
        )
        LOGGER.info("Press Ctrl+C to stop")
        
        # Wait for shutdown signal
        await shutdown_event.wait()
        
    finally:
        # Cleanup signal handlers
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.remove_signal_handler(sig)
            except (NotImplementedError, ValueError):
                pass
        
        await server.stop()
        LOGGER.info("REST server shutdown complete")


async def run_rest_server_with_runtime(
    host: str = "127.0.0.1",
    port: int = 9124,
    token: Optional[str] = None,
    workspace: Optional[str] = None,
    headless: bool = True,
) -> None:
    """Run REST server with a PyMOL runtime.
    
    Args:
        headless: If True, run without GUI (default). If False, show PyMOL GUI.

    This is a convenience function that:
    1. Starts a headless PyMOL runtime
    2. Creates BridgeHandlers with the PyMOL executor
    3. Runs the REST server

    Args:
        host: Host address to bind to
        port: Port to listen on
        token: Optional Bearer token for authentication
        workspace: Optional workspace path for memory/sessions
    """
    from pathlib import Path
    
    # Import PyMOL runtime
    try:
        from python.pymol.runtime import PyMOLRuntime
    except ImportError as exc:
        LOGGER.error("Failed to import PyMOLRuntime: %s", exc)
        raise RuntimeError("PyMOL runtime not available") from exc
    
    # Start PyMOL runtime
    mode = "headless" if headless else "GUI"
    LOGGER.info(f"Starting PyMOL runtime ({mode})...")
    runtime = PyMOLRuntime(headless=headless)
    
    try:
        runtime.start()
        LOGGER.info("PyMOL runtime started successfully")
        
        # Create handlers with PyMOL executor
        handlers = BridgeHandlers(
            command_executor=runtime.execute,
        )
        
        # Initialize memory if workspace provided
        if workspace:
            workspace_path = Path(workspace).resolve()
            try:
                handlers.initialize_memory(workspace_path)
                LOGGER.info("Memory initialized at %s", workspace_path)
            except Exception as exc:
                LOGGER.warning("Failed to initialize memory: %s", exc)
        
        # Run the REST server
        await run_rest_server(
            handlers=handlers,
            host=host,
            port=port,
            token=token,
        )
    
    finally:
        # Cleanup PyMOL runtime
        LOGGER.info("Stopping PyMOL runtime...")
        runtime.shutdown()
        LOGGER.info("PyMOL runtime stopped")
