from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class V17ReleaseClosureTests(unittest.TestCase):
    """Protect issue #78's repository-owned maintenance-mode closure."""

    def read(self, path: str) -> str:
        return (ROOT / path).read_text(encoding="utf-8")

    def test_implement_stops_cleanly_when_issue_queue_has_no_ready_work(self) -> None:
        skill = self.read(".agents/skills/implement/SKILL.md")
        self.assertIn("no ready issue", skill.lower())
        self.assertIn("stop cleanly", skill.lower())
        self.assertIn("do not invent", skill.lower())

    def test_issue_tracker_points_selection_at_the_clean_stop_rule(self) -> None:
        tracker = self.read("docs/agents/issue-tracker.md")
        self.assertIn("ready-for-agent", tracker)
        self.assertIn("no ready issue", tracker.lower())
        self.assertIn("stop cleanly", tracker.lower())

    def test_roadmap_is_a_v17_maintenance_frontier_not_a_second_task_tracker(self) -> None:
        roadmap = self.read("ROADMAP.md")
        required = [
            "v1.7",
            "#74",
            "#75",
            "#76",
            "#77",
            "#78",
            "concrete failure class",
            "repeated evidence",
            "meaningful ecosystem/upstream change",
            "bounded acceptance test",
            "GitHub Issues are authoritative",
            "Historical research and capability maintenance",
        ]
        for marker in required:
            with self.subTest(marker=marker):
                self.assertIn(marker, roadmap)
        self.assertNotIn("## Execution graph", roadmap)
        self.assertNotIn("### Portable v1.6 complete", roadmap)

    def test_public_landing_page_identifies_the_current_three_lane_product(self) -> None:
        landing = self.read("docs/index.html")
        required = [
            "v1.7",
            "Studio",
            "Review",
            "Document",
            "npx skills add George-RD/design-studio",
        ]
        for marker in required:
            with self.subTest(marker=marker):
                self.assertIn(marker, landing)
        self.assertNotIn("v1.5 · code-blind design workflow", landing)


if __name__ == "__main__":
    unittest.main()
