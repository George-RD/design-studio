from pathlib import Path
import json
import re
import shutil
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ClaudeAdapterCompatibilityTests(unittest.TestCase):
    def read(self, path: str) -> str:
        return (ROOT / path).read_text()

    def body_after_frontmatter(self, path: str) -> str:
        text = self.read(path)
        parts = text.split("---", 2)
        self.assertEqual(len(parts), 3, f"{path} must keep frontmatter")
        return parts[2]

    def test_commands_only_translate_claude_invocation_to_canonical_entries(self):
        expected = {
            "commands/create.md": "skills/design-studio/workflow.yaml",
            "commands/review.md": "skills/design-studio/references/review/polish.md",
        }
        for path, entrypoint in expected.items():
            with self.subTest(path=path):
                text = self.read(path)
                frontmatter = text.split("---", 2)[1]
                body = self.body_after_frontmatter(path)
                self.assertIn("description: Optional Claude Code command adapter", frontmatter)
                self.assertNotRegex(
                    frontmatter,
                    r"(?:mechanical preflight|blind evaluation|design-system capture|readiness verdict)",
                )
                self.assertIn("Claude Code adapter", body)
                self.assertIn("skills/design-studio/SKILL.md", body)
                self.assertIn(entrypoint, body)
                self.assertIn("invocation metadata only", body)
                self.assertNotRegex(body, r"\b(?:REFINE|PIVOT|SHIP|HALT)\b")

    def test_agent_stubs_contain_discovery_metadata_and_one_canonical_pointer(self):
        expected = {
            "agents/design-agent.md": "skills/design-studio/agents/design-agent.md",
            "agents/evaluator.md": "skills/design-studio/agents/evaluator.md",
        }
        for path, canonical in expected.items():
            with self.subTest(path=path):
                text = self.read(path)
                body = self.body_after_frontmatter(path)
                self.assertIn("Optional Claude Code discovery stub", text)
                self.assertNotIn("<example>", text)
                self.assertIn(canonical, body)
                self.assertIn("plugin stub", body)
                self.assertIn("Load that file as the full system prompt", body)

    def test_portable_skill_tree_has_no_dependency_on_root_claude_adapter(self):
        skill_root = ROOT / "skills/design-studio"
        adapter_markers = (
            ".claude-plugin/",
            "commands/create.md",
            "commands/review.md",
        )
        for path in skill_root.rglob("*"):
            if not path.is_file() or path.suffix not in {".md", ".json", ".yaml", ".yml"}:
                continue
            text = path.read_text()
            for marker in adapter_markers:
                self.assertNotIn(marker, text, f"{path.relative_to(ROOT)} references root adapter {marker}")

        evals = self.read("skills/design-studio/evals/evals.json")
        self.assertNotIn(".claude-plugin/", evals)
        self.assertNotIn("commands/create.md", evals)
        self.assertNotIn("commands/review.md", evals)

    def test_isolated_skill_copy_preserves_supported_capability_without_adapters(self):
        required = [
            "SKILL.md",
            "invocation.md",
            "workflow.yaml",
            "runtime-contract.md",
            "method-router.json",
            "references/runtime-integrity.md",
            "agents/design-agent.md",
            "agents/evaluator.md",
        ]
        with tempfile.TemporaryDirectory() as temporary:
            isolated_root = Path(temporary)
            isolated_skill = isolated_root / "skills/design-studio"
            shutil.copytree(ROOT / "skills/design-studio", isolated_skill)

            for adapter_root in (".claude-plugin", "commands", "agents"):
                self.assertFalse((isolated_root / adapter_root).exists())
            for relative in required:
                self.assertTrue((isolated_skill / relative).is_file(), relative)

            workflow = (isolated_skill / "workflow.yaml").read_text()
            skill = (isolated_skill / "SKILL.md").read_text()
            self.assertIn("required: [file_io, shell, isolated_subagents]", workflow)
            for capability in ("file I/O", "shell", "isolated"):
                self.assertIn(capability, skill)

    def test_public_docs_make_plugin_optional_and_define_capable_host(self):
        readme = self.read("README.md")
        required = [
            "canonical, host-portable artifact",
            "copy `skills/design-studio/`",
            "does not reduce supported Design Studio capability",
            "file I/O",
            "shell access",
            "isolated subagents",
            "browser automation",
            "runnable target",
            "optional convenience",
            "claude plugin marketplace add George-RD/design-studio",
            "claude plugin install design-studio@design-studio",
        ]
        for marker in required:
            self.assertIn(marker, readme)

    def test_cli_deferral_is_a_durable_architecture_decision(self):
        adr = ROOT / "docs/decisions/0003-claude-adapter-and-deferred-cli.md"
        self.assertTrue(adr.is_file(), "ADR 0003 must record adapter and CLI policy")
        text = adr.read_text()
        required = [
            "Status:** Accepted",
            "optional, thin adapter",
            "skills/design-studio/SKILL.md",
            "skills/design-studio/workflow.yaml",
            "skills/design-studio/references/runtime-integrity.md",
            "stable human-facing command API",
            "repeated cross-host need",
            "own no business or design logic",
        ]
        for marker in required:
            self.assertIn(marker, text)

        decision_index = self.read("docs/decisions/README.md")
        self.assertIn("0003-claude-adapter-and-deferred-cli.md", decision_index)

    def test_plugin_metadata_is_adapter_only_and_versions_match(self):
        plugin = json.loads(self.read(".claude-plugin/plugin.json"))
        marketplace = json.loads(self.read(".claude-plugin/marketplace.json"))
        skill = self.read("skills/design-studio/SKILL.md")
        skill_version = re.search(r"^version:\s*([^\s]+)", skill, re.M).group(1)
        marketplace_plugin = next(p for p in marketplace["plugins"] if p["name"] == "design-studio")

        self.assertIn("Optional Claude Code adapter", plugin["description"])
        self.assertIn("adapter", marketplace_plugin["description"].lower())
        self.assertEqual(plugin["version"], skill_version)
        self.assertEqual(marketplace_plugin["version"], skill_version)


if __name__ == "__main__":
    unittest.main()
