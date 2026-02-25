#!/usr/bin/env bash
set -euo pipefail

PYTHON_CMD="${PYMOLCODE_PYTHON_CMD:-$(command -v python3.11 || command -v python3 || echo python)}"

"${PYTHON_CMD}" - <<'PY'
import sys

if sys.version_info[:2] < (3, 11):
    current = f"{sys.version_info.major}.{sys.version_info.minor}"
    raise SystemExit(f"Python 3.11+ required, got {current}")
PY

"${PYTHON_CMD}" -m pytest "$@"
