from __future__ import annotations

import json
import logging
import sys
import time
from contextlib import contextmanager
from collections.abc import Iterator
from typing import BinaryIO, TextIO, cast

from python.bridge.handlers import BridgeHandlers, HandlerOutcome, JSONRPC_VERSION, JsonRpcError
from python.protocol.errors import FramingError, PARSE_ERROR
from python.protocol.framing import write_frame

LOGGER = logging.getLogger("python.bridge.server")
_logger_configured = False


def _configure_logger(stderr: TextIO) -> None:
    global _logger_configured
    if _logger_configured:
        return
    handler = logging.StreamHandler(stderr)
    formatter = logging.Formatter("[bridge] %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    LOGGER.addHandler(handler)
    LOGGER.setLevel(logging.INFO)
    LOGGER.propagate = False
    _logger_configured = True


class StdoutGuard:
    def __init__(self, stderr: TextIO) -> None:
        self._stderr: TextIO = stderr
        self._original: TextIO | None = None
        self._allow_write: bool = False

    def activate(self) -> None:
        if self._original is not None:
            return
        self._original = sys.stdout
        sys.stdout = self

    def deactivate(self) -> None:
        if self._original is None:
            return
        sys.stdout = self._original
        self._original = None

    @contextmanager
    def allow_framed_output(self) -> Iterator[None]:
        self._allow_write = True
        try:
            yield
        finally:
            self._allow_write = False

    def write(self, text: str) -> int:
        if self._allow_write:
            return len(text)
        _ = self._stderr.write("stdout guard blocked write attempt\n")
        _ = self._stderr.flush()
        raise RuntimeError("stdout writes are blocked; use framed response output")

    def flush(self) -> None:
        return None


class BridgeServer:
    def __init__(
        self,
        handlers: BridgeHandlers | None = None,
        input_stream: BinaryIO | None = None,
        output_stream: BinaryIO | None = None,
        stderr: TextIO | None = None,
    ) -> None:
        self._handlers: BridgeHandlers = handlers or BridgeHandlers()
        self._input_stream: BinaryIO = input_stream or sys.stdin.buffer
        self._output_stream: BinaryIO = output_stream or sys.stdout.buffer
        self._stderr: TextIO = stderr or sys.stderr
        self._stdout_guard: StdoutGuard = StdoutGuard(self._stderr)
        self._should_stop: bool = False
        _configure_logger(self._stderr)

    def serve_forever(self) -> None:
        self._stdout_guard.activate()
        try:
            while not self._should_stop:
                try:
                    request = self._read_message(self._input_stream)
                except FramingError:
                    self._write_error(None, -32700, "Parse error")
                    continue

                if request is None:
                    break

                response = self._handle_request(request)
                if response is not None:
                    self._write_response(response)
        finally:
            self._stdout_guard.deactivate()

    def _handle_request(self, request: dict[str, object]) -> dict[str, object] | None:
        started_at = time.perf_counter()
        request_id = request.get("id")
        method_for_log = request.get("method")
        method_name = method_for_log if isinstance(method_for_log, str) else "<invalid>"
        outcome_kind = "ok"

        try:
            if request.get("jsonrpc") != JSONRPC_VERSION:
                outcome_kind = "error"
                return self._error_response(request_id, -32600, "Invalid Request")

            method = request.get("method")
            if not isinstance(method, str):
                outcome_kind = "error"
                return self._error_response(request_id, -32600, "Invalid Request")

            try:
                outcome: HandlerOutcome = self._handlers.handle(method, request.get("params"))
            except JsonRpcError as exc:
                outcome_kind = "error"
                return self._error_response(request_id, exc.code, exc.message)
            except Exception as exc:
                outcome_kind = "error"
                LOGGER.exception(
                    "Unhandled method error", extra={"request_id": request_id, "method": method}
                )
                return self._error_response(request_id, -32000, str(exc))

            if outcome.should_shutdown:
                self._should_stop = True

            if request_id is None:
                outcome_kind = "notification"
                return None

            return {
                "jsonrpc": JSONRPC_VERSION,
                "id": request_id,
                "result": outcome.result,
            }
        finally:
            elapsed_ms = (time.perf_counter() - started_at) * 1000
            LOGGER.info(
                "request_complete method=%s request_id=%r outcome=%s elapsed_ms=%.2f",
                method_name,
                request_id,
                outcome_kind,
                elapsed_ms,
            )

    def _write_response(self, response: dict[str, object]) -> None:
        with self._stdout_guard.allow_framed_output():
            _ = self._output_stream.write(write_frame(response, validate=False))
            _ = self._output_stream.flush()

    def _write_error(self, request_id: object, code: int, message: str) -> None:
        LOGGER.warning(
            "writing_error_response request_id=%r code=%d message=%s", request_id, code, message
        )
        self._write_response(self._error_response(request_id, code, message))

    @staticmethod
    def _error_response(request_id: object, code: int, message: str) -> dict[str, object]:
        return {
            "jsonrpc": JSONRPC_VERSION,
            "id": request_id,
            "error": {
                "code": code,
                "message": message,
            },
        }

    @staticmethod
    def _read_message(stream: BinaryIO) -> dict[str, object] | None:
        first_line = stream.readline()
        while first_line not in (b"",) and not first_line.strip():
            first_line = stream.readline()

        if first_line == b"":
            return None

        stripped = first_line.lstrip()
        if stripped.startswith((b"{", b"[")):
            try:
                parsed_unknown = cast(object, json.loads(first_line.decode("utf-8")))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise FramingError("Invalid JSON payload", PARSE_ERROR) from exc
            if not isinstance(parsed_unknown, dict):
                raise FramingError("JSON-RPC payload must be an object", PARSE_ERROR)
            parsed_dict = cast(dict[object, object], parsed_unknown)
            return {str(key): value for key, value in parsed_dict.items()}

        headers = first_line
        while True:
            line = stream.readline()
            if line == b"":
                raise FramingError("Unexpected EOF while reading headers", PARSE_ERROR)
            headers += line
            if headers.endswith(b"\r\n\r\n"):
                break

        try:
            header_lines = headers.decode("ascii").split("\r\n")
        except UnicodeDecodeError as exc:
            raise FramingError("Header block must be ASCII", PARSE_ERROR) from exc

        content_length: int | None = None
        for header_line in header_lines:
            if not header_line:
                continue
            name, sep, value = header_line.partition(":")
            if not sep:
                continue
            if name.strip().lower() == "content-length":
                value_str = value.strip()
                if not value_str.isdigit():
                    raise FramingError("Content-Length must be numeric", PARSE_ERROR)
                content_length = int(value_str)
                break

        if content_length is None:
            raise FramingError("Missing Content-Length header", PARSE_ERROR)

        body = stream.read(content_length)
        if len(body) != content_length:
            raise FramingError("Unexpected EOF while reading payload", PARSE_ERROR)

        try:
            payload_unknown = cast(object, json.loads(body.decode("utf-8")))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise FramingError("Invalid JSON payload", PARSE_ERROR) from exc

        if not isinstance(payload_unknown, dict):
            raise FramingError("JSON-RPC payload must be an object", PARSE_ERROR)
        payload_dict = cast(dict[object, object], payload_unknown)
        return {str(key): value for key, value in payload_dict.items()}


def main() -> None:
    server = BridgeServer()
    server.serve_forever()


if __name__ == "__main__":
    main()
