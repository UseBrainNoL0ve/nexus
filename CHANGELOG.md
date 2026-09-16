# Changelog

All notable NEXUS changes are documented here.

The changelog records **project milestones**, while package version metadata may remain on an earlier alpha version during active architectural development. See `pyproject.toml` for the version currently published by the package metadata.

## [0.6.0-alpha] — 2026-09-16

### Operational platform

- Added a unified read-only operational summary combining system health, systemd state, package updates, and scheduler state.
- Added `nexus summary` for a human-readable operational overview.
- Added `nexus summary --json` for machine-readable integrations and automation.
- Added operational-summary presentation to the desktop Command Center.

### Scheduler

- Added generation of a user-level systemd scheduler service using the active Python environment.
- Added `nexus-scheduler install` without implicit activation.
- Added `nexus-scheduler install --enable` for explicit user-service activation.

### Engineering

- Added dedicated tests for summary aggregation and scheduler service generation.
- Expanded architecture documentation around observation, diagnosis, planning, confirmation, execution, and audit boundaries.

### Safety

- Operational summaries remain strictly read-only.
- Scheduler installation writes only the user-owned service unit unless explicit activation is requested.
- Scheduled operations remain restricted to the built-in allow-list.
- No arbitrary shell execution was introduced.

---

## [0.5.0-alpha] — 2026-09-16

### Desktop operations console

- Added functional navigation across Dashboard, Services, Packages, Doctor, Scheduler, and History.
- Added read-only systemd service detail views.
- Added read-only pacman update detail views.
- Added a dedicated Doctor health-check view.
- Added scheduler configuration and execution-history views.
- Added reusable read-only GUI detail-page components.
- Added active navigation state and a consistent NEXUS dark visual language.
- Added live dashboard refresh with background telemetry collection.
- Added service management with explicit confirmation for start, stop, and restart.
- Added package update management with explicit per-package confirmation.
- Added selectable service and package tables with state information.

### Safety

- GUI service and package mutations use the existing confirmation-gated engines.
- The GUI does not expose arbitrary shell execution.
- Background telemetry remains observation-only.
- Detail-page failures are contained within the affected page.
- Visual changes do not bypass core safety constraints.

---

## [0.4.0-alpha] — 2026-09-16

### Scheduler

- Added persistent JSON-backed recurring scheduler jobs.
- Added `nexus-scheduler add`, `list`, and `remove`.
- Added one-shot due-job execution through `nexus-scheduler run`.
- Added foreground daemon mode through `nexus-scheduler run --daemon`.
- Added allow-listed health-check and package-inspection actions.
- Added best-effort Linux desktop notifications through `notify-send` when available.
- Added injectable scheduler action and notification runners for deterministic tests.

### Safety

- Scheduler jobs cannot invoke arbitrary shell commands.
- Scheduled package work is read-only inspection.
- The scheduler does not automatically install packages or modify services.
- Schedules are stored as user-owned JSON under `.nexus/schedules.json`.

---

## [0.2.0-alpha] — 2026-09-16

### Controlled operations

- Added observation-only automation rules.
- Added disk-pressure and memory-pressure rules.
- Added `nexus automate` dry-run evaluation.
- Added systemd service inspection.
- Added safe service action planning for start, stop, and restart.
- Added explicit confirmation before service action execution.
- Added injectable command runners for deterministic execution tests.
- Added JSONL audit logging for service-action decisions and results.
- Added `nexus history` for recent service-action audit records.
- Added read-only pacman update inspection through `nexus packages`.
- Added package update planning and confirmation-gated execution.
- Added injectable package command runners and corresponding unit coverage.

### Safety

- Automation rules produce proposals rather than direct mutations.
- Service changes require explicit confirmation.
- Package inspection uses `pacman -Qu` without modifying packages.
- Package execution requires an explicit confirmation path.
- Controlled commands use argument sequences rather than shell strings.
- Audit records contain operational metadata rather than command output or environment secrets.

---

## [0.1.0-alpha] — 2026-09-16

### Foundation

- Added read-only Linux system status collection.
- Added CPU, memory, disk, and network sensors.
- Added non-destructive `status`, `doctor`, and `report` commands.
- Added JSON health-report export.
- Added unit tests and GitHub Actions CI.

---

## Upcoming

The next milestones focus on operational depth rather than UI-only expansion:

- Historical telemetry and trend analysis.
- Deterministic anomaly detection and baseline generation.
- Structured diagnostic incidents.
- Explainable remediation recommendations.
- Stable internal interfaces for future integrations.
- Additional Linux distribution backends after the core abstractions are validated.
