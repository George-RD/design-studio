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
    def test_pinned_impeccable_cli_dependencies_use_the_committed_bun_lockfile(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("Setup pinned Bun", workflow)
        self.assertIn("uses: oven-sh/setup-bun@v2", workflow)
        self.assertIn("bun-version: 1.3.14", workflow)
        self.assertIn("Install pinned Impeccable dependencies", workflow)
        self.assertIn("working-directory: vendor/impeccable", workflow)
        self.assertIn("bun install --frozen-lockfile --ignore-scripts", workflow)
        self.assertNotIn("npm ci", workflow)
        self.assertNotIn("bun-version: latest", workflow)


if __name__ == "__main__":
    unittest.main()
