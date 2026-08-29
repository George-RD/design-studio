from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MAP_PATH = ROOT / "docs" / "migration-map.json"
NARRATIVE_PATH = ROOT / "docs" / "migration-map.md"
SOURCES_PATH = ROOT / "docs" / "method-sources.json"
FEEDBACK_PATH = ROOT / "docs" / "research" / "horaxon-feedback-patterns.json"

BASELINE_REVISION = "492a874d0a7c935e51395d66f420608a997d9ed3"
RETIRED_POST_BASELINE_AUTHORITIES = {
    "skills/design-studio/references/planning.md",
    "skills/design-studio/references/evaluation.md",
    "skills/design-studio/references/iteration.md",
}
RETIRED_POST_BASELINE_SURFACES = {"references/methodology.md"}

EXPECTED_SURFACE_LABELS = {
    "canonical-skill",
    "optional-host-adapter",
    "compatibility-bridge",
    "repository-only-tooling",
    "delete-candidate",
}
EXPECTED_SCRIPT_LABELS = {
    "product-runtime",
    "host-adapter-support",
    "benchmark-research",
    "ci-dev-support",
    "compatibility-bridge",
    "delete-candidate",
}
EXPECTED_METHOD_DISPOSITIONS = {
    "keep-local",
    "adapt-local",
    "vendor-slice",
    "observe",
    "delete-reject",
}

EXPECTED_SURFACES = {
    "skills/design-studio/SKILL.md": "canonical-skill",
    "skills/design-studio/workflow.yaml": "canonical-skill",
    "skills/design-studio/agents/design-agent.md": "canonical-skill",
    "skills/design-studio/agents/evaluator.md": "canonical-skill",
    "skills/design-studio/evals/evals.json": "canonical-skill",
    ".claude-plugin/plugin.json": "optional-host-adapter",
    ".claude-plugin/marketplace.json": "optional-host-adapter",
    "commands/create.md": "compatibility-bridge",
    "commands/review.md": "compatibility-bridge",
    "agents/design-agent.md": "compatibility-bridge",
    "agents/evaluator.md": "compatibility-bridge",
    "docs/index.html": "repository-only-tooling",
    "docs/app.js": "repository-only-tooling",
    "references/methodology.md": "delete-candidate",
}

EXPECTED_SCRIPT_PATHS = {
    "scripts/browser_motion_evidence.mjs",
    "scripts/browser_profile_cleanup.mjs",
    "scripts/browser_websocket_ready.mjs",
    "scripts/probe_github_models.py",
    "scripts/run_boundary_benchmark.py",
    "scripts/run_boundary_benchmark_matrix.py",
    "scripts/run_boundary_benchmark_preference.py",
    "scripts/run_browser_capability.mjs",
    "scripts/run_browser_capability_completion.mjs",
    "scripts/run_copilot_cli_agent_capability.py",
    "scripts/run_copilot_cli_agent_capability_gate.py",
    "scripts/run_copilot_comparison.py",
    "scripts/run_copilot_comparison_lane.py",
    "scripts/run_copilot_comparison_matrix_generation.py",
    "scripts/run_with_deadline.py",
    "scripts/validate_benchmark_fixtures.py",
}

EXPECTED_BEHAVIOR_CONTRACTS = {
    "source-blind-role-isolation",
    "immutable-iterations-and-events",
    "precommitted-unattended-direction",
    "current-mechanical-snapshots",
    "required-rendered-evidence",
    "orchestrator-decision-and-final-acceptance",
    "cross-surface-version-parity",
}


def path_without_fragment(reference: str) -> str:
    """Return a repository path from a path-plus-fragment reference."""
    return reference.split("#", 1)[0]


class PortableProductMigrationMapTests(unittest.TestCase):
    """Freeze issue #44's no-behavior-change migration baseline."""

    def setUp(self) -> None:
        """Load the machine-readable migration baseline for each assertion."""
        self.record = json.loads(MAP_PATH.read_text(encoding="utf-8"))

    def test_baseline_and_taxonomies_are_explicit(self) -> None:
        """Pin baseline identity and the allowed classification vocabularies."""
        self.assertEqual(1, self.record["schemaVersion"])
        self.assertEqual("authoritative-baseline", self.record["status"])
        self.assertIs(self.record["externalRuntimeDependencyAllowed"], False)
        self.assertEqual("target-v1.6", self.record["externalRuntimeDependencyPolicy"])

        baseline = self.record["baseline"]
        self.assertEqual("George-RD/design-studio", baseline["repository"])
        self.assertEqual(BASELINE_REVISION, baseline["revision"])
        self.assertEqual("2026-08-28", baseline["recordedAt"])
        self.assertEqual("1.5.0", baseline["version"])
        self.assertEqual(
            "docs/decisions/0002-owned-method-kernel.md",
            baseline["governingDecision"],
        )
        self.assertEqual(
            "benchmarks/milestone-0/ownership-inventory.json",
            baseline["historicalInventory"],
        )

        self.assertEqual(EXPECTED_SURFACE_LABELS, set(self.record["surfaceLabels"]))
        self.assertEqual(EXPECTED_SCRIPT_LABELS, set(self.record["scriptLabels"]))
        self.assertEqual(
            EXPECTED_METHOD_DISPOSITIONS,
            set(self.record["externalMethodDispositions"]),
        )

    def test_current_external_runtime_branch_is_explicit_migration_debt(self) -> None:
        """Record v1.5's Impeccable availability branch without blessing it for v1.6."""
        branches = {row["id"]: row for row in self.record["currentRuntimeBranches"]}
        self.assertEqual({"optional-impeccable-mechanical-gate"}, set(branches))

        branch = branches["optional-impeccable-mechanical-gate"]
        self.assertEqual("migration-debt", branch["status"])
        self.assertEqual("impeccable-cli-available", branch["trigger"])
        self.assertIn("non-equivalent fallback", branch["behavior"])
        self.assertIn("#46", branch["migration"])
        self.assertIn("#47", branch["migration"])
        self.assertIn("#50", branch["migration"])
        for authority in branch["authorities"]:
            self.assertTrue((ROOT / authority).exists(), authority)

    def test_every_current_product_and_adapter_surface_is_classified_once(self) -> None:
        """Ensure every tracked invocation/adapter surface has one migration role."""
        rows = self.record["surfaces"]
        paths = [row["path"] for row in rows]
        self.assertEqual(len(paths), len(set(paths)))
        self.assertEqual(EXPECTED_SURFACES, {row["path"]: row["label"] for row in rows})

        for row in rows:
            with self.subTest(path=row["path"]):
                self.assertIn(row["label"], EXPECTED_SURFACE_LABELS)
                self.assertTrue(row["reason"].strip())
                if row["path"] in RETIRED_POST_BASELINE_SURFACES:
                    self.assertFalse((ROOT / row["path"]).exists())
                else:
                    self.assertTrue((ROOT / row["path"]).exists())
                if row["label"] in {
                    "optional-host-adapter",
                    "compatibility-bridge",
                    "delete-candidate",
                }:
                    self.assertTrue(row.get("target", "").strip())

    def test_script_families_cover_the_scripts_directory_without_promoting_research(self) -> None:
        """Classify every script recursively and keep the research harness out of runtime."""
        rows = self.record["scripts"]
        family_ids = [row["id"] for row in rows]
        self.assertEqual(len(family_ids), len(set(family_ids)))

        classified_paths = [path for row in rows for path in row["paths"]]
        self.assertEqual(len(classified_paths), len(set(classified_paths)))
        self.assertEqual(EXPECTED_SCRIPT_PATHS, set(classified_paths))

        actual_paths = {
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / "scripts").rglob("*")
            if path.is_file()
        }
        self.assertEqual(EXPECTED_SCRIPT_PATHS, actual_paths)

        for row in rows:
            with self.subTest(family=row["id"]):
                self.assertIn(row["label"], EXPECTED_SCRIPT_LABELS)
                self.assertTrue(row["reason"].strip())
                for path in row["paths"]:
                    self.assertTrue((ROOT / path).is_file())
                if row["label"] in {"compatibility-bridge", "delete-candidate"}:
                    self.assertTrue(row.get("target", "").strip())

        promoted = {
            row["id"]
            for row in rows
            if row["label"] in {"product-runtime", "host-adapter-support"}
        }
        self.assertEqual(set(), promoted)

    def test_concept_map_preserves_local_authority_and_external_provenance(self) -> None:
        """Keep the frozen pre-change authority/provenance inventory interpretable after contraction."""
        sources = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
        source_by_id = {source["id"]: source for source in sources["sources"]}
        feedback = json.loads(FEEDBACK_PATH.read_text(encoding="utf-8"))
        feedback_ids = {pattern["id"] for pattern in feedback["patterns"]}

        concepts = self.record["conceptMap"]
        concept_by_id = {concept["id"]: concept for concept in concepts}
        self.assertEqual(len(concepts), len(concept_by_id))
        self.assertIn("generated-specificity-and-subtraction", concept_by_id)
        self.assertIn("motion-craft-and-perceptibility", concept_by_id)
        self.assertIn("offer-copy-authority", concept_by_id)

        for concept in concepts:
            with self.subTest(concept=concept["id"]):
                self.assertIn(
                    concept["canonicalOwner"],
                    {"design-studio", "growth-arsenal", "shared-artifact"},
                )
                self.assertTrue(concept["reason"].strip())
                for local_path in concept.get("localAuthorities", []):
                    self.assertTrue(local_path.strip())
                    if local_path not in RETIRED_POST_BASELINE_AUTHORITIES:
                        self.assertTrue((ROOT / local_path).exists(), local_path)
                for evidence_id in concept.get("dogfoodEvidence", []):
                    self.assertIn(evidence_id, feedback_ids)
                for overlap in concept.get("externalOverlaps", []):
                    self.assertIn(overlap["source"], source_by_id)
                    self.assertEqual("observe", overlap["disposition"])
                    self.assertTrue(overlap["reason"].strip())
                    self.assertIs(source_by_id[overlap["source"]]["runtimeDependency"], False)

        direction = concept_by_id["source-blind-direction-and-evaluation"]
        self.assertIn(
            "emilkowalski/skills",
            {overlap["source"] for overlap in direction["externalOverlaps"]},
        )
        review = concept_by_id["review-orchestration"]
        self.assertIn(
            "emilkowalski/skills",
            {overlap["source"] for overlap in review["externalOverlaps"]},
        )

        specificity = concept_by_id["generated-specificity-and-subtraction"]
        self.assertIn("semantic-redundancy", specificity["dogfoodEvidence"])
        self.assertIn("product-specific-metaphor", specificity["dogfoodEvidence"])
        self.assertIn(
            "skills/design-studio/references/review/slop.md",
            specificity["localAuthorities"],
        )

        copy = concept_by_id["offer-copy-authority"]
        self.assertEqual("growth-arsenal", copy["canonicalOwner"])
        self.assertEqual([], copy["externalOverlaps"])

    def test_behavior_contracts_name_existing_protection_before_contraction(self) -> None:
        """Point contraction work at existing observable behavior protection."""
        contracts = self.record["behaviorContracts"]
        by_id = {contract["id"]: contract for contract in contracts}
        self.assertEqual(len(contracts), len(by_id))
        self.assertEqual(EXPECTED_BEHAVIOR_CONTRACTS, set(by_id))

        for contract in contracts:
            with self.subTest(contract=contract["id"]):
                self.assertTrue(contract["behavior"].strip())
                self.assertTrue(contract["protectedBy"])
                for reference in contract["protectedBy"]:
                    path = path_without_fragment(reference)
                    self.assertTrue((ROOT / path).exists(), reference)

        finalization = by_id["orchestrator-decision-and-final-acceptance"]["protectedBy"]
        self.assertIn("skills/design-studio/evals/evals.json#16", finalization)
        self.assertIn("skills/design-studio/evals/evals.json#29", finalization)

    def test_historical_evidence_stays_discoverable_and_out_of_runtime(self) -> None:
        """Retain benchmark provenance without classifying it as shipped product runtime."""
        evidence = self.record["historicalEvidence"]
        paths = [row["path"] for row in evidence]
        self.assertEqual(len(paths), len(set(paths)))
        self.assertIn("benchmarks/milestone-0/ownership-inventory.json", paths)
        self.assertIn(
            "benchmarks/milestone-0/evidence/copilot-cli-agent-capability.json", paths
        )
        self.assertIn(
            "benchmarks/milestone-0/evidence/github-models-capability.json", paths
        )

        for row in evidence:
            with self.subTest(path=row["path"]):
                self.assertEqual("repository-only-tooling", row["classification"])
                self.assertIs(row["shipsWithSkill"], False)
                self.assertTrue(row["reason"].strip())
                self.assertTrue((ROOT / row["path"]).exists())

    def test_narrative_states_scope_and_downstream_boundaries(self) -> None:
        """Keep the human-readable map aligned with the machine-readable baseline."""
        text = NARRATIVE_PATH.read_text(encoding="utf-8")
        self.assertIn("ADR 0002", text)
        self.assertIn(BASELINE_REVISION, text)
        self.assertIn("No production behavior changes in this ticket", text)
        self.assertIn("No current script family is product runtime", text)
        self.assertIn("non-equivalent fallback", text)
        self.assertIn("migration debt", text)
        self.assertIn("#46", text)
        self.assertIn("#47", text)
        self.assertIn("#49", text)
        self.assertIn("#50", text)
        self.assertIn("#45`, `#50` and `#51", text)
        self.assertIn("semantic-redundancy", text)
        self.assertIn("product-specific-metaphor", text)
        self.assertIn("does not make Horaxon a house style", text)
        self.assertIn("external runtime dependency", text.lower())


if __name__ == "__main__":
    unittest.main()
