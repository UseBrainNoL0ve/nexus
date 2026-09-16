# Changelog

All notable changes to NEXUS are documented here.

## [Unreleased] - 2026-09-16

### Added

- Historical observation storage through `nexus-observe`.
- Deterministic historical trend detection for persistent CPU, memory, and disk pressure.
- Structured diagnostic findings for resource pressure, failed systemd services, and available package updates.
- `nexus-diagnose` read-only diagnostic CLI with text and JSON output.
- Structured incident modeling for grouping related findings.
- Explainable remediation proposals containing evidence, rationale, risk, command representation, and confirmation metadata.
- Focused unit coverage for historical detection, diagnostics, incident grouping, and remediation planning.

### Safety

- Historical trend detection is observation-only and never executes remediation.
- Diagnostic collection failures are surfaced as evidence rather than triggering automatic changes.
- Incident creation does not authorize any operation.
- Remediation proposals are planning-only.
- Potentially mutating package and service operations remain behind explicit confirmation gates.
- High-level diagnostic features do not accept arbitrary shell commands.

### Documentation

- README updated to describe the observation → diagnosis → incident → planning pipeline.
- Architecture documentation expanded with layer responsibilities and mutation boundaries.
- Contributor guidance expanded with testing, documentation, and safety expectations.
- Dedicated diagnostic architecture documentation added.

## [0.5.0-alpha] - 2026-09-16

### Added

- Functional desktop navigation across Dashboard, Services, Packages, Doctor, Scheduler, and History.
- Read-only systemd service detail view backed by live inspection.
- Read-only pacman update detail view backed by live inspection.
- Dedicated Doctor health-check view.
- Scheduler configuration view backed by the persisted schedule store.
- Scheduler execution history view backed by the scheduler audit log.
- Reusable read-only GUI detail page component with explicit refresh controls.
- Active navigation state and consistent NEXUS dark visual language across pages.
- Richer dashboard presentation with icon-led metric cards, system identity telemetry, live monitor status, and refined navigation branding.
- Interactive visual states for navigation, health badges, refresh controls, metric cards, and read-only mode.
- Background dashboard worker so telemetry collection no longer blocks the Qt event loop.
- Near-real-time dashboard refresh with visible scan state and refresh-cycle telemetry.
- Interactive service management with explicit confirmation for start, stop, and restart.
- Interactive package update management with explicit per-package confirmation.
- Service and package tables with selectable rows, state columns, and action controls.

### Safety

- Service mutations remain behind the existing NEXUS confirmation-gated action engine.
- Package mutations remain behind the existing confirmation-gated package engine.
- The GUI does not expose arbitrary shell execution.
- Background telemetry is observation-only and does not mutate system state.
- Detail-page failures are contained in the page view instead of terminating the desktop application.
- Visual enhancements do not change the underlying system command safety model.

## [0.4.0-alpha] - 2026-09-16

### Added

- JSON-backed recurring scheduler for user-owned NEXUS jobs.
- `nexus-scheduler add` for creating recurring jobs with explicit intervals.
- `nexus-scheduler list` and `nexus-scheduler remove` for schedule management.
- `nexus-scheduler run` for one-shot execution of due jobs.
- `nexus-scheduler run --daemon` for a lightweight foreground scheduler loop.
- Safe built-in scheduled actions for health checks and package inspection.
- Linux desktop notifications through `notify-send` when available.
- Injectable scheduler action runners and notification runners for deterministic tests.
- Scheduler model and persistence unit tests.

### Safety

- Scheduled jobs can only invoke allow-listed NEXUS actions; arbitrary shell commands are not supported.
- The scheduler does not automatically install packages or modify services.
- Package scheduling is read-only inspection through `pacman -Qu`.
- Schedules are stored as user-owned JSON under `.nexus/schedules.json`.
- Desktop notifications are best-effort and do not affect scheduled action execution.

## [0.2.0-alpha] - 2026-09-16

### Added

- Observation-only automation rule engine.
- Disk-pressure and memory-pressure rules.
- `nexus automate` dry-run command.
- Read-only systemd service inspection.
- Safe systemd service action planning for start, stop, and restart.
- Explicit confirmation gate for service action execution.
- Injectable command runner for deterministic execution tests.
- JSON Lines audit logging for blocked and attempted service actions.
- Automatic `.nexus/audit.jsonl` recording from the service CLI.
- `nexus history` command for inspecting recent service action audit entries.
- Bounded audit history reader with missing-log and invalid-limit handling.
- Read-only pacman update inspection through `nexus packages`.
- Package update action planning through `nexus packages update`.
- Explicit confirmation metadata for package update proposals.
- Confirmation-gated package update execution engine.
- Injectable package command runner for deterministic execution tests.
- Explicit `nexus packages update --confirm` execution path.
- Unit coverage for automation rules, service actions, audit records, and package inspection/planning/execution.

### Safety

- Automation rules only produce action proposals.
- Service actions require explicit confirmation before execution.
- Package inspection invokes `pacman -Qu` only; it never installs, removes, or upgrades packages.
- Package update planning is observation-only until an explicit confirmation flag is supplied.
- Package execution uses an argument sequence without a shell and supports injected test runners.
- System commands can be replaced by deterministic test runners.
- Audit records contain action metadata and execution results, not command output or environment secrets.
- No package installation/removal or file deletion is performed without an explicit confirmation path.

## [0.1.0-alpha] - 2026-09-16

### Added

- Read-only Linux system status collection.
- CPU, memory, disk, and network sensors.
- Non-destructive `status`, `doctor`, and `report` commands.
- JSON health-report export.
- Unit tests and GitHub Actions CI.
