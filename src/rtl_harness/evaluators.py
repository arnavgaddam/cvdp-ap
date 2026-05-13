"""Evaluation helpers."""

from __future__ import annotations

from pathlib import Path

from .tasks import RTLTask
from .tools import compile_with_iverilog, simulate_with_iverilog


def evaluate_candidate(candidate: str, task: RTLTask, work_dir: Path, *, timeout_s: int = 10) -> tuple[bool, bool, bool, str, str]:
    compile_result = compile_with_iverilog(candidate, work_dir / "compile", timeout_s=timeout_s)
    if task.testbench:
        sim_result = simulate_with_iverilog(candidate, task.testbench, work_dir / "sim", timeout_s=timeout_s)
        passed = compile_result.ok and sim_result.ok
        return passed, compile_result.ok, sim_result.ok, compile_result.log, sim_result.log
    return compile_result.ok, compile_result.ok, False, compile_result.log, ""
