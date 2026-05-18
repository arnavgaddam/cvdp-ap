from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("usage: python scripts/make_tables.py runs/*/results.jsonl")
    rows = ["run,harness,tasks,compiled,simulated,passed,pass_rate,failures_by_reason"]
    for arg in sys.argv[1:]:
        path = Path(arg)
        results = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        total = len(results)
        compiled = sum(1 for result in results if result["compiled"])
        simulated = sum(1 for result in results if result["simulated"])
        passed = sum(1 for result in results if result["passed"])
        harness = results[0]["harness"] if results else ""
        failures = Counter(
            result.get("metadata", {}).get("verifier", {}).get("reason", result.get("error") or "unknown")
            for result in results
            if not result["passed"]
        )
        failure_summary = ";".join(f"{reason}:{count}" for reason, count in sorted(failures.items()))
        rows.append(
            f"{path.parent.name},{harness},{total},{compiled},{simulated},{passed},{passed / total if total else 0:.3f},{failure_summary}"
        )
    output = Path("results/tables/summary.csv")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
