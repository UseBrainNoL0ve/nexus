# NEXUS Usage Guide

This guide is the practical manual for running NEXUS on a Linux host, with CachyOS as the primary target. It explains what each command does, what it does **not** do, how to interpret the output, and where the authorization boundary begins.

## 1. What NEXUS is for

NEXUS is designed to turn common Linux maintenance and troubleshooting into a repeatable workflow:

```text
Observe → Diagnose → Understand → Plan → Authorize → Act → Audit
```

The important design rule is that inspection and diagnosis do not silently mutate the machine.

Use NEXUS when you want to answer questions such as:

- What is my system doing right now?
- Is something obviously unhealthy?
- Which signals deserve attention?
- What evidence caused NEXUS to flag them?
- What action is being proposed?
- What risk and confirmation boundary applies?
- What actions were actually executed later?

---

## 2. Installation

NEXUS currently requires Python 3.11 or newer.

### Recommended CachyOS setup

Do not install NEXUS into the system Python environment. CachyOS follows modern Python packaging rules, so use a virtual environment:

```bash
git clone https://github.com/UseBrainNoL0ve/nexus.git
cd nexus
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

Verify the installation:

```bash
nexus --help
```

You should see the main command groups including `status`, `doctor`, `diagnose`, `automate`, `services`, `packages`, `service`, `history`, and `report`.

### Why a virtual environment?

The project should not modify the distribution-managed Python installation. Avoid using `--break-system-packages` for NEXUS installation.

---

## 3. The recommended first command: `nexus diagnose`

If you do not know where to start, use:

```bash
nexus diagnose
```

This is the main user-facing diagnostic workflow. It collects available evidence, derives deterministic findings, groups related findings into incidents, and produces remediation proposals.

A typical flow is:

```text
Current Linux state
       ↓
Diagnostic evidence
       ↓
Findings
       ↓
Incidents
       ↓
Remediation proposals
```

The command is read-only. It does not execute the remediation proposals it prints.

### Machine-readable diagnosis

For scripts or other tools:

```bash
nexus diagnose --json
```

The JSON output contains fields such as:

- `finding_count`
- `findings`
- `incident_count`
- `incidents`
- `remediation_steps`
- `collection_errors`
- `read_only`

The JSON form is intended to be stable enough for local integrations while remaining human-readable.

---

## 4. Understanding `nexus status`

Run:

```bash
nexus status
```

This is the fastest live snapshot. It reports:

- operating-system/platform information
- kernel
- hostname
- CPU load percentage
- logical CPU count
- memory usage percentage
- disk usage percentage and path
- number of detected network interfaces

It is useful when you want current state without running the diagnostic pipeline.

For JSON:

```bash
nexus status --json
```

The JSON output explicitly marks the snapshot as `read_only`.

---

## 5. Understanding `nexus doctor`

Run:

```bash
nexus doctor
```

`doctor` performs non-destructive health checks and reports individual check statuses.

Use it when the question is:

> Is anything obviously wrong according to NEXUS's health checks?

Use `diagnose` instead when you want more context about evidence, incidents, and suggested next steps.

JSON output:

```bash
nexus doctor --json
```

The JSON result includes an overall `status`, individual `checks`, and a `read_only` marker.

### Exit status

A warning condition causes the doctor command to return a non-zero status. This is useful in shell scripts and CI-style checks where the exit code can be consumed separately from the text output.

---

## 6. Historical observations with `nexus-observe`

A single snapshot can miss problems that only become visible over time. NEXUS therefore has an observation store.

Run:

```bash
nexus-observe
```

This records a new observation and analyzes the available historical observations.

To inspect a larger history window:

```bash
nexus-observe --limit 20
```

For machine-readable output:

```bash
nexus-observe --limit 20 --json
```

Observations are stored locally under:

```text
.nexus/observations.jsonl
```

### Historical trend detection

The current deterministic trend detector looks for persistent resource pressure rather than reacting to one isolated spike.

Current rules include:

| Signal | Condition | Severity |
| --- | --- | --- |
| Memory | at least 90% on the latest three observations | warning |
| Disk | at least 85% on the latest three observations | warning |
| CPU | at least 80% on the latest three observations | info |

These thresholds are deliberately explicit. They are not an AI prediction system.

A single high reading is not treated as a persistent anomaly by these rules.

---

## 7. Systemd service inspection

Inspect services without changing them:

```bash
nexus services
```

For JSON:

```bash
nexus services --json
```

The command summarizes detected services and highlights failed units.

It is useful before restarting anything because it lets you inspect the current state first.

### Controlled service actions

NEXUS supports three service actions:

```bash
nexus service start <unit>
nexus service stop <unit>
nexus service restart <unit>
```

For example, a service unit can be inspected first and then a restart can be planned.

#### Always inspect the plan first

Use:

```bash
nexus service restart <unit> --dry-run
```

This prints:

- service unit
- requested action
- risk classification
- proposed command
- rationale

No service change is made by the dry-run.

#### Explicit execution

Execution requires the explicit confirmation flag:

```bash
nexus service restart <unit> --confirm
```

The action is then recorded in the NEXUS audit log.

Do not treat `--confirm` as a harmless display option: it crosses the mutation boundary and can change the running system.

---

## 8. Package inspection with pacman

Inspect available updates without changing packages:

```bash
nexus packages
```

NEXUS uses the pacman update-inspection path and reports available updates. This command does not install, remove, or upgrade packages.

JSON output:

```bash
nexus packages --json
```

### Package update planning

To see a proposed update plan:

```bash
nexus packages update
```

The output shows package names, current and available versions, risk metadata, confirmation requirements, and the proposed command.

Without `--confirm`, the command does not execute package changes.

### Explicit package update execution

Only after reviewing the plan should you use:

```bash
nexus packages update --confirm
```

This crosses the package mutation boundary. Package updates can have system-wide consequences, so the confirmation step is intentionally explicit.

---

## 9. Automation rules

Run:

```bash
nexus automate
```

The command evaluates NEXUS's known automation rules in dry-run mode.

It can report:

- rules that are currently OK
- rules that are triggered
- action proposals
- risk metadata
- rationale

The automation layer does not provide arbitrary shell execution. A proposal is not the same thing as an executed command.

---

## 10. Action history and auditability

NEXUS keeps an audit trail for controlled service actions.

View recent entries with:

```bash
nexus history
```

Increase the number of displayed records:

```bash
nexus history --limit 50
```

The service-action audit log is stored at:

```text
.nexus/audit.jsonl
```

Scheduled execution history is stored separately at:

```text
.nexus/scheduler-audit.jsonl
```

Audit records are intended to answer:

- when an action was requested
- what action was involved
- which service was targeted
- what risk metadata applied
- whether execution succeeded
- what return code was observed

NEXUS does not use the audit log as a replacement for normal system logs.

---

## 11. JSON reports

Create a health report file with:

```bash
nexus report --output reports/health.json
```

This is useful when you want to keep a point-in-time machine-readable snapshot for later inspection.

If the destination directory does not exist, create it first:

```bash
mkdir -p reports
nexus report --output reports/health.json
```

---

## 12. Scheduler

The scheduler provides recurring, allow-listed NEXUS jobs.

Basic commands are exposed through:

```bash
nexus-scheduler --help
```

The scheduler is deliberately constrained: it does not accept arbitrary shell commands as scheduled jobs.

Scheduler state is persisted locally, and executions are written to the scheduler audit log.

Use the scheduler when you want recurring NEXUS observations or checks rather than building your own cron wrapper around shell commands.

---

## 13. Desktop interface

Launch the PySide6 desktop operations dashboard with:

```bash
nexus-gui
```

The GUI is intended as a visual front end for NEXUS operations. The CLI remains the clearest interface for automation, scripting, and reproducible troubleshooting.

If the GUI has an issue, reproduce the underlying operation from the CLI first. This keeps debugging separated between the Linux operation itself and the presentation layer.

---

## 14. A practical troubleshooting workflow

When the machine feels slow or something appears wrong, use this sequence:

### Step 1 — Snapshot

```bash
nexus status
```

Ask: is CPU, memory, disk, or network state obviously unusual?

### Step 2 — Health checks

```bash
nexus doctor
```

Ask: does NEXUS identify a direct health warning?

### Step 3 — Diagnosis

```bash
nexus diagnose
```

Ask: what evidence supports the finding, which incident contains it, and what is the proposed next step?

### Step 4 — Inspect historical context

```bash
nexus-observe --limit 20
```

Ask: is this a one-time spike or a persistent condition?

### Step 5 — Inspect services if relevant

```bash
nexus services
```

Ask: are any units failed?

### Step 6 — Inspect package state if relevant

```bash
nexus packages
```

Ask: are updates available?

### Step 7 — Plan before acting

For a service:

```bash
nexus service restart <unit> --dry-run
```

For packages:

```bash
nexus packages update
```

### Step 8 — Authorize only after review

Use the corresponding `--confirm` flag only when you intentionally want the proposed mutation to happen.

### Step 9 — Verify the resulting state

Run the relevant read-only commands again:

```bash
nexus status
nexus doctor
nexus diagnose
```

The verification step is important: successful command execution is not automatically proof that the system reached the desired state.

---

## 15. Safety model

NEXUS separates operations into three broad classes.

### Read-only observation

Examples:

```bash
nexus status
nexus doctor
nexus diagnose
nexus services
nexus packages
nexus-observe
```

These commands inspect system state and do not intentionally modify services or packages.

### Planning

Examples:

```bash
nexus automate
nexus packages update
nexus service restart <unit> --dry-run
```

Planning produces proposals. A proposal is not execution.

### Mutation

Examples:

```bash
nexus service restart <unit> --confirm
nexus packages update --confirm
```

Mutation requires an explicit authorization flag and is subject to the corresponding action engine and audit path.

The diagnostic and remediation layers themselves do not execute their own proposed actions.

---

## 16. Working with JSON in shell scripts

Most inspection commands expose `--json`. This makes it possible to separate NEXUS's analysis from presentation.

Example:

```bash
nexus diagnose --json > diagnosis.json
```

Then inspect it with standard local tools:

```bash
python -m json.tool diagnosis.json
```

For a quick field-oriented workflow, `jq` can also be used if installed:

```bash
nexus diagnose --json | jq '.findings'
```

Do not assume that a JSON field represents causal certainty. Findings are evidence-based outputs from deterministic rules; they should be interpreted together with the evidence and collection warnings.

---

## 17. Collection warnings and partial evidence

Linux telemetry can fail for legitimate reasons: a subsystem may be unavailable, a command may return an error, or the host may differ from the environment NEXUS expects.

NEXUS is designed to keep collection failures visible rather than silently treating missing information as a healthy state.

When `nexus diagnose` reports `collection_errors`, investigate those warnings before treating the diagnosis as complete.

A diagnosis based on incomplete evidence should be treated as incomplete evidence—not as proof that the machine is healthy.

---

## 18. Exit codes and scripting

NEXUS commands generally use exit status to distinguish a normal result from a detected warning or operational error.

For example, `nexus doctor` and `nexus diagnose` return a non-zero status when their diagnostic findings contain warning-level conditions. This allows shell automation to detect attention-worthy states without parsing human-readable output.

For scripts, prefer `--json` plus the process exit code instead of scraping terminal formatting.

---

## 19. Development and tests

From the repository root:

```bash
source .venv/bin/activate
python -m unittest discover -s tests -v
```

NEXUS uses injectable system command runners in tests where external Linux commands would otherwise make tests non-deterministic.

When contributing a new mutation or operational feature, preserve the same sequence:

```text
evidence → plan → explicit authorization → execution → audit
```

Add focused tests and update the relevant documentation in the same change.

---

## 20. Command cheat sheet

| Command | Purpose | Mutation |
| --- | --- | --- |
| `nexus status` | current system snapshot | No |
| `nexus doctor` | basic health checks | No |
| `nexus diagnose` | findings, incidents, remediation proposals | No |
| `nexus automate` | automation-rule dry run | No |
| `nexus services` | systemd inspection | No |
| `nexus packages` | pacman update inspection | No |
| `nexus packages update` | package update planning | No |
| `nexus packages update --confirm` | execute reviewed package update plan | **Yes** |
| `nexus service restart X --dry-run` | service action planning | No |
| `nexus service restart X --confirm` | execute reviewed service action | **Yes** |
| `nexus history` | service action audit history | No |
| `nexus report --output FILE` | write JSON health report | No |
| `nexus-observe` | persist/analyze observation | No |
| `nexus-scheduler` | manage recurring allow-listed jobs | Depends on scheduled action |
| `nexus-gui` | launch desktop interface | Depends on selected UI action |

For the complete project architecture, see `docs/architecture.md`. For the diagnostic and incident model, see `docs/diagnostics.md`.
