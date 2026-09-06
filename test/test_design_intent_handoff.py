from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/design-studio"
RUNTIME = SKILL / "runtime/design-intent/index.mjs"


class DesignIntentHandoffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads((SKILL / "design-intent-contract.json").read_text(encoding="utf-8"))

    def intent_for(self, mode: str) -> dict:
        return copy.deepcopy(next(
            case["result"] for case in self.contract["classificationExamples"]
            if case["result"]["designMode"] == mode
        ))

    def validate(self, intent: dict, expected: int) -> str:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "intent.json"
            output = Path(directory) / "validated.json"
            source.write_text(json.dumps(intent), encoding="utf-8")
            result = subprocess.run(
                ["node", str(RUNTIME), str(source), str(output)],
                cwd=ROOT, text=True, capture_output=True, check=False, timeout=15,
            )
            self.assertEqual(expected, result.returncode, result.stderr)
            self.assertEqual(expected == 0, output.exists(), "only valid handoffs are published")
            if expected == 0:
                self.assertEqual(intent, json.loads(output.read_text(encoding="utf-8")))
            return result.stderr

    def test_each_mode_rejects_duplicate_execution(self) -> None:
        for mode in self.contract["enums"]["designMode"]:
            with self.subTest(mode=mode):
                intent = self.intent_for(mode)
                intent["selectedProcedures"] *= 2
                error = self.validate(intent, 2)
                self.assertIn("exactly one canonical lane procedure", error)

    def test_document_creation_requires_a_coherent_authority_effect_pair(self) -> None:
        allowed = {
            "none": {"establish"},
            "document-visual-contract": {"preserve", "extend", "replace"},
        }
        for authority, effects in allowed.items():
            for effect in ("establish", "preserve", "extend", "replace"):
                with self.subTest(authority=authority, effect=effect):
                    intent = self.intent_for("document-create")
                    intent["visualAuthority"] = authority
                    intent["systemEffect"] = effect
                    self.validate(intent, 0 if effect in effects else 2)


if __name__ == "__main__":
    unittest.main()
