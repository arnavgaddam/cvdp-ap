"""Command-line entrypoint."""

from __future__ import annotations

import argparse

from .config import load_config
from .runners import run_experiment


def main() -> None:
    parser = argparse.ArgumentParser(description="Run RTL LLM harness experiments.")
    parser.add_argument("config", help="Path to a JSON-compatible YAML config.")
    args = parser.parse_args()
    run_dir = run_experiment(load_config(args.config))
    print(run_dir)


if __name__ == "__main__":
    main()
