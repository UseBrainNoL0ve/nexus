# NEXUS Architecture

## v0.1 boundary

NEXUS is intentionally read-only. The CLI asks sensors for observations, converts those observations into typed models, and optionally evaluates health checks. Report generation serializes the same model into JSON.

```text
CLI
 │
 ├── Sensors ──> CPU / Memory / Disk / Network
 │
 ├── Doctor ──> health checks
 │
 └── Reporter ──> JSON
```

## Future action pipeline

```text
Sensors -> Rules -> Action Planner -> Confirmation -> Action Adapter
```

The confirmation boundary is deliberate. A future package update, service restart, or cleanup action should be represented as a planned operation before anything mutates the host.

## Platform strategy

- `/proc` is used for Linux kernel metrics such as memory and CPU accounting.
- `/sys/class/net` is used for local network interface statistics.
- `shutil.disk_usage` provides filesystem capacity data.
- External services are not required for the core health report.
