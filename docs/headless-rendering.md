# Headless Rendering

> Running pymolcode without a display

## Requirements

- Use a virtual X server when hardware OpenGL is required: `xvfb-run -a <command>`
- If GLX/OpenGL is not available, set `PYMOL_NO_OPENGL=1` to force software rendering
- Bridge `initialize` responses expose `render_capability` so callers can decide whether screenshot operations are supported
- Screenshot commands fail with an explicit runtime error when rendering is unsupported

## Running Headless

### With Virtual X Server (Recommended)

```bash
# Install xvfb if needed
sudo apt-get install xvfb

# Run bridge with virtual display
xvfb-run -a pymolcode-bridge

# Or with specific display
xvfb-run -a --server-args="-screen 0 1024x768x24" pymolcode-bridge
```

### With Software Rendering

```bash
# Force software rendering (no OpenGL)
export PYMOL_NO_OPENGL=1
pymolcode-bridge
```

## Capability Signals

The `render_capability` object in `initialize` response includes:

| Field | Type | Description |
|-------|------|-------------|
| `supported` | bool | Whether rendering is currently available |
| `mode` | string | Detected mode (`headless-hardware`, `headless-software`, `interactive-hardware`, `unsupported`) |
| `display` | string | X display from `DISPLAY` env var |
| `display_available` | bool | Whether X display is accessible |
| `hardware_acceleration` | bool | GLX import probe result |
| `software_rendering` | bool | `PYMOL_NO_OPENGL` fallback flag |
| `message` | string | Actionable remediation guidance |

## Example Response

```json
{
  "jsonrpc": "2.0",
  "result": {
    "protocol_version": "1.0.0",
    "render_capability": {
      "supported": true,
      "mode": "headless-software",
      "display": ":99",
      "display_available": true,
      "hardware_acceleration": false,
      "software_rendering": true,
      "message": "Using software rendering (PYMOL_NO_OPENGL=1)"
    }
  }
}
```

## Screenshot Behavior

- When `render_capability.supported` is `true`: Screenshots work normally
- When `render_capability.supported` is `false`: Screenshot commands return error with remediation steps

## See Also

- [API Reference](./api.md) - Bridge server API
