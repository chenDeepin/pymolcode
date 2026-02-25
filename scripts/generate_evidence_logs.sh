#!/usr/bin/env bash
# Generate evidence logs for Tasks 1-18
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
EVIDENCE_DIR="$ROOT_DIR/.sisyphus/evidence"

mkdir -p "$EVIDENCE_DIR"

PYTHON_CMD="${PYMOLCODE_PYTHON_CMD:-$(command -v python3.11 || command -v python3 || echo python)}"

echo "Generating evidence logs for Tasks 1-18..."
echo "Using Python: $PYTHON_CMD"
echo "Evidence directory: $EVIDENCE_DIR"
echo

# Task 1: Serialized execution policy
echo "=== Task 1: Serialized Execution Policy ==="
"$PYTHON_CMD" -m pytest tests/unit/test_bridge_server.py::test_bridge_server_rejects_when_busy -v 2>&1 | tee "$EVIDENCE_DIR/task-01-serialized-execution.log"
echo

# Task 2: Contract parity
echo "=== Task 2: Contract Parity ==="
"$PYTHON_CMD" -m pytest tests/unit/test_bridge_server.py::test_bridge_server_ping_returns_contract_metadata -v 2>&1 | tee "$EVIDENCE_DIR/task-02-contract-parity.log"
echo

# Task 3: Runtime gate
echo "=== Task 3: Runtime Gate ==="
"$PYTHON_CMD" -m pytest tests/unit/test_cli_bridge.py::test_python_runtime_gate_requires_py311 -v 2>&1 | tee "$EVIDENCE_DIR/task-03-runtime-gate.log"
echo

# Task 4: Report bundle models
echo "=== Task 4: Report Bundle Models ==="
"$PYTHON_CMD" -m pytest tests/unit/test_artifact_bundle_phase4.py::test_create_report_bundle_writes_archive_and_required_files -v 2>&1 | tee "$EVIDENCE_DIR/task-04-report-bundle.log"
echo

# Task 5: Upstream mirror policy
echo "=== Task 5: Upstream Mirror Policy ==="
{
  echo "Checking third_party/README.md for read-only policy..."
  grep -i "read-only" "$ROOT_DIR/third_party/README.md" || echo "NOT FOUND"
  echo
  echo "Checking manifest exists..."
  ls -la "$ROOT_DIR/third_party/pymol-open-source/manifest.yaml" || echo "NOT FOUND"
} 2>&1 | tee "$EVIDENCE_DIR/task-05-upstream-mirror.log"
echo

# Task 6: Pytest markers
echo "=== Task 6: Pytest Markers ==="
"$PYTHON_CMD" -m pytest --markers 2>&1 | head -50 | tee "$EVIDENCE_DIR/task-06-pytest-markers.log"
echo

# Task 7: Bridge JSON-RPC methods
echo "=== Task 7: Bridge JSON-RPC Methods ==="
"$PYTHON_CMD" -m pytest tests/unit/test_bridge_server.py::test_bridge_server_handles_set_representation_request \
  tests/unit/test_bridge_server.py::test_bridge_server_handles_color_object_request \
  tests/unit/test_bridge_server.py::test_bridge_server_handles_align_and_export_requests -v 2>&1 | tee "$EVIDENCE_DIR/task-07-jsonrpc-methods.log"
echo

# Task 8: Typed BridgeClient helpers
echo "=== Task 8: Typed BridgeClient Helpers ==="
"$PYTHON_CMD" -m pytest tests/unit/test_bridge_client.py -v 2>&1 | tee "$EVIDENCE_DIR/task-08-bridge-client.log"
echo

# Task 9: CLI bridge commands
echo "=== Task 9: CLI Bridge Commands ==="
"$PYTHON_CMD" -m pytest tests/unit/test_cli_bridge.py::test_bridge_load_structure_python_runner \
  tests/unit/test_cli_bridge.py::test_bridge_control_commands_python_runner \
  tests/unit/test_cli_bridge.py::test_bridge_align_objects_command -v 2>&1 | tee "$EVIDENCE_DIR/task-09-cli-commands.log"
echo

# Task 10: TUI command palette
echo "=== Task 10: TUI Command Palette ==="
"$PYTHON_CMD" -m pytest tests/unit/test_tui_bridge_actions.py -v 2>&1 | tee "$EVIDENCE_DIR/task-10-tui-command-palette.log"
echo

# Task 11: GUI quick actions
echo "=== Task 11: GUI Quick Actions ==="
"$PYTHON_CMD" -m pytest tests/unit/test_gui_quick_actions.py -v 2>&1 | tee "$EVIDENCE_DIR/task-11-gui-quick-actions.log"
echo

# Task 12: Comparative output
echo "=== Task 12: Comparative Output ==="
"$PYTHON_CMD" -m pytest tests/unit/test_phase3_features.py -k "workflow" -v 2>&1 | tee "$EVIDENCE_DIR/task-12-comparative-output.log"
echo

# Task 13: Headless demos
echo "=== Task 13: Headless Demos ==="
{
  echo "=== Core Demo ==="
  "$PYTHON_CMD" "$ROOT_DIR/examples/bridge/core_demo.py" --source "$ROOT_DIR/.pymolcode_artifacts/smoke/task20_full/fixtures/mobile.pdb" --name mobile --output-dir "$ROOT_DIR/.pymolcode_artifacts/evidence/task13_core" 2>&1 || echo "Core demo failed"
  echo
  echo "=== Comparative Demo ==="
  "$PYTHON_CMD" "$ROOT_DIR/examples/bridge/comparative_demo.py" \
    --mobile-source "$ROOT_DIR/.pymolcode_artifacts/smoke/task20_full/fixtures/mobile.pdb" \
    --target-source "$ROOT_DIR/.pymolcode_artifacts/smoke/task20_full/fixtures/target.pdb" \
    --output-dir "$ROOT_DIR/.pymolcode_artifacts/evidence/task13_comparative" 2>&1 || echo "Comparative demo failed"
} | tee "$EVIDENCE_DIR/task-13-headless-demos.log"
echo

# Task 14: Allowlist enforcement
echo "=== Task 14: Allowlist Enforcement ==="
"$PYTHON_CMD" -m pytest tests/unit/test_executor_phase4.py::test_executor_policy_blocks_non_allowlisted_bridge_action \
  tests/unit/test_planner_phase4.py::test_planner_downgrades_non_allowlisted_bridge_tool_to_chat -v 2>&1 | tee "$EVIDENCE_DIR/task-14-allowlist.log"
echo

# Task 15: Mini workflow
echo "=== Task 15: Mini Workflow ==="
"$PYTHON_CMD" -m pytest tests/unit/test_mini_workflow_phase4.py -v 2>&1 | tee "$EVIDENCE_DIR/task-15-mini-workflow.log"
echo

# Task 16: Workflow bundle wiring
echo "=== Task 16: Workflow Bundle Wiring ==="
"$PYTHON_CMD" -m pytest tests/unit/test_artifact_bundle_phase4.py -v 2>&1 | tee "$EVIDENCE_DIR/task-16-workflow-bundle.log"
echo

# Task 17: Policy checks in workflow
echo "=== Task 17: Policy Checks in Workflow ==="
"$PYTHON_CMD" -m pytest tests/unit/test_mini_workflow_phase4.py::test_run_skill_bridge_mini_workflow_respects_bridge_policy -v 2>&1 | tee "$EVIDENCE_DIR/task-17-policy-checks.log"
echo

# Task 18: CLI workflow demo
echo "=== Task 18: CLI Workflow Demo ==="
"$PYTHON_CMD" -m pytest tests/unit/test_cli_bridge.py::test_bridge_workflow_demo_command \
  tests/unit/test_cli_bridge.py::test_bridge_workflow_demo_command_failure -v 2>&1 | tee "$EVIDENCE_DIR/task-18-workflow-demo.log"
echo

echo "=== Evidence Generation Complete ==="
echo "Evidence files generated in: $EVIDENCE_DIR"
ls -lh "$EVIDENCE_DIR"/task-*.log
