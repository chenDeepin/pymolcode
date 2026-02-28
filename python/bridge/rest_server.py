"""REST API server for PymolCode remote control."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from aiohttp import web

from python.bridge.handlers import JSONRPC_VERSION, BridgeHandlers, HandlerOutcome, JsonRpcError

LOGGER = logging.getLogger("python.bridge.rest_server")


class RestServer:
    """aiohttp-based REST server for PymolCode bridge.

    Endpoints:
        POST /rpc    - JSON-RPC 2.0 method calls
        GET  /health - Health check endpoint
        WS   /ws     - WebSocket (stub for future use)
    """

    def __init__(
        self,
        handlers: BridgeHandlers,
        host: str = "127.0.0.1",
        port: int = 9124,
        token: str | None = None,
    ) -> None:
        self._handlers = handlers
        self._host = host
        self._port = port
        self._token = token
        self._app: web.Application | None = None
        self._runner: web.AppRunner | None = None
        self._site: web.TCPSite | None = None
        self._shutdown_event: asyncio.Event | None = None

    async def start(self) -> None:
        """Start the REST server."""
        self._app = web.Application()
        self._app["rest_server"] = self

        # Register routes
        self._app.router.add_post("/rpc", self._handle_rpc)
        self._app.router.add_get("/health", self._handle_health)
        self._app.router.add_get("/ws", self._handle_websocket)

        # Add middleware for auth
        self._app.middlewares.append(self._auth_middleware)

        # Setup runner
        self._runner = web.AppRunner(self._app)
        await self._runner.setup()

        self._site = web.TCPSite(self._runner, self._host, self._port)
        await self._site.start()

        self._shutdown_event = asyncio.Event()

        LOGGER.info(
            "RestServer started on http://%s:%d (auth=%s)",
            self._host,
            self._port,
            "enabled" if self._token else "disabled",
        )

    async def stop(self) -> None:
        """Stop the REST server gracefully."""
        LOGGER.info("RestServer stopping...")

        if self._shutdown_event:
            self._shutdown_event.set()

        if self._site:
            await self._site.stop()
            self._site = None

        if self._runner:
            await self._runner.cleanup()
            self._runner = None

        if self._app:
            await self._app.shutdown()
            await self._app.cleanup()
            self._app = None

        LOGGER.info("RestServer stopped")

    @web.middleware
    async def _auth_middleware(
        self,
        request: web.Request,
        handler: Any,
    ) -> web.StreamResponse:
        """Middleware for optional Bearer token authentication."""
        # Skip auth for health endpoint
        if request.path == "/health":
            return await handler(request)

        # Skip auth if no token configured
        if not self._token:
            return await handler(request)

        # Check Authorization header
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return web.json_response(
                {"error": "Unauthorized", "message": "Missing or invalid Authorization header"},
                status=401,
            )

        provided_token = auth_header[7:]  # Remove "Bearer " prefix
        if provided_token != self._token:
            return web.json_response(
                {"error": "Unauthorized", "message": "Invalid token"},
                status=401,
            )

        return await handler(request)

    async def _handle_rpc(self, request: web.Request) -> web.Response:
        """Handle JSON-RPC 2.0 requests via POST /rpc."""
        try:
            # Parse request body
            try:
                body = await request.text()
                payload = json.loads(body) if body.strip() else {}
            except json.JSONDecodeError as exc:
                return self._jsonrpc_error(
                    None,
                    -32700,
                    f"Parse error: {exc}",
                    status=400,
                )

            # Validate JSON-RPC structure
            if not isinstance(payload, dict):
                return self._jsonrpc_error(
                    None,
                    -32600,
                    "Invalid Request: payload must be an object",
                    status=400,
                )

            request_id = payload.get("id")

            # Check JSON-RPC version
            if payload.get("jsonrpc") != JSONRPC_VERSION:
                return self._jsonrpc_error(
                    request_id,
                    -32600,
                    "Invalid Request: missing or invalid jsonrpc version",
                    status=400,
                )

            method = payload.get("method")
            if not isinstance(method, str):
                return self._jsonrpc_error(
                    request_id,
                    -32600,
                    "Invalid Request: method must be a string",
                    status=400,
                )

            params = payload.get("params")

            # Execute the method
            try:
                outcome: HandlerOutcome = self._handlers.handle(method, params)
            except JsonRpcError as exc:
                return self._jsonrpc_error(request_id, exc.code, exc.message)
            except Exception as exc:
                LOGGER.exception("Unhandled error in method %s", method)
                return self._jsonrpc_error(
                    request_id,
                    -32000,
                    f"Internal error: {exc}",
                    status=500,
                )

            # Check for shutdown request
            if outcome.should_shutdown:
                asyncio.create_task(self._delayed_shutdown())

            # Return success response
            return web.json_response({
                "jsonrpc": JSONRPC_VERSION,
                "id": request_id,
                "result": outcome.result,
            })

        except Exception as exc:
            LOGGER.exception("Unexpected error in RPC handler")
            return self._jsonrpc_error(None, -32603, f"Internal error: {exc}", status=500)

    async def _handle_health(self, request: web.Request) -> web.Response:
        """Handle GET /health endpoint."""
        return web.json_response({"status": "ok"})

    async def _handle_websocket(self, request: web.Request) -> web.WebSocketResponse:
        """Handle WebSocket connections (stub for future use)."""
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        LOGGER.info("WebSocket connection opened")

        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    # For now, just echo back with a stub response
                    try:
                        payload = json.loads(msg.data)
                        response = {
                            "jsonrpc": JSONRPC_VERSION,
                            "id": payload.get("id"),
                            "result": {"message": "WebSocket support coming soon"},
                        }
                        await ws.send_json(response)
                    except json.JSONDecodeError:
                        await ws.send_json({
                            "jsonrpc": JSONRPC_VERSION,
                            "error": {"code": -32700, "message": "Parse error"},
                        })
                elif msg.type == web.WSMsgType.ERROR:
                    LOGGER.error("WebSocket error: %s", ws.exception())
        finally:
            LOGGER.info("WebSocket connection closed")

        return ws

    async def _delayed_shutdown(self) -> None:
        """Schedule a delayed shutdown to allow response to be sent."""
        await asyncio.sleep(0.5)
        if self._shutdown_event:
            self._shutdown_event.set()

    @staticmethod
    def _jsonrpc_error(
        request_id: Any,
        code: int,
        message: str,
        status: int = 200,
    ) -> web.Response:
        """Create a JSON-RPC error response."""
        return web.json_response(
            {
                "jsonrpc": JSONRPC_VERSION,
                "id": request_id,
                "error": {
                    "code": code,
                    "message": message,
                },
            },
            status=status,
        )

    @property
    def host(self) -> str:
        """Get the server host."""
        return self._host

    @property
    def port(self) -> int:
        """Get the server port."""
        return self._port

    @property
    def url(self) -> str:
        """Get the server base URL."""
        return f"http://{self._host}:{self._port}"
