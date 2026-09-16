# Changelog

All notable changes to NEXUS are documented here.

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
- Unit coverage for automation rules, service actions, audit records, and package inspection/planning.

### Safety

- Automation rules only produce action proposals.
- Service actions require explicit confirmation before execution.
- Package inspection invokes `pacman -Qu` only; it never installs, removes, or upgrades packages.
- Package update planning is observation-only and does not execute the proposed `pacman` command.
- System commands are executed without a shell and can be replaced by test runners.
- Audit records contain action metadata and execution results, not command output or environment secrets.
- No package installation/removal or file deletion is performed by the current action engine.

## [0.1.0-alpha] - 2026-09-16

### Added

- Read-only Linux system status collection.
- CPU, memory, disk, and network sensors.
- Non-destructive `status`, `doctor`, and `report` commands.
- JSON health-report export.
- Unit tests and GitHub Actions CI.
