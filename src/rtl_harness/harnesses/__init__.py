"""Harness registry."""

from __future__ import annotations

from rtl_harness.config import ExperimentConfig
from rtl_harness.harnesses.baseline import BaselineHarness
from rtl_harness.harnesses.best_of_k import BestOfKHarness
from rtl_harness.harnesses.compile_repair import CompileRepairHarness
from rtl_harness.harnesses.plan_then_code import PlanThenCodeHarness
from rtl_harness.harnesses.prompt_only import PromptOnlyHarness
from rtl_harness.harnesses.sim_repair import SimulationRepairHarness


def make_harness(config: ExperimentConfig):
    harnesses = {
        "baseline": BaselineHarness,
        "prompt_only": PromptOnlyHarness,
        "compile_repair": CompileRepairHarness,
        "sim_repair": SimulationRepairHarness,
        "best_of_k": BestOfKHarness,
        "plan_then_code": PlanThenCodeHarness,
    }
    try:
        return harnesses[config.harness](config)
    except KeyError as exc:
        raise ValueError(f"Unknown harness '{config.harness}'") from exc
