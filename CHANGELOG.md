# Changelog

All notable changes to NEXUS are documented here.

## [0.2.0-alpha] - 2026-09-16

### Added

- Observation-only automation rule engine.
- Disk-pressure and memory-pressure rules.
- `nexus automate` dry-run command.
- Unit coverage for triggered and non-triggered automation rules.

### Safety

- Automation rules only produce action proposals.
- No package installation/removal, service mutation, file deletion, or privileged command execution is performed.

## [0.1.0-alpha] - 2026-09-16

### Added

- Read-only Linux system status collection.
- CPU, memory, disk, and network sensors.
- Non-destructive `status`, `doctor`, and `report` commands.
- JSON health-report export.
- Unit tests and GitHub Actions CI.
