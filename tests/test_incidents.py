import unittest

from nexus.diagnostics.engine import DiagnosticFinding
from nexus.diagnostics.incidents import build_incidents
from nexus.diagnostics.remediation import build_remediation_plan


class IncidentEngineTests(unittest.TestCase):
    def test_related_findings_form_one_incident(self):
        findings = [
            DiagnosticFinding(
                id="disk-pressure",
                category="storage",
                severity="warning",
                title="Root filesystem usage is high",
                evidence="88% used",
                recommendation="Inspect large files.",
            ),
            DiagnosticFinding(
                id="disk-cache-pressure",
                category="storage",
                severity="info",
                title="Cache usage is notable",
                evidence="cache is large",
                recommendation="Review caches.",
            ),
        ]
        incidents = build_incidents(findings)
        self.assertEqual(len(incidents), 1)
        self.assertEqual(incidents[0].severity, "warning")
        self.assertEqual(incidents[0].findings, ("disk-pressure", "disk-cache-pressure"))

    def test_categories_are_kept_separate(self):
        findings = [
            DiagnosticFinding("memory-pressure", "resource", "warning", "Memory pressure", "92%", "Inspect memory."),
            DiagnosticFinding("disk-pressure", "storage", "warning", "Disk pressure", "88%", "Inspect disk."),
        ]
        incidents = build_incidents(findings)
        self.assertEqual({item.category for item in incidents}, {"resource", "storage"})

    def test_failed_service_produces_read_only_log_inspection_step(self):
        finding = DiagnosticFinding(
            id="failed-service:example.service",
            category="service",
            severity="warning",
            title="Systemd service is failed",
            evidence="active=failed",
            recommendation="Inspect logs.",
        )
        steps = build_remediation_plan([finding])
        self.assertEqual(len(steps), 1)
        self.assertEqual(steps[0].risk, "low")
        self.assertFalse(steps[0].requires_confirmation)
        self.assertIn("journalctl -u example.service", steps[0].command)

    def test_package_plan_requires_confirmation(self):
        finding = DiagnosticFinding(
            id="package-updates-available",
            category="packages",
            severity="info",
            title="Package updates are available",
            evidence="12 updates",
            recommendation="Review update plan.",
            requires_confirmation=True,
        )
        step = build_remediation_plan([finding])[0]
        self.assertEqual(step.risk, "medium")
        self.assertTrue(step.requires_confirmation)
        self.assertEqual(step.command, "pacman -Qu")


if __name__ == "__main__":
    unittest.main()
