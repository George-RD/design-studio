from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "skills-lock.json"


def skill_folder_hash(skill_dir: Path) -> str:
    """Match the deterministic full-directory hash used by the skills CLI."""
    digest = hashlib.sha256()
    files = sorted(
        (path for path in skill_dir.rglob("*") if path.is_file()),
        key=lambda path: path.relative_to(skill_dir).as_posix().casefold(),
    )
    for path in files:
        digest.update(path.relative_to(skill_dir).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


class EngineeringSkillManagementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
        cls.skills = cls.lock["skills"]

    def test_lock_represents_the_full_installed_upstream_set(self) -> None:
        self.assertEqual(1, self.lock["version"])
        self.assertEqual(37, len(self.skills))

        for name, metadata in self.skills.items():
            with self.subTest(skill=name):
                self.assertEqual("mattpocock/skills", metadata["source"])
                self.assertEqual("github", metadata["sourceType"])
                skill_dir = ROOT / ".agents" / "skills" / name
                self.assertTrue((skill_dir / "SKILL.md").is_file())
                self.assertEqual(metadata["computedHash"], skill_folder_hash(skill_dir))

    def test_host_links_cover_every_locked_skill(self) -> None:
        expected = set(self.skills)
        for directory in (ROOT / ".claude" / "skills", ROOT / "skills"):
            links = {path.name for path in directory.iterdir() if path.is_symlink()}
            with self.subTest(directory=directory):
                self.assertEqual(expected, links)
                for name in links:
                    expected_target = (ROOT / ".agents" / "skills" / name).resolve()
                    self.assertEqual(expected_target, (directory / name).resolve())

        self.assertTrue((ROOT / "skills" / "design-studio").is_dir())
        self.assertFalse((ROOT / "skills" / "design-studio").is_symlink())

    def test_repository_authority_stays_outside_locked_skill_directories(self) -> None:
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
        management = (ROOT / ".agents" / "skills" / "README.md").read_text(
            encoding="utf-8"
        )
        updates = (ROOT / "docs" / "agents" / "skill-updates.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("GitHub Issues are the executable backlog", agents)
        self.assertIn("docs/agents/work-selection.md", agents)
        self.assertIn("docs/agents/planning.md", agents)
        self.assertIn("docs/agents/code-review.md", agents)
        self.assertIn("docs/agents/codebase-design.md", agents)
        self.assertIn("docs/agents/skill-updates.md", agents)
        self.assertIn("do not patch their directories locally", agents)
        self.assertNotIn("## Work selection", roadmap)
        self.assertNotIn("- [ ]", roadmap)
        self.assertIn("docs/agents/skill-updates.md", management)
        self.assertIn("npx skills@latest experimental_install", updates)
        self.assertIn("not an immutable commit reference", updates)


if __name__ == "__main__":
    unittest.main()
