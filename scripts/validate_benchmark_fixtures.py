#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


SUITE_ROOT = Path("benchmarks") / "milestone-0"
EXPECTED_FIXTURES = {
    "marketing-surface": "new-marketing-surface",
    "product-overhaul": "existing-product-overhaul",
    "review-polish": "review-and-polish",
    "cinematic-experience": "new-visually-ambitious-experience",
}
EXPECTED_LANES = {
    "impeccable-alone",
    "design-studio-current",
    "design-studio-impeccable",
}
EXPECTED_METRICS = {
    "outputPreference",
    "taskClarity",
    "originality",
    "functionalDefects",
    "elapsedSeconds",
    "tokenCost",
    "toolCost",
    "failedSteps",
    "recoveryEffort",
}
LANE_TERMS = ("impeccable", "design studio", "design-studio-current", "design-studio-impeccable")


def load_json(path: Path, errors: list[str]) -> Any:
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        errors.append(f"missing JSON file: {path}")
    except json.JSONDecodeError as exc:
        errors.append(f"invalid JSON in {path}: {exc}")
    return {}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_keys(value: dict[str, Any], keys: set[str], label: str, errors: list[str]) -> None:
    missing = sorted(keys - set(value))
    if missing:
        errors.append(f"{label} is missing keys: {missing}")


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    suite_root = root / SUITE_ROOT
    manifest_path = suite_root / "manifest.json"
    lock_path = suite_root / "fixture-lock.json"
    manifest = load_json(manifest_path, errors)
    lock = load_json(lock_path, errors)

    if not isinstance(manifest, dict):
        errors.append("manifest.json must contain an object")
        return errors
    if not isinstance(lock, dict):
        errors.append("fixture-lock.json must contain an object")
        return errors

    require_keys(
        manifest,
        {"schemaVersion", "suite", "version", "frozenAt", "comparisonLanes", "requiredMetrics", "fixtures", "changePolicy"},
        "manifest.json",
        errors,
    )

    lane_ids = {
        lane.get("id")
        for lane in manifest.get("comparisonLanes", [])
        if isinstance(lane, dict)
    }
    if lane_ids != EXPECTED_LANES:
        errors.append(f"comparisonLanes must be exactly {sorted(EXPECTED_LANES)}; got {sorted(str(item) for item in lane_ids)}")

    metrics = set(manifest.get("requiredMetrics", []))
    if metrics != EXPECTED_METRICS:
        errors.append(f"requiredMetrics must be exactly {sorted(EXPECTED_METRICS)}; got {sorted(str(item) for item in metrics)}")

    fixture_entries = manifest.get("fixtures", [])
    if not isinstance(fixture_entries, list):
        errors.append("fixtures must be an array")
        fixture_entries = []

    seen_ids: set[str] = set()
    for entry in fixture_entries:
        if not isinstance(entry, dict):
            errors.append("each fixture entry must be an object")
            continue
        fixture_id = entry.get("id")
        relative_manifest = entry.get("path")
        if not isinstance(fixture_id, str) or not isinstance(relative_manifest, str):
            errors.append(f"fixture entry needs string id and path: {entry}")
            continue
        if fixture_id in seen_ids:
            errors.append(f"duplicate fixture id: {fixture_id}")
        seen_ids.add(fixture_id)

        fixture_path = suite_root / relative_manifest
        fixture = load_json(fixture_path, errors)
        if not isinstance(fixture, dict):
            errors.append(f"{relative_manifest} must contain an object")
            continue

        require_keys(
            fixture,
            {
                "schemaVersion",
                "id",
                "version",
                "kind",
                "title",
                "brief",
                "acceptance",
                "baseline",
                "viewports",
                "requiredCapabilities",
                "outputContract",
            },
            relative_manifest,
            errors,
        )

        if fixture.get("id") != fixture_id:
            errors.append(f"{relative_manifest} id does not match root manifest: {fixture.get('id')} != {fixture_id}")
        expected_kind = EXPECTED_FIXTURES.get(fixture_id)
        if fixture.get("kind") != expected_kind:
            errors.append(f"{relative_manifest} kind must be {expected_kind!r}; got {fixture.get('kind')!r}")
        if not isinstance(fixture.get("version"), int) or fixture.get("version", 0) < 1:
            errors.append(f"{relative_manifest} version must be a positive integer")

        fixture_dir = fixture_path.parent
        brief_value = fixture.get("brief")
        acceptance_value = fixture.get("acceptance")
        if not isinstance(brief_value, str) or not (fixture_dir / brief_value).is_file():
            errors.append(f"{relative_manifest} brief is missing: {brief_value}")
        else:
            brief_text = (fixture_dir / brief_value).read_text().lower()
            biased = [term for term in LANE_TERMS if term in brief_text]
            if biased:
                errors.append(f"{relative_manifest} brief must remain lane-neutral; found {biased}")

        if not isinstance(acceptance_value, str) or not (fixture_dir / acceptance_value).is_file():
            errors.append(f"{relative_manifest} acceptance file is missing: {acceptance_value}")
        else:
            acceptance = load_json(fixture_dir / acceptance_value, errors)
            if isinstance(acceptance, dict):
                require_keys(acceptance, {"mustDeliver", "mustNot", "functionalChecks", "evaluationFocus"}, f"{fixture_id} acceptance", errors)
                checks = acceptance.get("functionalChecks", [])
                if not isinstance(checks, list) or len(checks) < 4:
                    errors.append(f"{fixture_id} acceptance needs at least four functionalChecks")
                for index, check in enumerate(checks):
                    if not isinstance(check, dict) or not {"id", "action", "expected"}.issubset(check):
                        errors.append(f"{fixture_id} functionalChecks[{index}] needs id, action and expected")

        viewports = fixture.get("viewports")
        if viewports != ["1440x900", "1150x900", "390x844"]:
            errors.append(f"{relative_manifest} must use the frozen viewport list")

        baseline = fixture.get("baseline")
        if not isinstance(baseline, list):
            errors.append(f"{relative_manifest} baseline must be an array")
            baseline = []
        if fixture_id in {"product-overhaul", "review-polish"} and not baseline:
            errors.append(f"{relative_manifest} requires a runnable baseline")
        if fixture_id in {"marketing-surface", "cinematic-experience"} and baseline:
            errors.append(f"{relative_manifest} must remain a greenfield fixture without baseline files")
        for relative_baseline in baseline:
            baseline_path = fixture_dir / relative_baseline
            if not baseline_path.is_file():
                errors.append(f"{fixture_id} baseline file is missing: {relative_baseline}")

        output = fixture.get("outputContract")
        if not isinstance(output, dict):
            errors.append(f"{relative_manifest} outputContract must be an object")
        else:
            if output.get("entrypoint") != "index.html":
                errors.append(f"{relative_manifest} output entrypoint must be index.html")
            if output.get("mustRunWithoutBuildStep") is not True:
                errors.append(f"{relative_manifest} mustRunWithoutBuildStep must be true")
            if output.get("externalNetworkRequired") is not False:
                errors.append(f"{relative_manifest} externalNetworkRequired must be false")

    if seen_ids != set(EXPECTED_FIXTURES):
        errors.append(f"fixture ids must be exactly {sorted(EXPECTED_FIXTURES)}; got {sorted(seen_ids)}")

    lock_files = lock.get("files")
    if lock.get("algorithm") != "sha256" or not isinstance(lock_files, dict):
        errors.append("fixture-lock.json must declare sha256 and a files object")
        lock_files = {}

    actual_files = {
        path.relative_to(suite_root).as_posix()
        for path in suite_root.rglob("*")
        if path.is_file()
        and path.name != "fixture-lock.json"
        and (path.relative_to(suite_root).as_posix().startswith("fixtures/") or path.name in {"manifest.json", "README.md"})
    }
    locked_files = set(lock_files)
    missing_from_lock = sorted(actual_files - locked_files)
    stale_lock_entries = sorted(locked_files - actual_files)
    if missing_from_lock:
        errors.append(f"files missing from fixture lock: {missing_from_lock}")
    if stale_lock_entries:
        errors.append(f"stale fixture lock entries: {stale_lock_entries}")

    for relative_path in sorted(actual_files & locked_files):
        path = suite_root / relative_path
        expected = lock_files.get(relative_path)
        actual = sha256(path)
        if expected != actual:
            errors.append(f"hash mismatch for {relative_path}: expected {expected}, got {actual}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate frozen Milestone 0 benchmark fixtures.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root")
    args = parser.parse_args()

    errors = validate(args.root.resolve())
    if errors:
        for error in errors:
            print(f"ERROR {error}")
        print(f"\nBenchmark fixture validation failed with {len(errors)} error(s).")
        return 1

    print("Benchmark fixture contract passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
