from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "design-studio"
ROUTER_PATH = SKILL_ROOT / "method-router.json"
AUTHORITY_MAP_PATH = ROOT / "docs" / "method-authority-map.json"
SOURCES_PATH = ROOT / "docs" / "method-sources.json"

REQUIRED_LEAF_HEADINGS = {
    "## Purpose",
    "## Triggers",
    "## Required context",
    "## Outputs and handoff",
    "## Authority boundary",
    "## Failure behavior",
    "## Evaluation hooks",
}
SIGNAL_KEYS = {"task", "surface", "interaction", "evidence"}
REMOVED_COMPATIBILITY_LEAVES = {
    "references/planning.md",
    "references/evaluation.md",
    "references/iteration.md",
}
RETIRED_RUNTIME_PHRASES = {
    "npx impeccable",
    "Prefer Impeccable",
    "Impeccable availability",
    "business-copy-style",
}


class MethodKernelRoutingTests(unittest.TestCase):
    """Protect the progressive-disclosure contract from issues #43 and #51."""

    @staticmethod
    def load(path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    def test_router_declares_bounded_signal_based_routes(self) -> None:
        router = self.load(ROUTER_PATH)
        self.assertEqual(1, router["schemaVersion"])
        self.assertEqual("authoritative-method-router", router["status"])
        self.assertEqual(
            "docs/method-authority-map.json",
            router["authorityMap"],
        )
        self.assertEqual(
            "docs/decisions/0002-owned-method-kernel.md",
            router["governingDecision"],
        )

        routes = router["routes"]
        self.assertTrue(routes)
        self.assertEqual(len(routes), len({route["id"] for route in routes}))
        all_leaf_paths = {leaf["path"] for leaf in router["leaves"]}

        used_signal_kinds: set[str] = set()
        for route in routes:
            with self.subTest(route=route["id"]):
                self.assertEqual(SIGNAL_KEYS, set(route["signals"]))
                populated = {
                    kind
                    for kind, values in route["signals"].items()
                    if values
                }
                self.assertTrue(populated)
                used_signal_kinds.update(populated)
                self.assertTrue(route["leaves"])
                self.assertTrue(set(route["leaves"]).issubset(all_leaf_paths))
                self.assertTrue(route["handoff"].strip())

        self.assertEqual(SIGNAL_KEYS, used_signal_kinds)

    def test_every_declared_leaf_uses_the_standard_contract(self) -> None:
        router = self.load(ROUTER_PATH)
        paths = [leaf["path"] for leaf in router["leaves"]]
        self.assertEqual(len(paths), len(set(paths)))

        for leaf in router["leaves"]:
            path = SKILL_ROOT / leaf["path"]
            with self.subTest(path=leaf["path"]):
                self.assertTrue(path.is_file(), leaf["path"])
                text = path.read_text(encoding="utf-8")
                headings = {
                    line.strip()
                    for line in text.splitlines()
                    if line.startswith("## ")
                }
                self.assertTrue(
                    REQUIRED_LEAF_HEADINGS.issubset(headings),
                    f"{leaf['path']} missing {sorted(REQUIRED_LEAF_HEADINGS - headings)}",
                )
                self.assertTrue(leaf["conceptIds"])

    def test_adopted_methods_match_authority_map_and_record_exact_provenance(self) -> None:
        router = self.load(ROUTER_PATH)
        authority_map = self.load(AUTHORITY_MAP_PATH)
        registry = self.load(SOURCES_PATH)
        sources = {source["id"]: source for source in registry["sources"]}

        expected: set[tuple[str, str, str]] = set()
        forbidden: set[tuple[str, str, str]] = set()
        for concept in authority_map["concepts"]:
            for overlap in concept["externalOverlaps"]:
                key = (concept["conceptId"], overlap["sourceId"], overlap["methodName"])
                if overlap["disposition"] in {"adapt-local", "vendor-slice"}:
                    self.assertEqual("adopted", overlap["implementationStatus"])
                    expected.add(key)
                else:
                    forbidden.add(key)

        adopted = {
            (item["conceptId"], item["sourceId"], item["methodName"])
            for item in router["adoptedExternalMethods"]
        }
        self.assertEqual(expected, adopted)
        self.assertTrue(adopted.isdisjoint(forbidden))

        leaf_paths = {leaf["path"] for leaf in router["leaves"]}
        for item in router["adoptedExternalMethods"]:
            with self.subTest(method=item["methodName"]):
                self.assertIn(item["leaf"], leaf_paths)
                source = sources[item["sourceId"]]
                text = (SKILL_ROOT / item["leaf"]).read_text(encoding="utf-8")
                self.assertIn("## Source provenance", text)
                self.assertIn(item["sourceId"], text)
                self.assertIn(source["revision"], text)
                self.assertIn(source["license"], text)

    def test_installed_kernel_has_no_retired_parallel_runtime_paths(self) -> None:
        for relative in REMOVED_COMPATIBILITY_LEAVES:
            self.assertFalse((SKILL_ROOT / relative).exists(), relative)

        for path in SKILL_ROOT.rglob("*"):
            if not path.is_file() or path.suffix not in {".md", ".json", ".yaml"}:
                continue
            text = path.read_text(encoding="utf-8")
            for phrase in RETIRED_RUNTIME_PHRASES:
                with self.subTest(path=path.relative_to(ROOT), phrase=phrase):
                    self.assertNotIn(phrase, text)

    def test_always_loaded_skill_is_a_small_authority_kernel(self) -> None:
        text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertLess(len(text.encode("utf-8")), 8000)
        self.assertIn("method-router.json", text)
        self.assertIn("workflow.yaml", text)
        self.assertIn("Orchestrator is the sole decision owner", text)
        self.assertNotIn("iterations/<n>/", text)
        self.assertNotIn("| quick | 2 |", text)

    def test_source_blind_role_boundaries_remain_explicit(self) -> None:
        director = (SKILL_ROOT / "agents" / "design-agent.md").read_text(encoding="utf-8")
        evaluator = (SKILL_ROOT / "agents" / "evaluator.md").read_text(encoding="utf-8")
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("You must not receive or use:", director)
        self.assertIn("HTML, CSS, JavaScript, JSX", director)
        self.assertIn("source", evaluator.lower())
        self.assertIn("Visual Director never receives HTML", skill)
        self.assertIn("Evaluator never receives source", skill)

    def test_growth_arsenal_stays_outside_the_method_kernel(self) -> None:
        authority_map = self.load(AUTHORITY_MAP_PATH)
        boundaries = {
            item["domain"]: item["owner"]
            for item in authority_map["domainBoundaries"]
        }
        self.assertEqual("growth-arsenal", boundaries["copy-offer"])

        router = self.load(ROUTER_PATH)
        self.assertTrue(
            all(
                item["sourceId"] != "growth-arsenal"
                for item in router["adoptedExternalMethods"]
            )
        )
        copy_leaf = (SKILL_ROOT / "references" / "copy.md").read_text(encoding="utf-8")
        self.assertNotIn("business-copy-style", copy_leaf)
        self.assertIn("Growth Arsenal", copy_leaf)
        self.assertIn("outside the Design Studio method kernel", copy_leaf)


if __name__ == "__main__":
    unittest.main()
