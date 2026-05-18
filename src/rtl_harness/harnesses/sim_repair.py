"""Simulation-feedback repair harness."""

from __future__ import annotations

from pathlib import Path

from rtl_harness.config import ExperimentConfig
from rtl_harness.evaluators import evaluate_candidate
from rtl_harness.extract import extract_verilog, has_required_signature
from rtl_harness.logging import log
from rtl_harness.models import ModelClient
from rtl_harness.prompts import (
    build_attempt_repair_prompt,
    build_baseline_prompt,
    build_diagnosis_prompt,
    format_structured_feedback,
    summarize_verifier_feedback,
)
from rtl_harness.tasks import RTLTask, RunResult


class SimulationRepairHarness:
    name = "sim_repair"

    def __init__(self, config: ExperimentConfig):
        self.config = config

    def run(self, task: RTLTask, model: ModelClient, work_dir: Path) -> RunResult:
        prompt = build_baseline_prompt(task)
        candidate = ""
        compile_log = ""
        sim_log = ""
        attempts = []
        for attempt in range(1, self.config.max_repair_iters + 2):
            log(f"{task.task_id}: attempt {attempt} generating candidate with {model.name}")
            candidate = extract_verilog(model.generate(prompt, temperature=self.config.temperature))
            if not has_required_signature(candidate, task.module_signature):
                log(f"{task.task_id}: attempt {attempt} missing required module signature")
                evaluation_metadata = {
                    "passed": False,
                    "compiled": False,
                    "simulated": False,
                    "reason": "signature_missing",
                    "details": "required module name was not present",
                    "compile_log": "",
                    "sim_log": "",
                }
                feedback = summarize_verifier_feedback("signature_missing", evaluation_metadata["details"], "")
                log(f"{task.task_id}: attempt {attempt} diagnosing signature failure")
                diagnosis = self._diagnose_failure(task, model, candidate, feedback)
                attempts.append(
                    {
                        "attempt": attempt,
                        "verifier": evaluation_metadata,
                        "structured_feedback": feedback,
                        "diagnosis": diagnosis,
                    }
                )
                prompt = build_attempt_repair_prompt(
                    task,
                    candidate,
                    format_structured_feedback(feedback),
                    diagnosis=diagnosis,
                    repair_attempt=attempt,
                )
                continue
            log(f"{task.task_id}: attempt {attempt} running CVDP verifier")
            evaluation = evaluate_candidate(candidate, task, work_dir / f"attempt_{attempt}", timeout_s=self.config.timeout_s)
            compile_log = evaluation.compile_log
            sim_log = evaluation.sim_log
            log(f"{task.task_id}: attempt {attempt} verifier result reason={evaluation.reason}, passed={evaluation.passed}")
            if evaluation.passed:
                attempts.append({"attempt": attempt, "verifier": evaluation.to_metadata()})
                return RunResult(
                    task.task_id,
                    self.name,
                    True,
                    evaluation.compiled,
                    evaluation.simulated,
                    candidate,
                    attempt,
                    compile_log,
                    sim_log,
                    metadata={"attempts": attempts, "verifier": evaluation.to_metadata()},
                )
            feedback = summarize_verifier_feedback(evaluation.reason, evaluation.details, sim_log or compile_log)
            log(f"{task.task_id}: attempt {attempt} diagnosing verifier failure")
            diagnosis = self._diagnose_failure(task, model, candidate, feedback)
            attempts.append(
                {
                    "attempt": attempt,
                    "verifier": evaluation.to_metadata(),
                    "structured_feedback": feedback,
                    "diagnosis": diagnosis,
                }
            )
            prompt = build_attempt_repair_prompt(
                task,
                candidate,
                format_structured_feedback(feedback),
                diagnosis=diagnosis,
                repair_attempt=attempt,
            )
        final_verifier = attempts[-1]["verifier"] if attempts else {"reason": "no_attempts", "details": "no candidates generated"}
        return RunResult(
            task.task_id,
            self.name,
            False,
            bool(final_verifier.get("compiled", False)),
            False,
            candidate,
            self.config.max_repair_iters + 1,
            compile_log,
            sim_log,
            metadata={"attempts": attempts, "verifier": final_verifier},
        )

    def _diagnose_failure(self, task: RTLTask, model: ModelClient, candidate: str, feedback: dict[str, str]) -> str:
        if not self.config.prompt.get("diagnose_failures", True):
            return ""
        diagnosis_prompt = build_diagnosis_prompt(task, candidate, format_structured_feedback(feedback))
        return model.generate(diagnosis_prompt, temperature=0.0).strip()
