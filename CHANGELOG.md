# Changelog

All notable changes to NEXUS are documented here.

## [Unreleased] - 2026-09-17

### Added

- Added capability-based Linux distribution detection from `/etc/os-release`.
- Added native package-manager detection for pacman, apt, dnf, yum, zypper, apk, xbps, and eopkg.
- Added portable package-update inspection that conservatively parses supported native managers.
- Added native service-manager command mapping for systemd, OpenRC, runit, s6-rc, and dinit.
- Added distribution-agnostic platform documentation and explicit fail-closed behavior for unsupported capabilities.

### User value

- NEXUS core functionality no longer depends on CachyOS or Arch Linux.
- Debian/Ubuntu, Fedora/RHEL-family, SUSE, Alpine, Void, Solus, Arch-family, and other distributions can use the same NEXUS application when a supported native capability is present.
- Unknown distributions remain usable for telemetry and diagnosis instead of being rejected by a distro allow-list.

### Safety

- Distribution detection never executes a command.
- Package and service operations use native backends rather than guessed commands.
- Unsupported package/service capabilities fail closed; NEXUS does not invent a mutation command.
- Existing confirmation gates, dry-run behavior, and audit boundaries remain unchanged.

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
