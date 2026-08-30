from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "design-studio"
CONTRACT_PATH = SKILL_ROOT / "design-intent-contract.json"
REFERENCE_PATH = SKILL_ROOT / "references" / "design-intent.md"
RUNTIME_PATH = SKILL_ROOT / "runtime" / "design-intent" / "index.mjs"
AUTHORITY_MAP_PATH = ROOT / "docs" / "method-authority-map.json"


class DesignIntentContractTests(unittest.TestCase):
    """Acceptance contract for issue #89's host-neutral front door."""

    @staticmethod
    def read(path: Path) -> str:
        return path.read_text(encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> dict:
        return json.loads(cls.read(path))

    def test_contract_declares_one_host_neutral_front_door(self) -> None:
        contract = self.load(CONTRACT_PATH)

        self.assertEqual(1, contract["schemaVersion"])
        self.assertEqual("authoritative-design-intent-contract", contract["status"])
        self.assertIs(contract["hostNeutral"], True)
        self.assertEqual(
            "docs/decisions/0005-intent-router-and-website-composition.md",
            contract["governingDecision"],
        )
        self.assertEqual("designMode", contract["classificationField"])
        self.assertEqual("composition-contract.json", contract["compositionAuthority"])
        self.assertEqual(
            ["task", "surface", "interaction", "evidence"],
            contract["routerSignalDimensions"],
        )

        self.assertEqual(["Studio", "Review", "Document"], contract["enums"]["lane"])
        self.assertEqual(
            [
                "create",
                "extend",
                "polish",
                "overhaul",
                "document-create",
                "document-review",
            ],
            contract["enums"]["designMode"],
        )
        self.assertEqual(
            {
                "schemaVersion",
                "lane",
                "designMode",
                "surface",
                "visualAuthority",
                "compositionState",
                "systemEffect",
                "requiredCapabilities",
                "selectedProcedures",
                "assumptions",
                "unresolved",
                "precedenceRule",
            },
            set(contract["requiredFields"]),
        )
        self.assertNotIn("authorityDomains", contract)
        self.assertNotIn("artifactRoles", contract)

    def test_reference_documents_six_distinct_modes_and_ranked_precedence(self) -> None:
        reference = self.read(REFERENCE_PATH)
        headings = {
            line.strip()
            for line in reference.splitlines()
            if line.startswith("## ")
        }
        for heading in {
            "## Purpose",
            "## Triggers",
            "## Required context",
            "## Outputs and handoff",
            "## Authority boundary",
            "## Failure behavior",
            "## Evaluation hooks",
            "## Source provenance",
        }:
            self.assertIn(heading, headings)

        for mode in (
            "create",
            "extend",
            "polish",
            "overhaul",
            "document-create",
            "document-review",
        ):
            with self.subTest(mode=mode):
                self.assertIn(f"`{mode}`", reference)

        self.assertIn("`composition-contract.json`", reference)
        self.assertIn("`runtime-contract.md`", reference)
        self.assertIn("full execution of `extend`", reference)
        self.assertIn("ranked precedence", reference.lower())
        self.assertIn("page or print", reference.lower())
        self.assertIn("audit or polish", reference.lower())

    def test_contract_examples_cover_modes_authority_and_prompt_order(self) -> None:
        contract = self.load(CONTRACT_PATH)
        examples = contract["classificationExamples"]
        self.assertEqual(
            set(contract["enums"]["designMode"]),
            {example["result"]["designMode"] for example in examples},
        )
        self.assertIn("none", {example["result"]["visualAuthority"] for example in examples})
        self.assertIn(
            "accepted-design-system",
            {example["result"]["visualAuthority"] for example in examples},
        )
        self.assertIn(
            "paginated-artifact",
            {example["result"]["surface"] for example in examples},
        )
        self.assertTrue(any(len(example["promptVariants"]) > 1 for example in examples))

        precedence = contract["precedence"]
        self.assertEqual(
            list(range(1, len(precedence) + 1)),
            [rule["rank"] for rule in precedence],
        )
        self.assertEqual(len(precedence), len({rule["id"] for rule in precedence}))
        for example in examples:
            with self.subTest(example=example["id"]):
                self.assertTrue(all(prompt.strip() for prompt in example["promptVariants"]))
                self.assertIn(
                    example["result"]["precedenceRule"],
                    {rule["id"] for rule in precedence},
                )

    def test_runtime_validates_representative_design_intents(self) -> None:
        contract = self.load(CONTRACT_PATH)
        self.assertTrue(RUNTIME_PATH.is_file())

        for example in contract["classificationExamples"]:
            with self.subTest(example=example["id"]), tempfile.TemporaryDirectory() as directory:
                input_path = Path(directory) / "intent.json"
                input_path.write_text(json.dumps(example["result"]), encoding="utf-8")
                run = subprocess.run(
                    ["node", str(RUNTIME_PATH), str(input_path)],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(0, run.returncode, run.stderr)
                self.assertEqual(example["result"], json.loads(run.stdout))

    def test_runtime_rejects_inconsistent_or_parallel_taxonomy(self) -> None:
        contract = self.load(CONTRACT_PATH)
        baseline = contract["classificationExamples"][0]["result"]
        invalid_cases = [
            ("wrong lane", {**baseline, "lane": "Document"}, "requires lane Studio"),
            (
                "wrong surface",
                {**baseline, "surface": "paginated-artifact"},
                "does not allow surface paginated-artifact",
            ),
            (
                "unknown mode",
                {**baseline, "designMode": "redesign"},
                "designMode must be one of",
            ),
            (
                "unknown precedence",
                {**baseline, "precedenceRule": "prompt-order"},
                "precedenceRule must be one of",
            ),
            (
                "missing lane procedure",
                {**baseline, "selectedProcedures": ["references/rationale.md"]},
                "selectedProcedures must include workflow.yaml",
            ),
        ]

        for name, payload, expected_error in invalid_cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                input_path = Path(directory) / "intent.json"
                input_path.write_text(json.dumps(payload), encoding="utf-8")
                run = subprocess.run(
                    ["node", str(RUNTIME_PATH), str(input_path)],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(2, run.returncode)
                self.assertIn(expected_error, run.stderr)

    def test_skill_routes_through_design_intent_before_lane_authority(self) -> None:
        skill = self.read(SKILL_ROOT / "SKILL.md")
        load_and_route = skill.split("## Load and route", 1)[1].split("## Required references", 1)[0]
        self.assertLess(load_and_route.index("design-intent-contract.json"), load_and_route.index("workflow.yaml"))
        self.assertLess(load_and_route.index("references/design-intent.md"), load_and_route.index("method-router.json"))
        self.assertIn("task`, `surface`, `interaction` and `evidence", load_and_route)

        router = self.load(SKILL_ROOT / "method-router.json")
        self.assertEqual(
            {"task", "surface", "interaction", "evidence"},
            set(router["routes"][0]["signals"]),
        )
        self.assertIn("design-intent-contract.json", router["coreAuthorities"])
        self.assertIn("references/design-intent.md", router["coreAuthorities"])
        leaf = next(item for item in router["leaves"] if item["path"] == "references/design-intent.md")
        self.assertEqual("canonical", leaf["authorityRole"])
        self.assertEqual(["design-intent"], leaf["conceptIds"])

    def test_invocation_and_runtime_share_one_adapter_taxonomy(self) -> None:
        invocation = self.read(SKILL_ROOT / "invocation.md")
        runtime_contract = self.read(SKILL_ROOT / "runtime-contract.md")
        runtime_readme = self.read(SKILL_ROOT / "runtime" / "README.md")

        self.assertIn("## Design Intent input mapping", invocation)
        self.assertIn("references/design-intent.md", invocation)
        self.assertNotIn(
            "Audit or polish-only language routes to Review instead of Studio",
            invocation,
        )
        self.assertIn("`validate_design_intent`", runtime_contract)
        self.assertIn("highest behavioural test seam", runtime_contract)
        self.assertIn("no second intent taxonomy", runtime_contract)
        self.assertIn("## Design Intent", runtime_readme)
        self.assertIn("design-intent/index.mjs", runtime_readme)
        self.assertIn("does not infer", runtime_readme)

    def test_governance_records_design_intent_once_and_splits_release_gate(self) -> None:
        authority_map = self.load(AUTHORITY_MAP_PATH)
        concept = next(item for item in authority_map["concepts"] if item["conceptId"] == "design-intent")
        self.assertEqual("orchestration-runtime", concept["domain"])
        self.assertEqual("canonical-local", concept["authority"]["kind"])
        self.assertEqual(
            "skills/design-studio/references/design-intent.md",
            concept["authority"]["canonicalPath"],
        )
        self.assertEqual("always", concept["routing"]["mode"])
        self.assertIs(concept["upstreamRuntimeRequired"], False)
        self.assertEqual([], concept["externalOverlaps"])

        domain = self.read(ROOT / "docs" / "agents" / "domain.md")
        authority_markdown = self.read(ROOT / "docs" / "method-authority-map.md")
        adr = self.read(ROOT / "docs" / "decisions" / "0005-intent-router-and-website-composition.md")
        roadmap = self.read(ROOT / "ROADMAP.md")
        self.assertIn("**Design Intent**", domain)
        self.assertIn("| Design Intent |", authority_markdown)
        self.assertIn("release/v1.7.0", adr)
        self.assertIn("#98", adr)
        self.assertNotIn("#78 must close before product behaviour changes", adr)
        self.assertIn("release/v1.7.0", roadmap)
        self.assertIn("#89", roadmap)
        self.assertIn("#98", roadmap)
        self.assertNotIn("All product-behaviour work in that graph is blocked", roadmap)


if __name__ == "__main__":
    unittest.main()
