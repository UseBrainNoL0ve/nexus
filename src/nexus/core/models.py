from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class CpuSnapshot:
    load_percent: float
    logical_cores: int


@dataclass(frozen=True)
class MemorySnapshot:
    total_bytes: int
    available_bytes: int
    used_percent: float


@dataclass(frozen=True)
class DiskSnapshot:
    path: str
    total_bytes: int
    free_bytes: int
    used_percent: float


@dataclass(frozen=True)
class NetworkInterface:
    name: str
    rx_bytes: int
    tx_bytes: int


@dataclass(frozen=True)
class SystemSnapshot:
    hostname: str
    platform: str
    kernel: str
    python_version: str
    cpu: CpuSnapshot
    memory: MemorySnapshot
    disk: DiskSnapshot
    network: tuple[NetworkInterface, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
