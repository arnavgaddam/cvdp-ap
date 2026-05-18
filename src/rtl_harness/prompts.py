"""Prompt construction helpers."""

from __future__ import annotations

from .tasks import RTLTask


BASE_SYSTEM_INSTRUCTIONS = """You are generating synthesizable Verilog RTL.
Return only Verilog code. Do not include Markdown fences, explanations, or verification code.
Preserve the exact module name and port list when one is provided.
"""


def build_baseline_prompt(task: RTLTask) -> str:
    parts = [BASE_SYSTEM_INSTRUCTIONS.strip()]
    if task.module_signature:
        parts.append("Required module interface:\n" + task.module_signature.strip())
    parts.append("Task specification:\n" + task.prompt.strip())
    return "\n\n".join(parts)


def build_diagnosis_prompt(task: RTLTask, candidate: str, feedback: str) -> str:
    return "\n\n".join(
        [
            "You are diagnosing a failed Verilog/SystemVerilog RTL candidate.",
            "Do not write revised RTL. Return a concise diagnosis with the likely root cause and repair strategy.",
            f"Required module interface:\n{task.module_signature or 'Not provided.'}",
            f"Task specification:\n{task.prompt.strip()}",
            f"Failed candidate:\n{candidate.strip()}",
            f"Verifier feedback:\n{feedback.strip()}",
        ]
    )


def build_attempt_repair_prompt(
    task: RTLTask,
    candidate: str,
    feedback: str,
    *,
    diagnosis: str,
    repair_attempt: int,
) -> str:
    if repair_attempt <= 1:
        instruction = "The previous RTL candidate failed. Fix the immediate verifier issue while preserving the required interface."
    else:
        instruction = (
            "The previous repair also failed. Re-check the full specification, the diagnosis, and the verifier feedback. "
            "Rewrite the RTL if needed, but preserve the required interface."
        )
    parts = [
        BASE_SYSTEM_INSTRUCTIONS.strip(),
        instruction,
        f"Required module interface:\n{task.module_signature or 'Not provided.'}",
        f"Task specification:\n{task.prompt.strip()}",
        f"Previous candidate:\n{candidate.strip()}",
    ]
    if diagnosis:
        parts.append(f"Diagnosis from previous failure:\n{diagnosis.strip()}")
    parts.append(f"Structured verifier feedback:\n{feedback.strip()}")
    return "\n\n".join(parts)


def format_structured_feedback(feedback: dict[str, str]) -> str:
    return "\n".join(
        [
            f"Failure category: {feedback['category']}",
            f"Summary: {feedback['summary']}",
            f"Action: {feedback['action']}",
            f"Relevant log excerpt:\n{feedback['excerpt']}",
        ]
    )


def summarize_verifier_feedback(reason: str, details: str, log: str, *, max_chars: int = 4000) -> dict[str, str]:
    excerpt = _tail(log.strip(), max_chars=max_chars)
    if reason == "signature_missing":
        return {
            "category": "interface_error",
            "summary": details,
            "action": "Return a module with the exact required top-level module name and ports.",
            "excerpt": excerpt or details,
        }
    if reason == "compile_failed":
        return {
            "category": "compile_error",
            "summary": "The candidate did not compile in the CVDP harness.",
            "action": "Fix syntax, declarations, module name, ports, widths, and unsupported constructs before changing behavior.",
            "excerpt": excerpt,
        }
    if reason == "simulation_failed":
        return {
            "category": "simulation_mismatch",
            "summary": "The candidate compiled but failed one or more CVDP checks.",
            "action": "Use the assertion failure and the original specification to correct the RTL behavior.",
            "excerpt": excerpt,
        }
    return {
        "category": reason or "verifier_failure",
        "summary": details or "The candidate failed the CVDP verifier.",
        "action": "Use the verifier log and original specification to produce a corrected RTL implementation.",
        "excerpt": excerpt,
    }


def _tail(text: str, *, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[-max_chars:]
