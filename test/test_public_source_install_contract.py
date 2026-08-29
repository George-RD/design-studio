from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "validate-agent-skill-install.yml"
ADR = ROOT / "docs" / "decisions" / "0004-installer-compatibility-proof.md"


class PublicSourceInstallContractTests(unittest.TestCase):
    """Protect issue #76's public installation and installer-compatibility boundary."""

    def read(self, path: str) -> str:
        return (ROOT / path).read_text(encoding="utf-8")

    def job_block(self, workflow: str, name: str) -> str:
        match = re.search(
            rf"(?ms)^  {re.escape(name)}:\n(.*?)(?=^  [A-Za-z0-9_-]+:\n|\Z)",
            workflow,
        )
        self.assertIsNotNone(match, f"missing workflow job: {name}")
        return match.group(1)

    def assert_public_install_checks(self, job: str) -> None:
        required = [
            'test -f "$skill_root/invocation.md"',
            'test -f "$skill_root/workflow.yaml"',
            'test -f "$skill_root/runtime-contract.md"',
            'test -f "$skill_root/runtime/README.md"',
            'test -f "$skill_root/runtime/mechanical/index.mjs"',
            'test -f "$skill_root/references/runtime-integrity.md"',
            'node "$skill_root/runtime/mechanical/index.mjs"',
            'result.detector !== "design-studio"',
            "for forbidden in scripts benchmarks test .github commands .claude-plugin",
        ]
        for marker in required:
            with self.subTest(marker=marker):
                self.assertIn(marker, job)

    def test_pinned_exact_revision_proof_remains_blocking(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        clean_install = self.job_block(workflow, "clean-install")
        self.assertNotIn("continue-on-error: true", clean_install)
        self.assertIn('npx --yes skills@1.5.23 add "$GITHUB_WORKSPACE"', clean_install)
        self.assertIn("agent: [codex, claude-code]", clean_install)
        self.assertIn(
            'cmp "$GITHUB_WORKSPACE/skills/design-studio/SKILL.md" "$installed_skill"',
            clean_install,
        )

    def test_pinned_public_source_proof_is_blocking_and_revision_clear(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        public_job = self.job_block(workflow, "public-source-install")

        self.assertNotIn("continue-on-error: true", public_job)
        self.assertIn("npx --yes skills@1.5.23 add George-RD/design-studio", public_job)
        self.assertNotIn("George-RD/design-studio#", public_job)
        self.assertIn("resolves the repository default branch main", public_job)
        self.assertIn("PR head", public_job)
        self.assertIn("is not public yet", public_job)
        self.assertIn("is expected to resolve merged main commit", public_job)
        self.assertIn('if [[ "$PUBLIC_PARITY" == "1" ]]; then', public_job)
        self.assertIn("agent: [codex, claude-code]", public_job)
        self.assertIn('--agent "${{ matrix.agent }}"', public_job)
        self.assert_public_install_checks(public_job)

    def test_latest_public_source_proof_is_explicitly_advisory(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        advisory_job = self.job_block(workflow, "advisory-latest-installer")

        self.assertIn("continue-on-error: true", advisory_job)
        self.assertIn("npx --yes skills@latest add George-RD/design-studio", advisory_job)
        self.assertNotIn("George-RD/design-studio#", advisory_job)
        self.assertIn("agent: [codex, claude-code]", advisory_job)
        self.assertIn('--agent "${{ matrix.agent }}"', advisory_job)
        self.assertIn(
            "upstream installer release must not erase the known-good product proof",
            advisory_job,
        )
        self.assert_public_install_checks(advisory_job)

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
