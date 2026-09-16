from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from nexus.core.models import SystemSnapshot


DEFAULT_PATH = Path(".nexus/observations.jsonl")


@dataclass(frozen=True)
class Observation:
    timestamp: str
    snapshot: dict[str, Any]

    @classmethod
    def from_snapshot(cls, snapshot: SystemSnapshot) -> "Observation":
        return cls(
            timestamp=datetime.now(timezone.utc).isoformat(),
            snapshot=snapshot.to_dict(),
        )

    def to_dict(self) -> dict[str, Any]:
        return {"timestamp": self.timestamp, "snapshot": self.snapshot}


def append_observation(snapshot: SystemSnapshot, path: Path = DEFAULT_PATH) -> Observation:
    observation = Observation.from_snapshot(snapshot)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(observation.to_dict(), sort_keys=True) + "\n")
    return observation


def read_observations(path: Path = DEFAULT_PATH, limit: int = 100) -> list[Observation]:
    if limit < 1 or not path.exists():
        return []

    entries: list[Observation] = []
    for line in path.read_text(encoding="utf-8").splitlines()[-limit:]:
        if not line.strip():
            continue
        payload = json.loads(line)
        entries.append(Observation(timestamp=payload["timestamp"], snapshot=payload["snapshot"]))
    return entries


def _delta(current: float, previous: float) -> float:
    return round(current - previous, 2)


def analyze_observations(observations: list[Observation]) -> dict[str, Any]:
    if not observations:
        return {"observations": 0, "baseline_available": False}

    current = observations[-1].snapshot
    result: dict[str, Any] = {
        "observations": len(observations),
        "baseline_available": len(observations) >= 2,
        "current": {
            "timestamp": observations[-1].timestamp,
            "cpu_load_percent": current["cpu"]["load_percent"],
            "memory_used_percent": current["memory"]["used_percent"],
            "disk_used_percent": current["disk"]["used_percent"],
        },
    }

    if len(observations) < 2:
        return result

    previous = observations[-2].snapshot
    result["delta"] = {
        "cpu_load_percent": _delta(current["cpu"]["load_percent"], previous["cpu"]["load_percent"]),
        "memory_used_percent": _delta(current["memory"]["used_percent"], previous["memory"]["used_percent"]),
        "disk_used_percent": _delta(current["disk"]["used_percent"], previous["disk"]["used_percent"]),
    }

    current_interfaces = {item["name"]: item for item in current["network"]}
    previous_interfaces = {item["name"]: item for item in previous["network"]}
    traffic: dict[str, dict[str, int]] = {}
    for name in sorted(current_interfaces.keys() & previous_interfaces.keys()):
        current_interface = current_interfaces[name]
        previous_interface = previous_interfaces[name]
        traffic[name] = {
            "rx_bytes_delta": max(0, current_interface["rx_bytes"] - previous_interface["rx_bytes"]),
            "tx_bytes_delta": max(0, current_interface["tx_bytes"] - previous_interface["tx_bytes"]),
        }
    result["network_delta"] = traffic
    return result
