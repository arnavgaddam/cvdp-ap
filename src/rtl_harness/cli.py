"""Command-line entrypoint."""

from __future__ import annotations

import argparse
import os
import shlex
from pathlib import Path

from .config import load_config
from .runners import run_experiment


def main() -> None:
    parser = argparse.ArgumentParser(description="Run RTL LLM harness experiments.")
    parser.add_argument("config", help="Path to a JSON-compatible YAML config.")
    args = parser.parse_args()
    load_dotenv(Path(".env"))
    run_dir = run_experiment(load_config(args.config))
    print(run_dir)


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            raise RuntimeError(f"Invalid .env line: {line}")
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise RuntimeError("Invalid .env line with empty key")
        parsed = shlex.split(value, comments=False, posix=True)
        os.environ.setdefault(key, parsed[0] if parsed else "")


if __name__ == "__main__":
    main()
