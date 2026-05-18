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
    output_path: str | None = None
    module_signature: str | None = None
    harness_files: dict[str, str] = field(default_factory=dict)
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


def load_cvdp_tasks(path: str | Path) -> list[RTLTask]:
    tasks: list[RTLTask] = []
    with Path(path).open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            output_context = row["output"]["context"]
            output_path = next(iter(output_context))
            env = row["harness"]["files"].get("src/.env", "")
            module_name = _env_value(env, "TOPLEVEL")
            tasks.append(
                RTLTask(
                    task_id=row["id"],
                    prompt=row["input"]["prompt"],
                    output_path=output_path,
                    module_signature=f"module {module_name}" if module_name else None,
                    harness_files=row["harness"]["files"],
                    metadata={
                        "source": "cvdp",
                        "categories": row["categories"],
                        "output_path": output_path,
                        "toplevel": module_name,
                        "module": _env_value(env, "MODULE"),
                    },
                )
            )
    return tasks


def load_tasks(path: str | Path, dataset_format: str = "rtl_task") -> list[RTLTask]:
    if dataset_format == "cvdp":
        return load_cvdp_tasks(path)
    raise ValueError(f"Unknown dataset format '{dataset_format}'")


def _env_value(env: str, key: str) -> str | None:
    for line in env.splitlines():
        if "=" not in line:
            continue
        name, value = line.split("=", 1)
        if name.strip() == key:
            return value.strip()
    return None


def write_jsonl_results(path: str | Path, results: list[RunResult]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        for result in results:
            fh.write(result.to_json() + "\n")
