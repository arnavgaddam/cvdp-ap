"""Experiment runner."""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from .config import ExperimentConfig
from .harnesses import make_harness
from .logging import log
from .models import make_model
from .tasks import RunResult, load_tasks, write_jsonl_results


def run_experiment(config: ExperimentConfig) -> Path:
    log(f"Loading dataset {config.dataset} ({config.dataset_format})")
    tasks = load_tasks(config.dataset, config.dataset_format)
    if config.limit is not None:
        tasks = tasks[: config.limit]
    run_name = datetime.now().strftime("%Y%m%d_%H%M%S") + f"_{config.name}"
    run_dir = Path(config.output_dir) / run_name
    run_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(config.dataset, run_dir / "dataset.jsonl")
    log(f"Run directory: {run_dir}")
    log(f"Config: harness={config.harness}, model={config.model}, tasks={len(tasks)}, temperature={config.temperature}")

    model = make_model(config.model)
    harness = make_harness(config)
    results: list[RunResult] = []
    for index, task in enumerate(tasks, start=1):
        task_dir = run_dir / "artifacts" / task.task_id
        log(f"[{index}/{len(tasks)}] Starting {task.task_id}")
        result = harness.run(task, model, task_dir)
        log(f"[{index}/{len(tasks)}] Finished {task.task_id}: passed={result.passed}, attempts={result.attempts}")
        results.append(result)
        task_dir.mkdir(parents=True, exist_ok=True)
        (task_dir / "candidate.v").write_text(result.candidate, encoding="utf-8")
        (task_dir / "compile.log").write_text(result.compile_log, encoding="utf-8")
        (task_dir / "sim.log").write_text(result.sim_log, encoding="utf-8")

    write_jsonl_results(run_dir / "results.jsonl", results)
    passed = sum(result.passed for result in results)
    summary = f"tasks: {len(results)}\npassed: {passed}\npass_rate: {passed / len(results) if results else 0:.3f}\n"
    (run_dir / "summary.txt").write_text(summary, encoding="utf-8")
    log(f"Completed run: passed={passed}/{len(results)} ({passed / len(results) if results else 0:.3f})")
    return run_dir
