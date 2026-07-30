from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "validate_benchmark_fixtures.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_benchmark_fixtures", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load validator from {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class BenchmarkFixtureContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_validator()

    def copy_benchmarks(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        shutil.copytree(REPO_ROOT / "benchmarks", root / "benchmarks")
        return temporary, root

    def rewrite_lock_hash(self, root: Path, relative_path: str) -> None:
        lock_path = root / "benchmarks" / "milestone-0" / "fixture-lock.json"
        lock = json.loads(lock_path.read_text())
        target = root / "benchmarks" / "milestone-0" / relative_path
        lock["files"][relative_path] = sha256(target)
        lock_path.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n")

    def test_repository_fixture_set_is_valid(self) -> None:
        self.assertEqual([], self.validator.validate(REPO_ROOT))

    def test_locked_fixture_content_cannot_change_silently(self) -> None:
        temporary, root = self.copy_benchmarks()
        self.addCleanup(temporary.cleanup)
        brief = root / "benchmarks" / "milestone-0" / "fixtures" / "marketing-surface" / "brief.md"
        brief.write_text(brief.read_text() + "\nUnversioned mutation.\n")

        errors = self.validator.validate(root)

        self.assertTrue(any("hash mismatch" in error for error in errors), errors)

    def test_briefs_reject_lane_specific_instructions_even_when_relocked(self) -> None:
        temporary, root = self.copy_benchmarks()
        self.addCleanup(temporary.cleanup)
        relative = "fixtures/marketing-surface/brief.md"
        brief = root / "benchmarks" / "milestone-0" / relative
        brief.write_text(brief.read_text() + "\nUse Design Studio for this lane.\n")
        self.rewrite_lock_hash(root, relative)

        errors = self.validator.validate(root)

        self.assertTrue(any("lane-neutral" in error for error in errors), errors)

    def test_overhaul_fixture_requires_its_declared_baseline(self) -> None:
        temporary, root = self.copy_benchmarks()
        self.addCleanup(temporary.cleanup)
        relative = "fixtures/product-overhaul/input/app.js"
        target = root / "benchmarks" / "milestone-0" / relative
        target.unlink()
        lock_path = root / "benchmarks" / "milestone-0" / "fixture-lock.json"
        lock = json.loads(lock_path.read_text())
        del lock["files"][relative]
        lock_path.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n")

        errors = self.validator.validate(root)

        self.assertTrue(any("baseline file is missing" in error for error in errors), errors)

    def test_all_roadmap_metrics_remain_required(self) -> None:
        temporary, root = self.copy_benchmarks()
        self.addCleanup(temporary.cleanup)
        manifest_path = root / "benchmarks" / "milestone-0" / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["requiredMetrics"].remove("recoveryEffort")
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

        errors = self.validator.validate(root)

        self.assertTrue(any("requiredMetrics" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
