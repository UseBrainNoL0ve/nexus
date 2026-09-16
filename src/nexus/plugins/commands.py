from __future__ import annotations

import argparse

from nexus.plugins.api import load_plugins


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect installed NEXUS plugins")
    parser.add_argument("--json", action="store_true", help="emit machine-readable plugin metadata")
    args = parser.parse_args(argv)
    registry, manifests = load_plugins()
    if args.json:
        import json
        print(json.dumps({
            "api_version": "1",
            "plugins": [manifest.__dict__ for manifest in manifests],
            "registrations": registry.summary(),
        }, indent=2, sort_keys=True))
        return 0
    print("NEXUS plugin runtime")
    print("API version: 1")
    if not manifests:
        print("No external plugins installed.")
    for manifest in manifests:
        print(f"- {manifest.name} {manifest.version}: {manifest.description or 'no description'}")
    print(f"Registrations: {registry.summary()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
