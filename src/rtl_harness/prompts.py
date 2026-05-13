"""Prompt construction helpers."""

from __future__ import annotations

from .tasks import RTLTask


BASE_SYSTEM_INSTRUCTIONS = """You are generating synthesizable Verilog RTL.
Return only Verilog code. Do not include Markdown fences, explanations, or a testbench.
Preserve the exact module name and port list when one is provided.
"""


def build_baseline_prompt(task: RTLTask) -> str:
    parts = [BASE_SYSTEM_INSTRUCTIONS.strip()]
    if task.module_signature:
        parts.append("Required module interface:\n" + task.module_signature.strip())
    parts.append("Task specification:\n" + task.prompt.strip())
    return "\n\n".join(parts)


def build_repair_prompt(task: RTLTask, candidate: str, feedback: str) -> str:
    return "\n\n".join(
        [
            BASE_SYSTEM_INSTRUCTIONS.strip(),
            "The previous Verilog candidate failed. Fix it while preserving the required interface.",
            f"Required module interface:\n{task.module_signature or 'Not provided.'}",
            f"Task specification:\n{task.prompt.strip()}",
            f"Previous candidate:\n{candidate.strip()}",
            f"Tool feedback:\n{feedback.strip()}",
        ]
    )
