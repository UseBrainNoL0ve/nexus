import unittest

from nexus.packages.actions import plan_package_updates
from nexus.packages.pacman import PackageUpdate


class PackageActionTests(unittest.TestCase):
    def test_package_updates_are_planned_without_execution(self):
        updates = [
            PackageUpdate("linux", "6.17-1", "6.17-2", "core"),
            PackageUpdate("example", "1.2.0-1", "1.3.0-1", "extra"),
        ]

        proposals = plan_package_updates(updates)

        self.assertEqual(len(proposals), 2)
        self.assertTrue(all(proposal.requires_confirmation for proposal in proposals))
        self.assertEqual(proposals[0].risk, "medium")
        self.assertEqual(
            proposals[0].command,
            ("sudo", "pacman", "-S", "core/linux"),
        )

    def test_empty_update_list_has_no_proposals(self):
        self.assertEqual(plan_package_updates([]), [])


if __name__ == "__main__":
    unittest.main()
