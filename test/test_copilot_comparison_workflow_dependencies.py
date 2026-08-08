from __future__ import annotations

from pathlib import Path
import unittest


WORKFLOW = (
    Path(__file__).resolve().parents[1]
    / ".github"
    / "workflows"
    / "milestone-0-comparison-generation.yml"
)


class CopilotComparisonWorkflowDependencyTests(unittest.TestCase):
    def test_pinned_impeccable_cli_dependencies_are_installed_from_lockfile(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("Install pinned Impeccable dependencies", workflow)
        self.assertIn("working-directory: vendor/impeccable", workflow)
        self.assertIn("npm ci --ignore-scripts --no-audit --no-fund", workflow)
        self.assertNotIn("npm install\n", workflow)


if __name__ == "__main__":
    unittest.main()
