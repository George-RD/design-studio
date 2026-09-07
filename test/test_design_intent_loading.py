from __future__ import annotations

import json
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "design-studio"
INTENT_RUNTIME = SKILL_ROOT / "runtime" / "design-intent" / "index.mjs"


class DesignIntentLoadingTests(unittest.TestCase):
    """Observe activated authorities at the Design Intent handoff (#88/#90)."""

    def test_review_and_document_activation_exclude_studio_lifecycle(self) -> None:
        contract = json.loads((SKILL_ROOT / "design-intent-contract.json").read_text(encoding="utf-8"))
        router = json.loads((SKILL_ROOT / "method-router.json").read_text(encoding="utf-8"))
        examples = {item["id"]: item["result"] for item in contract["classificationExamples"]}
        for example_id in ("interactive-polish", "new-paginated-proposal", "existing-pdf-review"):
            with self.subTest(example=example_id):
                completed = subprocess.run(
                    ["node", str(INTENT_RUNTIME)],
                    input=json.dumps(examples[example_id]),
                    text=True,
                    capture_output=True,
                    check=False,
                    timeout=30,
                )
                self.assertEqual(0, completed.returncode, completed.stderr)
                intent = json.loads(completed.stdout)
                activated = set(router["coreAuthorities"]) | set(intent["selectedProcedures"])
                self.assertNotIn("workflow.yaml", activated)


if __name__ == "__main__":
    unittest.main()
