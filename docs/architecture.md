# NEXUS Architecture

## 1. Architectural goal

NEXUS is designed as a **local-first Linux operations platform** rather than a collection of unrelated CLI commands.

The architecture separates five concerns:

```text
COLLECT → UNDERSTAND → PLAN → EXECUTE → RECORD
```

- **Collect** system state from Linux-native interfaces.
- **Understand** state through health checks, summaries, and historical analysis.
- **Plan** changes as explicit, inspectable proposals.
- **Execute** only through controlled adapters with confirmation boundaries.
- **Record** decisions and results for later inspection.

The central rule is that **read capability and mutation capability are separate concerns**.

---

## 2. System architecture

```text
                         ┌─────────────────────┐
                         │   User Interfaces   │
                         │                     │
                         │ CLI · GUI · future  │
                         │ API / integrations  │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    Domain Layer     │
                         │                     │
                         │ models · summary    │
                         │ diagnostics · rules │
                         └──────────┬──────────┘
                                    │
                 ┌──────────────────┼──────────────────┐
                 ▼                  ▼                  ▼
        ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
        │  Observation   │ │    Planning    │ │    Scheduling  │
        │                │ │                │ │                │
        │ sensors        │ │ proposals      │ │ jobs           │
        │ systemd read   │ │ risk/rationale │ │ allow-list     │
        │ pacman read    │ │ confirmation   │ │ execution      │
        └───────┬────────┘ └───────┬────────┘ └───────┬────────┘
                │                  │                  │
                └──────────────────┼──────────────────┘
                                   ▼
                         ┌─────────────────────┐
                         │    Infrastructure   │
                         │                     │
                         │ systemd · pacman   │
                         │ /proc · /sys · FS   │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Persistence / Audit │
                         │                     │
                         │ observations JSONL  │
                         │ action audit JSONL  │
                         │ scheduler history   │
                         └─────────────────────┘
```

The GUI and CLI are consumers of the same domain and infrastructure layers. They are not separate implementations of system-management logic.

---

## 3. Observation layer

The observation layer is responsible for reading host state without changing it.

Current Linux-native sources include:

| Source | Purpose |
|---|---|
| `/proc` | CPU and memory information |
| `/sys/class/net` | network interface counters |
| filesystem APIs | capacity and usage |
| `systemctl` | service state |
| `pacman -Qu` | available package updates |
| scheduler store | configured and due jobs |

Observation results should be represented as typed domain data before presentation.

This keeps formatting, GUI code, and future APIs independent from Linux command output.

---

## 4. Diagnostics and analysis

Diagnostics consume observations and produce structured findings.

```text
Observation
    │
    ├── current health checks
    │
    ├── historical comparison
    │
    ├── change detection
    │
    └── future anomaly detection
            │
            ▼
       Finding / Insight
```

A diagnostic finding should explain:

- what was observed,
- which resource is affected,
- why it is notable,
- how confident the detection is, where applicable,
- and what evidence supports the finding.

NEXUS should prefer deterministic, explainable rules before introducing opaque machine-learning models.

---

## 5. Planning and mutation boundary

Any operation capable of changing the host crosses an explicit planning boundary:

```text
Observation
    ↓
Condition / rule
    ↓
Action proposal
    ↓
Risk + rationale + affected resource
    ↓
Explicit confirmation
    ↓
Controlled adapter
    ↓
Result
    ↓
Audit record
```

The action layer must not accept arbitrary shell strings. Commands should be represented as structured argument sequences and executed through controlled runners.

This design also makes mutation behavior straightforward to test without modifying a real machine.

---

## 6. Scheduler architecture

The scheduler is intentionally constrained.

```text
Persistent Job
     ↓
Due check
     ↓
Allow-listed action
     ↓
Read-only execution
     ↓
Result + notification
     ↓
Scheduler audit
```

A scheduled job does not become a general-purpose shell task. The scheduler currently operates on built-in NEXUS actions such as diagnostics and package inspection.

The user-level systemd integration follows the same principle: installation, enabling, and execution are explicit stages rather than implicit side effects.

---

## 7. Persistence strategy

NEXUS uses lightweight local persistence rather than requiring a database or remote service for its core workflows.

Current stores include:

```text
.nexus/
├── audit.jsonl
├── scheduler-audit.jsonl
├── schedules.json
└── observations.jsonl
```

JSONL is useful for append-oriented operational records because it is:

- human-readable,
- streamable,
- easy to inspect from shell tools,
- resilient to partial append failures compared with rewriting one large document,
- straightforward to migrate into a database later.

A future SQLite-backed storage layer can be introduced without changing the domain model if long-term queries become a performance requirement.

---

## 8. Testability

System integration is designed around injectable command runners and deterministic data sources where practical.

This allows tests to verify:

- parsing of Linux command output,
- health-check decisions,
- action planning,
- confirmation behavior,
- scheduler execution,
- audit records,
- historical observation deltas,
- and error handling

without requiring the test suite to mutate the host.

The target is not merely high line coverage. The important goal is **confidence at system boundaries**.

---

## 9. Security and safety boundaries

NEXUS is not a sandbox and does not claim to make every administrative operation inherently safe. Instead, it reduces accidental mutation through explicit engineering boundaries.

### Current constraints

- no arbitrary shell execution interface,
- read-only observation commands by default,
- explicit confirmation for supported mutations,
- scheduler action allow-list,
- user-owned scheduler service,
- persistent audit metadata,
- command runners suitable for deterministic testing.

Sensitive command output and environment secrets should not be persisted in audit records.

---

## 10. Platform strategy

The first implementation targets CachyOS because it provides a concrete development environment and a well-defined Linux stack.

The longer-term architecture separates distribution-specific concerns behind adapters:

```text
              NEXUS Domain
                   │
          ┌────────┴────────┐
          ▼                 ▼
     Linux Backend     Linux Backend
       Arch/CachyOS        future
          │                 │
     pacman/systemd     package/service
```

The domain layer should not depend directly on package-manager-specific semantics when an abstraction can preserve useful behavior across distributions.

However, portability is subordinate to correctness. A generic abstraction should not be introduced until there are at least two concrete implementations that justify it.

---

## 11. Architectural priorities

Future work should follow this order:

1. Correctness and deterministic tests.
2. Explainable diagnostics and historical analysis.
3. Safe remediation planning.
4. Stable internal APIs.
5. Additional interfaces and integrations.
6. Cross-distribution support.

This prevents the project from becoming a visually polished wrapper around unreliable system operations.
