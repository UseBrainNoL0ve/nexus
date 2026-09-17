from __future__ import annotations

import argparse
import json

from nexus.capture.manager import CaptureManager


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="nexus-capture", description="Privacy-first local screen activity capture")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status", help="show the latest capture session")
    sub.add_parser("list", help="list local capture session metadata")
    sub.add_parser("start", help="request a capture session; disabled until explicitly enabled")
    sub.add_parser("pause", help="pause the active capture session")
    sub.add_parser("resume", help="resume the active capture session")
    sub.add_parser("stop", help="stop the active capture session")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    manager = CaptureManager()

    try:
        if args.command == "status":
            session = manager.status()
            payload = session.to_dict() if session else {"state": "off"}
            print(json.dumps(payload, indent=2, sort_keys=True))
            return 0
        if args.command == "list":
            print(json.dumps([session.to_dict() for session in manager.list()], indent=2, sort_keys=True))
            return 0
        if args.command == "start":
            session = manager.start()
        elif args.command == "pause":
            session = manager.pause()
        elif args.command == "resume":
            session = manager.resume()
        else:
            session = manager.stop()
    except (PermissionError, RuntimeError, ValueError) as exc:
        print(f"NEXUS capture: {exc}")
        return 2

    print(json.dumps(session.to_dict(), indent=2, sort_keys=True))
    return 0
