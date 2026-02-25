#!/usr/bin/env bash
set -euo pipefail

python -m pip install -q pip-audit bandit || true

echo "[security] dependency audit"
pip-audit || true

echo "[security] static analysis"
bandit -r src/pymolcode -q || true

echo "[security] tests"
python -m pytest tests/unit -q
