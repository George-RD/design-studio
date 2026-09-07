from __future__ import annotations

import json
from pathlib import Path
import unittest

from test_method_kernel_routing import matching_route_ids


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "design-studio"
EVALUATOR = "agents/evaluator.md"


class ReviewAuthorityLoadingTests(unittest.TestCase):
    """Keep evaluator safeguards reachable without loading the Studio lifecycle."""

    def test_review_routes_its_evaluator_authority(self) -> None:
        """Require the shared role at every interactive Review handoff, not globally."""
        router = json.loads((SKILL_ROOT / "method-router.json").read_text(encoding="utf-8"))
        self.assertNotIn(EVALUATOR, router["coreAuthorities"])
        for task in ("review", "polish"):
            for surface in ("persuade", "operate", "read", "experience"):
                with self.subTest(task=task, surface=surface):
                    matches = matching_route_ids(router, {"task": {task}, "surface": {surface}})
                    roles = {
                        path
                        for route in router["routes"]
                        if route["id"] in matches
                        for path in route.get("agents", [])
                    }
                    self.assertEqual({EVALUATOR}, roles)
                    self.assertTrue((SKILL_ROOT / EVALUATOR).is_file())

    def test_review_procedure_hands_off_the_evaluator_contract(self) -> None:
        """Require a stage-specific role reference before browser-grounded review."""
        procedure = SKILL_ROOT / "references" / "review" / "polish.md"
        text = procedure.read_text(encoding="utf-8")
        handoff = text.split("## Outputs and handoff", 1)[1].split("\n## ", 1)[0]
        self.assertIn("`../../agents/evaluator.md`", handoff)
        self.assertEqual(
            (SKILL_ROOT / EVALUATOR).resolve(),
            (procedure.parent / "../../agents/evaluator.md").resolve(),
        )


if __name__ == "__main__":
    unittest.main()
