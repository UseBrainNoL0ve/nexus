# NEXUS Operational Workflows

This document covers the two operational features added after the diagnostic/incident milestone: the unified read-only summary and the user-level scheduler service.

## Operational summary

Use `nexus-summary` when you want a compact answer to **"what is the current operational state of this machine?"** without running several separate commands.

```bash
nexus-summary
```

The summary combines:

- overall health-check status,
- CPU, memory, disk, and network state,
- total and failed systemd services,
- available pacman updates,
- configured/enabled/due scheduler jobs.

It is strictly read-only.

For integrations:

```bash
nexus-summary --json
```

The JSON form exposes the same information as structured data and includes `read_only: true`.

### Recommended workflow

```text
nexus-summary
      ↓
notice something unusual?
      ↓
nexus diagnose
      ↓
inspect evidence / incidents
      ↓
plan a controlled action
```

The summary is intentionally not a replacement for diagnosis. Its job is to provide a fast operational control-plane view before deeper investigation.

## Scheduler as a user service

NEXUS can generate a user-owned systemd unit for the scheduler:

```bash
nexus-scheduler install
```

Installation writes:

```text
~/.config/systemd/user/nexus-scheduler.service
```

The command **does not enable or start the service by default**. It prints the explicit next step:

```bash
systemctl --user enable --now nexus-scheduler.service
```

If you deliberately want NEXUS to enable and start the service as part of installation:

```bash
nexus-scheduler install --enable
```

The generated unit points at the Python interpreter from the active NEXUS environment, so installation should normally be performed while the project's virtual environment is active.

### Safety boundary

Scheduler installation and scheduler execution are separate concerns:

1. `install` writes a user-owned unit.
2. `--enable` explicitly requests activation.
3. The scheduler itself still accepts only its allow-listed NEXUS actions.
4. Scheduled jobs do not become arbitrary shell commands.

This keeps persistent background operation explicit rather than making installation silently start a daemon.
