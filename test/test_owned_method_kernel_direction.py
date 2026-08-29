from __future__ import annotations

import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
LEGACY_ADR_PATH = ROOT / "docs" / "decisions" / "0001-impeccable-foundation.md"
ADR_PATH = ROOT / "docs" / "decisions" / "0002-owned-method-kernel.md"
DECISION_INDEX_PATH = ROOT / "docs" / "decisions" / "README.md"
README_PATH = ROOT / "README.md"
ROADMAP_PATH = ROOT / "ROADMAP.md"
SOURCES_PATH = ROOT / "docs" / "method-sources.json"
FEEDBACK_PATH = ROOT / "docs" / "research" / "horaxon-feedback-patterns.json"

EXPECTED_SOURCES = {
    "pbakaus/impeccable": ("63b04e2530f5c7b41ea83c133daab24f34912456", "Apache-2.0"),
    "emilkowalski/skills": ("d23d7f88a2e21c9e4b1418c7abe420f5c1052ba7", "MIT"),
}

EXPECTED_FEEDBACK_PATTERNS = {
    "semantic-redundancy",
    "whole-page-responsive-composition",
    "real-device-perceptibility",
    "product-specific-metaphor",
    "action-hierarchy-and-consistency",
    "false-affordance",
    "settled-world-preservation",
    "cross-surface-contract-drift",
}


class OwnedMethodKernelDirectionTests(unittest.TestCase):
    """Protect the architecture reset and its machine-readable evidence."""

    def test_new_adr_supersedes_the_required_upstream_foundation(self) -> None:
        """ADR 0002 must make the local kernel the authoritative runtime model."""
        text = ADR_PATH.read_text(encoding="utf-8")
        self.assertIn("# ADR 0002: Design Studio owns its method kernel", text)
        self.assertIn("**Supersedes:** ADR 0001", text)
        self.assertIn("one supported Design Studio runtime", text)
        self.assertIn("No upstream project is a required runtime foundation", text)
        self.assertIn("periodic source review", text)
        self.assertIn("owner-feedback learning loop", text)
        self.assertIn("progressive disclosure", text)

    def test_superseded_adr_marks_its_own_status_and_successor(self) -> None:
        """Opening ADR 0001 directly must not present it as an active v1.6 decision."""
        legacy = LEGACY_ADR_PATH.read_text(encoding="utf-8")
        self.assertIn("- **Status:** Superseded", legacy)
        self.assertIn(
            "- **Superseded by:** [ADR 0002](0002-owned-method-kernel.md)",
            legacy,
        )
        self.assertIn("- **Historical target:** Design Studio v1.6", legacy)
        self.assertNotIn("- **Status:** Accepted", legacy)
        self.assertNotIn("- **Applies from:** Design Studio v1.6", legacy)

    def test_decision_index_marks_the_new_record_authoritative(self) -> None:
        """The decision index must expose both status changes and precedence."""
        index = DECISION_INDEX_PATH.read_text(encoding="utf-8")
        self.assertIn("0001-impeccable-foundation.md) | Superseded", index)
        self.assertIn("0002-owned-method-kernel.md) | Accepted", index)
        self.assertIn(
            "the newest accepted ADR that explicitly supersedes an earlier record is authoritative",
            index,
        )

    def test_public_readme_matches_the_owned_kernel_direction(self) -> None:
        """Primary user guidance must describe one local runtime without upstream requirements."""
        readme = README_PATH.read_text(encoding="utf-8")
        self.assertIn("## v1.7 product boundary", readme)
        self.assertIn("one self-contained Design Studio runtime", readme)
        self.assertIn("local deterministic mechanical runtime", readme)
        self.assertIn("External systems are research inputs, not runtime dependencies", readme)
        self.assertIn(
            "Impeccable and Emil Kowalski's skills are credited sources, not install requirements",
            readme,
        )
        self.assertIn("ADR 0002", readme)
        self.assertNotIn("detector: fallback", readme)
        self.assertNotIn(
            "The v1.6 roadmap makes a compatible Impeccable install required",
            readme,
        )

    def test_roadmap_moves_from_runtime_modes_to_one_curated_product(self) -> None:
        """The roadmap must retain evidence without restoring environment-dependent modes."""
        roadmap = ROADMAP_PATH.read_text(encoding="utf-8")
        self.assertIn("curated method kernel", roadmap)
        self.assertIn("one supported runtime", roadmap)
        self.assertIn("method intake", roadmap)
        self.assertIn("feedback-to-eval loop", roadmap)
        self.assertNotIn("Impeccable becomes the required base design engine", roadmap)
        self.assertNotIn("current Design Studio with Impeccable enabled", roadmap)

        # Preserve the completed historical evidence contracts without keeping
        # the old comparison architecture as a release gate.
        self.assertIn(
            "- [x] Inventory every Design Studio step, reference, schema and check.",
            roadmap,
        )
        self.assertIn(
            "- [x] Identify workflows that only reproduce an Impeccable command",
            roadmap,
        )
        self.assertIn("benchmarks/milestone-0/OWNERSHIP_INVENTORY.md", roadmap)
        self.assertIn("- [ ] Confirm the smallest differentiated product:", roadmap)
        self.assertIn("- [ ] Run the same fixed briefs through:", roadmap)

    def test_upstream_sources_are_pinned_research_inputs_not_runtime_switches(self) -> None:
        """Validate every source record, then protect the known exact source pins."""
        registry = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
        self.assertEqual(1, registry["schemaVersion"])
        self.assertEqual("curated-local-kernel", registry["operatingModel"])
        self.assertEqual("manual-evidence-gated", registry["updatePolicy"])
        self.assertIs(registry["externalRuntimeDependencyAllowed"], False)

        registered = registry["sources"]
        self.assertIsInstance(registered, list)
        self.assertTrue(registered)
        permitted_dispositions = set(
            registry["intakePolicy"]["permittedDispositions"]
        )
        source_ids: list[str] = []
        for index, source in enumerate(registered):
            with self.subTest(index=index):
                self.assertIsInstance(source, dict)
                source_id = source.get("id")
                self.assertIsInstance(source_id, str)
                self.assertTrue(source_id.strip())
                source_ids.append(source_id)

                repository = source.get("repository")
                self.assertIsInstance(repository, str)
                self.assertTrue(repository.startswith("https://github.com/"))
                self.assertRegex(source.get("revision", ""), r"^[0-9a-f]{40}$")
                self.assertIsInstance(source.get("observedRelease"), str)
                self.assertTrue(source["observedRelease"].strip())
                self.assertIsInstance(source.get("license"), str)
                self.assertTrue(source["license"].strip())
                self.assertEqual("research-input", source.get("role"))
                self.assertIs(source.get("runtimeDependency"), False)
                self.assertIn(
                    source.get("currentDisposition"),
                    permitted_dispositions,
                )

                methods = source.get("relevantMethods")
                self.assertIsInstance(methods, list)
                self.assertTrue(methods)
                self.assertTrue(
                    all(isinstance(method, str) and method.strip() for method in methods)
                )
                self.assertIsInstance(source.get("attribution"), str)
                self.assertTrue(source["attribution"].strip())

        self.assertEqual(len(source_ids), len(set(source_ids)))
        sources = {source["id"]: source for source in registered}
        self.assertTrue(EXPECTED_SOURCES.keys() <= sources.keys())
        for source_id, (revision, license_id) in EXPECTED_SOURCES.items():
            with self.subTest(source=source_id):
                source = sources[source_id]
                self.assertEqual(revision, source["revision"])
                self.assertEqual(license_id, source["license"])
                self.assertEqual("observe", source["currentDisposition"])

        cadence = registry["reviewCadence"]
        self.assertEqual("quarterly", cadence["minimum"])
        self.assertIn("dogfood-gap", cadence["triggers"])
        self.assertIn("major-upstream-release", cadence["triggers"])

    def test_horaxon_feedback_is_recorded_as_failure_classes_not_style_preferences(self) -> None:
        """Dogfood evidence must abstract reusable failures without prescribing a house style."""
        record = json.loads(FEEDBACK_PATH.read_text(encoding="utf-8"))
        self.assertEqual(1, record["schemaVersion"])
        self.assertEqual("George-RD/horaxon-web", record["dogfoodRepository"])
        self.assertIn(59, record["primaryPullRequests"])

        patterns = record["patterns"]
        ids = [pattern["id"] for pattern in patterns]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(EXPECTED_FEEDBACK_PATTERNS, set(ids))
        for pattern in patterns:
            with self.subTest(pattern=pattern["id"]):
                self.assertTrue(pattern["failureClass"])
                self.assertTrue(pattern["evidence"])
                self.assertTrue(pattern["workflowIntervention"])
                self.assertTrue(pattern["validation"])
                self.assertFalse(pattern.get("stylePrescription", True))

        guardrails = record["learningGuardrails"]
        self.assertIn("Do not codify one site's visual language as a universal rule.", guardrails)
        self.assertIn(
            "Promote feedback into the kernel only when it identifies a reusable failure class.",
            guardrails,
        )


if __name__ == "__main__":
    unittest.main()
