from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MAP_PATH = ROOT / "docs" / "method-authority-map.json"
COMPANION_PATH = ROOT / "docs" / "method-authority-map.md"
SOURCES_PATH = ROOT / "docs" / "method-sources.json"
MIGRATION_MAP_PATH = ROOT / "docs" / "migration-map.json"
ADR_PATH = ROOT / "docs" / "decisions" / "0002-owned-method-kernel.md"

EXPECTED_DOMAINS = {
    "design-engineering": "design-studio",
    "orchestration-runtime": "design-studio",
    "copy-offer": "growth-arsenal",
}


class MethodAuthorityMapTests(unittest.TestCase):
    """Protect the concept-level authority and provenance contract from #47."""

    def load_map(self) -> dict:
        """Load the authority map after asserting that the new artifact exists."""
        self.assertTrue(MAP_PATH.is_file(), "#47 requires docs/method-authority-map.json")
        return json.loads(MAP_PATH.read_text(encoding="utf-8"))

    def test_map_is_the_authoritative_concept_level_record(self) -> None:
        """The new map must declare its governing sources and dependency boundary."""
        record = self.load_map()
        self.assertEqual(1, record["schemaVersion"])
        self.assertEqual("authoritative-method-map", record["status"])
        self.assertEqual("docs/decisions/0002-owned-method-kernel.md", record["governingDecision"])
        self.assertEqual("docs/method-sources.json", record["sourceRegistry"])
        self.assertEqual("docs/migration-map.json", record["migrationInput"])
        self.assertIs(record["externalRuntimeDependencyAllowed"], False)
        self.assertEqual(
            ["reject", "observe", "adapt-local", "vendor-slice"],
            record["permittedExternalDispositions"],
        )

    def test_current_concept_baseline_has_one_explicit_authority_each(self) -> None:
        """Every #44 concept must resolve to one authority without parallel rulebooks."""
        record = self.load_map()
        migration = json.loads(MIGRATION_MAP_PATH.read_text(encoding="utf-8"))
        expected_ids = {concept["id"] for concept in migration["conceptMap"]}
        concepts = record["concepts"]
        actual_ids = [concept["conceptId"] for concept in concepts]
        self.assertEqual(len(actual_ids), len(set(actual_ids)))
        self.assertEqual(expected_ids, set(actual_ids))

        for concept in concepts:
            with self.subTest(concept=concept["conceptId"]):
                authority = concept["authority"]
                self.assertEqual(1, len([authority]))
                self.assertIn(authority["owner"], {"design-studio", "growth-arsenal"})
                self.assertIn(authority["kind"], {"canonical-local", "external-domain"})

                if authority["owner"] == "design-studio":
                    self.assertEqual("canonical-local", authority["kind"])
                    canonical = ROOT / authority["canonicalPath"]
                    self.assertTrue(canonical.is_file(), authority["canonicalPath"])
                    self.assertTrue(authority["canonicalPath"].startswith("skills/design-studio/"))
                else:
                    self.assertEqual("external-domain", authority["kind"])
                    boundary = ROOT / authority["localBoundaryPath"]
                    self.assertTrue(boundary.is_file(), authority["localBoundaryPath"])
                    self.assertNotIn("canonicalPath", authority)

                for supporting in concept.get("supportingReferences", []):
                    self.assertTrue((ROOT / supporting).is_file(), supporting)

    def test_domain_ownership_separates_design_copy_and_runtime(self) -> None:
        """Growth Arsenal's copy domain must remain distinct from Design Studio methods."""
        record = self.load_map()
        boundaries = {
            item["domain"]: item["owner"] for item in record["domainBoundaries"]
        }
        self.assertEqual(EXPECTED_DOMAINS, boundaries)

        for concept in record["concepts"]:
            with self.subTest(concept=concept["conceptId"]):
                self.assertIn(concept["domain"], EXPECTED_DOMAINS)
                if concept["domain"] == "copy-offer":
                    self.assertEqual("growth-arsenal", concept["authority"]["owner"])
                else:
                    self.assertEqual("design-studio", concept["authority"]["owner"])

    def test_routing_is_explicit_and_suitable_for_progressive_disclosure(self) -> None:
        """Every authority record must say when it is always loaded, routed, or composed."""
        record = self.load_map()
        for concept in record["concepts"]:
            with self.subTest(concept=concept["conceptId"]):
                routing = concept["routing"]
                self.assertIn(routing["mode"], {"always", "routed", "composition"})
                triggers = routing["triggers"]
                self.assertIsInstance(triggers, list)
                self.assertTrue(triggers)
                self.assertTrue(all(isinstance(item, str) and item.strip() for item in triggers))
                self.assertIs(concept["upstreamRuntimeRequired"], False)

    def test_external_overlaps_resolve_through_pinned_source_provenance(self) -> None:
        """Candidate methods must resolve to one pinned source, licence, path and disposition."""
        record = self.load_map()
        registry = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
        sources = {source["id"]: source for source in registry["sources"]}
        permitted = set(record["permittedExternalDispositions"])
        seen_methods: set[tuple[str, str, str]] = set()

        for concept in record["concepts"]:
            for overlap in concept["externalOverlaps"]:
                key = (concept["conceptId"], overlap["sourceId"], overlap["methodName"])
                with self.subTest(concept=concept["conceptId"], method=overlap["methodName"]):
                    self.assertNotIn(key, seen_methods)
                    seen_methods.add(key)
                    source = sources[overlap["sourceId"]]
                    self.assertRegex(source["revision"], r"^[0-9a-f]{40}$")
                    self.assertTrue(source["repository"].startswith("https://github.com/"))
                    self.assertTrue(source["license"])
                    self.assertIs(source["runtimeDependency"], False)
                    self.assertIn(overlap["disposition"], permitted)
                    self.assertIn(overlap["implementationStatus"], {"candidate", "not-adopted"})
                    self.assertTrue(overlap["upstreamPathAtRevision"].strip())
                    self.assertTrue(overlap["modificationProvenance"].strip())
                    self.assertTrue(overlap["evidenceBasis"])
                    if overlap["disposition"] in {"adapt-local", "vendor-slice"}:
                        self.assertEqual("candidate", overlap["implementationStatus"])
                    else:
                        self.assertEqual("not-adopted", overlap["implementationStatus"])

        self.assertTrue(seen_methods, "The map must resolve the external overlaps identified by #44")

    def test_duplicate_guidance_has_a_retirement_or_supersession_path(self) -> None:
        """Known duplicate local guidance must name what survives and when deletion is safe."""
        record = self.load_map()
        resolutions = record["duplicateResolutions"]
        self.assertTrue(resolutions)
        for resolution in resolutions:
            with self.subTest(path=resolution["duplicatePath"]):
                self.assertIn(resolution["action"], {"supersede", "delete-after"})
                self.assertTrue((ROOT / resolution["duplicatePath"]).exists())
                self.assertTrue(resolution["retainedAuthorities"])
                for retained in resolution["retainedAuthorities"]:
                    self.assertTrue((ROOT / retained).exists(), retained)
                self.assertTrue(resolution["condition"].strip())

    def test_comparison_requests_are_targeted_not_default_work(self) -> None:
        """Any future comparison must name one unresolved intake question rather than broad dogfood."""
        record = self.load_map()
        for comparison in record["targetedComparisons"]:
            with self.subTest(comparison=comparison.get("id")):
                self.assertTrue(comparison["id"].strip())
                self.assertTrue(comparison["conceptId"].strip())
                self.assertTrue(comparison["question"].strip())
                self.assertTrue(comparison["evidenceNeeded"].strip())

    def test_human_companion_exposes_source_pins_and_boundary_decisions(self) -> None:
        """Maintainers must be able to audit provenance and domain ownership without parsing JSON."""
        self.assertTrue(COMPANION_PATH.is_file())
        text = COMPANION_PATH.read_text(encoding="utf-8")
        registry = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
        self.assertIn("# Method authority map", text)
        self.assertIn("Growth Arsenal", text)
        self.assertIn("No upstream repository is required at runtime", text)
        for source in registry["sources"]:
            with self.subTest(source=source["id"]):
                self.assertIn(source["repository"], text)
                self.assertIn(source["revision"], text)
                self.assertIn(source["license"], text)

        adr = ADR_PATH.read_text(encoding="utf-8")
        self.assertIn("Every source record includes an exact revision, licence", adr)


if __name__ == "__main__":
    unittest.main()
