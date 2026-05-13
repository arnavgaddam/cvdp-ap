"""Experiment runner."""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from .config import ExperimentConfig
from .harnesses import make_harness
from .models import make_model
from .tasks import RunResult, load_jsonl_tasks, write_jsonl_results


def run_experiment(config: ExperimentConfig) -> Path:
    tasks = load_jsonl_tasks(config.dataset)
    if config.limit is not None:
        tasks = tasks[: config.limit]
    run_name = datetime.now().strftime("%Y%m%d_%H%M%S") + f"_{config.name}"
    run_dir = Path(config.output_dir) / run_name
    run_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(config.dataset, run_dir / "dataset.jsonl")

    model = make_model(config.model)
    harness = make_harness(config)
    results: list[RunResult] = []
    for task in tasks:
        task_dir = run_dir / "artifacts" / task.task_id
        result = harness.run(task, model, task_dir)
        results.append(result)
        task_dir.mkdir(parents=True, exist_ok=True)
        (task_dir / "candidate.v").write_text(result.candidate, encoding="utf-8")
        (task_dir / "compile.log").write_text(result.compile_log, encoding="utf-8")
        (task_dir / "sim.log").write_text(result.sim_log, encoding="utf-8")

    write_jsonl_results(run_dir / "results.jsonl", results)
    passed = sum(result.passed for result in results)
    summary = f"tasks: {len(results)}\npassed: {passed}\npass_rate: {passed / len(results) if results else 0:.3f}\n"
    (run_dir / "summary.txt").write_text(summary, encoding="utf-8")
    return run_dir
