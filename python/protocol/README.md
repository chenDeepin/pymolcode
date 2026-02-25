# JSON-RPC Framing Contract

This package defines the `pymolcode` JSON-RPC 2.0 transport contract over
LSP-style `Content-Length` framed messages.

## Transport framing

Each message must be framed as:

```
Content-Length: <number-of-json-bytes>\r\n
\r\n
<json-payload-bytes>
```

- Header name is case-insensitive, but canonical form is `Content-Length`.
- Header block must be ASCII.
- Payload must be UTF-8 JSON bytes.
- No newline-delimited ad-hoc JSON mode is allowed.

## JSON-RPC envelope

All envelopes must include:

- `jsonrpc: "2.0"`

Request shape:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "bridge.ping",
  "params": {}
}
```

Success response shape:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocol": "pymolcode-jsonrpc",
    "protocol_version": "1.0.0"
  }
}
```

Error response shape:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32601,
    "message": "Method not found"
  }
}
```

## Method catalog and versioning

- Protocol name: `pymolcode-jsonrpc`
- Protocol version: `1.0.0`
- JSON-RPC version: `2.0`

Method catalog:

- `bridge.ping`
- `pymol.load_structure`
- `pymol.set_representation`
- `pymol.color_object`
- `pymol.align_objects`
- `pymol.export_image`

## Error codes

JSON-RPC 2.0 standard errors:

- Parse error: `-32700`
- Invalid Request: `-32600`
- Method not found: `-32601`
- Invalid params: `-32602`
- Internal error: `-32603`

Custom server error range:

- `-32000` to `-32099`

The parser/writer in `framing.py` raises structured framing exceptions and maps
to JSON-RPC compatible error codes from `errors.py`.
