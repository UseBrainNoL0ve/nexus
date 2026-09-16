from __future__ import annotations

import subprocess
from collections.abc import Callable


Runner = Callable[[tuple[str, ...]], subprocess.CompletedProcess[str]]


def notify(title: str, message: str, runner: Runner | None = None) -> bool:
    """Send a best-effort Linux desktop notification via notify-send."""
    command = ("notify-send", "--app-name=NEXUS", title, message)
    execute = runner or _default_runner
    try:
        result = execute(command)
    except OSError:
        return False
    return result.returncode == 0


def _default_runner(command: tuple[str, ...]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True, check=False)
