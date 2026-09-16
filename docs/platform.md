# NEXUS Platform Architecture

This document closes the v0.6–v1 roadmap boundary: a desktop investigation center, richer historical telemetry, a stable plugin API, and a policy-gated automation runtime.

## Incident & Remediation Center

`nexus-gui` now exposes an **Incidents** page. It collects current evidence, groups findings into incidents, and renders explainable remediation proposals. The page is intentionally read-only: diagnosis and planning do not execute changes.

## Historical visualization

The **Telemetry** page reads `.nexus/observations.jsonl` and renders CPU, memory, and disk utilization without adding a charting dependency. It uses the existing observation store, so the visualization remains local and deterministic.

Build history with:

```bash
nexus-observe --limit 20
```

Then launch:

```bash
nexus-gui
```

## v0.6 plugin system

Plugins are discovered through the Python packaging entry-point group `nexus.plugins`.

A plugin provides:

- `PluginManifest` with a stable API version (`1`)
- `register(context)` to register capabilities
- optional sensor, diagnostic, action, and UI registrations

Discovery is deterministic by entry-point name and rejects incompatible API versions. The registry has no shell-execution primitive; plugins must expose named capabilities through the registry.

Inspect installed plugins:

```bash
nexus-plugins
nexus-plugins --json
```

The API is intentionally small so a future v0.7 release can evolve implementations without making plugin authors depend on internal NEXUS modules.

## v1 automation platform

The automation runtime introduces four explicit layers:

```text
Named Action
    ↓
Action Registry (allow-list)
    ↓
Automation Policy (dry-run / confirmation)
    ↓
Execution Handler
    ↓
Platform Audit (.nexus/platform-audit.jsonl)
```

`AutomationPlatform` never accepts arbitrary shell strings. An action must first be registered with an `ActionSpec` and a Python handler. Mutating actions default to requiring confirmation. Dry-run is the default execution mode and still writes an audit record.

This gives NEXUS a stable orchestration boundary for systemd, package management, scheduler jobs, plugins, and future Linux capabilities without collapsing them into one unrestricted command runner.

## Safety contract

1. Observation and diagnosis remain non-mutating.
2. Every automation capability is named and allow-listed.
3. Dry-run is the default.
4. Mutating actions require explicit authorization unless a registered action explicitly declares otherwise.
5. Execution results are recorded in JSON Lines audit storage.
6. Plugins are version-gated and do not receive an arbitrary shell interface.

The result is a complete platform boundary rather than a single monolithic automation command: NEXUS can grow new Linux capabilities while keeping authorization and auditability centralized.
