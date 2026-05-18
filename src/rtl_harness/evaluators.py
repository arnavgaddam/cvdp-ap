"""Evaluation helpers."""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .logging import log
from .tasks import RTLTask


@dataclass(frozen=True)
class EvaluationResult:
    """Domain-success result for one generated RTL candidate."""

    passed: bool
    compiled: bool
    simulated: bool
    reason: str
    details: str
    compile_log: str = ""
    sim_log: str = ""

    def to_metadata(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_candidate(candidate: str, task: RTLTask, work_dir: Path, *, timeout_s: int = 120) -> EvaluationResult:
    image = os.getenv("CVDP_SIM_IMAGE", "nvidia/cvdp-sim:v1.0.0")
    if not task.output_path:
        raise RuntimeError(f"CVDP task {task.task_id} did not specify an RTL output path")
    if not task.harness_files:
        raise RuntimeError(f"CVDP task {task.task_id} did not include harness files")
    if shutil.which("docker") is None:
        raise RuntimeError("docker was not found; build and run the CVDP simulation image before running experiments")

    src_dir = work_dir / "src"
    rtl_dir = work_dir / "rtl"
    log(f"{task.task_id}: preparing verifier workspace {work_dir}")
    src_dir.mkdir(parents=True, exist_ok=True)
    rtl_dir.mkdir(parents=True, exist_ok=True)

    for relative_path, content in task.harness_files.items():
        target = work_dir / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(_rewrite_cvdp_paths(content), encoding="utf-8")

    candidate_path = work_dir / task.output_path
    candidate_path.parent.mkdir(parents=True, exist_ok=True)
    candidate_path.write_text(candidate, encoding="utf-8")

    env_args = []
    for key, value in _parse_cvdp_env((src_dir / ".env").read_text(encoding="utf-8")).items():
        env_args.extend(["-e", f"{key}={value}"])

    command = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{src_dir.resolve()}:/src:ro",
        "-v",
        f"{rtl_dir.resolve()}:/code/rtl:ro",
        "-v",
        f"{(work_dir / 'rundir').resolve()}:/code/rundir",
        *env_args,
        "-w",
        "/code/rundir",
        image,
        "pytest",
        "-s",
        "-o",
        "cache_dir=/code/rundir/.cache",
        "/src/test_runner.py",
        "-v",
    ]

    (work_dir / "rundir").mkdir(parents=True, exist_ok=True)
    log(f"{task.task_id}: docker run {image} pytest /src/test_runner.py")
    try:
        proc = subprocess.run(command, capture_output=True, text=True, timeout=timeout_s, check=False)
    except subprocess.TimeoutExpired as exc:
        verifier_log = (exc.stdout or "") + (exc.stderr or "")
        raise RuntimeError(f"CVDP Docker harness timed out for {task.task_id}\n{verifier_log}") from exc

    verifier_log = proc.stdout + proc.stderr
    log(f"{task.task_id}: docker verifier exited with code {proc.returncode}")
    if proc.returncode == 0:
        return EvaluationResult(
            passed=True,
            compiled=True,
            simulated=True,
            reason="passed",
            details="candidate passed the CVDP Docker simulation harness",
            sim_log=verifier_log,
        )
    reason = _classify_cvdp_failure(verifier_log)
    if reason == "infrastructure_failed":
        raise RuntimeError(f"CVDP Docker infrastructure failed for {task.task_id}\n{verifier_log}")
    return EvaluationResult(
        passed=False,
        compiled=reason != "compile_failed",
        simulated=False,
        reason=reason,
        details="candidate failed the CVDP Docker simulation harness",
        sim_log=verifier_log,
    )


def _rewrite_cvdp_paths(content: str) -> str:
    return content.replace("/rundir/harness/.cache", "/code/rundir/.cache")


def _parse_cvdp_env(content: str) -> dict[str, str]:
    env: dict[str, str] = {}
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip()
    return env


def _classify_cvdp_failure(log: str) -> str:
    lowered = log.lower()
    if "unable to find image" in lowered or "pull access denied" in lowered or "cannot connect to the docker daemon" in lowered:
        return "infrastructure_failed"
    if "error:" in lowered and "compil" in lowered:
        return "compile_failed"
    if "assert" in lowered or "failed" in lowered:
        return "simulation_failed"
    return "harness_failed"
