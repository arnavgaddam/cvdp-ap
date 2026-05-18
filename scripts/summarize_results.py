from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: python scripts/summarize_results.py runs/<run_dir>/results.jsonl")
    path = Path(sys.argv[1])
    results = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    passed = sum(1 for result in results if result["passed"])
    compiled = sum(1 for result in results if result["compiled"])
    total = len(results)
    print(f"tasks: {total}")
    print(f"compiled: {compiled} ({compiled / total if total else 0:.3f})")
    print(f"passed: {passed} ({passed / total if total else 0:.3f})")


if __name__ == "__main__":
    main()
