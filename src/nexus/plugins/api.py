from __future__ import annotations

from dataclasses import dataclass, field
from importlib import metadata
from typing import Any, Protocol

PLUGIN_API_VERSION = "1"
ENTRY_POINT_GROUP = "nexus.plugins"


@dataclass(frozen=True)
class PluginManifest:
    name: str
    version: str
    api_version: str = PLUGIN_API_VERSION
    description: str = ""
    capabilities: tuple[str, ...] = ()


@dataclass
class PluginContext:
    """Stable, intentionally small surface exposed to third-party plugins."""

    registry: "PluginRegistry"
    metadata: dict[str, Any] = field(default_factory=dict)


class NexusPlugin(Protocol):
    manifest: PluginManifest

    def register(self, context: PluginContext) -> None: ...


class PluginRegistry:
    """Deterministic registry for sensors, diagnostics, actions, and UI hooks."""

    def __init__(self) -> None:
        self._items: dict[str, dict[str, Any]] = {
            "sensor": {},
            "diagnostic": {},
            "action": {},
            "ui": {},
        }

    def add(self, kind: str, name: str, value: Any) -> None:
        if kind not in self._items:
            raise ValueError(f"unsupported plugin registration kind: {kind}")
        if not name or name.strip() != name:
            raise ValueError("plugin registration name must be non-empty and trimmed")
        if name in self._items[kind]:
            raise ValueError(f"duplicate plugin registration: {kind}:{name}")
        self._items[kind][name] = value

    def get(self, kind: str) -> dict[str, Any]:
        if kind not in self._items:
            raise ValueError(f"unsupported plugin registration kind: {kind}")
        return dict(sorted(self._items[kind].items()))

    def summary(self) -> dict[str, int]:
        return {kind: len(values) for kind, values in self._items.items()}


def discover_plugins() -> list[NexusPlugin]:
    """Load installed entry-point plugins in stable name order.

    A plugin is rejected when its manifest is missing or targets another API
    generation. Discovery is opt-in at the application boundary; importing
    this module never executes third-party code.
    """
    plugins: list[NexusPlugin] = []
    entry_points = metadata.entry_points()
    selected = entry_points.select(group=ENTRY_POINT_GROUP)
    for entry_point in sorted(selected, key=lambda item: item.name):
        plugin = entry_point.load()()
        manifest = getattr(plugin, "manifest", None)
        if not isinstance(manifest, PluginManifest):
            raise TypeError(f"plugin {entry_point.name!r} has no valid manifest")
        if manifest.api_version != PLUGIN_API_VERSION:
            raise RuntimeError(
                f"plugin {manifest.name!r} targets API {manifest.api_version}, "
                f"but NEXUS requires API {PLUGIN_API_VERSION}"
            )
        plugins.append(plugin)
    return plugins


def load_plugins(registry: PluginRegistry | None = None) -> tuple[PluginRegistry, list[PluginManifest]]:
    registry = registry or PluginRegistry()
    context = PluginContext(registry=registry)
    manifests: list[PluginManifest] = []
    for plugin in discover_plugins():
        plugin.register(context)
        manifests.append(plugin.manifest)
    return registry, manifests
