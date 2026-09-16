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
- Unit coverage for triggered and non-triggered automation rules and service actions.

### Safety

- Automation rules only produce action proposals.
- Service actions require explicit confirmation before execution.
- System commands are executed without a shell and can be replaced by a test runner.
- No package installation/removal or file deletion is performed by the current action engine.

## [0.1.0-alpha] - 2026-09-16

### Added

- Read-only Linux system status collection.
- CPU, memory, disk, and network sensors.
- Non-destructive `status`, `doctor`, and `report` commands.
- JSON health-report export.
- Unit tests and GitHub Actions CI.
