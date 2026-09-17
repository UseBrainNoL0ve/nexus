# Changelog

All notable changes to NEXUS are documented here.

## [Unreleased] - 2026-09-17

### Added

- Added capability-based Linux distribution detection from `/etc/os-release`.
- Added native package-manager detection for pacman, apt, dnf, yum, zypper, apk, xbps, and eopkg.
- Added explicit Debian-family mappings for Pardus, Kali Linux, and Parrot OS.
- Added portable package-update inspection that conservatively parses supported native managers.
- Added native service-manager command mapping for systemd, OpenRC, runit, s6-rc, and dinit.
- Added distribution-agnostic platform documentation and explicit fail-closed behavior for unsupported capabilities.
- Added a privacy-first design specification for an opt-in local screen activity recorder, including visible state, local-only storage, retention controls, and a Wayland/XDG Desktop Portal strategy.
- Added a native system-wide installer that places NEXUS under `/usr/local` and exposes commands directly on `PATH`, without a repository-local venv or pipx environment.
- Added the first screen-capture lifecycle foundation: explicit policy gate, persistent local session metadata, state machine, backend interface, and `nexus-capture` CLI.
- Added a Wayland/XDG Desktop Portal capability backend that probes the user-session portal without starting a capture.
- Added compatibility tests covering Pardus, Ubuntu, Fedora, Kali, Parrot, and CachyOS package-manager selection.

### User value

- NEXUS core functionality no longer depends on CachyOS or Arch Linux.
- Common Linux distributions can use the same application when a supported native capability is present.
- Unknown distributions remain usable for telemetry and diagnosis instead of being rejected by a distro allow-list.
- End users can run NEXUS as a normal system command without activating the repository's development virtual environment.
- The screen activity roadmap now has a testable lifecycle and Wayland capability boundary before platform-specific frame recording is introduced.

### Fixed

- Package command-runner injection is resolved at call time, avoiding import-time default binding and making tests deterministic.
- Portable package parsing was hardened for apt update output and other native-manager formats.
- Service-name validation is now backend-aware: systemd retains its `.service` unit contract while other supported service managers can use native service names.
- Cross-distro tests explicitly inject package and service backends instead of depending on the GitHub Actions host.
- Usage and screen-capture documentation now distinguish capability coverage from full end-to-end feature support.

### Safety

- Distribution detection never executes a command.
- Package and service operations use native backends rather than guessed commands.
- Unsupported package/service capabilities fail closed; NEXUS does not invent a mutation command.
- Existing confirmation gates, dry-run behavior, and audit boundaries remain unchanged.
- Screen capture is disabled by default and the current backend refuses to claim recording until an approved PipeWire recorder exists.
- Screen activity is designed with no hidden activation, no remote activation path, no network upload, and no permission bypass.
- Screen recordings are treated as sensitive local data because they may contain credentials or private content.

## [Previous Unreleased]

### Added

- Added a unified operational summary that combines health, host telemetry, failed services, package updates, and scheduler state into one read-only view.
- Added `nexus-summary` with human-readable and `--json` output for quick operational triage.
- Added `nexus-scheduler install` to generate a user-level systemd service from the active Python environment.
- Added explicit `nexus-scheduler install --enable` support for deliberate service activation.
- Added the GUI Incident & Remediation Center for evidence-first incident investigation and explainable planning.
- Added a dependency-free historical telemetry chart for CPU, memory, and disk observations.
- Added the v0.6 plugin runtime with API-versioned manifests, deterministic entry-point discovery, and capability registration.
- Added `nexus-plugins` and `nexus-plugins --json` for plugin inspection.
- Added the v1 policy-gated automation platform with named action registration, dry-run execution, confirmation boundaries, and platform audit logging.

### Fixed

- Historical trend findings now use an explicit deterministic metric order.
- Failed-service diagnostic evidence now includes the exact systemd unit name.

### Safety

- Diagnostic collection failures are surfaced as evidence rather than triggering automatic changes.
- Remediation proposals are planning-only.
- Plugin registrations are named and capability-scoped; the plugin API provides no arbitrary shell interface.
- Automation defaults to dry-run and requires explicit confirmation for registered mutating actions.
