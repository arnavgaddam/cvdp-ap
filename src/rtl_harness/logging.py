"""Small stderr logger for long-running experiments."""

from __future__ import annotations

import sys
from datetime import datetime


def log(message: str) -> None:
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}", file=sys.stderr, flush=True)
