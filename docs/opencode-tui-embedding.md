# OpenCode TUI Embedding Notes (Reference Only)

> Note: Current primary architecture for pymolcode is **single-Python bridge**.
> This document records how OpenCode’s TUI works in case we later choose
> to integrate it as a separate process.

## OpenCode TUI Structure

- Location: `scripts/opencode-dev/packages/opencode/src/cli/cmd/tui/`
- Key files:
  - `thread.ts` – main TUI command (`TuiThreadCommand`)
  - `attach.ts` – attach to running server (`AttachCommand`)
  - `worker.ts` – worker RPC
  - `ui/`, `component/`, `util/` – UI implementation and helpers

### TuiThreadCommand (High-Level)

File: `thread.ts`

- Declared via `cmd({ command: "$0 [project]", describe: "start opencode tui", ... })`
- Responsibilities:
  - Parse CLI options:
    - network options (host, port)
    - model selection (`--model`)
    - session control (`--continue`, `--session`, `--fork`)
    - initial prompt / agent selection
  - Resolve working directory
  - Set up RPC client to worker (`Rpc.client<typeof rpc>`)
  - Create:
    - `fetch` shim (`createWorkerFetch`)
    - `EventSource` shim (`createEventSource`)
  - Start TUI loop via `tui(...)` from `./app`

### AttachCommand (High-Level)

File: `attach.ts`

- Command: `attach <url>`
- Responsibilities:
  - Attach TUI to a running OpenCode server
  - Handle Windows terminal quirks (Ctrl+C guard, processed input)
  - Forward directory and auth headers to server

## Embedding Considerations

If we later decide to embed OpenCode TUI inside PyMOL’s Qt panel:

1. **Process Model**
   - Run OpenCode TUI as a separate Node process.
   - Use PTY or pipes to capture TUI output.

2. **Output Handling**
   - TUI writes to stdout/stderr.
   - A wrapper (e.g. `embedded-tui.ts`) could:
     - Capture output
     - Forward events over JSON-RPC to Python
     - Allow Python to render a simplified view in Qt.

3. **Control Flow**
   - Qt panel would not render the full TUI terminal.
   - Instead, it would:
     - Send commands to TUI process (via stdin or RPC)
     - Receive high-level “events” (chat chunks, tool results)
     - Display them in a richer Qt-native UI.

## Current Decision

- For now, pymolcode will:
  - Implement its own Python-only agent + skills layer.
  - Use PyMOL’s Python API directly.
- This document is kept as a reference if we later:
  - Need full OpenCode TUI integration, or
  - Want to reuse existing ACP tooling.

