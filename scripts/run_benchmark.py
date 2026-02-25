from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def run_pytest_benchmark(target: str, runs: int) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for index in range(runs):
        env = os.environ.copy()
        env["PYTHONHASHSEED"] = str(100 + index)
        cmd = [sys.executable, "-m", "pytest", target, "-q"]
        completed = subprocess.run(cmd, capture_output=True, text=True, check=False, env=env)
        results.append(
            {
                "run": index + 1,
                "returncode": completed.returncode,
                "stdout_tail": completed.stdout[-500:],
                "stderr_tail": completed.stderr[-500:],
            }
        )
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Run reproducibility benchmark for pytest target")
    parser.add_argument("target", help="pytest target path")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--output", default="results/benchmark.json")
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "platform": platform.platform(),
        "target": args.target,
        "runs": args.runs,
        "results": run_pytest_benchmark(args.target, args.runs),
    }
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(str(output_path))


if __name__ == "__main__":
    main()
