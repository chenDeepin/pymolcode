from __future__ import annotations

import json
from collections.abc import Mapping
from typing import cast

from .errors import (
    INTERNAL_ERROR,
    INVALID_PARAMS,
    INVALID_REQUEST,
    PARSE_ERROR,
    IncompleteFrameError,
    MalformedFrameError,
)
from .spec import BODY_ENCODING, CONTENT_LENGTH_HEADER, HEADER_ENCODING, HEADER_TERMINATOR


def _is_valid_id(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, bool):
        return False
    return isinstance(value, (str, int, float))


def _validate_error_payload(error: object) -> None:
    if not isinstance(error, Mapping):
        raise MalformedFrameError("JSON-RPC error must be an object", INVALID_REQUEST)
    error_map = cast(Mapping[str, object], error)
    code = error_map.get("code")
    message = error_map.get("message")
    if isinstance(code, bool) or not isinstance(code, int):
        raise MalformedFrameError("JSON-RPC error code must be an integer", INVALID_REQUEST)
    if not isinstance(message, str):
        raise MalformedFrameError("JSON-RPC error message must be a string", INVALID_REQUEST)


def validate_jsonrpc_message(message: Mapping[str, object]) -> None:
    if message.get("jsonrpc") != "2.0":
        raise MalformedFrameError("JSON-RPC version must be '2.0'", INVALID_REQUEST)

    if "method" in message:
        method = message.get("method")
        if not isinstance(method, str) or not method:
            raise MalformedFrameError("JSON-RPC method must be a non-empty string", INVALID_REQUEST)
        if "params" in message:
            params = message.get("params")
            if not isinstance(params, (list, dict)):
                raise MalformedFrameError(
                    "JSON-RPC params must be an array or object",
                    INVALID_PARAMS,
                )
        if "id" in message and not _is_valid_id(message.get("id")):
            raise MalformedFrameError("JSON-RPC id has an invalid type", INVALID_REQUEST)
        return

    has_result = "result" in message
    has_error = "error" in message
    if has_result == has_error:
        raise MalformedFrameError(
            "JSON-RPC response must contain exactly one of result or error",
            INVALID_REQUEST,
        )
    if "id" not in message or not _is_valid_id(message.get("id")):
        raise MalformedFrameError("JSON-RPC response id is missing or invalid", INVALID_REQUEST)
    if has_error:
        _validate_error_payload(message.get("error"))


def _parse_headers(raw_headers: bytes) -> dict[str, str]:
    try:
        header_text = raw_headers.decode(HEADER_ENCODING)
    except UnicodeDecodeError as exc:
        raise MalformedFrameError("Header block is not ASCII", INVALID_REQUEST) from exc

    lines = header_text.split("\r\n")
    headers: dict[str, str] = {}
    for line in lines:
        if not line:
            continue
        if ":" not in line:
            raise MalformedFrameError("Malformed header line", INVALID_REQUEST)
        key, value = line.split(":", 1)
        normalized_key = key.strip().lower()
        if not normalized_key:
            raise MalformedFrameError("Header name cannot be empty", INVALID_REQUEST)
        if normalized_key in headers:
            raise MalformedFrameError("Duplicate header", INVALID_REQUEST)
        headers[normalized_key] = value.strip()
    return headers


def _parse_content_length(headers: Mapping[str, str]) -> int:
    raw_length = headers.get(CONTENT_LENGTH_HEADER.lower())
    if raw_length is None:
        raise MalformedFrameError("Missing Content-Length header", INVALID_REQUEST)
    if not raw_length or not raw_length.isdigit():
        raise MalformedFrameError("Content-Length must be a non-negative integer", INVALID_REQUEST)
    return int(raw_length)


def _decode_json_payload(payload_text: str) -> object:
    return cast(object, json.loads(payload_text))


def parse_next_frame(buffer: bytes) -> tuple[dict[str, object], bytes]:
    header_end = buffer.find(HEADER_TERMINATOR)
    if header_end == -1:
        raise IncompleteFrameError("Incomplete header block", PARSE_ERROR)

    header_block = buffer[:header_end]
    payload_start = header_end + len(HEADER_TERMINATOR)
    headers = _parse_headers(header_block)
    content_length = _parse_content_length(headers)
    payload_end = payload_start + content_length

    if len(buffer) < payload_end:
        raise IncompleteFrameError("Body shorter than Content-Length", PARSE_ERROR)

    payload_bytes = buffer[payload_start:payload_end]
    remaining = buffer[payload_end:]

    try:
        payload_text = payload_bytes.decode(BODY_ENCODING)
    except UnicodeDecodeError as exc:
        raise MalformedFrameError("Payload must be valid UTF-8", PARSE_ERROR) from exc

    try:
        parsed_json = _decode_json_payload(payload_text)
    except json.JSONDecodeError as exc:
        raise MalformedFrameError("Invalid JSON payload", PARSE_ERROR) from exc

    if not isinstance(parsed_json, dict):
        raise MalformedFrameError("JSON-RPC payload must be an object", INVALID_REQUEST)

    payload: dict[str, object] = {}
    parsed_map = cast(Mapping[object, object], parsed_json)
    for key, value in parsed_map.items():
        if not isinstance(key, str):
            raise MalformedFrameError("JSON-RPC keys must be strings", INVALID_REQUEST)
        payload[key] = value

    validate_jsonrpc_message(payload)
    return payload, remaining


def parse_frames(buffer: bytes) -> tuple[list[dict[str, object]], bytes]:
    messages: list[dict[str, object]] = []
    pending = buffer
    while pending:
        try:
            message, pending = parse_next_frame(pending)
        except IncompleteFrameError:
            break
        messages.append(message)
    return messages, pending


def parse_frame(frame: bytes) -> dict[str, object]:
    message, trailing = parse_next_frame(frame)
    if trailing:
        raise MalformedFrameError("Unexpected trailing bytes after frame", INTERNAL_ERROR)
    return message


def write_frame(message: Mapping[str, object], validate: bool = True) -> bytes:
    payload = dict(message)
    if validate:
        validate_jsonrpc_message(payload)

    body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode(BODY_ENCODING)
    header = f"{CONTENT_LENGTH_HEADER}: {len(body)}\r\n\r\n".encode(HEADER_ENCODING)
    return header + body
