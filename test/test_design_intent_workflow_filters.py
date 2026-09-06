from __future__ import annotations

from fnmatch import fnmatchcase
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/runtime-portability.yml"

# Inputs read by the Design Intent, runtime-seam and Document suites.
PORTABILITY_INPUTS = (
    "ROADMAP.md",
    "docs/agents/domain.md",
    "docs/decisions/0005-intent-router-and-website-composition.md",
    "commands/create.md",
    "commands/review.md",
    "skills/design-studio/SKILL.md",
    "skills/design-studio/invocation.md",
    "skills/design-studio/method-router.json",
    "skills/design-studio/design-intent-contract.json",
    "skills/design-studio/workflow.yaml",
    "skills/design-studio/runtime-contract.md",
    "skills/design-studio/runtime/README.md",
    "skills/design-studio/runtime/design-intent/index.mjs",
    "skills/design-studio/references/design-intent.md",
    "skills/design-studio/agents/design-agent.md",
    "skills/design-studio/agents/evaluator.md",
    "skills/design-studio/assets/design-system-skill/SKILL.md.template",
    "test/fixtures/document-artifact/horaxon-foundation-sprint/fixture.json",
    "test/test_design_intent_contract.py",
    "test/test_design_intent_workflow_filters.py",
    "test/test_runtime_contract.py",
    "test/test_mechanical_runtime.mjs",
    "test/test_document_artifact_lane.py",
    ".github/workflows/runtime-portability.yml",
)


class DesignIntentWorkflowFilterTests(unittest.TestCase):
    def test_each_runtime_input_triggers_both_portability_events(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        # This workflow uses block-style events and quoted positive path lists.
        # Reject a changed representation rather than silently skipping coverage.
        events = re.split(r"(?m)^  (?=[a-z_]+:\s*$)", text)
        for event in ("pull_request", "push"):
            with self.subTest(event=event):
                block = next(part for part in events if part.startswith(f"{event}:\n"))
                paths = re.findall(r"(?m)^      - ['\"]([^'\"\n]+)['\"]\s*$", block)
                self.assertTrue(paths, f"{event} path filters must be inspectable")
                self.assertFalse(any(path.startswith("!") for path in paths))
                missing = [
                    path for path in PORTABILITY_INPUTS
                    if not any(fnmatchcase(path, pattern) for pattern in paths)
                ]
                self.assertEqual([], missing, f"{event} skips runtime inputs: {missing}")


if __name__ == "__main__":
    unittest.main()
