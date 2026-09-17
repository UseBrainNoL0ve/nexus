# NEXUS Usage Guide

This guide is the practical manual for running NEXUS on Linux. NEXUS is distribution-agnostic at the platform layer and uses native package/service managers when a supported backend is detected.

The core workflow is:

```text
Observe → Diagnose → Understand → Plan → Authorize → Act → Audit
```

Inspection and diagnosis do not silently mutate the machine.

## 1. Installation

NEXUS requires Python 3.11 or newer.

### System-wide command installation

For normal day-to-day use, NEXUS can be installed as a regular Linux command without a repository-local virtual environment and without pipx:

```bash
cd ~/nexus
sudo ./scripts/install-system.sh
```

The installer uses the host `python3`, installs NEXUS under `/usr/local/lib/pythonX.Y/site-packages`, and creates command launchers under `/usr/local/bin`.

Verify:

```bash
command -v nexus
nexus --help
nexus status
```

Companion commands include `nexus-gui`, `nexus-scheduler`, `nexus-observe`, `nexus-diagnose`, `nexus-summary`, and `nexus-plugins`.

The installer intentionally does not create `.venv` or a pipx environment. `.venv` remains useful for repository development and test isolation. Do not use `--break-system-packages` for normal NEXUS installation.

A custom prefix is supported:

```bash
sudo NEXUS_PREFIX=/opt/nexus ./scripts/install-system.sh
```

The installer is a portable `/usr/local` installation mechanism, not a replacement for native distribution packaging. Native packages can be added later for distributions that provide them.

## 2. Platform detection

NEXUS reads `/etc/os-release` and detects the host distribution. Package backends currently cover common managers including pacman, apt, dnf/yum, zypper, apk, xbps, and eopkg when their executables are available.

Service-manager detection covers systemd, OpenRC, runit, s6-rc, and dinit when supported executables are present.

If no supported backend is available, NEXUS fails closed for that subsystem instead of guessing a command.

## 3. `nexus diagnose`

Start here when you want an explanation rather than only a snapshot:

```bash
nexus diagnose
nexus diagnose --json
```

The pipeline collects evidence, derives deterministic findings, groups related findings into incidents, and produces remediation proposals. It is read-only and does not execute its own proposals.

JSON output includes fields such as `finding_count`, `findings`, `incident_count`, `incidents`, `remediation_steps`, `collection_errors`, and `read_only`.

## 4. `nexus status`

```bash
nexus status
nexus status --json
```

Reports operating-system information, kernel, hostname, CPU load, logical CPU count, memory usage, disk usage/path, and detected network interfaces. The JSON form marks the snapshot as read-only.

## 5. `nexus doctor`

```bash
nexus doctor
nexus doctor --json
```

Performs non-destructive health checks. Warning conditions produce a non-zero exit status, making the command suitable for shell automation.

## 6. Historical observations

A single snapshot can miss persistent pressure. Use:

```bash
nexus-observe
nexus-observe --limit 20
nexus-observe --limit 20 --json
```

Observations are stored locally in `.nexus/observations.jsonl`.

Current deterministic trend rules include persistent pressure across the latest three observations: memory at or above 90% produces a warning, disk at or above 85% produces a warning, and CPU at or above 80% produces an informational finding. A single spike is not classified as a persistent anomaly.

## 7. Service inspection and controlled actions

Inspect services without changing them:

```bash
nexus services
nexus services --json
```

NEXUS maps service actions to the detected native service manager.

Always inspect a proposed action first:

```bash
nexus service restart <unit> --dry-run
```

Execution requires explicit authorization:

```bash
nexus service restart <unit> --confirm
```

The mutation is recorded in the NEXUS audit path. `--confirm` is an authorization boundary, not a display option.

## 8. Package inspection and updates

Inspect available package updates without changing packages:

```bash
nexus packages
nexus packages --json
```

NEXUS selects a supported native package backend rather than assuming a particular distribution.

Plan an update:

```bash
nexus packages update
```

Execute only after reviewing the plan:

```bash
nexus packages update --confirm
```

Package mutation remains confirmation-gated.

## 9. Automation

```bash
nexus automate
```

Automation evaluates known allow-listed rules in dry-run mode. It does not provide arbitrary shell execution, and a proposal is not the same as an executed command.

## 10. Audit history

```bash
nexus history
nexus history --limit 50
```

Service actions are recorded in `.nexus/audit.jsonl`; scheduled executions use `.nexus/scheduler-audit.jsonl`.

Audit records are intended to capture requested action, target, risk metadata, execution result, and return code. They complement rather than replace normal Linux logs.

## 11. JSON reports

Create a machine-readable point-in-time report:

```bash
mkdir -p reports
nexus report --output reports/health.json
```

## 12. Scheduler

```bash
nexus-scheduler --help
```

The scheduler provides recurring allow-listed NEXUS jobs. It does not accept arbitrary shell commands as scheduled jobs. Scheduler state and execution history are persisted locally.

## 13. Desktop interface

Launch the PySide6 operations dashboard with:

```bash
nexus-gui
```

The CLI remains the clearest interface for scripting and reproducible troubleshooting. Reproduce GUI issues with the corresponding CLI operation first when possible.

## 14. Practical troubleshooting workflow

Use this sequence when the machine behaves unexpectedly:

1. `nexus status` — establish current state.
2. `nexus doctor` — check direct health warnings.
3. `nexus diagnose` — inspect evidence, findings, incidents, and proposals.
4. `nexus-observe --limit 20` — determine whether pressure persists.
5. `nexus services` — inspect failed services if relevant.
6. `nexus packages` — inspect package state if relevant.
7. Use `--dry-run` or the planning command before any mutation.
8. Use `--confirm` only after reviewing the proposed mutation.
9. Re-run read-only checks to verify the resulting state.

Successful command execution is not automatically proof that the desired system state was reached.

## 15. Safety model

### Observation

Examples:

```bash
nexus status
nexus doctor
nexus diagnose
nexus services
nexus packages
nexus-observe
```

These inspect system state without intentionally modifying services or packages.

### Planning

Examples:

```bash
nexus automate
nexus packages update
nexus service restart <unit> --dry-run
```

Planning produces proposals.

### Mutation

Examples:

```bash
nexus service restart <unit> --confirm
nexus packages update --confirm
```

Mutation requires explicit authorization and passes through the corresponding action and audit paths.

## 16. JSON and shell scripting

Prefer structured output over terminal scraping:

```bash
nexus diagnose --json > diagnosis.json
python -m json.tool diagnosis.json
```

If installed, `jq` can select fields:

```bash
nexus diagnose --json | jq '.findings'
```

Findings are deterministic evidence-based outputs, not guarantees of causal certainty.

## 17. Collection warnings

Linux telemetry can be unavailable because a subsystem is missing, a command fails, or the host differs from expected environments. NEXUS keeps collection errors visible instead of silently interpreting missing information as healthy state.

When `nexus diagnose` reports `collection_errors`, investigate them before treating a diagnosis as complete.

## 18. Exit codes

Commands use process exit status to distinguish normal results from warning or operational conditions. For scripts, prefer `--json` together with the exit code rather than parsing human-readable terminal formatting.

## 19. Development and tests

For repository development:

```bash
source .venv/bin/activate
python -m unittest discover -s tests -v
```

Development environments may use `.venv`; the system-wide installer is intended for normal installed use.

NEXUS uses injectable command runners so tests do not need to execute real package-manager or service-manager mutations. New operational features should preserve:

```text
evidence → plan → explicit authorization → execution → audit
```

Update tests and documentation in the same logical change.

## 20. Screen activity recorder roadmap

NEXUS has a privacy-first design for an optional local screen-activity recorder intended for incident investigation. It is not a covert monitoring system.

The design requires:

- explicit local opt-in
- recording off by default
- a visible recording state/indicator
- user-controlled start, pause, resume, and stop
- local-only storage
- retention and storage quotas
- restrictive file permissions and optional encryption at rest
- no remote activation
- no hidden capture
- no permission bypass
- no network upload
- fail-closed behavior when no safe capture backend exists

On Wayland, the preferred integration is XDG Desktop Portal ScreenCast with PipeWire. Planned commands are:

```bash
nexus capture status
nexus capture start
nexus capture pause
nexus capture resume
nexus capture stop
nexus capture list
nexus capture delete <id>
```

The recorder should correlate capture periods with NEXUS audit and operational timestamps so an incident can be investigated chronologically. Actual screen capture remains a separate implementation phase after the policy, state, storage, capability, and test foundations are in place.

## 21. Command cheat sheet

| Command | Purpose | Mutation |
| --- | --- | --- |
| `nexus status` | current system snapshot | No |
| `nexus doctor` | basic health checks | No |
| `nexus diagnose` | findings, incidents, remediation proposals | No |
| `nexus automate` | automation-rule dry run | No |
| `nexus services` | service inspection | No |
| `nexus packages` | package update inspection | No |
| `nexus packages update` | package update planning | No |
| `nexus packages update --confirm` | execute reviewed package update plan | **Yes** |
| `nexus service restart X --dry-run` | service action planning | No |
| `nexus service restart X --confirm` | execute reviewed service action | **Yes** |
| `nexus history` | audit history | No |
| `nexus report --output FILE` | write JSON health report | No |
| `nexus-observe` | persist/analyze observation | No |
| `nexus-scheduler` | recurring allow-listed jobs | Depends on scheduled action |
| `nexus-gui` | desktop interface | Depends on selected UI action |

For architecture details, see `docs/architecture.md`. For diagnostic and incident details, see `docs/diagnostics.md`. For the system installer, see `docs/system-install.md`. For the screen-activity design, see `docs/screen-activity.md`.
