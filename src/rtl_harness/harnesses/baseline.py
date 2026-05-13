"""Single-shot generation harness."""

from __future__ import annotations

from pathlib import Path

from rtl_harness.config import ExperimentConfig
from rtl_harness.evaluators import evaluate_candidate
from rtl_harness.extract import extract_verilog, has_required_signature
from rtl_harness.models import ModelClient
from rtl_harness.prompts import build_baseline_prompt
from rtl_harness.tasks import RTLTask, RunResult


class BaselineHarness:
    name = "baseline"

    def __init__(self, config: ExperimentConfig):
        self.config = config

    def run(self, task: RTLTask, model: ModelClient, work_dir: Path) -> RunResult:
        response = model.generate(build_baseline_prompt(task), temperature=self.config.temperature)
        candidate = extract_verilog(response)
        if not has_required_signature(candidate, task.module_signature):
            return RunResult(task.task_id, self.name, False, False, False, candidate, 1, error="required module signature missing")
        passed, compiled, simulated, compile_log, sim_log = evaluate_candidate(
            candidate, task, work_dir, timeout_s=self.config.timeout_s
        )
        return RunResult(task.task_id, self.name, passed, compiled, simulated, candidate, 1, compile_log, sim_log)
