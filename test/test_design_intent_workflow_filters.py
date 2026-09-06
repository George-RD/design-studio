from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/runtime-portability.yml"

# Inputs read by the Design Intent, runtime-seam and Document suites.
PORTABILITY_INPUTS = (
    "ROADMAP.md",
    "docs/agents/domain.md",
    "docs/decisions/README.md",
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


def matches_path_filter(path: str, pattern: str) -> bool:
    """Match the workflow's exact paths, segment stars and trailing directory globstars.

    Other GitHub filter syntax needs an explicit extension rather than a false pass.
    """
    if not re.fullmatch(r"[A-Za-z0-9_./*-]+", pattern):
        raise ValueError(f"unsupported path filter syntax: {pattern}")
    if "**" in pattern and (not pattern.endswith("/**") or "**" in pattern[:-3]):
        raise ValueError(f"only trailing directory globstars are supported: {pattern}")
    expression = re.escape(pattern).replace(r"\*\*", ".*").replace(r"\*", "[^/]*")
    return re.fullmatch(expression, path) is not None


class DesignIntentWorkflowFilterTests(unittest.TestCase):
    def test_single_star_cannot_match_nested_paths(self) -> None:
        nested = "skills/design-studio/runtime/design-intent/index.mjs"
        cases = (
            (nested, "skills/*", False),
            (nested, "skills/design-studio/*", False),
            (nested, "skills/**", True),
            (nested, "skills/design-studio/**", True),
            ("skills/SKILL.md", "skills/*", True),
            ("other/SKILL.md", "skills/**", False),
            ("ROADMAP.md", "ROADMAP.md", True),
            ("docs/ROADMAP.md", "ROADMAP.md", False),
        )
        for path, pattern, expected in cases:
            with self.subTest(path=path, pattern=pattern):
                self.assertEqual(expected, matches_path_filter(path, pattern))

    def test_unsupported_filter_syntax_fails_closed(self) -> None:
        for pattern in ("!skills/**", "skills/[ab].md", "skills/a?.md", "**/SKILL.md"):
            with self.subTest(pattern=pattern), self.assertRaises(ValueError):
                matches_path_filter("skills/a.md", pattern)

    def test_architecture_index_keeps_publication_separate_from_implementation(self) -> None:
        index = (ROOT / "docs/decisions/README.md").read_text(encoding="utf-8")
        row = next(line for line in index.splitlines() if "[0005:" in line)
        for marker in ("release/v1.7.0", "#78", "#98", "parked"):
            self.assertIn(marker, row)
        self.assertNotIn("Product implementation begins only after v1.7 release closure", row)

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
                    if not any(matches_path_filter(path, pattern) for pattern in paths)
                ]
                self.assertEqual([], missing, f"{event} skips runtime inputs: {missing}")


if __name__ == "__main__":
    unittest.main()
