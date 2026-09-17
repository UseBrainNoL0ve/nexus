# NEXUS

> A safety-first Linux system intelligence and automation platform.

NEXUS is a local Linux operations platform built around a deliberate pipeline: observe the host, diagnose evidence, model incidents, prepare explainable remediation plans, and only then cross an explicit authorization boundary for mutating actions.

The project is Linux-native and distribution-agnostic at the platform layer. It detects native package and service backends instead of assuming one distribution, while keeping unsupported capabilities fail-closed.

## Why NEXUS?

Most Linux troubleshooting starts with a pile of commands: check memory, inspect services, look for package updates, read logs, and decide what to do next. NEXUS turns those separate checks into one repeatable workflow.

**The practical user story is:**

```text
"Is my machine actually healthy?"
          ↓
      nexus diagnose
          ↓
"What is wrong, why does it matter, and what should I inspect next?"
          ↓
"Here is an explainable proposal. Nothing has been changed."
          ↓
"If I choose to act, the mutation is explicitly confirmed and audited."
```

This makes NEXUS a personal Linux operations copilot rather than another system-information dashboard.

## Current status

**Version:** 0.2.0-alpha  
**Platform:** Linux, with distribution-agnostic capability detection  
**Python:** 3.11+

> **Project state:** NEXUS is being wrapped up as a completed portfolio/learning milestone. The core operations platform is stable enough to preserve and showcase; larger experimental features are intentionally deferred rather than rushed into the codebase.

The repository remains usable and open for future maintenance. The current screen-activity work stops at a privacy-first lifecycle and Wayland portal capability foundation; actual frame recording is deliberately deferred until a well-tested PipeWire recorder can be integrated without weakening the safety model.

## What NEXUS can answer

| Question | NEXUS surface | Result |
| --- | --- | --- |
| What is my machine doing right now? | `nexus status` | CPU, memory, disk, network snapshot |
| Is something unhealthy? | `nexus doctor` | Explicit health checks |
| What actually needs attention? | `nexus diagnose` | Findings grouped into incidents |
| Why was it flagged? | `nexus diagnose` | Evidence and deterministic rules |
| What should I do next? | `nexus diagnose` | Explainable remediation proposals |
| What changed over time? | `nexus-observe` / GUI Telemetry | Historical observations and trend detection |
| What is the current incident? | GUI Incidents | Evidence, grouping, and remediation plan |
| Are services failing? | `nexus services` / diagnosis | Native service-manager evidence |
| Are packages waiting for updates? | `nexus packages` / diagnosis | Native package-manager evidence |
| Can I automate recurring checks? | `nexus-scheduler` | Allow-listed scheduled jobs |
| Can I extend NEXUS? | `nexus-plugins` | Versioned plugin API and capability registry |
| Can I operate this visually? | `nexus-gui` | Desktop operations, incidents, and telemetry |

The important distinction is that **NEXUS does not hide the decision behind an automation button**. Diagnosis and planning are read-only. Mutating actions remain explicit, confirmation-gated, named, and auditable.

## Features

### System intelligence

- `nexus status` — inspect CPU load, memory, disk, and network state.
- `nexus doctor` — run non-destructive health checks with JSON output.
- `nexus report` — export a JSON health report.
- `nexus-observe` — persist system observations and inspect historical resource trends.
- Historical anomaly detection for persistent CPU, memory, and disk pressure.

### Diagnostics and incident modeling

- `nexus diagnose` — the main user-facing command for "what needs attention and what should I do next?".
- `nexus-diagnose` — standalone diagnostic entry point for the same analysis pipeline.
- Failed services are surfaced as structured findings through the detected native service backend.
- Available package updates are represented as informational findings with confirmation metadata.
- Related findings can be grouped into structured incidents.
- Incidents preserve severity, evidence, finding identifiers, and confirmation requirements.

### Explainable remediation

- Remediation proposals are generated from known findings rather than arbitrary shell input.
- Each proposal exposes a rationale, risk level, command representation, and confirmation requirement.
- Diagnostic and remediation layers are planning-only: they do not execute commands.
- Mutating service and package operations remain behind the existing confirmation-gated action engines.

### Operations, GUI, plugins, and automation

- `nexus automate` — evaluate safe automation rules in dry-run mode.
- `nexus services` — inspect supported native service-manager state.
- `nexus packages` — inspect available updates through the detected native package manager.
- `nexus packages update` — prepare confirmation-gated package update proposals.
- `nexus service start|stop|restart ...` — plan controlled service actions with an explicit confirmation gate.
- `nexus history` — inspect recent service-action audit records.
- `nexus-scheduler` — manage safe recurring NEXUS jobs.
- `nexus-gui` — launch the PySide6 desktop operations dashboard.
- GUI **Incidents** — investigate current findings and remediation proposals in one place.
- GUI **Telemetry** — visualize persisted CPU, memory, and disk history.
- `nexus-plugins` — inspect installed third-party plugins through the versioned plugin API.
- Policy-gated automation — named action registry, centralized policy, dry-run execution, confirmation gates, and audit logging.
- JSON Lines audit logging under `.nexus/` for operational decisions.

### Privacy-first screen activity foundation

- `nexus-capture` — inspect the local capture lifecycle.
- Capture policy is disabled by default.
- Session metadata is stored locally with restrictive permissions.
- Wayland/XDG Desktop Portal capability is detected without silently starting capture.
- The current backend fails closed instead of pretending that a recording exists.
- Actual frame recording is intentionally deferred to a future, separately validated milestone.

## Linux compatibility

NEXUS detects distribution and native capability rather than requiring one hard-coded distro:

| Linux family | Package backend | Common service backend |
| --- | --- | --- |
| Arch / CachyOS / Manjaro / EndeavourOS | pacman | systemd |
| Debian / Ubuntu / Mint / Pardus / Kali / Parrot | apt | systemd |
| Fedora / RHEL / Rocky / Alma / Nobara | dnf | systemd |
| openSUSE / SLES | zypper | systemd |
| Alpine | apk | OpenRC |
| Void | xbps | runit |
| Solus | eopkg | systemd |

This table describes detected capability coverage, not a claim that every NEXUS feature behaves identically on every distribution. Unsupported native capabilities fail closed.

## Operational pipeline

```text
Observation → Diagnosis → Planning → Authorization → Execution → Audit
```

The boundary is intentional. Plugins and automation extend the platform through named capabilities rather than arbitrary shell access.

## Quick start

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

NEXUS also provides a native-style system installer that installs with the host Python and exposes commands directly on `PATH` without pipx:

```bash
cd nexus
sudo ./scripts/install-system.sh
nexus diagnose
```

See `docs/system-install.md` and `docs/usage.md` for the complete installation and operations workflow.

## Documentation

- `docs/usage.md` — practical command manual and troubleshooting guide.
- `docs/architecture.md` — execution boundaries and system architecture.
- `docs/diagnostics.md` — diagnostic and incident pipeline.
- `docs/platform.md` — plugin and automation platform contract.
- `docs/screen-activity.md` — privacy model and deferred screen-capture roadmap.
- `docs/system-install.md` — system-wide installation workflow.
- `CONTRIBUTING.md` — branch, test, documentation, commit, and safety workflow.
- `CHANGELOG.md` — project history and milestone notes.

## Roadmap / milestone history

The major learning milestones are complete:

- [x] system intelligence CLI
- [x] dry-run automation rule engine
- [x] service inspection and controlled action engine
- [x] package update inspection and action planning
- [x] scheduler and audit history
- [x] desktop GUI foundation
- [x] diagnostic engine and structured findings
- [x] historical observation and anomaly detection
- [x] incident modeling and explainable remediation planning
- [x] integrated `nexus diagnose` command center
- [x] GUI incident/remediation center
- [x] richer historical visualization
- [x] versioned plugin system
- [x] policy-gated Linux automation platform
- [x] distribution-agnostic capability detection
- [x] native system-wide installer
- [x] privacy-first capture lifecycle and Wayland portal capability foundation
- [ ] full Portal → PipeWire frame recorder — deliberately deferred

The unchecked recorder is intentional. The project is being closed as a coherent, documented milestone rather than extended indefinitely.

## Development

```bash
python -m unittest discover -s tests -v
```

System command runners are injectable for deterministic tests. New system mutations should have focused tests, a dry-run or proposal path, and an explicit authorization boundary.

## License

MIT. See `LICENSE`.
