"""Model client interfaces.

The offline client makes the harness runnable before API integration. Real
providers can implement the same ``generate`` method.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class ModelClient(Protocol):
    name: str

    def generate(self, prompt: str, *, temperature: float = 0.2) -> str:
        ...


@dataclass
class OfflineModel:
    name: str = "offline"

    def generate(self, prompt: str, *, temperature: float = 0.2) -> str:
        return (
            "// OfflineModel placeholder. Replace with a real provider.\n"
            "module placeholder;\n"
            "endmodule\n"
        )


def make_model(name: str) -> ModelClient:
    if name == "offline":
        return OfflineModel()
    raise ValueError(f"Unknown model '{name}'. Add a provider in rtl_harness.models.")
