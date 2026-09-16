# Changelog

All notable changes to NEXUS are documented here.

## [Unreleased] - 2026-09-16

### Added

- Added a unified operational summary that combines health, host telemetry, failed services, package updates, and scheduler state into one read-only view.
- Added `nexus-summary` with human-readable and `--json` output for quick operational triage.
- Added `nexus-scheduler install` to generate a user-level systemd service from the active Python environment.
- Added explicit `nexus-scheduler install --enable` support for deliberate service activation.
- Added focused tests for operational-summary aggregation and scheduler installation side-effect boundaries.
- Added `docs/operations.md` covering the operational summary and persistent scheduler workflow.
- Historical observation storage through `nexus-observe`.
- Deterministic historical trend detection for persistent CPU, memory, and disk pressure.
- Structured diagnostic findings for resource pressure, failed systemd services, and available package updates.
- `nexus-diagnose` read-only diagnostic CLI with text and JSON output.
- Integrated `nexus diagnose` command as the primary user-facing entry point for diagnosis.
- `nexus diagnose` combines findings, incident grouping, evidence, and explainable next-step proposals in one command.
- Structured incident modeling for grouping related findings.
- Explainable remediation proposals containing evidence, rationale, risk, command representation, and confirmation metadata.
- Focused unit coverage for historical detection, diagnostics, incident grouping, remediation planning, and the integrated CLI surface.
- Detailed `docs/usage.md` command manual covering installation, command behavior, output interpretation, JSON workflows, historical observations, controlled actions, scheduler usage, auditing, troubleshooting, safety boundaries, scripting, and the command cheat sheet.

### Fixed

- Historical trend findings now use an explicit deterministic metric order so output remains stable across runs.
- Failed-service diagnostic evidence now includes the exact systemd unit name, making the finding directly traceable to the affected service.

### User value

- NEXUS now has a concrete first-run workflow: ask one command what needs attention instead of manually combining multiple Linux inspection commands.
- The operational summary provides a compact read-only control-plane view before deeper diagnosis.
- The scheduler can be installed as a user-owned systemd service without implicit activation.
- The README now documents the user problem, expected answers, and the distinction between diagnosis, planning, and authorized mutation.
- The repository now includes a dedicated practical usage manual so new users can understand commands before attempting system-changing operations.

### Safety

- Historical trend detection is observation-only and never executes remediation.
- Diagnostic collection failures are surfaced as evidence rather than triggering automatic changes.
- Incident creation does not authorize any operation.
- Remediation proposals are planning-only.
- `nexus diagnose` is read-only and never executes its proposed commands.
- Operational summaries are read-only.
- Scheduler installation writes only the user-owned unit; enabling and starting it require an explicit `--enable` request.
- The usage guide explicitly separates read-only inspection, planning, and confirmation-gated mutation workflows.
