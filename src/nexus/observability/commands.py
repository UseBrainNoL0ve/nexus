from __future__ import annotations

import argparse
import json

from nexus.observability.history import analyze_observations, append_observation, read_observations
from nexus.sensors.system import collect_snapshot


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nexus-observe",
        description="Record and analyze historical NEXUS system telemetry.",
    )
    parser.add_argument("--limit", type=int, default=20, help="number of recent observations to analyze")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.limit < 1:
        print("Observation limit must be at least 1.")
        return 2

    snapshot = collect_snapshot()
    observation = append_observation(snapshot)
    observations = read_observations(limit=args.limit)
    analysis = analyze_observations(observations)
    analysis["recorded_at"] = observation.timestamp

    if args.json:
        print(json.dumps(analysis, indent=2, sort_keys=True))
        return 0

    print("NEXUS historical observability")
    print(f"Recorded:     {observation.timestamp}")
    print(f"Observations: {analysis['observations']}")
    print(f"CPU:          {analysis['current']['cpu_load_percent']:.1f}%")
    print(f"Memory:       {analysis['current']['memory_used_percent']:.1f}%")
    print(f"Disk:         {analysis['current']['disk_used_percent']:.1f}%")

    if not analysis["baseline_available"]:
        print("Baseline:     waiting for a second observation")
        print("Run nexus-observe again later to calculate deltas.")
        return 0

    delta = analysis["delta"]
    print("Since previous observation:")
    print(f"  CPU:        {delta['cpu_load_percent']:+.1f} percentage points")
    print(f"  Memory:     {delta['memory_used_percent']:+.1f} percentage points")
    print(f"  Disk:       {delta['disk_used_percent']:+.1f} percentage points")

    for interface, traffic in analysis["network_delta"].items():
        print(
            f"  Network {interface}: "
            f"RX +{traffic['rx_bytes_delta']} bytes / "
            f"TX +{traffic['tx_bytes_delta']} bytes"
        )
    return 0
