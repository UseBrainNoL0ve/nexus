# NEXUS Architecture

NEXUS is structured as a Linux operations pipeline rather than a collection of unrelated commands. The architecture separates observation, interpretation, planning, authorization, execution, and audit so that each stage can be tested independently.

## System pipeline

```text
Linux Host
    │
    ▼
Sensors ───────────────► Observation Store ─────► Historical Analysis
    │                            │                         │
    └──────────────┬─────────────┴────────────────────────┘
                   ▼
          Diagnostic Engine
                   │
                   ▼
            Incident Engine
                   │
                   ▼
          Remediation Planner
                   │
                   ▼
           Human Confirmation
                   │
                   ▼
        Policy-Gated Automation Platform
                   │
                   ├── named Action Registry
                   ├── centralized Policy
                   ├── execution handlers
                   └── platform audit
                   │
                   ▼
              Linux mutation
```

The important invariant is that **diagnostics never imply authorization**. A finding can recommend an operation without being allowed to execute it.

## Layer responsibilities

### Sensors

Collect local telemetry from Linux-native interfaces. Sensor code should return typed data and avoid side effects.

### Doctor

Runs non-destructive health checks against the current snapshot. Doctor results are evidence, not commands.

### Observability

`nexus-observe` persists timestamped snapshots in `.nexus/observations.jsonl`. Historical analysis looks for explicit, explainable persistence rather than reacting to a single spike.

Current trend rules cover sustained resource pressure:

- memory: three consecutive observations at or above 90%
- disk: three consecutive observations at or above 85%
- CPU: three consecutive observations at or above 80%

The desktop Telemetry page renders these persisted observations with a dependency-free Qt chart.

### Diagnostics

The diagnostic engine converts current evidence into deterministic `DiagnosticFinding` objects. A finding contains an identifier, category, severity, title, evidence, recommendation, and confirmation metadata.

Collection failures are represented as diagnostic collection warnings where possible so that one unavailable integration does not silently cause unrelated actions.

### Incidents

The incident layer groups related findings into a higher-level operational unit. The GUI Incident & Remediation Center presents incident severity, evidence, findings, and the corresponding explainable remediation proposals.

The implementation is deliberately deterministic. It does not use an opaque model score to decide whether findings are related.

### Remediation planning

The remediation layer transforms known findings into explicit proposals. A proposal contains the intended operation, rationale, risk, command representation, and confirmation requirement.

The planner is **proposal-only**. It does not execute commands.

### Plugin layer

The v0.6 plugin runtime uses the Python `nexus.plugins` entry-point group. Each plugin declares a versioned `PluginManifest` and registers named capabilities through `PluginRegistry`.

Plugins may register sensors, diagnostics, actions, or UI integrations. Discovery is deterministic and rejects incompatible API versions. The plugin contract intentionally does not expose arbitrary shell execution.

### Automation platform

The v1 automation platform centralizes execution policy in `AutomationPlatform`:

1. `ActionRegistry` allow-lists named capabilities and their handlers.
2. `AutomationPolicy` decides dry-run, confirmation, and authorization.
3. `AutomationPlatform` invokes only the registered handler for the selected action.
4. Execution results are written to `.nexus/platform-audit.jsonl`.

The platform is therefore an orchestration boundary, not a generic command runner. Existing systemd/package engines can remain specialized while plugins and future Linux capabilities use the same authorization and audit contract.

### Existing action engines

Service and package action engines remain specialized Linux integrations. They use argument sequences rather than arbitrary shell execution and keep confirmation requirements explicit. The v1 platform provides the higher-level policy boundary around named capabilities rather than replacing those domain-specific safety checks.

### Audit

Operational decisions are written to JSON Lines history. Audit records avoid command output and environment secrets. The goal is to preserve what NEXUS decided and whether an action was attempted, not to capture sensitive host contents.

## Desktop architecture

The PySide6 GUI consumes the same domain services as the CLI. Background workers keep telemetry collection out of the Qt event loop. The current desktop flow is:

```text
Dashboard
   ├── Services / Packages
   ├── Doctor / Command Center
   ├── Incidents / Remediation
   ├── Telemetry / Historical visualization
   └── Scheduler / History
```

The GUI should not create a second system-control implementation. It presents the same tested domain logic used by the CLI.

## Testing strategy

System integrations use injectable command runners where practical. This allows deterministic tests without mutating the host.

Feature work should normally include:

1. domain-model tests;
2. rule/decision tests;
3. command-output tests where a CLI surface changes;
4. safety tests for confirmation boundaries;
5. documentation updates for user-visible behavior.

The local validation command is:

```bash
python -m unittest discover -s tests -v
```

## Platform strategy

- `/proc` is used for Linux kernel metrics such as memory and CPU accounting.
- `/sys/class/net` is used for local network interface statistics.
- `shutil.disk_usage` provides filesystem capacity data.
- systemd is inspected through controlled subprocess argument sequences.
- pacman is queried through controlled subprocess argument sequences.
- External services are not required for the core observation and diagnostic pipeline.
- Plugins extend capabilities through a versioned Python API.
- Automation execution is constrained by named registration, centralized policy, explicit confirmation, and audit logging.
