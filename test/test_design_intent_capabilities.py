from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/design-studio"


class DesignIntentCapabilityTests(unittest.TestCase):
    def test_capabilities_are_the_selected_modes_unique_set(self) -> None:
        contract = json.loads((SKILL / "design-intent-contract.json").read_text(encoding="utf-8"))
        for mode in contract["enums"]["designMode"]:
            baseline = next(
                case["result"] for case in contract["classificationExamples"]
                if case["result"]["designMode"] == mode
            )
            capabilities = baseline["requiredCapabilities"]
            unrelated = "browser_automation" if baseline["lane"] == "Document" else "page_artifact_rendering"
            cases = (
                ("reordered", list(reversed(capabilities)), 0),
                ("duplicate", capabilities + [capabilities[0]], 2),
                ("cross-lane", capabilities + [unrelated], 2),
            )
            for name, required, expected in cases:
                with self.subTest(mode=mode, case=name):
                    intent = copy.deepcopy(baseline)
                    intent["requiredCapabilities"] = required
                    result = subprocess.run(
                        ["node", str(SKILL / "runtime/design-intent/index.mjs")],
                        input=json.dumps(intent), cwd=ROOT, text=True,
                        capture_output=True, check=False, timeout=15,
                    )
                    self.assertEqual(expected, result.returncode, result.stderr)
                    if expected == 0:
                        self.assertEqual(intent, json.loads(result.stdout))
                    else:
                        self.assertEqual("", result.stdout)
                        self.assertIn("requiredCapabilities must be the mode's unique set", result.stderr)


if __name__ == "__main__":
    unittest.main()
