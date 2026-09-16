from __future__ import annotations

import argparse
import json

from nexus.summary import collect_summary, format_summary


def main() -> int:
    parser = argparse.ArgumentParser(prog="nexus-summary", description="Show a unified read-only NEXUS operational summary")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON output")
    args = parser.parse_args()

    payload = collect_summary()
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(format_summary(payload))
    return 0 if payload["status"] == "healthy" else 1
