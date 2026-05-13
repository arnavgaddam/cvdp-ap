"""Wrappers around local RTL tools."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ToolResult:
    ok: bool
    log: str


def tool_available(name: str) -> bool:
    return shutil.which(name) is not None


def compile_with_iverilog(candidate: str, work_dir: Path, *, timeout_s: int = 10) -> ToolResult:
    if not tool_available("iverilog"):
        return ToolResult(False, "iverilog not found")
    work_dir.mkdir(parents=True, exist_ok=True)
    rtl_path = work_dir / "candidate.v"
    out_path = work_dir / "candidate.out"
    rtl_path.write_text(candidate, encoding="utf-8")
    proc = subprocess.run(
        ["iverilog", "-g2012", "-o", str(out_path), str(rtl_path)],
        cwd=work_dir,
        capture_output=True,
        text=True,
        timeout=timeout_s,
        check=False,
    )
    return ToolResult(proc.returncode == 0, proc.stdout + proc.stderr)


def simulate_with_iverilog(candidate: str, testbench: str | None, work_dir: Path, *, timeout_s: int = 10) -> ToolResult:
    if testbench is None:
        return ToolResult(False, "no testbench provided")
    if not tool_available("iverilog") or not tool_available("vvp"):
        return ToolResult(False, "iverilog/vvp not found")
    work_dir.mkdir(parents=True, exist_ok=True)
    rtl_path = work_dir / "candidate.v"
    tb_path = work_dir / "testbench.v"
    out_path = work_dir / "sim.out"
    rtl_path.write_text(candidate, encoding="utf-8")
    tb_path.write_text(testbench, encoding="utf-8")
    compile_proc = subprocess.run(
        ["iverilog", "-g2012", "-o", str(out_path), str(tb_path), str(rtl_path)],
        cwd=work_dir,
        capture_output=True,
        text=True,
        timeout=timeout_s,
        check=False,
    )
    if compile_proc.returncode != 0:
        return ToolResult(False, compile_proc.stdout + compile_proc.stderr)
    sim_proc = subprocess.run(
        ["vvp", str(out_path)],
        cwd=work_dir,
        capture_output=True,
        text=True,
        timeout=timeout_s,
        check=False,
    )
    return ToolResult(sim_proc.returncode == 0, sim_proc.stdout + sim_proc.stderr)
