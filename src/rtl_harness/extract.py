"""Verilog extraction and lightweight sanitation."""

from __future__ import annotations

import re


FENCE_RE = re.compile(r"```(?:systemverilog|verilog|sv)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)
MODULE_RE = re.compile(r"\bmodule\b.*?\bendmodule\b", re.DOTALL)


def extract_verilog(text: str) -> str:
    """Extract the most likely Verilog module from a model response."""
    fenced = FENCE_RE.findall(text)
    search_space = "\n\n".join(fenced) if fenced else text
    modules = MODULE_RE.findall(search_space)
    if modules:
        return "\n\n".join(module.strip() for module in modules) + "\n"
    return search_space.strip() + "\n"


def has_required_signature(candidate: str, module_signature: str | None) -> bool:
    if not module_signature:
        return True
    match = re.search(r"\bmodule\s+([A-Za-z_][A-Za-z0-9_$]*)", module_signature)
    if not match:
        return True
    return re.search(rf"\bmodule\s+{re.escape(match.group(1))}\b", candidate) is not None
