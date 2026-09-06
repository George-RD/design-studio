from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class CapabilityGateBrowserWiringTests(unittest.TestCase):
    def test_public_gate_preserves_browser_failure_evidence(self) -> None:
        """Reach the real browser runner through the public Python gate without AI calls."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            site = root / "empty-site"
            site.mkdir()
            evidence = root / "evidence"
            probe = """
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import run_copilot_cli_agent_capability_gate as gate
try:
    gate.core.default_browser_runner(Path(sys.argv[2]), Path(sys.argv[3]))
except (gate.ContractError, gate.CapabilityBlocked):
    pass
"""
            result = subprocess.run(
                [sys.executable, "-c", probe, str(ROOT / "scripts"), str(site), str(evidence)],
                cwd=root, text=True, capture_output=True, check=False, timeout=30,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            report_path = evidence / "browser/browser-report.json"
            self.assertTrue(report_path.is_file(), "browser entrypoint must emit its failure report")
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual("failed", report["status"])
            self.assertEqual("contract", report["phase"], report)
            self.assertNotIn("MODULE_NOT_FOUND", (evidence / "browser/stderr.log").read_text())


if __name__ == "__main__":
    unittest.main()
