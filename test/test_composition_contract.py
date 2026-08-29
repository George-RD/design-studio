from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "design-studio"
CONTRACT_PATH = SKILL_ROOT / "composition-contract.json"
REFERENCE_PATH = SKILL_ROOT / "references" / "composition-contract.md"
FIXTURE_PATH = ROOT / "test" / "fixtures" / "composition-contract.json"
LEGACY_METHODOLOGY_PATH = ROOT / "references" / "methodology.md"


class CompositionContractTests(unittest.TestCase):
    """Protect the neutral Design Studio <-> Growth Arsenal composition seam from #48."""

    @staticmethod
    def load(path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    def test_contract_is_host_neutral_and_neither_skill_is_a_runtime_dependency(self) -> None:
        contract = self.load(CONTRACT_PATH)
        self.assertEqual(1, contract["schemaVersion"])
        self.assertEqual("authoritative-composition-contract", contract["status"])
        self.assertIs(contract["hostNeutral"], True)
        self.assertEqual(["design-studio", "growth-arsenal"], contract["participants"])
        self.assertIs(contract["runtimeDependencies"]["designStudioRequiresGrowthArsenal"], False)
        self.assertIs(contract["runtimeDependencies"]["growthArsenalRequiresDesignStudio"], False)

    def test_domain_owners_and_artifact_roles_are_explicit(self) -> None:
        contract = self.load(CONTRACT_PATH)
        domains = {item["id"]: item["owner"] for item in contract["authorityDomains"]}
        self.assertEqual(
            {
                "product-truth": "shared-product-context",
                "offer-copy": "growth-arsenal",
                "visual-design": "design-studio",
            },
            domains,
        )

        roles = {item["role"]: item for item in contract["artifactRoles"]}
        self.assertEqual(set(domains), set(roles))
        self.assertEqual(["PRODUCT.md"], roles["product-truth"]["defaultPaths"])
        self.assertEqual(["OFFER.md", "COPY.md"], roles["offer-copy"]["defaultPaths"])
        self.assertEqual(["DESIGN.md"], roles["visual-design"]["defaultPaths"])
        self.assertEqual("confirmed", roles["product-truth"]["requiredState"])
        self.assertEqual("approved", roles["offer-copy"]["requiredState"])
        self.assertEqual("accepted", roles["visual-design"]["requiredState"])
        for role in roles.values():
            self.assertEqual("project", role["scope"])
            self.assertTrue(role["authorityEvidence"])
            self.assertTrue(role["whenOwnerAbsent"].strip())

    def test_resolution_never_uses_basename_prompt_order_or_mtime_as_authority(self) -> None:
        resolution = self.load(CONTRACT_PATH)["resolution"]
        self.assertEqual(
            [
                "declared-role-and-scope",
                "explicit-approval-or-acceptance-provenance",
                "canonical-project-context-location",
            ],
            resolution["selectionOrder"],
        )
        self.assertIs(resolution["basenameAloneAuthoritative"], False)
        self.assertIs(resolution["promptOrderAuthoritative"], False)
        self.assertIs(resolution["mtimeAuthoritative"], False)
        self.assertEqual("unresolved", resolution["ambiguousSameRole"])

    def test_precedence_conflicts_and_staleness_cover_the_three_authority_domains(self) -> None:
        contract = self.load(CONTRACT_PATH)
        precedence = [item["authority"] for item in sorted(contract["precedence"], key=lambda item: item["rank"])]
        self.assertEqual(
            [
                "explicit-current-user-instruction",
                "confirmed-product-truth",
                "approved-growth-arsenal-offer-copy",
                "current-surface-brief",
                "accepted-design-system-or-selected-direction",
            ],
            precedence,
        )
        conflicts = {item["id"]: item for item in contract["conflicts"]}
        self.assertEqual(
            {
                "copy-vs-product-truth",
                "product-change-vs-downstream",
                "copy-vs-visual-capacity",
                "design-vs-offer-copy",
                "duplicate-role-artifacts",
            },
            set(conflicts),
        )
        self.assertEqual("confirmed-product-truth", conflicts["copy-vs-product-truth"]["winner"])
        self.assertEqual("unresolved", conflicts["duplicate-role-artifacts"]["winner"])
        self.assertEqual(3, len(contract["stalenessRules"]))

    def test_composition_fixture_resolves_the_same_authorities_regardless_of_input_order(self) -> None:
        contract = self.load(CONTRACT_PATH)
        fixture = self.load(FIXTURE_PATH)
        role_contract = {item["role"]: item for item in contract["artifactRoles"]}

        def resolve(artifacts: list[dict]) -> dict[str, str]:
            resolved: dict[str, str] = {}
            for role, role_rule in role_contract.items():
                candidates = [
                    item
                    for item in artifacts
                    if item.get("role") == role
                    and item.get("scope") == role_rule["scope"]
                    and item.get("state") == role_rule["requiredState"]
                ]
                self.assertLessEqual(len(candidates), 1, f"fixture leaves {role} ambiguous")
                if candidates:
                    resolved[role] = candidates[0]["path"]
            return resolved

        for scenario in fixture["scenarios"]:
            with self.subTest(scenario=scenario["id"]):
                expected = scenario["expectedAuthorities"]
                self.assertEqual(expected, resolve(scenario["artifacts"]))
                self.assertEqual(expected, resolve(list(reversed(scenario["artifacts"]))))

    def test_installed_reference_states_the_non_duplication_boundary(self) -> None:
        text = REFERENCE_PATH.read_text(encoding="utf-8")
        self.assertIn("Growth Arsenal owns offer, positioning, persuasion strategy and authoritative commercial copy", text)
        self.assertIn("Design Studio owns visual direction, design implementation, rendered evaluation and accepted visual-system output", text)
        self.assertIn("does not invoke, copy or reimplement Growth Arsenal methods", text)
        self.assertIn("Prompt order, file modification time and basename alone never establish authority", text)

    def test_legacy_top_level_methodology_is_retired_after_composition_migration(self) -> None:
        self.assertFalse(LEGACY_METHODOLOGY_PATH.exists())


if __name__ == "__main__":
    unittest.main()
