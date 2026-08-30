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
        self.assertEqual(
            [
                "workflow.yaml",
                "references/review/polish.md",
                "references/document/document.md",
            ],
            contract["laneProcedures"],
        )
        self.assertIn("runnable_target", contract["enums"]["requiredCapability"])

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
        self.assertIn("Issue #90 owns lane-first procedure loading", reference)
        self.assertNotIn("Load only the selected procedure", reference)

    def test_contract_examples_cover_modes_authority_prompt_order_and_extraction(self) -> None:
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

        extraction = next(
            example for example in examples if example["id"] == "existing-codebase-extraction"
        )["result"]
        self.assertEqual("Review", extraction["lane"])
        self.assertEqual("polish", extraction["designMode"])
        self.assertEqual("none", extraction["visualAuthority"])
        self.assertEqual("extract", extraction["systemEffect"])
        self.assertIn("extract", contract["modeRules"]["polish"]["systemEffects"])

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
                required = contract["modeRules"][example["result"]["designMode"]][
                    "requiredCapabilities"
                ]
                self.assertTrue(
                    set(required).issubset(example["result"]["requiredCapabilities"])
                )
                if example["result"]["surface"] != "paginated-artifact":
                    self.assertIn(
                        "runnable_target",
                        example["result"]["requiredCapabilities"],
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
        review = next(
            example["result"]
            for example in contract["classificationExamples"]
            if example["result"]["designMode"] == "polish"
        )
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
                "parallel taxonomy",
                {**baseline, "mode": "create"},
                "design intent has unexpected fields: mode",
            ),
            (
                "unknown precedence",
                {**baseline, "precedenceRule": "prompt-order"},
                "precedenceRule must be one of",
            ),
            (
                "missing runnable target",
                {
                    **baseline,
                    "requiredCapabilities": [
                        item
                        for item in baseline["requiredCapabilities"]
                        if item != "runnable_target"
                    ],
                },
                "requiredCapabilities must include runnable_target",
            ),
            (
                "missing browser capability",
                {
                    **baseline,
                    "requiredCapabilities": [
                        item
                        for item in baseline["requiredCapabilities"]
                        if item != "browser_automation"
                    ],
                },
                "requiredCapabilities must include browser_automation",
            ),
            (
                "missing lane procedure",
                {**baseline, "selectedProcedures": ["references/rationale.md"]},
                "selectedProcedures must include workflow.yaml",
            ),
            (
                "cross-lane procedure",
                {
                    **review,
                    "selectedProcedures": [
                        "references/review/polish.md",
                        "workflow.yaml",
                    ],
                },
                "selectedProcedures cannot include lane procedure workflow.yaml for polish",
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
        self.assertNotIn(
            "references/design-intent.md",
            {item["path"] for item in router["leaves"]},
            "Design Intent is a core front-door authority, not a conditionally disclosed method leaf",
        )

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

        for command in (ROOT / "commands" / "create.md", ROOT / "commands" / "review.md"):
            with self.subTest(command=command.name):
                text = self.read(command)
                self.assertIn("design-intent-contract.json", text)
                self.assertIn("references/design-intent.md", text)
                self.assertIn("validated Design Intent", text)

    def test_governance_records_design_intent_once_and_splits_release_gate(self) -> None:
        domain = self.read(ROOT / "docs" / "agents" / "domain.md")
        adr = self.read(ROOT / "docs" / "decisions" / "0005-intent-router-and-website-composition.md")
        roadmap = self.read(ROOT / "ROADMAP.md")
        reference = self.read(REFERENCE_PATH)

        self.assertIn("**Design Intent**", domain)
        self.assertIn("**Design Intent** decision is the highest stable interface", adr)
        self.assertIn("This reference owns request classification vocabulary and precedence", reference)
        self.assertIn("release/v1.7.0", adr)
        self.assertIn("#98", adr)
        self.assertNotIn("#78 must close before product behaviour changes", adr)
        self.assertIn("release/v1.7.0", roadmap)
        self.assertIn("#89", roadmap)
        self.assertIn("#98", roadmap)
        self.assertNotIn("All product-behaviour work in that graph is blocked", roadmap)


if __name__ == "__main__":
    unittest.main()
