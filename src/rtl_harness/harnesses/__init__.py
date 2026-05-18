"""Harness registry."""

from __future__ import annotations

from rtl_harness.config import ExperimentConfig
from rtl_harness.harnesses.baseline import BaselineHarness
from rtl_harness.harnesses.sim_repair import SimulationRepairHarness


def make_harness(config: ExperimentConfig):
    harnesses = {
        "baseline": BaselineHarness,
        "sim_repair": SimulationRepairHarness,
    }
    try:
        return harnesses[config.harness](config)
    except KeyError as exc:
        raise ValueError(f"Unknown harness '{config.harness}'") from exc
