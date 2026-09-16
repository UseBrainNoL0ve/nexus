from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from nexus.automation.platform import ActionRegistry, ActionSpec, AutomationPlatform
from nexus.plugins.api import PluginManifest, PluginRegistry


class PlatformTests(unittest.TestCase):
    def test_registry_is_deterministic(self) -> None:
        registry = ActionRegistry()
        registry.register(ActionSpec("zeta", "Z", "low"), lambda _: "z")
        registry.register(ActionSpec("alpha", "A", "low"), lambda _: "a")
        self.assertEqual([item.id for item in registry.list()], ["alpha", "zeta"])

    def test_dry_run_never_calls_handler(self) -> None:
        calls: list[dict] = []
        registry = ActionRegistry()
        registry.register(ActionSpec("demo", "Demo", "low"), lambda value: calls.append(value) or "done")
        with tempfile.TemporaryDirectory() as directory:
            platform = AutomationPlatform(registry, Path(directory) / "audit.jsonl")
            result = platform.execute("demo", {"x": 1}, dry_run=True)
        self.assertEqual(result.status, "planned")
        self.assertFalse(result.executed)
        self.assertEqual(calls, [])

    def test_confirmation_gate_blocks_mutation(self) -> None:
        registry = ActionRegistry()
        registry.register(ActionSpec("demo", "Demo", "medium"), lambda _: "done")
        with tempfile.TemporaryDirectory() as directory:
            platform = AutomationPlatform(registry, Path(directory) / "audit.jsonl")
            result = platform.execute("demo", dry_run=False, confirmed=False)
        self.assertEqual(result.status, "blocked")
        self.assertFalse(result.executed)

    def test_plugin_registry_rejects_duplicates(self) -> None:
        registry = PluginRegistry()
        registry.add("sensor", "demo", object())
        with self.assertRaises(ValueError):
            registry.add("sensor", "demo", object())

    def test_plugin_manifest_is_versioned(self) -> None:
        manifest = PluginManifest("example", "1.0", capabilities=("sensor",))
        self.assertEqual(manifest.api_version, "1")


if __name__ == "__main__":
    unittest.main()
