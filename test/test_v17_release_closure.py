from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class V17ReleaseClosureTests(unittest.TestCase):
    """Protect issue #78's repository-owned maintenance-mode closure."""

    def read(self, path: str) -> str:
        return (ROOT / path).read_text(encoding="utf-8")

    def test_work_selection_stops_cleanly_when_queue_has_no_ready_work(self) -> None:
        selection = self.read("docs/agents/work-selection.md")
        self.assertIn("ready-for-agent", selection)
        self.assertIn("no ready issue", selection.lower())
        self.assertIn("stop cleanly", selection.lower())
        self.assertIn("do not invent", selection.lower())

    def test_issue_tracker_routes_to_the_work_selection_authority(self) -> None:
        tracker = self.read("docs/agents/issue-tracker.md")
        self.assertIn("ready-for-agent", tracker)
        self.assertIn("docs/agents/work-selection.md", tracker)

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

    def test_public_landing_tracks_v17_product_positioning(self) -> None:
        landing = self.read("docs/index.html")
        self.assertIn("Design Studio v1.7", landing)
        self.assertIn("v1.7 · portable design-engineering Agent Skill", landing)
        self.assertIn("Studio · Review · Document", landing)
        self.assertNotIn("Design Studio v1.5", landing)
        self.assertNotIn("Optional Impeccable gate", landing)

    def test_release_record_cannot_claim_acceptance_before_external_publication(self) -> None:
        record = self.read("docs/releases/v1.7.0.md")
        self.assertIn("**Status:** Prepared", record)
        self.assertIn("repository description", record)
        self.assertIn("v1.7.0` tag/GitHub Release", record)
        self.assertIn("#78", record)


if __name__ == "__main__":
    unittest.main()
