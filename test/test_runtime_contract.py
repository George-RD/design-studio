from __future__ import annotations

from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "skills" / "design-studio"
CONTRACT_PATH = SKILL_ROOT / "references" / "runtime-contract.md"


class RuntimeContractTests(unittest.TestCase):
    def contract_text(self) -> str:
        self.assertTrue(CONTRACT_PATH.is_file(), "runtime contract must ship with the Agent Skill")
        return CONTRACT_PATH.read_text()

    def test_runtime_contract_is_part_of_the_canonical_skill_graph(self) -> None:
        skill = (SKILL_ROOT / "SKILL.md").read_text()
        workflow = (SKILL_ROOT / "workflow.yaml").read_text()

        self.assertIn("`references/runtime-contract.md`", skill)
        self.assertIn("runtimeContract: references/runtime-contract.md", workflow)

    def test_contract_names_the_stable_deterministic_operations(self) -> None:
        contract = self.contract_text()

        for operation in (
            "initialise",
            "resume_validate",
            "resolve_roots",
            "probe_capabilities",
            "prepare_direction_assignment",
            "mechanical_preflight",
            "decide",
            "finish_select",
            "finish_correction_decide",
            "accept",
            "report",
            "append_event",
        ):
            with self.subTest(operation=operation):
                self.assertIn(f"`{operation}`", contract)

    def test_contract_keeps_schema_and_integrity_authority_outside_the_seam(self) -> None:
        contract = self.contract_text()

        self.assertIn("`workflow.yaml` owns the step graph and artifact schemas", contract)
        self.assertIn("`references/runtime-integrity.md` owns the integrity invariants", contract)
        self.assertIn("does not restate those schemas", contract)

    def test_contract_has_explicit_capability_and_failure_semantics(self) -> None:
        contract = self.contract_text()

        for token in (
            "file_io",
            "shell",
            "isolated_subagents",
            "full",
            "build-once-unselected",
            "mechanical-review",
            "block before planning",
            "never silently",
        ):
            with self.subTest(token=token):
                self.assertIn(token, contract)

    def test_contract_excludes_research_only_concepts(self) -> None:
        contract = self.contract_text()

        for phrase in (
            "blind comparison",
            "lane matrix",
            "fixture validation",
            "model probing",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, contract)
        self.assertIn("excluded from the runtime seam", contract)

    def test_claude_commands_delegate_to_the_same_runtime_contract(self) -> None:
        for relative in ("commands/create.md", "commands/review.md"):
            command = (REPO_ROOT / relative).read_text()
            with self.subTest(command=relative):
                self.assertIn("skills/design-studio/references/runtime-contract.md", command)
                self.assertIn("canonical Agent Skill", command)


if __name__ == "__main__":
    unittest.main()
