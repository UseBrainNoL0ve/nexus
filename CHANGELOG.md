# Changelog

All notable changes to NEXUS are documented here.

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
