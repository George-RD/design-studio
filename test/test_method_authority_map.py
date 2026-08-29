from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MAP_PATH = ROOT / "docs" / "method-authority-map.json"
COMPANION_PATH = ROOT / "docs" / "method-authority-map.md"
SOURCES_PATH = ROOT / "docs" / "method-sources.json"
MIGRATION_PATH = ROOT / "docs" / "migration-map.json"
ADR_PATH = ROOT / "docs" / "decisions" / "0002-owned-method-kernel.md"

EXPECTED_DOMAINS = {
    "design-engineering": "design-studio",
    "orchestration-runtime": "design-studio",
    "copy-offer": "growth-arsenal",
}


class MethodAuthorityMapTests(unittest.TestCase):
    """Protect the concept-level authority and provenance contract from #47/#51."""

    @staticmethod
    def load(path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    def test_map_declares_governing_contract(self) -> None:
        record = self.load(MAP_PATH)
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

    def test_every_inventory_concept_resolves_to_one_existing_authority(self) -> None:
        record = self.load(MAP_PATH)
        migration = self.load(MIGRATION_PATH)
        baseline = {item["id"]: item for item in migration["conceptMap"]}
        concepts = {item["conceptId"]: item for item in record["concepts"]}
        self.assertEqual(len(concepts), len(record["concepts"]))
        self.assertEqual(set(baseline), set(concepts))

        for concept_id, concept in concepts.items():
            with self.subTest(concept=concept_id):
                before = baseline[concept_id]
                authority = concept["authority"]
                self.assertEqual(before["canonicalOwner"], authority["owner"])
                if authority["owner"] == "design-studio":
                    self.assertEqual({"owner", "kind", "canonicalPath"}, set(authority))
                    self.assertEqual("canonical-local", authority["kind"])
                    path = authority["canonicalPath"]
                else:
                    self.assertEqual({"owner", "kind", "localBoundaryPath"}, set(authority))
                    self.assertEqual("growth-arsenal", authority["owner"])
                    self.assertEqual("external-domain", authority["kind"])
                    path = authority["localBoundaryPath"]

                self.assertIn(path, before["localAuthorities"])
                self.assertTrue((ROOT / path).is_file(), path)

                expected_sources = {item["source"] for item in before["externalOverlaps"]}
                mapped_sources = {item["sourceId"] for item in concept["externalOverlaps"]}
                self.assertEqual(expected_sources, mapped_sources)

                for supporting in concept.get("supportingReferences", []):
                    self.assertTrue((ROOT / supporting).is_file(), supporting)

    def test_domain_ownership_and_routing_are_explicit(self) -> None:
        record = self.load(MAP_PATH)
        boundaries = {item["domain"]: item["owner"] for item in record["domainBoundaries"]}
        self.assertEqual(EXPECTED_DOMAINS, boundaries)

        for concept in record["concepts"]:
            with self.subTest(concept=concept["conceptId"]):
                domain = concept["domain"]
                self.assertIn(domain, EXPECTED_DOMAINS)
                self.assertEqual(EXPECTED_DOMAINS[domain], concept["authority"]["owner"])
                routing = concept["routing"]
                self.assertIn(routing["mode"], {"always", "routed", "composition"})
                self.assertTrue(routing["triggers"])
                self.assertTrue(all(isinstance(item, str) and item.strip() for item in routing["triggers"]))
                self.assertIs(concept["upstreamRuntimeRequired"], False)

    def test_external_overlaps_resolve_to_pinned_source_provenance(self) -> None:
        record = self.load(MAP_PATH)
        registry = self.load(SOURCES_PATH)
        sources = {item["id"]: item for item in registry["sources"]}
        permitted = set(record["permittedExternalDispositions"])
        seen: set[tuple[str, str, str]] = set()

        for concept in record["concepts"]:
            for overlap in concept["externalOverlaps"]:
                key = (concept["conceptId"], overlap["sourceId"], overlap["methodName"])
                with self.subTest(concept=concept["conceptId"], method=overlap["methodName"]):
                    self.assertNotIn(key, seen)
                    seen.add(key)
                    source = sources[overlap["sourceId"]]
                    self.assertRegex(source["revision"], r"^[0-9a-f]{40}$")
                    self.assertTrue(source["repository"].startswith("https://github.com/"))
                    self.assertTrue(source["license"])
                    self.assertIs(source["runtimeDependency"], False)
                    self.assertIn(overlap["disposition"], permitted)
                    self.assertTrue(overlap["upstreamPathAtRevision"].strip())
                    self.assertTrue(overlap["modificationProvenance"].strip())
                    self.assertTrue(overlap["evidenceBasis"])
                    if overlap["disposition"] in {"adapt-local", "vendor-slice"}:
                        self.assertIn(overlap["implementationStatus"], {"candidate", "adopted"})
                    else:
                        self.assertEqual("not-adopted", overlap["implementationStatus"])

        self.assertTrue(seen)

    def test_duplicates_and_comparisons_have_bounded_followups(self) -> None:
        record = self.load(MAP_PATH)
        self.assertTrue(record["duplicateResolutions"])
        for resolution in record["duplicateResolutions"]:
            self.assertIn(resolution["action"], {"supersede", "delete-after"})
            self.assertTrue((ROOT / resolution["duplicatePath"]).exists())
            self.assertTrue(resolution["retainedAuthorities"])
            self.assertTrue(all((ROOT / path).exists() for path in resolution["retainedAuthorities"]))
            self.assertTrue(resolution["condition"].strip())

        for comparison in record["targetedComparisons"]:
            self.assertTrue(comparison["id"].strip())
            self.assertTrue(comparison["conceptId"].strip())
            self.assertTrue(comparison["question"].strip())
            self.assertTrue(comparison["evidenceNeeded"].strip())

    def test_human_companion_exposes_source_pins_and_boundaries(self) -> None:
        text = COMPANION_PATH.read_text(encoding="utf-8")
        registry = self.load(SOURCES_PATH)
        self.assertIn("# Method authority map", text)
        self.assertIn("Growth Arsenal", text)
        self.assertIn("No upstream repository is required at runtime", text)
        for source in registry["sources"]:
            self.assertIn(source["repository"], text)
            self.assertIn(source["revision"], text)
            self.assertIn(source["license"], text)

        adr = ADR_PATH.read_text(encoding="utf-8")
        self.assertIn("Every source record includes an exact revision, licence", adr)


if __name__ == "__main__":
    unittest.main()
