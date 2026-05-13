"""Task and result schemas."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RTLTask:
    task_id: str
    prompt: str
    module_signature: str | None = None
    testbench: str | None = None
    reference: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RunResult:
    task_id: str
    harness: str
    passed: bool
    compiled: bool
    simulated: bool
    candidate: str
    attempts: int
    compile_log: str = ""
    sim_log: str = ""
    error: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True)


def load_jsonl_tasks(path: str | Path) -> list[RTLTask]:
    tasks: list[RTLTask] = []
    with Path(path).open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            tasks.append(RTLTask(**json.loads(line)))
    return tasks


def write_jsonl_results(path: str | Path, results: list[RunResult]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        for result in results:
            fh.write(result.to_json() + "\n")
