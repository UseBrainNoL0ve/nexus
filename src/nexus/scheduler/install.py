from __future__ import annotations

import subprocess
import sys
from pathlib import Path


DEFAULT_UNIT_PATH = Path.home() / ".config/systemd/user/nexus-scheduler.service"


def unit_text(python_executable: str | None = None) -> str:
    executable = python_executable or sys.executable
    return f'''[Unit]
Description=NEXUS user scheduler
After=default.target

[Service]
Type=simple
ExecStart={executable} -m nexus.scheduler.commands run --daemon
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
'''


def install_user_service(path: Path = DEFAULT_UNIT_PATH, python_executable: str | None = None) -> Path:
    """Install a user-level systemd unit; does not enable or start it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(unit_text(python_executable), encoding="utf-8")
    return path


def enable_user_service() -> subprocess.CompletedProcess[str]:
    """Enable and start the already-installed user service."""
    return subprocess.run(
        ["systemctl", "--user", "enable", "--now", "nexus-scheduler.service"],
        text=True,
        capture_output=True,
        check=False,
    )
