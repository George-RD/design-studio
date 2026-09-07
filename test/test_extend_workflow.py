"""Extend execution contracts at the validated Design Intent / workflow seam."""

import json
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/design-studio"


def workflow_contract():
    result = subprocess.run(
        ["ruby", "-ryaml", "-rjson", "-e",
         "puts JSON.generate(YAML.load_file(ARGV.fetch(0)))",
         str(SKILL / "workflow.yaml")],
        text=True, capture_output=True, check=True,
    )
    return json.loads(result.stdout)["workflow"]


class ExtendWorkflowTests(unittest.TestCase):
    def test_validated_extension_is_an_executable_studio_mode(self):
        contract = json.loads((SKILL / "design-intent-contract.json").read_text())
        intent = next(case["result"] for case in contract["classificationExamples"]
                      if case["id"] == "accepted-world-new-route")
        result = subprocess.run(
            ["node", str(SKILL / "runtime/design-intent/index.mjs")],
            input=json.dumps(intent), text=True, capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        validated = json.loads(result.stdout)
        self.assertEqual(validated["designMode"], "extend")
        self.assertIn(
            validated["designMode"],
            workflow_contract()["schemas"]["runManifest"]["properties"]["mode"]["enum"],
            "A validated extension must execute without being recast as greenfield or overhaul",
        )


if __name__ == "__main__":
    unittest.main()
