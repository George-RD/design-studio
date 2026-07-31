from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_boundary_agent_capability_gate as capability


class BoundaryAgentEvaluatorPromptTests(unittest.TestCase):
    def test_form_visibility_is_defined_by_visible_input_and_submit_button(self):
        payload = capability.evaluator_payload(
            "openai/gpt-4.1", "A public brief", b"image"
        )
        user_content = payload["messages"][1]["content"]
        prompt = user_content[0]["text"].lower()
        self.assertIn("labeled text input", prompt)
        self.assertIn("submit button", prompt)
        self.assertIn("after submission", prompt)
        self.assertEqual("high", user_content[1]["image_url"]["detail"])

        schema = payload["response_format"]["json_schema"]["schema"]
        description = schema["properties"]["formVisible"]["description"].lower()
        self.assertIn("labeled text input", description)
        self.assertIn("submit button", description)


if __name__ == "__main__":
    unittest.main()
