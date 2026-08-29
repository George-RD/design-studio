from __future__ import annotations

import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "test" / "support" / "validate_clean_install.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_clean_install", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load validator from {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CleanInstallContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_validator()

    def copy_repository(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        for relative in (
            "runtime-surface.json",
            "skills/design-studio",
            ".claude-plugin",
            "agents",
            "commands",
            "README.md",
            "docs/index.html",
        ):
            source = REPO_ROOT / relative
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if source.is_dir():
                shutil.copytree(source, target)
            else:
                shutil.copy2(source, target)
        return temporary, root

    def test_repository_clean_install_contract_is_valid(self) -> None:
        self.assertEqual([], self.validator.validate(REPO_ROOT))

    def test_missing_runtime_surface_manifest_is_rejected(self) -> None:
        temporary, root = self.copy_repository()
        self.addCleanup(temporary.cleanup)
        (root / "runtime-surface.json").unlink()

        errors = self.validator.validate(root)

        self.assertTrue(any("missing runtime surface manifest" in error for error in errors), errors)

    def test_missing_in_skill_invocation_contract_is_rejected(self) -> None:
        temporary, root = self.copy_repository()
        self.addCleanup(temporary.cleanup)
        invocation = root / "skills" / "design-studio" / "invocation.md"
        invocation.unlink()

        errors = self.validator.validate(root)

        self.assertTrue(any("missing required reference" in error for error in errors), errors)

    def test_plugin_only_invocation_reference_is_rejected(self) -> None:
        temporary, root = self.copy_repository()
        self.addCleanup(temporary.cleanup)
        skill_path = root / "skills" / "design-studio" / "SKILL.md"
        skill = skill_path.read_text()
        skill = skill.replace("`invocation.md`", "`../../commands/create.md`")
        skill_path.write_text(skill)
        (root / "skills" / "design-studio" / "invocation.md").unlink()

        errors = self.validator.validate(root)

        self.assertTrue(any("plugin-only surface" in error for error in errors), errors)

    def test_installed_skill_cannot_require_external_design_skill(self) -> None:
        temporary, root = self.copy_repository()
        self.addCleanup(temporary.cleanup)
        invocation = root / "skills" / "design-studio" / "invocation.md"
        invocation.write_text(
            invocation.read_text()
            + "\nImpeccable is required to start a Design Studio run.\n"
        )

        errors = self.validator.validate(root)

        self.assertTrue(any("external design-skill dependency" in error for error in errors), errors)

    def test_installed_skill_cannot_call_repository_only_tooling(self) -> None:
        temporary, root = self.copy_repository()
        self.addCleanup(temporary.cleanup)
        invocation = root / "skills" / "design-studio" / "invocation.md"
        invocation.write_text(
            invocation.read_text()
            + "\nRun `python3 scripts/run_boundary_benchmark.py` before planning.\n"
        )

        errors = self.validator.validate(root)

        self.assertTrue(any("repository-only tooling dependency" in error for error in errors), errors)

    def test_optional_adapter_cannot_call_repository_only_tooling(self) -> None:
        temporary, root = self.copy_repository()
        self.addCleanup(temporary.cleanup)
        command = root / "commands" / "create.md"
        command.write_text(
            command.read_text()
            + "\nRun `python3 scripts/run_boundary_benchmark.py` before invoking the skill.\n"
        )

        errors = self.validator.validate(root)

        self.assertTrue(any("repository-only tooling dependency" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
