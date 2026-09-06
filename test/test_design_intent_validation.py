from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/design-studio"


class DesignIntentValidationTests(unittest.TestCase):
    def test_undeclared_procedures_are_rejected_before_publication(self) -> None:
        contract = json.loads((SKILL / "design-intent-contract.json").read_text(encoding="utf-8"))
        cases = (
            ("create", "unknown-procedure.md"),
            ("create", "../growth-arsenal/SKILL.md"),
            ("polish", "./workflow.yaml"),
            ("polish", "references/../workflow.yaml"),
        )
        for mode, procedure in cases:
            with self.subTest(mode=mode, procedure=procedure), tempfile.TemporaryDirectory() as directory:
                intent = copy.deepcopy(next(
                    example["result"] for example in contract["classificationExamples"]
                    if example["result"]["designMode"] == mode
                ))
                intent["selectedProcedures"].append(procedure)
                source = Path(directory) / "input.json"
                output = Path(directory) / "validated-intent.json"
                source.write_text(json.dumps(intent), encoding="utf-8")
                result = subprocess.run(
                    ["node", str(SKILL / "runtime/design-intent/index.mjs"), str(source), str(output)],
                    cwd=ROOT, text=True, capture_output=True, check=False, timeout=15,
                )
                self.assertEqual(2, result.returncode, result.stderr)
                self.assertIn("selectedProcedures contains undeclared procedure", result.stderr)
                self.assertFalse(output.exists(), "invalid intent must not be published")


if __name__ == "__main__":
    unittest.main()
