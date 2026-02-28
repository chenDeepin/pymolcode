from __future__ import annotations

from dataclasses import dataclass

from .spec import JSONRPC_VERSION, SERVER_ERROR_MAX, SERVER_ERROR_MIN

PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603


def is_server_error_code(code: int) -> bool:
    return SERVER_ERROR_MIN <= code <= SERVER_ERROR_MAX


@dataclass(frozen=True)
class JsonRpcError(Exception):
    code: int
    message: str
    data: object | None = None

    def __post_init__(self) -> None:
        Exception.__init__(self, self.message)

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {"code": self.code, "message": self.message}
        if self.data is not None:
            payload["data"] = self.data
        return payload


@dataclass(frozen=True)
class JsonRpcErrorEnvelope:
    id: object | None
    error: JsonRpcError
    jsonrpc: str = JSONRPC_VERSION

    def to_dict(self) -> dict[str, object]:
        return {
            "jsonrpc": self.jsonrpc,
            "id": self.id,
            "error": self.error.to_dict(),
        }


def make_error_response(
    request_id: object | None,
    code: int,
    message: str,
    data: object | None = None,
) -> dict[str, object]:
    return JsonRpcErrorEnvelope(
        id=request_id,
        error=JsonRpcError(code=code, message=message, data=data),
    ).to_dict()


class FramingError(ValueError):
    def __init__(self, message: str, code: int) -> None:
        super().__init__(message)
        self.code: int = code


class IncompleteFrameError(FramingError):
    pass


class MalformedFrameError(FramingError):
    pass
