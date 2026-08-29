from __future__ import annotations

from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "skills" / "design-studio"
CONTRACT_PATH = SKILL_ROOT / "runtime-contract.md"
WORKFLOW_PATH = SKILL_ROOT / "workflow.yaml"
QUALITY_GATE_PATH = SKILL_ROOT / "references" / "quality-gates.md"
MECHANICAL_RUNTIME_PATH = SKILL_ROOT / "runtime" / "mechanical" / "index.mjs"


class RuntimeContractTests(unittest.TestCase):
    def contract_text(self) -> str:
        self.assertTrue(CONTRACT_PATH.is_file(), "runtime contract must ship with the Agent Skill")
        return CONTRACT_PATH.read_text()

    def test_runtime_contract_is_part_of_the_canonical_skill_graph(self) -> None:
        skill = (SKILL_ROOT / "SKILL.md").read_text()

        self.assertIn("`runtime-contract.md`", skill)

    def test_contract_names_operations_that_exist_in_the_canonical_workflow(self) -> None:
        contract = self.contract_text()
        workflow = WORKFLOW_PATH.read_text()
        operations = (
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
            "halt",
        )

        for operation in operations:
            with self.subTest(operation=operation):
                self.assertIn(f"`{operation}`", contract)
                self.assertIn(f"- id: {operation}\n", workflow)
        self.assertIn("`append_event`", contract)
        self.assertIn("events.jsonl", workflow)

    def test_contract_keeps_schema_and_integrity_authority_outside_the_seam(self) -> None:
        contract = self.contract_text()

        self.assertIn("`workflow.yaml` owns the step graph and artifact schemas", contract)
        self.assertIn("`references/runtime-integrity.md` owns the integrity invariants", contract)
        self.assertIn("does not restate those schemas", contract)

    def test_contract_capability_semantics_match_the_machine_workflow(self) -> None:
        contract = self.contract_text()
        workflow = WORKFLOW_PATH.read_text()

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
        self.assertIn("required: [file_io, shell, isolated_subagents]", workflow)
        self.assertIn("enum: [full, build-once-unselected, mechanical-review]", workflow)

    def test_local_mechanical_runtime_is_the_only_supported_detector_path(self) -> None:
        workflow = WORKFLOW_PATH.read_text()
        quality_gate = QUALITY_GATE_PATH.read_text()

        self.assertTrue(MECHANICAL_RUNTIME_PATH.is_file())
        self.assertIn("detector: { enum: [design-studio] }", workflow)
        self.assertNotIn("impeccable_cli", workflow)
        self.assertIn("node runtime/mechanical/index.mjs", quality_gate)
        self.assertIn("External detector availability must not change the supported rule set", quality_gate)
        self.assertNotIn("npx impeccable", quality_gate)

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
                self.assertIn("skills/design-studio/runtime-contract.md", command)
                self.assertIn("canonical Agent Skill", command)

    def test_contract_does_not_promote_research_scripts_into_product_runtime(self) -> None:
        contract = self.contract_text()

        for path in (
            "scripts/run_boundary_benchmark.py",
            "scripts/run_copilot_cli_agent_capability.py",
            "scripts/run_with_deadline.py",
        ):
            with self.subTest(path=path):
                self.assertNotIn(f"`{path}`", contract)
        self.assertIn("must not import or shell into benchmark/research tooling", contract)


if __name__ == "__main__":
    unittest.main()
