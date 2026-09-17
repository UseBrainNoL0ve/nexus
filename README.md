# NEXUS

> **A safety-first Linux system intelligence and automation platform.**
>
> Observe your machine. Understand what is happening. Plan a fix. Authorize changes. Keep an audit trail.

[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Linux-orange.svg)](#linux-compatibility)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

NEXUS is a local Linux operations platform that turns scattered troubleshooting commands into a structured workflow. It collects system evidence, diagnoses problems, groups related findings into incidents, generates explainable remediation plans, and keeps every mutating operation behind an explicit authorization boundary.

It is deliberately more than a system-information dashboard — and deliberately less than a tool that blindly runs commands on your machine.

---

## The idea

Linux administration often looks like this:

```text
check CPU → check RAM → inspect services → check updates → read logs → guess → run commands → hope
```

NEXUS turns that into a repeatable operational pipeline:

```text
┌──────────────┐
│  OBSERVATION │  What is happening?
└──────┬───────┘
       ↓
┌──────────────┐
│  DIAGNOSIS   │  What looks abnormal?
└──────┬───────┘
       ↓
┌──────────────┐
│   INCIDENT   │  What findings belong together?
└──────┬───────┘
       ↓
┌──────────────┐
│   PLANNING   │  What could fix it, and why?
└──────┬───────┘
       ↓
┌──────────────┐
│ AUTHORIZATION│  Did the user explicitly approve it?
└──────┬───────┘
       ↓
┌──────────────┐
│  EXECUTION   │  Perform only the named operation.
└──────┬───────┘
       ↓
┌──────────────┐
│    AUDIT     │  What happened?
└──────────────┘
```

That boundary is the core design principle of NEXUS.

> **Diagnosis is not execution. A proposal is not permission. Automation is not unrestricted shell access.**

---

## Why this project exists

NEXUS started as a practical Linux diagnostic toolkit and grew into an exploration of what a small, safety-conscious **personal Linux operations platform** could look like.

Along the way, the project became a hands-on implementation of several real engineering ideas:

- system telemetry and historical observations
- deterministic diagnostics
- structured findings and incident modeling
- explainable remediation planning
- confirmation-gated system mutations
- audit logging
- scheduled automation
- desktop GUI design
- plugin architecture and capability registries
- cross-distribution capability detection
- privacy-first capture architecture
- testable system command boundaries

The result is intentionally personal, local-first, and inspectable. There is no cloud control plane hiding behind the interface.

---

## What can NEXUS actually do?

| Need | Command / Surface | What you get |
| --- | --- | --- |
| Inspect the machine | `nexus status` | CPU, memory, disk, network snapshot |
| Run health checks | `nexus doctor` | Non-destructive health findings |
| Export health data | `nexus report` | Structured JSON report |
| Diagnose problems | `nexus diagnose` | Findings → incidents → remediation proposals |
| Track system history | `nexus-observe` | Persisted observations and trend detection |
| Inspect services | `nexus services` | Native service-manager state |
| Inspect packages | `nexus packages` | Native package-manager update information |
| Plan package changes | `nexus packages update` | Confirmation-gated update proposals |
| Control a service | `nexus service start/stop/restart` | Named, confirmed, auditable actions |
| Review operations | `nexus history` | Audit history |
| Automate safely | `nexus automate` | Allow-listed dry-run automation |
| Schedule jobs | `nexus-scheduler` | Controlled recurring jobs |
| Use a desktop interface | `nexus-gui` | GUI operations, incidents and telemetry |
| Extend the platform | `nexus-plugins` | Versioned plugin API and capability registry |
| Inspect capture state | `nexus-capture` | Privacy-first local capture lifecycle |

### The command that ties it together

```bash
nexus diagnose
```

The goal is not merely to print a warning. NEXUS tries to answer:

1. **What was observed?**
2. **Why does it matter?**
3. **Which findings are related?**
4. **What could be done about them?**
5. **Would that action change the system?**
6. **If so, where is the explicit authorization boundary?**

---

## A few examples

### See the current system state

```bash
nexus status
```

### Run a non-destructive health check

```bash
nexus doctor
```

### Get the complete diagnostic pipeline

```bash
nexus diagnose
```

### Inspect package updates

```bash
nexus packages
```

### Inspect services

```bash
nexus services
```

### Review what NEXUS has recorded as operational history

```bash
nexus history
```

### Launch the desktop dashboard

```bash
nexus-gui
```

---

## Safety model

NEXUS treats system mutation as a privileged boundary rather than an implementation detail.

A typical operation follows:

```text
Finding
  ↓
Remediation proposal
  ↓
Named action
  ↓
Policy check
  ↓
Explicit confirmation
  ↓
Execution
  ↓
Audit record
```

This means diagnostic code does not casually gain the ability to execute arbitrary shell commands. Actions are represented as known operations with explicit confirmation requirements and audit records.

The same principle applies to automation: **dry-run first, authorize second, execute only the capabilities that the platform explicitly exposes.**

---

## GUI

NEXUS includes a PySide6 desktop interface intended to turn the same operational model into something easier to inspect visually.

The GUI includes:

- system status
- operational overview
- incident investigation
- remediation proposals
- telemetry history
- resource trend visualization
- operational controls

The GUI is not a separate product with its own logic. It sits on top of the same diagnostic and operational model.

---

## Historical intelligence

NEXUS can persist observations and use historical data to identify persistent resource pressure rather than reacting to one noisy sample.

The system can reason about trends such as:

```text
CPU pressure      ────────────────╮
                                  ├── persistent trend
Memory pressure   ────────────────╯

Disk pressure     ────────╮
                          └──────── isolated event
```

This distinction matters: a single high reading and a sustained resource problem are not the same diagnostic signal.

---

## Cross-distribution Linux support

NEXUS is designed around detected Linux capabilities rather than one hard-coded distribution.

| Linux family | Package backend | Common service backend |
| --- | --- | --- |
| Arch / CachyOS / Manjaro / EndeavourOS | pacman | systemd |
| Debian / Ubuntu / Mint / Pardus / Kali / Parrot | apt | systemd |
| Fedora / RHEL / Rocky / Alma / Nobara | dnf | systemd |
| openSUSE / SLES | zypper | systemd |
| Alpine | apk | OpenRC |
| Void | xbps | runit |
| Solus | eopkg | systemd |

This is **capability coverage**, not a claim that every feature behaves identically on every Linux distribution. Unsupported capabilities fail closed instead of pretending they work.

---

## Privacy-first screen activity foundation

NEXUS also explored a Recall-like local screen-activity workflow, but the project deliberately stopped at a complete, privacy-first **capture lifecycle foundation** rather than shipping a recorder that could not be honestly verified across Linux environments.

The implemented foundation includes:

- capture lifecycle and state modeling
- capture policy, disabled by default
- restrictive local session metadata storage
- `nexus-capture` lifecycle inspection
- Wayland/XDG Desktop Portal capability detection
- fail-closed behavior when a safe recording backend is unavailable

The full **Portal → PipeWire frame recorder is intentionally outside the final project scope**. No checkbox claims that NEXUS records the screen when the underlying runtime recorder is not implemented and verified.

This is part of the engineering boundary: sensitive functionality should not be marked complete merely to make a README look complete.

---

## Architecture

At a high level:

```text
                    ┌─────────────────────┐
                    │     Linux host      │
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │ Observation layer  │
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │ Diagnostic engine  │
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │ Incident modeling  │
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │ Remediation planner│
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │ Policy / authorize │
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │ Action engines      │
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │ Audit + history    │
                    └─────────────────────┘
```

The architecture also exposes extension points through the plugin system and controlled automation layer.

---

## Engineering details

NEXUS is intentionally built with boring, inspectable primitives where they make sense:

- Python 3.11+
- `unittest` test suite
- injectable system command runners for deterministic tests
- structured dataclasses/models for findings and incidents
- JSON and JSON Lines for machine-readable output and audit records
- native Linux package/service capability detection
- PySide6 for the desktop UI
- GitHub Actions CI across Python 3.11, 3.12 and 3.13
- system-wide installation using the host Python, without requiring pipx

The project favors small explicit boundaries over a large framework abstraction.

---

## Installation

### Development checkout

```bash
git clone https://github.com/UseBrainNoL0ve/nexus.git
cd nexus
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python -m unittest discover -s tests -v
```

### Normal system installation

For normal use, NEXUS can be installed system-wide and exposed directly on `PATH`:

```bash
cd nexus
sudo ./scripts/install-system.sh
nexus diagnose
```

The installer uses the host Python and does **not** require pipx. The repository-local `.venv` is for development and testing.

See `docs/system-install.md` and `docs/usage.md` for the complete workflow.

---

## Documentation

- [`docs/usage.md`](docs/usage.md) — practical command manual and troubleshooting
- [`docs/architecture.md`](docs/architecture.md) — execution boundaries and architecture
- [`docs/diagnostics.md`](docs/diagnostics.md) — diagnostics and incident pipeline
- [`docs/platform.md`](docs/platform.md) — plugin and automation platform contract
- [`docs/screen-activity.md`](docs/screen-activity.md) — privacy model and capture roadmap
- [`docs/system-install.md`](docs/system-install.md) — system-wide installation
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — development and contribution workflow
- [`CHANGELOG.md`](CHANGELOG.md) — project history and milestones

---

## Project journey

NEXUS was developed as a sequence of increasingly ambitious engineering milestones:

```text
Linux telemetry
      ↓
Health checks
      ↓
Diagnostics
      ↓
Historical observations
      ↓
Incident modeling
      ↓
Explainable remediation
      ↓
Authorization + audit
      ↓
Automation + scheduler
      ↓
Desktop GUI
      ↓
Plugin system
      ↓
Cross-distribution support
      ↓
Privacy-first capture foundation
```

Each step was kept testable and documented rather than treating the project as one giant feature.

---

## Project status

**NEXUS is being wrapped up as a completed portfolio and learning milestone.**

The core platform is intentionally preserved in a coherent state rather than expanded indefinitely. Future maintenance or focused experiments can continue from the existing architecture, but larger deferred experiments — especially full screen recording — are explicitly outside this release scope.

### Completed milestones

- [x] Linux system intelligence CLI
- [x] non-destructive health checks
- [x] historical observation and anomaly detection
- [x] diagnostic engine and structured findings
- [x] incident modeling
- [x] explainable remediation planning
- [x] confirmation-gated service and package actions
- [x] audit history
- [x] policy-gated automation
- [x] scheduler
- [x] desktop GUI
- [x] GUI incident/remediation center
- [x] telemetry visualization
- [x] versioned plugin system
- [x] distribution-agnostic capability detection
- [x] native system-wide installer
- [x] privacy-first capture lifecycle foundation
- [x] Wayland/XDG Portal capability detection

**Scope boundary:** the Portal → PipeWire frame recorder remains a future experiment rather than an incomplete milestone. Everything listed above is part of the intentionally completed NEXUS scope.

---

## Development

Run the test suite with:

```bash
python -m unittest discover -s tests -v
```

When extending NEXUS, system mutations should remain covered by focused tests, an explicit planning or dry-run path, an authorization boundary, and auditability.

---

## License

MIT. See [`LICENSE`](LICENSE).

---

<p align="center">
  <sub>Built as a Linux systems engineering and software architecture learning project.</sub>
</p>
