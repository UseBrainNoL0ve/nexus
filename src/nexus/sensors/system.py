from pathlib import Path
import os
import platform
import shutil

from nexus.core.models import (
    CpuSnapshot,
    DiskSnapshot,
    MemorySnapshot,
    NetworkInterface,
    SystemSnapshot,
)


def _memory() -> MemorySnapshot:
    values: dict[str, int] = {}
    for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
        key, value = line.split(":", 1)
        values[key] = int(value.strip().split()[0]) * 1024
    total = values.get("MemTotal", 0)
    available = values.get("MemAvailable", values.get("MemFree", 0))
    used = 0.0 if total == 0 else (1 - available / total) * 100
    return MemorySnapshot(total, available, round(used, 2))


def _cpu() -> CpuSnapshot:
    cores = os.cpu_count() or 1
    try:
        load = os.getloadavg()[0]
        percent = min(100.0, max(0.0, load / cores * 100))
    except (AttributeError, OSError):
        percent = 0.0
    return CpuSnapshot(round(percent, 2), cores)


def _disk() -> DiskSnapshot:
    usage = shutil.disk_usage("/")
    used = 0.0 if usage.total == 0 else (usage.used / usage.total) * 100
    return DiskSnapshot("/", usage.total, usage.free, round(used, 2))


def _network() -> tuple[NetworkInterface, ...]:
    base = Path("/sys/class/net")
    interfaces: list[NetworkInterface] = []
    if not base.exists():
        return ()
    for interface in sorted(base.iterdir()):
        stats = interface / "statistics"
        try:
            rx = int((stats / "rx_bytes").read_text().strip())
            tx = int((stats / "tx_bytes").read_text().strip())
        except (FileNotFoundError, ValueError):
            continue
        interfaces.append(NetworkInterface(interface.name, rx, tx))
    return tuple(interfaces)


def collect_snapshot() -> SystemSnapshot:
    """Collect local, read-only system information."""
    return SystemSnapshot(
        hostname=platform.node(),
        platform=platform.system(),
        kernel=platform.release(),
        python_version=platform.python_version(),
        cpu=_cpu(),
        memory=_memory(),
        disk=_disk(),
        network=_network(),
    )
