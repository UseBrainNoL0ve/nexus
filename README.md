# NEXUS

> **Safety-first Linux observability, diagnostics, and controlled operations platform.**

NEXUS is a local-first Linux engineering platform for turning low-level system state into **actionable, auditable operational intelligence**.

It brings system telemetry, health diagnostics, service management, package inspection, scheduled maintenance, historical observations, and confirmation-gated remediation into one consistent workflow.

**Design principle:** NEXUS should help answer *what is happening, why it matters, what can be done, and what will change* before it changes the host.

---

## Project status

| Area | Status |
|---|---|
| Platform | Linux · CachyOS-first |
| Python | 3.11+ |
| Interface | CLI + PySide6 desktop GUI |
| Architecture | Local-first, modular, Linux-native |
| Mutating operations | Explicit confirmation required |
| Auditability | JSONL audit and observation history |
| CI | GitHub Actions · Python 3.11–3.13 |
| Stability | Alpha / active development |

> **Note:** The package metadata currently reports `0.2.0a1`. The changelog tracks subsequent alpha milestones independently while the project architecture is being stabilized.

---

## Why NEXUS?

Linux already provides excellent primitives: `systemd`, `pacman`, `/proc`, `/sys`, filesystem statistics, and standard command-line tooling. The problem is that operational work is often fragmented across unrelated commands and scripts.

NEXUS provides a structured control layer around those primitives.

Instead of:

```text
systemctl → pacman → journalctl → scripts → notes → manual decisions
```

NEXUS aims for:

```text
OBSERVE → DIAGNOSE → ANALYZE → PLAN → CONFIRM → EXECUTE → AUDIT
```

The project is intentionally **CachyOS-first** while keeping the core interfaces modular enough to support additional Linux distributions and backends later.

---

## Core capabilities

### System observability

```bash
nexus status
nexus summary
nexus-observe
nexus-observe --json
```

Collects CPU, memory, disk, network, host, kernel, service, package, scheduler, and historical observation data without requiring a remote monitoring service.

### Diagnostics

```bash
nexus doctor
nexus report --output reports/health.json
```

Runs non-destructive health checks and produces structured diagnostic reports suitable for both humans and automation.

### Controlled operations

```bash
nexus services
nexus packages
nexus service restart <service>
nexus packages update
```

Operational changes are represented as explicit proposals and protected by confirmation boundaries. NEXUS does not provide an arbitrary shell-execution escape hatch.

### Automation and scheduling

```bash
nexus automate
nexus-scheduler add health-check --action doctor --every 300
nexus-scheduler add package-check --action packages --every 1800
nexus-scheduler run
nexus-scheduler history
```

The scheduler supports an allow-list of built-in operations and records execution history. It does not silently install packages or modify services.

### Desktop operations console

```bash
nexus-gui
```

The PySide6 application provides a consistent interface for telemetry, diagnostics, services, packages, scheduler state, history, and controlled operations.

The GUI uses the same core safety boundaries as the CLI; visual controls do not bypass confirmation or authorization logic.

---

## Operational model

```text
┌──────────────┐
│   OBSERVE    │  /proc · /sys · systemd · pacman · filesystem
└──────┬───────┘
       ↓
┌──────────────┐
│  DIAGNOSE    │  health checks · validation · system state
└──────┬───────┘
       ↓
┌──────────────┐
│   ANALYZE    │  history · trends · change detection
└──────┬───────┘
       ↓
┌──────────────┐
│    PLAN      │  proposal · rationale · affected resources
└──────┬───────┘
       ↓
┌──────────────┐
│   CONFIRM    │  explicit user authorization
└──────┬───────┘
       ↓
┌──────────────┐
│   EXECUTE    │  controlled argument-based operations
└──────┬───────┘
       ↓
┌──────────────┐
│    AUDIT     │  decision · result · timestamp · metadata
└──────────────┘
```

This separation is a fundamental architectural constraint. **Observation code must not acquire mutation privileges simply because its data is displayed in the GUI.**

---

## Safety model

NEXUS treats host mutation as a privileged workflow rather than a convenience feature.

1. **Observation by default** — status, diagnostics, summaries, service inspection, package inspection, and telemetry collection are non-destructive.
2. **Planning before execution** — proposed changes are represented explicitly before mutation.
3. **Explicit confirmation** — service and package changes require a deliberate confirmation path.
4. **No arbitrary shell execution** — controlled operations use argument sequences rather than shell strings.
5. **Allow-listed scheduling** — scheduled tasks can invoke only supported NEXUS operations.
6. **Persistent audit metadata** — controlled actions and scheduler executions are recorded under `.nexus/`.
7. **GUI parity** — desktop actions use the same core engines and safety constraints as the CLI.
8. **Least surprise** — installation of the scheduler unit does not automatically enable or start it unless explicitly requested.

NEXUS is not intended to replace administrator judgment. It is intended to make that judgment more informed and the resulting actions more inspectable.

---

## Quick start

### 1. Clone

```bash
git clone https://github.com/UseBrainNoL0ve/nexus.git
cd nexus
```

### 2. Create an isolated environment

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

Using a virtual environment is recommended on modern Arch/CachyOS installations because system Python environments may enforce PEP 668 package-management restrictions.

### 3. Inspect the host

```bash
nexus status
nexus doctor
nexus summary
nexus-observe
```

### 4. Run the test suite

```bash
python -m unittest discover -s tests -v
```

### 5. Launch the desktop console

```bash
nexus-gui
```

---

## Scheduler service

NEXUS can generate a user-level systemd service for continuous scheduler execution.

Installation is intentionally separate from activation:

```bash
nexus-scheduler install
systemctl --user enable --now nexus-scheduler.service
```

Or, when activation is explicitly intended:

```bash
nexus-scheduler install --enable
```

The generated service runs within the selected Python environment and invokes only the NEXUS scheduler entry point.

---

## Repository layout

```text
nexus/
├── src/nexus/
│   ├── sensors/          # Linux telemetry collection
│   ├── doctor/            # health and diagnostic checks
│   ├── systemd/           # service inspection and controlled actions
│   ├── pacman/            # package inspection and update planning
│   ├── scheduler/         # recurring jobs and execution history
│   ├── observability/     # persistent observations and change analysis
│   ├── gui/               # PySide6 desktop application
│   ├── audit.py            # action audit records
│   ├── summary.py          # unified operational summary
│   └── cli.py              # command-line interface
├── tests/                 # deterministic unit and integration-style tests
├── docs/                  # architecture and engineering documentation
└── .github/workflows/     # continuous integration
```

The project deliberately keeps **collection, analysis, planning, execution, and presentation** separated so individual components can evolve without silently expanding their privileges.

---

## Engineering principles

- **Local-first:** core functionality should not require a cloud service.
- **Observable:** important operations should produce structured state or audit information.
- **Deterministic:** system integrations should be injectable and testable.
- **Explicit:** mutation should be visible to the user before it happens.
- **Composable:** CLI, GUI, scheduler, and future APIs should reuse the same domain logic.
- **Linux-native:** use stable Linux interfaces instead of unnecessary abstractions.
- **Professional by construction:** documentation, tests, commit history, and architecture should reflect production engineering practices.

---

## Roadmap

### Observability

- [x] Point-in-time system telemetry
- [x] Persistent observation history
- [x] Observation-to-observation change detection
- [ ] Long-term trend analysis
- [ ] Baseline generation
- [ ] Deterministic anomaly detection

### Operations

- [x] systemd inspection
- [x] confirmation-gated service operations
- [x] pacman update inspection
- [x] confirmation-gated package operations
- [x] recurring scheduler
- [ ] Diagnostic incident model
- [ ] Remediation recommendation engine
- [ ] Rollback-aware operation planning

### Platform

- [x] CLI
- [x] PySide6 desktop console
- [x] JSON output
- [x] Audit history
- [ ] Stable internal API
- [ ] Plugin interface
- [ ] Additional Linux distribution backends
- [ ] 1.0 release hardening

The roadmap is deliberately weighted toward **depth, reliability, and operational value** rather than accumulating superficial UI features.

---

## Documentation

- [`docs/architecture.md`](docs/architecture.md) — system architecture and design boundaries
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — development workflow and engineering expectations
- [`CHANGELOG.md`](CHANGELOG.md) — release history and notable changes
- [`LICENSE`](LICENSE) — MIT license

---

## License

NEXUS is released under the MIT License. See [`LICENSE`](LICENSE).
