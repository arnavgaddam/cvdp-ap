"""Configuration loading for experiments."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ExperimentConfig:
    name: str
    dataset: str
    harness: str
    dataset_format: str = "rtl_task"
    model: str = "offline"
    output_dir: str = "runs"
    limit: int | None = None
    temperature: float = 0.2
    max_candidates: int = 1
    max_repair_iters: int = 0
    timeout_s: int = 10
    verifier: dict[str, Any] = field(default_factory=dict)
    prompt: dict[str, Any] = field(default_factory=dict)


def load_config(path: str | Path) -> ExperimentConfig:
    """Load a JSON-compatible YAML config using only the standard library."""
    config_path = Path(path)
    raw = config_path.read_text(encoding="utf-8")
    data = json.loads(raw)
    return ExperimentConfig(**data)
