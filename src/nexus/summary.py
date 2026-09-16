from __future__ import annotations

from nexus.doctor import checks_to_dict, overall_status, run_checks
from nexus.packages.pacman import inspect_updates
from nexus.scheduler.store import ScheduleStore
from nexus.sensors.system import collect_snapshot
from nexus.services.systemd import inspect_services


def collect_summary() -> dict:
    """Collect a read-only operational snapshot across NEXUS subsystems."""
    snapshot = collect_snapshot()
    checks = run_checks(snapshot)
    services = inspect_services()
    updates = inspect_updates()
    jobs = ScheduleStore().load()

    failed_services = [service.unit for service in services if service.active_state == "failed"]

    return {
        "status": overall_status(checks),
        "host": snapshot.hostname,
        "kernel": snapshot.kernel,
        "cpu_load_percent": snapshot.cpu.load_percent,
        "memory_used_percent": snapshot.memory.used_percent,
        "disk_used_percent": snapshot.disk.used_percent,
        "network_interfaces": len(snapshot.network),
        "health_checks": checks_to_dict(checks),
        "services": {
            "count": len(services),
            "running": sum(service.active_state == "active" for service in services),
            "failed": len(failed_services),
            "failed_units": failed_services,
        },
        "packages": {
            "updates": len(updates),
            "items": [
                {
                    "repository": update.repository,
                    "name": update.name,
                    "current_version": update.current_version,
                    "available_version": update.available_version,
                }
                for update in updates
            ],
        },
        "scheduler": {
            "jobs": len(jobs),
            "enabled": sum(job.enabled for job in jobs),
            "due": sum(job.due() for job in jobs),
        },
        "read_only": True,
    }


def format_summary(payload: dict) -> str:
    """Render the operational summary for humans."""
    services = payload["services"]
    packages = payload["packages"]
    scheduler = payload["scheduler"]
    lines = [
        f"NEXUS operational summary — {payload['host']}",
        f"Health:    {payload['status'].upper()}",
        f"CPU:       {payload['cpu_load_percent']:.1f}% load",
        f"Memory:    {payload['memory_used_percent']:.1f}% used",
        f"Disk:      {payload['disk_used_percent']:.1f}% used",
        f"Network:   {payload['network_interfaces']} interface(s)",
        f"Services:  {services['running']} running / {services['failed']} failed / {services['count']} total",
        f"Packages:  {packages['updates']} update(s) available",
        f"Scheduler: {scheduler['enabled']} enabled / {scheduler['due']} due / {scheduler['jobs']} total",
    ]
    if services["failed_units"]:
        lines.append("Failed services:")
        lines.extend(f"  - {unit}" for unit in services["failed_units"])
    if packages["items"]:
        lines.append("Pending package updates:")
        lines.extend(
            f"  - {item['repository']}/{item['name']}: {item['current_version']} -> {item['available_version']}"
            for item in packages["items"]
        )
    return "\n".join(lines)
