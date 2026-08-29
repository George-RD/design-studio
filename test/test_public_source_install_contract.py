from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "validate-agent-skill-install.yml"
ADR = ROOT / "docs" / "decisions" / "0004-installer-compatibility-proof.md"


class PublicSourceInstallContractTests(unittest.TestCase):
    """Protect issue #76's public installation and installer-compatibility boundary."""

    def read(self, path: str) -> str:
        return (ROOT / path).read_text(encoding="utf-8")

    def test_pinned_exact_revision_proof_remains_blocking(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("clean-install:", workflow)
        self.assertIn('npx --yes skills@1.5.23 add "$GITHUB_WORKSPACE"', workflow)
        self.assertIn("agent: [codex, claude-code]", workflow)
        self.assertIn('cmp "$GITHUB_WORKSPACE/skills/design-studio/SKILL.md" "$installed_skill"', workflow)

    def test_pinned_public_source_proof_is_blocking_and_revision_clear(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("public-source-install:", workflow)
        self.assertIn("npx --yes skills@1.5.23 add George-RD/design-studio#main", workflow)
        self.assertIn("Public source George-RD/design-studio#main represents merged main", workflow)
        self.assertIn("PR head", workflow)
        self.assertIn("is not public yet", workflow)
        self.assertIn("is expected to match merged main commit", workflow)
        self.assertIn('node "$skill_root/runtime/mechanical/index.mjs"', workflow)
        self.assertIn('if [[ "$PUBLIC_PARITY" == "1" ]]; then', workflow)

        public_job = workflow.split("  public-source-install:\n", 1)[1].split(
            "\n  advisory-latest-installer:\n", 1
        )[0]
        self.assertNotIn("continue-on-error: true", public_job)
        self.assertIn("agent: [codex, claude-code]", public_job)
        self.assertIn('--agent "${{ matrix.agent }}"', public_job)

    def test_latest_public_source_proof_is_explicitly_advisory(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("advisory-latest-installer:", workflow)
        advisory_job = workflow.split("  advisory-latest-installer:\n", 1)[1]
        self.assertIn("continue-on-error: true", advisory_job)
        self.assertIn("npx --yes skills@latest add George-RD/design-studio#main", advisory_job)
        self.assertIn("agent: [codex, claude-code]", advisory_job)
        self.assertIn('--agent "${{ matrix.agent }}"', advisory_job)
        self.assertIn('node "$skill_root/runtime/mechanical/index.mjs"', advisory_job)
        self.assertIn("upstream installer release must not erase the known-good product proof", advisory_job)

    def test_docs_contract_installer_vs_runtime_and_no_registry_requirement(self) -> None:
        readme = self.read("README.md")
        runtime_boundary = self.read("docs/runtime-boundary.md")
        decisions = self.read("docs/decisions/README.md")

        self.assertIn("`npx skills` is the installer", readme)
        self.assertIn("not a Design Studio runtime dependency", readme)
        self.assertIn("public-source", runtime_boundary)
        self.assertIn("advisory", runtime_boundary)
        self.assertIn("0004", decisions)
        self.assertTrue(ADR.is_file())
        adr = ADR.read_text(encoding="utf-8")
        self.assertIn("no skills.sh registration or publishing step is required", adr)
        self.assertIn("codex", adr)
        self.assertIn("claude-code", adr)


if __name__ == "__main__":
    unittest.main()
