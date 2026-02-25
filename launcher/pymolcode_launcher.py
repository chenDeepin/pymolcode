#!/usr/bin/env python3
# pyright: reportUnusedCallResult=false, reportExplicitAny=false, reportUnannotatedClassAttribute=false, reportAny=false, reportUnknownVariableType=false
from __future__ import annotations

import argparse
import json
import os
import select
import shlex
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def log(message: str) -> None:
    sys.stderr.write(f"[launcher] {message}\n")
    sys.stderr.flush()


@dataclass
class ProcessSpec:
    name: str
    argv: list[str]
    cwd: Path


class BridgeProtocol:
    def __init__(self, process: subprocess.Popen[bytes]) -> None:
        stdin = process.stdin
        stdout = process.stdout
        if stdin is None or stdout is None:
            raise RuntimeError("bridge stdio pipes are not available")
        self._process = process
        self._stdin = stdin
        self._stdout = stdout
        self._buffer = bytearray()
        self._next_id = 0

    def call(
        self, method: str, timeout_seconds: float, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        self._next_id += 1
        request_id = self._next_id
        request: dict[str, Any] = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
        }
        if params is not None:
            request["params"] = params

        payload = json.dumps(request, separators=(",", ":")).encode("utf-8")
        frame = f"Content-Length: {len(payload)}\r\n\r\n".encode("ascii") + payload

        self._stdin.write(frame)
        self._stdin.flush()

        deadline = time.monotonic() + timeout_seconds
        while True:
            response = self._read_message(deadline)
            if response.get("id") != request_id:
                continue
            if "error" in response:
                error_obj = response.get("error")
                raise RuntimeError(f"bridge {method} failed: {error_obj}")
            result = response.get("result")
            if not isinstance(result, dict):
                raise RuntimeError(f"bridge {method} returned non-object result")
            return result

    def _read_message(self, deadline: float) -> dict[str, Any]:
        fd = self._stdout.fileno()
        while True:
            header_end = self._buffer.find(b"\r\n\r\n")
            if header_end >= 0:
                body_start = header_end + 4
                header = bytes(self._buffer[:header_end]).decode("ascii", errors="strict")
                content_length = self._parse_content_length(header)
                body_end = body_start + content_length
                if len(self._buffer) >= body_end:
                    body = bytes(self._buffer[body_start:body_end])
                    del self._buffer[:body_end]
                    parsed = json.loads(body.decode("utf-8"))
                    if not isinstance(parsed, dict):
                        raise RuntimeError("bridge response is not a JSON object")
                    return parsed

            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("timed out waiting for bridge response")

            readable, _, _ = select.select([fd], [], [], remaining)
            if not readable:
                raise TimeoutError("timed out waiting for bridge response")

            chunk = os.read(fd, 65536)
            if not chunk:
                raise RuntimeError("bridge stdout closed")
            self._buffer.extend(chunk)

    @staticmethod
    def _parse_content_length(header: str) -> int:
        for line in header.split("\r\n"):
            name, sep, value = line.partition(":")
            if not sep:
                continue
            if name.strip().lower() == "content-length":
                text = value.strip()
                if not text.isdigit():
                    break
                return int(text)
        raise RuntimeError("invalid bridge frame: missing Content-Length")


class Launcher:
    def __init__(
        self,
        bridge_spec: ProcessSpec,
        node_spec: ProcessSpec,
        handshake_timeout: float,
        shutdown_timeout: float,
        node_ready_seconds: float,
        heartbeat_seconds: float,
    ) -> None:
        self._bridge_spec = bridge_spec
        self._node_spec = node_spec
        self._handshake_timeout = handshake_timeout
        self._shutdown_timeout = shutdown_timeout
        self._node_ready_seconds = node_ready_seconds
        self._heartbeat_seconds = heartbeat_seconds

        self._bridge_process: subprocess.Popen[bytes] | None = None
        self._node_process: subprocess.Popen[bytes] | None = None
        self._bridge_protocol: BridgeProtocol | None = None
        self._stop_requested = False

    def request_stop(self, signum: int) -> None:
        if self._stop_requested:
            return
        self._stop_requested = True
        log(f"received signal {signum}; starting graceful shutdown")

    def run(self) -> int:
        try:
            self._start_bridge()
            self._start_node()
            return self._monitor_loop()
        except Exception as exc:
            log(f"fatal launcher error: {exc}")
            self._shutdown(graceful=False)
            return 1

    def _start_bridge(self) -> None:
        log(f"starting python bridge: {' '.join(self._bridge_spec.argv)}")
        self._bridge_process = subprocess.Popen(
            self._bridge_spec.argv,
            cwd=str(self._bridge_spec.cwd),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=sys.stderr,
            start_new_session=True,
        )
        self._bridge_protocol = BridgeProtocol(self._bridge_process)

        result = self._bridge_protocol.call("initialize", timeout_seconds=self._handshake_timeout)
        protocol = result.get("protocolVersion")
        log(f"python bridge healthy (protocol={protocol})")

    def _start_node(self) -> None:
        log(f"starting node runtime: {' '.join(self._node_spec.argv)}")
        self._node_process = subprocess.Popen(
            self._node_spec.argv,
            cwd=str(self._node_spec.cwd),
            stdin=subprocess.DEVNULL,
            stdout=sys.stderr,
            stderr=sys.stderr,
            start_new_session=True,
        )

        deadline = time.monotonic() + self._node_ready_seconds
        while time.monotonic() < deadline:
            if self._node_process.poll() is not None:
                raise RuntimeError(
                    f"node runtime exited during startup (code={self._node_process.returncode})"
                )
            time.sleep(0.05)

        if self._bridge_process and self._bridge_process.poll() is not None:
            raise RuntimeError(
                f"python bridge exited during node startup (code={self._bridge_process.returncode})"
            )

        log("node runtime healthy")

    def _monitor_loop(self) -> int:
        assert self._bridge_process is not None
        assert self._node_process is not None
        assert self._bridge_protocol is not None

        log("launcher ready")
        next_heartbeat = time.monotonic() + self._heartbeat_seconds

        while True:
            if self._stop_requested:
                self._shutdown(graceful=True)
                return 0

            bridge_code = self._bridge_process.poll()
            node_code = self._node_process.poll()

            if bridge_code is not None:
                log(f"python bridge exited unexpectedly (code={bridge_code})")
                self._shutdown(graceful=False)
                return 1 if bridge_code == 0 else bridge_code

            if node_code is not None:
                log(f"node runtime exited unexpectedly (code={node_code})")
                self._shutdown(graceful=False)
                return 1 if node_code == 0 else node_code

            now = time.monotonic()
            if now >= next_heartbeat:
                try:
                    self._bridge_protocol.call(
                        "initialize", timeout_seconds=self._handshake_timeout
                    )
                except Exception as exc:
                    log(f"bridge heartbeat failed: {exc}")
                    self._shutdown(graceful=False)
                    return 1
                next_heartbeat = now + self._heartbeat_seconds

            time.sleep(0.1)

    def _shutdown(self, graceful: bool) -> None:
        bridge = self._bridge_process
        node = self._node_process

        self._bridge_process = None
        self._node_process = None
        self._bridge_protocol = None

        if bridge is None and node is None:
            return

        if graceful:
            log("graceful shutdown: python bridge then node runtime")
            self._graceful_bridge_shutdown(bridge)
            self._terminate_process(node, "node runtime")
        else:
            log("forced shutdown: terminating children")
            self._terminate_process(bridge, "python bridge")
            self._terminate_process(node, "node runtime")

    def _graceful_bridge_shutdown(self, process: subprocess.Popen[bytes] | None) -> None:
        if process is None:
            return
        if process.poll() is not None:
            return

        try:
            protocol = BridgeProtocol(process)
            _ = protocol.call("shutdown", timeout_seconds=self._handshake_timeout)
        except Exception as exc:
            log(f"bridge shutdown RPC failed: {exc}")

        self._terminate_process(process, "python bridge")

    def _terminate_process(self, process: subprocess.Popen[bytes] | None, name: str) -> None:
        if process is None:
            return

        code = process.poll()
        if code is not None:
            log(f"{name} already exited (code={code})")
            return

        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            return

        try:
            process.wait(timeout=self._shutdown_timeout)
            log(f"{name} stopped (code={process.returncode})")
            return
        except subprocess.TimeoutExpired:
            log(f"{name} did not stop after SIGTERM; sending SIGKILL")

        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass

        try:
            process.wait(timeout=self._shutdown_timeout)
            log(f"{name} killed (code={process.returncode})")
        except subprocess.TimeoutExpired:
            log(f"{name} could not be reaped after SIGKILL")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Launch and supervise pymolcode node runtime + python bridge"
    )
    parser.add_argument(
        "--project-root",
        default=str(Path(__file__).resolve().parents[1]),
        help="project root directory (default: parent of launcher directory)",
    )
    parser.add_argument(
        "--python-cmd",
        default=f"{shlex.quote(sys.executable)} -m python.bridge.server",
        help="python bridge command",
    )
    parser.add_argument(
        "--node-cmd",
        default="node node/dist/index.js",
        help="node runtime command",
    )
    parser.add_argument(
        "--handshake-timeout",
        type=float,
        default=10.0,
        help="seconds to wait for bridge initialize/shutdown responses",
    )
    parser.add_argument(
        "--shutdown-timeout",
        type=float,
        default=8.0,
        help="seconds to wait before escalating SIGTERM to SIGKILL",
    )
    parser.add_argument(
        "--node-ready-seconds",
        type=float,
        default=1.5,
        help="seconds node process must stay alive to be considered healthy",
    )
    parser.add_argument(
        "--heartbeat-seconds",
        type=float,
        default=10.0,
        help="bridge heartbeat interval in seconds",
    )
    return parser.parse_args(argv)


def split_command(command: str) -> list[str]:
    argv = shlex.split(command)
    if not argv:
        raise ValueError("empty command")
    return argv


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    root = Path(args.project_root).resolve()

    bridge_spec = ProcessSpec(name="python bridge", argv=split_command(args.python_cmd), cwd=root)
    node_spec = ProcessSpec(name="node runtime", argv=split_command(args.node_cmd), cwd=root)

    launcher = Launcher(
        bridge_spec=bridge_spec,
        node_spec=node_spec,
        handshake_timeout=args.handshake_timeout,
        shutdown_timeout=args.shutdown_timeout,
        node_ready_seconds=args.node_ready_seconds,
        heartbeat_seconds=args.heartbeat_seconds,
    )

    signal.signal(signal.SIGINT, lambda signum, _frame: launcher.request_stop(signum))
    signal.signal(signal.SIGTERM, lambda signum, _frame: launcher.request_stop(signum))

    return launcher.run()


if __name__ == "__main__":
    raise SystemExit(main())
