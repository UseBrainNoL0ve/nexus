# NEXUS Platform Architecture

NEXUS is distribution-agnostic at the architecture boundary: core telemetry, diagnostics, incident modeling, remediation planning, plugins, and automation do not depend on a specific Linux distribution.

## Distribution and capability detection

NEXUS reads `/etc/os-release` when available and detects native capabilities instead of branching on a hard-coded distro list. Unknown distributions remain usable for system telemetry and diagnosis.

Package operations use a native backend selected from the executable available on the host:

- pacman — Arch Linux family and derivatives
- apt — Debian/Ubuntu family and derivatives
- dnf — Fedora/RHEL-family systems
- yum — legacy RHEL-family systems
- zypper — openSUSE/SUSE systems
- apk — Alpine Linux
- xbps-install — Void Linux
- eopkg — Solus

If no supported package manager is installed, NEXUS does not guess. Package inspection simply has no backend and the rest of the platform remains available.

Service actions similarly detect systemd, OpenRC, runit, s6-rc, or dinit. Systemd inspection remains available where systemd is present; on other init systems, NEXUS exposes the service-manager capability without pretending that systemd-specific state exists.

This capability model is intentionally broader than a distro allow-list: a new distribution can work without a code change when it provides a supported native interface.

## Incident & Remediation Center

`nexus-gui` exposes an **Incidents** page. It collects current evidence, groups findings into incidents, and renders explainable remediation proposals. The page is intentionally read-only: diagnosis and planning do not execute changes.

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

## Safety contract

1. Observation and diagnosis remain non-mutating.
2. Every automation capability is named and allow-listed.
3. Dry-run is the default.
4. Mutating actions require explicit authorization unless a registered action explicitly declares otherwise.
5. Execution results are recorded in JSON Lines audit storage.
6. Plugins are version-gated and do not receive an arbitrary shell interface.
7. Distribution-specific operations are delegated to detected native backends; unsupported capabilities fail closed.

The result is a portable Linux platform: NEXUS does not require CachyOS or Arch Linux for its core functionality, while preserving native package/service behavior where the host provides it.
